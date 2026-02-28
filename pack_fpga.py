#!/usr/bin/env python3
"""
FPGA二进制文件打包工具
基于Makefile中的pack命令功能实现，使用Python重写
支持自定义bootgen路径、FSBL、uboot、bit文件路径
"""

import os
import sys
import argparse
import subprocess
import shutil
import hashlib
import datetime
import re
from pathlib import Path

# 默认配置
DEFAULT_BOOTGEN_PATH = r"C:\Xilinx\SDK\2018.2\bin\bootgen.bat"
DEFAULT_FPGA_ARCH = "zynq"
DEFAULT_BIT_DIR = r"build\bitstreams"
DEFAULT_BIT_NAME = "system_wrapper.bit"
DEFAULT_FSBL_PATH = r"bin\FSBL.elf"
DEFAULT_UBOOT_PATH = r"bin\u-boot.elf"
DEFAULT_VERSION_FILE = r"fpga_project.yaml"
DEFAULT_OUTPUT_DIR = "bin"
DEFAULT_PROJECT_NAME = "project"
DEFAULT_IMPL_NUM = "impl_1"
DEFAULT_FPGA_TOP = "system_wrapper"

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='FPGA二进制文件打包工具')
    parser.add_argument('--bootgen', default=DEFAULT_BOOTGEN_PATH,
                        help=f'bootgen.bat路径 (默认: {DEFAULT_BOOTGEN_PATH})')
    parser.add_argument('--fsbl', default=DEFAULT_FSBL_PATH,
                        help=f'FSBL.elf路径 (默认: {DEFAULT_FSBL_PATH})')
    parser.add_argument('--uboot', default=DEFAULT_UBOOT_PATH,
                        help=f'u-boot.elf路径 (默认: {DEFAULT_UBOOT_PATH})')
    parser.add_argument('--bit',
                        help=f'bit文件路径 (默认: {DEFAULT_BIT_DIR}\\{DEFAULT_BIT_NAME})')
    parser.add_argument('--arch', default=DEFAULT_FPGA_ARCH,
                        help=f'FPGA架构 (默认: {DEFAULT_FPGA_ARCH})')
    parser.add_argument('--version-file', default=DEFAULT_VERSION_FILE,
                        help=f'版本文件路径 (默认: {DEFAULT_VERSION_FILE})')
    parser.add_argument('--output-dir', default=DEFAULT_OUTPUT_DIR,
                        help=f'输出目录 (默认: {DEFAULT_OUTPUT_DIR})')
    parser.add_argument('--fpga-top', default=DEFAULT_FPGA_TOP,
                        help=f'FPGA顶层模块名 (默认: {DEFAULT_FPGA_TOP})')
    parser.add_argument('--no-copy-bit', action='store_true',
                        help='不复制bit文件到输出目录，直接使用原路径')
    parser.add_argument('--keep-bif', action='store_true',
                        help='保留临时BIF文件（默认删除）')
    parser.add_argument('--dry-run', action='store_true',
                        help='仅显示将要执行的命令，不实际执行')
    parser.add_argument('--pure-fpga', action='store_true',
                        help='纯FPGA模式，不包含FSBL和uboot')

    return parser.parse_args()

def ensure_dir(path):
    """确保目录存在"""
    Path(path).mkdir(parents=True, exist_ok=True)

def read_version_file(filepath):
    """从YAML文件读取版本号，返回版本字符串（如"V26.02.0.0.2"）"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        # 从YAML中提取版本号，格式: version: 26.02.0.0.2
        match = re.search(r'version:\s*([\d.]+)', content)
        if match:
            version_str = match.group(1)
            # 确保版本号格式为XX.XX.X.X.X（5部分）
            parts = version_str.split('.')
            if len(parts) == 5:
                # 添加V前缀以保持与现有命名一致
                return f"V{version_str}"
            else:
                print(f"警告: 版本号格式不正确，应为XX.XX.X.X.X: {version_str}")
                return "V00.00.0.0.0"
        else:
            print(f"警告: 无法从YAML文件提取版本号: {filepath}")
            return "V00.00.0.0.0"
    except Exception as e:
        print(f"错误: 读取YAML版本文件失败: {e}")
        return "V00.00.0.0.0"

def get_git_head():
    """获取当前git HEAD的前7位"""
    try:
        result = subprocess.run(['git', 'rev-parse', 'HEAD'],
                               capture_output=True, text=True, check=True)
        full_hash = result.stdout.strip()
        return full_hash[:7] if len(full_hash) >= 7 else "0000000"
    except Exception as e:
        print(f"警告: 获取git HEAD失败: {e}")
        return "0000000"

def get_current_date():
    """返回当前日期的月日格式，如"0227"（2月27日）"""
    now = datetime.datetime.now()
    return f"{now.month:02d}{now.day:02d}"

def calculate_md5(filepath):
    """计算文件的MD5哈希值"""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"错误: 计算MD5失败: {e}")
        return "0" * 32

def extract_timestamp_from_bit(bit_path):
    """从bit文件中提取时间戳（格式HH:MM:SS）"""
    try:
        with open(bit_path, 'rb') as f:
            data = f.read(500)  # 读取前500字节，足够包含头部

            # 搜索时间戳模式：两个数字，冒号，两个数字，冒号，两个数字
            # 对应字节模式：\d\d:\d\d:\d\d
            import re
            # 使用正则表达式在字节数据中搜索模式
            # re.DOTALL使.匹配任何字符，包括换行
            pattern = rb'(\d\d):(\d\d):(\d\d)'
            match = re.search(pattern, data)
            if match:
                timestamp_bytes = match.group(0)
                if len(timestamp_bytes) == 8:
                    return timestamp_bytes
                else:
                    print(f"警告: 找到的时间戳长度不正确: {timestamp_bytes}")

            # 如果正则匹配失败，回退到固定偏移110（向后兼容）
            if len(data) >= 118:
                f.seek(110)
                timestamp_bytes = f.read(8)
                if len(timestamp_bytes) == 8:
                    # 验证格式：应该是数字和冒号
                    if all(48 <= b <= 57 or b == 58 for b in timestamp_bytes):  # 0-9或:
                        return timestamp_bytes

            print(f"警告: 无法从bit文件提取时间戳: {bit_path}")
            return b'00:00:00'  # 默认值
    except Exception as e:
        print(f"警告: 提取bit文件时间戳失败: {e}")
        return b'00:00:00'

def fix_bin_timestamp(bin_path, bit_path):
    """修复bin文件的时间戳，使其与bit文件一致"""
    try:
        # 从bit文件获取时间戳
        timestamp = extract_timestamp_from_bit(bit_path)

        with open(bin_path, 'r+b') as f:  # 读写二进制模式
            data = f.read()

            # 在bin文件中搜索时间戳模式
            import re
            pattern = rb'(\d\d):(\d\d):(\d\d)'
            match = re.search(pattern, data)
            if match:
                current = match.group(0)
                if current != timestamp:
                    # 替换时间戳
                    start = match.start()
                    f.seek(start)
                    f.write(timestamp)
                    print(f"修复bin文件时间戳: {current.decode('ascii', errors='ignore')} -> {timestamp.decode('ascii', errors='ignore')}")
                    return True
                else:
                    # 时间戳已相同，无需修复
                    return True
            else:
                # 未找到时间戳模式，尝试固定偏移110
                if len(data) >= 118:
                    f.seek(110)
                    current = f.read(8)
                    if current != timestamp:
                        f.seek(110)
                        f.write(timestamp)
                        print(f"修复bin文件时间戳(固定偏移): {current.decode('ascii', errors='ignore')} -> {timestamp.decode('ascii', errors='ignore')}")
                        return True
                print(f"警告: 在bin文件中未找到时间戳模式: {bin_path}")
                return False
    except Exception as e:
        print(f"警告: 修复bin文件时间戳失败: {e}")
        return False

def create_bif_file(bif_path, arch, bootloader, bitfile, uboot, pure_fpga=False):
    """创建BIF文件"""
    if pure_fpga:
        # 纯FPGA模式，只包含bit文件
        content = f"""//arch = {arch}; split = false; format = BIN
the_ROM_image:
{{
    {bitfile}
}}"""
    else:
        # 完整Zynq模式，包含bootloader和uboot
        content = f"""//arch = {arch}; split = false; format = BIN
the_ROM_image:
{{
    [bootloader]{bootloader}
    {bitfile}
    {uboot}
}}"""
    with open(bif_path, 'w') as f:
        f.write(content)
    print(f"创建BIF文件: {bif_path}")
    return True

def run_bootgen(bootgen_path, bif_path, arch, output_bin, dry_run=False):
    """运行bootgen.bat生成bin文件"""
    cmd = [bootgen_path, '-image', bif_path, '-arch', arch, '-o', output_bin, '-w']
    print(f"执行命令: {' '.join(cmd)}")

    if dry_run:
        return True

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("bootgen执行成功")
        if result.stdout:
            print(f"bootgen输出: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"错误: bootgen执行失败，返回码: {e.returncode}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"错误: 执行bootgen时发生异常: {e}")
        return False

def find_ltx_file(bit_path):
    """查找对应的.ltx文件"""
    bit_dir = os.path.dirname(bit_path)
    bit_name = os.path.basename(bit_path)
    ltx_name = os.path.splitext(bit_name)[0] + ".ltx"

    # 首先在bit文件同目录查找
    ltx_path = os.path.join(bit_dir, ltx_name)
    if os.path.exists(ltx_path):
        return ltx_path

    # 然后在build/bitstreams目录查找
    ltx_path = os.path.join("build", "bitstreams", ltx_name)
    if os.path.exists(ltx_path):
        return ltx_path

    # 最后在project目录查找（Makefile中的路径）
    project_ltx = os.path.join(DEFAULT_PROJECT_NAME, DEFAULT_PROJECT_NAME + ".runs",
                              DEFAULT_IMPL_NUM, ltx_name)
    if os.path.exists(project_ltx):
        return project_ltx

    return None

def main():
    args = parse_arguments()

    # 确定输入文件路径（可能是.bit或.bin）
    if args.bit:
        input_file = args.bit
    else:
        # 默认bit文件路径
        input_file = os.path.join(DEFAULT_BIT_DIR, DEFAULT_BIT_NAME)

    if not os.path.exists(input_file):
        print(f"错误: 输入文件不存在: {input_file}")
        sys.exit(1)

    # 确定文件扩展名
    file_ext = os.path.splitext(input_file)[1].lower()
    input_is_bin = (file_ext == '.bin')
    input_is_bit = (file_ext == '.bit')
    if not input_is_bin and not input_is_bit:
        print(f"警告: 输入文件扩展名不是.bit或.bin: {input_file}")
        # 继续尝试处理，但可能失败

    # 确保输出目录存在
    ensure_dir(args.output_dir)

    # 复制输入文件到输出目录（除非指定不复制）
    if args.no_copy_bit:
        file_in_output = input_file
        if input_is_bin:
            print(f"警告: 输入文件是bin文件且使用了--no-copy-bit选项，重命名将移动原始文件: {input_file}")
    else:
        file_in_output = os.path.join(args.output_dir, os.path.basename(input_file))
        if not args.dry_run and input_file != file_in_output:
            print(f"复制输入文件: {input_file} -> {file_in_output}")
            shutil.copy2(input_file, file_in_output)

    # 确定是否为纯FPGA模式
    pure_fpga = args.pure_fpga
    # 如果未显式指定pure_fpga，但fsbl和uboot文件都不存在，则自动检测为纯FPGA模式
    if not pure_fpga and not args.pure_fpga:
        # 检查默认路径下的文件是否存在，且用户未显式覆盖fsbl/uboot参数
        # 如果fsbl和uboot都不存在，则可能是纯FPGA工程
        if (args.fsbl == DEFAULT_FSBL_PATH and args.uboot == DEFAULT_UBOOT_PATH and
            not os.path.exists(args.fsbl) and not os.path.exists(args.uboot)):
            pure_fpga = True
            print("检测到FSBL和uboot文件不存在，自动启用纯FPGA模式")

    # 调整架构：纯FPGA模式默认使用fpga架构
    if pure_fpga and args.arch == DEFAULT_FPGA_ARCH:
        args.arch = "fpga"
        print(f"纯FPGA模式，设置架构为: {args.arch}")

    # 纯FPGA模式下，不需要检查FSBL和uboot文件
    if not pure_fpga:
        # 检查FSBL和uboot文件是否存在
        if not os.path.exists(args.fsbl):
            print(f"警告: FSBL文件不存在: {args.fsbl}")
        if not os.path.exists(args.uboot):
            print(f"警告: u-boot文件不存在: {args.uboot}")
    else:
        print("纯FPGA模式，跳过FSBL和uboot检查")

    # 创建临时BIF文件路径（仅在需要时使用）
    bif_path = os.path.join(args.output_dir, "create_bin.bif")

    # 根据输入文件类型决定处理流程
    if input_is_bin:
        # 直接使用现有的bin文件
        print(f"输入文件是bin文件，跳过bootgen步骤")
        initial_bin = file_in_output
        # 不需要BIF文件和bootgen
        bif_needed = False
    else:
        # 输入是bit文件或其他，需要运行bootgen
        bif_needed = True
        # 创建BIF文件（根据是否为纯FPGA模式）
        if not create_bif_file(bif_path, args.arch, args.fsbl, file_in_output, args.uboot, pure_fpga):
            sys.exit(1)

        # 输出bin文件路径（初始名称）
        initial_bin = os.path.join(args.output_dir, f"{args.fpga_top}.bin")

        # 运行bootgen
        if not run_bootgen(args.bootgen, bif_path, args.arch, initial_bin, args.dry_run):
            if not args.keep_bif:
                if os.path.exists(bif_path) and not args.dry_run:
                    os.remove(bif_path)
            sys.exit(1)

        # 删除临时BIF文件（除非指定保留）
        if not args.keep_bif and os.path.exists(bif_path) and not args.dry_run:
            os.remove(bif_path)
            print(f"删除临时BIF文件: {bif_path}")

    # 如果是dry-run模式，到此结束
    if args.dry_run:
        print("dry-run模式，跳过后续步骤")
        return

    # 修复bin文件时间戳以确保MD5一致性
    if not args.dry_run:
        # 确定bit文件路径用于时间戳修复
        bit_for_timestamp = None
        if input_is_bit:
            # 输入是bit文件，使用原始bit文件
            bit_for_timestamp = input_file
        elif input_is_bin:
            # 输入是bin文件，尝试查找对应的bit文件
            # 首先尝试同目录同名的.bit文件
            possible_bit = os.path.splitext(input_file)[0] + '.bit'
            if os.path.exists(possible_bit):
                bit_for_timestamp = possible_bit
            else:
                # 尝试默认bit文件路径
                default_bit = os.path.join(DEFAULT_BIT_DIR, DEFAULT_BIT_NAME)
                if os.path.exists(default_bit):
                    bit_for_timestamp = default_bit
                else:
                    print("警告: 无法找到对应的bit文件用于时间戳修复，MD5可能不一致")

        if bit_for_timestamp and os.path.exists(bit_for_timestamp):
            if not fix_bin_timestamp(initial_bin, bit_for_timestamp):
                print("警告: 时间戳修复失败，MD5可能不一致")
        else:
            print("警告: 未找到bit文件用于时间戳修复，MD5可能不一致")

    # 计算生成的bin文件的MD5
    if not os.path.exists(initial_bin):
        print(f"错误: 生成的bin文件不存在: {initial_bin}")
        sys.exit(1)

    md5_full = calculate_md5(initial_bin)
    md5_short = md5_full[:6]
    print(f"bin文件MD5: {md5_full}")
    print(f"MD5前6位: {md5_short}")

    # 读取版本号
    version_str = read_version_file(args.version_file)
    # 使用完整的版本字符串（包含V前缀），如"V25.09.0.0.1"
    ver_part = version_str  # 直接使用，不截断

    # 获取git HEAD
    git_head = get_git_head()

    # 获取当前日期
    current_date = get_current_date()

    # 构建新文件名
    new_basename = f"{ver_part}_{current_date}_{git_head}_{md5_short}"
    new_bin_name = f"{new_basename}.bin"
    new_bin_path = os.path.join(args.output_dir, new_bin_name)

    # 重命名bin文件
    print(f"重命名bin文件: {os.path.basename(initial_bin)} -> {new_bin_name}")
    os.rename(initial_bin, new_bin_path)

    # 查找并重命名ltx文件
    ltx_source = find_ltx_file(input_file)
    if ltx_source:
        ltx_name = os.path.basename(ltx_source)
        ltx_dest = os.path.join(args.output_dir, ltx_name)
        # 复制ltx文件到输出目录
        shutil.copy2(ltx_source, ltx_dest)
        # 重命名
        new_ltx_name = f"{new_basename}.ltx"
        new_ltx_path = os.path.join(args.output_dir, new_ltx_name)
        os.rename(ltx_dest, new_ltx_path)
        print(f"复制并重命名ltx文件: {ltx_name} -> {new_ltx_name}")
    else:
        print("警告: 未找到对应的.ltx文件")

    # 保存bin文件名到文件（类似Makefile中的BINNAME）
    binname_file = os.path.join(args.output_dir, "BINNAME")
    with open(binname_file, 'w') as f:
        f.write(new_bin_path)

    # 保存MD5到文件（类似Makefile中的APP_MD5_TXT）
    md5_file = os.path.join(args.output_dir, "APP_MD5_TXT")
    with open(md5_file, 'w') as f:
        f.write(f"MD5哈希值: {md5_full}\n")

    # 输出打包信息
    print("\n" + "-" * 70)
    print(" " * 30 + "打包成功")
    print("-" * 70)
    print(f"[bin文件]: {new_bin_path}")
    print(f"[bin MD5]: {md5_full}")
    print(f"[FLASH命令]: qspibootudp /apps/{new_bin_name}")
    print(f"[上传命令]: .\\xota3.bat ..\\..\\bin\\{new_bin_name} .\\all.txt")
    print("-" * 70)

    # 记录日志（可选）
    try:
        # 获取当前分支
        branch_result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                                      capture_output=True, text=True)
        current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"

        # 获取完整git HEAD
        head_result = subprocess.run(['git', 'rev-parse', 'HEAD'],
                                    capture_output=True, text=True)
        current_head = head_result.stdout.strip() if head_result.returncode == 0 else "unknown"

        log_msg = f"make pack:{new_bin_name} branch:{current_branch} head:{current_head} MD5:{md5_full}"
        print(f"[日志]: {log_msg}")
    except:
        pass

    print("-" * 70)

if __name__ == '__main__':
    main()