#!/usr/bin/env python3
"""
FPGABuilder打包脚本

用于创建可分发安装包和可执行文件。
支持：
1. 源代码分发包（sdist, wheel）
2. 独立可执行文件（PyInstaller）
3. Windows安装程序（可选）
"""

import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path
import argparse

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core import __version__


class Packager:
    """打包器"""

    def __init__(self, output_dir=None):
        self.project_root = Path(__file__).parent.parent
        self.output_dir = Path(output_dir) if output_dir else self.project_root / "dist"
        self.version = __version__

    def clean(self):
        """清理构建文件"""
        print("清理构建文件...")

        dirs_to_clean = [
            "build",
            "dist",
            "*.egg-info",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache"
        ]

        for pattern in dirs_to_clean:
            for path in self.project_root.rglob(pattern):
                if path.is_dir():
                    print(f"  删除目录: {path}")
                    shutil.rmtree(path, ignore_errors=True)
                elif path.is_file():
                    print(f"  删除文件: {path}")
                    path.unlink(missing_ok=True)

        # 删除pycache目录
        for pycache in self.project_root.rglob("__pycache__"):
            if pycache.is_dir():
                shutil.rmtree(pycache, ignore_errors=True)

        print("清理完成")

    def build_source_distribution(self):
        """构建源代码分发包"""
        print("构建源代码分发包...")

        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 运行python -m build
        cmd = [sys.executable, "-m", "build", "--outdir", str(self.output_dir)]

        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"构建失败: {result.stderr}")
            return False

        print("源代码分发包构建完成")
        return True

    def build_wheel(self):
        """构建wheel包"""
        print("构建wheel包...")

        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 运行python -m build --wheel
        cmd = [sys.executable, "-m", "build", "--wheel", "--outdir", str(self.output_dir)]

        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"构建wheel失败: {result.stderr}")
            return False

        print("wheel包构建完成")
        return True

    def build_executable(self, onefile=True):
        """构建独立可执行文件"""
        print("构建独立可执行文件...")

        try:
            import PyInstaller
        except ImportError:
            print("错误: PyInstaller未安装")
            print("运行: pip install pyinstaller")
            return False

        # 创建临时spec文件
        spec_content = fr"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{(self.project_root / "src" / "core" / "cli.py").as_posix()}'],
    pathex=['{(self.project_root).as_posix()}'],
    binaries=[],
    datas=[
        ('{(self.project_root / "src" / "core").as_posix()}', 'core'),
        ('{(self.project_root / "src" / "plugins").as_posix()}', 'plugins'),
        ('{(self.project_root / "src" / "templates").as_posix()}', 'templates'),
        ('{(self.project_root / "src" / "utils").as_posix()}', 'utils'),
    ],
    hiddenimports=[
        'core.config',
        'core.project',
        'core.plugin_manager',
        'core.plugin_base',
        'plugins.vivado.plugin',
        'plugins.vivado.file_scanner',
        'plugins.vivado.tcl_templates',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=2,
    upx=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FPGABuilder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

{'# 单文件模式' if onefile else ''}
"""

        # 写入spec文件
        spec_file = self.project_root / "FPGABuilder.spec"
        with open(spec_file, "w", encoding="utf-8") as f:
            f.write(spec_content)

        # 运行PyInstaller
        cmd = [sys.executable, "-m", "PyInstaller", "--clean",
               "--distpath", str(self.output_dir),
               "--workpath", str(self.project_root / "build"),
               str(spec_file)]

        # 单文件模式已通过spec文件配置
        # 不再添加--onefile选项以避免冲突

        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)

        # 清理spec文件
        if spec_file.exists():
            spec_file.unlink()

        if result.returncode != 0:
            print(f"构建可执行文件失败: {result.stderr}")
            return False

        # 检查可执行文件是否已创建
        if self.output_dir.exists():
            for exe_file in self.output_dir.glob("FPGABuilder*"):
                if exe_file.is_file():
                    print(f"可执行文件已创建: {exe_file}")
        else:
            print("警告: 未找到可执行文件，可能构建失败")

        print("独立可执行文件构建完成")
        return True

    def build_windows_installer(self):
        """构建Windows安装程序（使用Inno Setup）"""
        print("构建Windows安装程序...")

        if sys.platform != "win32":
            print("警告: Windows安装程序只能在Windows系统上构建")
            return False

        # 检查Inno Setup是否安装
        inno_paths = []
        # 从环境变量获取程序文件路径
        program_files_x86 = os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")
        program_files = os.environ.get("PROGRAMFILES", "C:/Program Files")

        # 常见安装路径
        possible_paths = [
            f"{program_files_x86}/Inno Setup 6/iscc.exe",
            f"{program_files}/Inno Setup 6/iscc.exe",
            f"{program_files_x86}/Inno Setup 6.7.1/iscc.exe",
            f"{program_files}/Inno Setup 6.7.1/iscc.exe",
            f"{program_files_x86}/Inno Setup/iscc.exe",
            f"{program_files}/Inno Setup/iscc.exe",
            "C:/Inno Setup/iscc.exe",
        ]

        # 检查环境变量ISCC
        iscc_env = os.environ.get("ISCC")
        if iscc_env:
            possible_paths.insert(0, iscc_env)

        # 转换为Path对象
        inno_paths = [Path(p) for p in possible_paths]

        inno_compiler = None
        for path in inno_paths:
            if path.exists():
                inno_compiler = path
                break

        if not inno_compiler:
            print("错误: Inno Setup未安装")
            print("请从 https://jrsoftware.org/isdl.php 下载并安装Inno Setup")
            return False

        # 首先构建可执行文件
        if not self.build_executable(onefile=True):
            print("构建可执行文件失败，无法创建安装程序")
            return False

        # 创建Inno Setup脚本
        iss_content = r"""; FPGABuilder安装脚本
; 由packager.py自动生成

#define MyAppName "FPGABuilder"
#define MyAppVersion "{version}"
#define MyAppPublisher "YiHok"
#define MyAppURL "https://github.com/yhn20112011/FPGABuilder"
#define MyAppExeName "FPGABuilder.exe"

[Setup]
AppId={{{{{{FC2B9F7F-3B2A-4B8E-9F6D-7C8E5A3B2D1A}}}}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
AppPublisherURL={{#MyAppURL}}
AppSupportURL={{#MyAppURL}}
AppUpdatesURL={{#MyAppURL}}
DefaultDirName={{autopf}}\{{#MyAppName}}
DefaultGroupName={{#MyAppName}}
AllowNoIcons=yes
LicenseFile={{src}}\LICENSE
OutputDir={{#OutputDir}}
OutputBaseFileName=FPGABuilder-Setup-{{#MyAppVersion}}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked

[Files]
Source: "{{src}}\dist\FPGABuilder.exe"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "{{src}}\README.md"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "{{src}}\LICENSE"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "{{src}}\docs\*"; DestDir: "{{app}}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\{{#MyAppName}}"; Filename: "{{app}}\{{#MyAppExeName}}"
Name: "{{group}}\{{cm:UninstallProgram,{{#MyAppName}}}}"; Filename: "{{uninstallexe}}"
Name: "{{commondesktop}}\{{#MyAppName}}"; Filename: "{{app}}\{{#MyAppExeName}}"; Tasks: desktopicon

[Run]
Filename: "{{app}}\{{#MyAppExeName}}"; Description: "{{cm:LaunchProgram,{{#StringChange(MyAppName, '&', '&&')}}}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  // 检查Python是否安装（可选）
  // 检查依赖等
end;
"""
        # 替换版本号
        iss_content = iss_content.replace("{version}", self.version)

        # 修复预处理变量语法
        iss_content = iss_content.replace("{{#MyAppName}}", "{#MyAppName}")
        iss_content = iss_content.replace("{{#MyAppVersion}}", "{#MyAppVersion}")
        iss_content = iss_content.replace("{{#MyAppPublisher}}", "{#MyAppPublisher}")
        iss_content = iss_content.replace("{{#MyAppURL}}", "{#MyAppURL}")
        iss_content = iss_content.replace("{{#MyAppExeName}}", "{#MyAppExeName}")
        iss_content = iss_content.replace("{{#OutputDir}}", "{#OutputDir}")
        iss_content = iss_content.replace("{{#StringChange", "{#StringChange")
        iss_content = iss_content.replace(")}}", ")}")
        iss_content = iss_content.replace("{{src}}", "{#src}")
        # 移除中文语言支持（避免缺失文件错误）
        iss_content = iss_content.replace('Name: "chinesesimplified"; MessagesFile: "compiler:Languages\\ChineseSimplified.isl"\n', '')

        # 写入ISS文件
        iss_file = self.project_root / "FPGABuilder.iss"
        with open(iss_file, "w", encoding="utf-8") as f:
            f.write(iss_content)

        # 运行Inno Setup编译器
        cmd = [str(inno_compiler), f"/O{self.output_dir}",
               f"/DOutputDir={self.output_dir}",
               f"/Dsrc={self.project_root}", str(iss_file)]

        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True, encoding='utf-8', errors='ignore')

        # 清理ISS文件（仅在成功时）
        if result.returncode == 0 and iss_file.exists():
            iss_file.unlink()
        elif iss_file.exists():
            print(f"ISS文件保留以供调试: {iss_file}")

        if result.returncode != 0:
            print(f"构建安装程序失败: {result.stderr}")
            return False

        print("Windows安装程序构建完成")
        return True

    def build_windows_offline_installer(self):
        """构建Windows离线安装程序（包含Python解释器和所有依赖）"""
        print("构建Windows离线安装程序...")

        if sys.platform != "win32":
            print("警告: Windows安装程序只能在Windows系统上构建")
            return False

        # 检查Inno Setup是否安装
        inno_paths = []
        # 从环境变量获取程序文件路径
        program_files_x86 = os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")
        program_files = os.environ.get("PROGRAMFILES", "C:/Program Files")

        # 常见安装路径
        possible_paths = [
            f"{program_files_x86}/Inno Setup 6/iscc.exe",
            f"{program_files}/Inno Setup 6/iscc.exe",
            f"{program_files_x86}/Inno Setup 6.7.1/iscc.exe",
            f"{program_files}/Inno Setup 6.7.1/iscc.exe",
            f"{program_files_x86}/Inno Setup/iscc.exe",
            f"{program_files}/Inno Setup/iscc.exe",
            "C:/Inno Setup/iscc.exe",
        ]

        # 检查环境变量ISCC
        iscc_env = os.environ.get("ISCC")
        if iscc_env:
            possible_paths.insert(0, iscc_env)

        # 转换为Path对象
        inno_paths = [Path(p) for p in possible_paths]

        inno_compiler = None
        for path in inno_paths:
            if path.exists():
                inno_compiler = path
                break

        if not inno_compiler:
            print("错误: Inno Setup未安装")
            print("请从 https://jrsoftware.org/isdl.php 下载并安装Inno Setup")
            return False

        # 首先构建可执行文件（确保是单文件模式）
        print("构建独立可执行文件（单文件模式）...")
        if not self.build_executable(onefile=True):
            print("构建可执行文件失败，无法创建安装程序")
            return False

        # 创建增强的Inno Setup脚本（离线安装版）
        iss_content = f"""; FPGABuilder安装脚本 - 离线安装版
; 由packager.py自动生成
; 版本: {self.version}

#define MyAppName "FPGABuilder"
#define MyAppVersion "{self.version}"
#define MyAppPublisher "YiHok"
#define MyAppURL "https://github.com/yhn20112011/FPGABuilder"
#define MyAppExeName "FPGABuilder.exe"

[Setup]
AppId={{{{{{FC2B9F7F-3B2A-4B8E-9F6D-7C8E5A3B2D1A}}}}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
AppPublisherURL={{#MyAppURL}}
AppSupportURL={{#MyAppURL}}
AppUpdatesURL={{#MyAppURL}}
DefaultDirName={{autopf}}\{{#MyAppName}}
DefaultGroupName={{#MyAppName}}
AllowNoIcons=yes
LicenseFile={{#src}}\LICENSE
OutputDir={{#OutputDir}}
OutputBaseFileName=FPGABuilder-Offline-Setup-{{#MyAppVersion}}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
; 始终以管理员权限运行，以便修改PATH
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked
Name: "addtopath"; Description: "将FPGABuilder添加到系统PATH"; GroupDescription: "系统设置:"; Flags: checkedonce

[Files]
Source: "{{#src}}\dist\FPGABuilder.exe"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "{{#src}}\README.md"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "{{#src}}\LICENSE"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "{{#src}}\docs\*"; DestDir: "{{app}}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs
; 包含额外的依赖和Python运行时（如果需要）
Source: "{{#src}}\requirements.txt"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{group}}\{{#MyAppName}}"; Filename: "{{app}}\{{#MyAppExeName}}"
Name: "{{group}}\{{cm:UninstallProgram,{{#MyAppName}}}}"; Filename: "{{uninstallexe}}"
Name: "{{commondesktop}}\{{#MyAppName}}"; Filename: "{{app}}\{{#MyAppExeName}}"; Tasks: desktopicon

[Run]
Filename: "{{app}}\{{#MyAppExeName}}"; Description: "{{cm:LaunchProgram,{{#StringChange(MyAppName, '&', '&&')}}}}"; Flags: nowait postinstall skipifsilent

[Code]
// 函数：检查Python是否已安装（可选）
function IsPythonInstalled(): Boolean;
var
  PythonPath: string;
begin
  // 尝试从注册表查找Python
  Result := False;
  if RegQueryStringValue(HKLM, 'SOFTWARE\\Python\\PythonCore\\3.12\\InstallPath', '', PythonPath) then
  begin
    Result := True;
    Exit;
  end;
  if RegQueryStringValue(HKLM, 'SOFTWARE\\Python\\PythonCore\\3.11\\InstallPath', '', PythonPath) then
  begin
    Result := True;
    Exit;
  end;
  if RegQueryStringValue(HKLM, 'SOFTWARE\\Python\\PythonCore\\3.10\\InstallPath', '', PythonPath) then
  begin
    Result := True;
    Exit;
  end;
  if RegQueryStringValue(HKLM, 'SOFTWARE\\Python\\PythonCore\\3.9\\InstallPath', '', PythonPath) then
  begin
    Result := True;
    Exit;
  end;
  if RegQueryStringValue(HKLM, 'SOFTWARE\\Python\\PythonCore\\3.8\\InstallPath', '', PythonPath) then
  begin
    Result := True;
    Exit;
  end;
  // 也检查HKCU（当前用户）
  if RegQueryStringValue(HKCU, 'SOFTWARE\\Python\\PythonCore\\3.12\\InstallPath', '', PythonPath) then
  begin
    Result := True;
    Exit;
  end;
  if RegQueryStringValue(HKCU, 'SOFTWARE\\Python\\PythonCore\\3.11\\InstallPath', '', PythonPath) then
  begin
    Result := True;
    Exit;
  end;
  if RegQueryStringValue(HKCU, 'SOFTWARE\\PythonCore\\3.10\\InstallPath', '', PythonPath) then
  begin
    Result := True;
    Exit;
  end;
  if RegQueryStringValue(HKCU, 'SOFTWARE\\Python\\PythonCore\\3.9\\InstallPath', '', PythonPath) then
  begin
    Result := True;
    Exit;
  end;
  if RegQueryStringValue(HKCU, 'SOFTWARE\\Python\\PythonCore\\3.8\\InstallPath', '', PythonPath) then
  begin
    Result := True;
    Exit;
  end;
end;

// 函数：检查是否已安装必要的依赖
function CheckDependencies(): Boolean;
begin
  // 这里可以添加更复杂的依赖检查逻辑
  // 目前只是返回True，因为PyInstaller可执行文件是自包含的
  Result := True;
end;

// 函数：修改系统PATH环境变量
procedure AddToPath(InstallDir: string);
var
  PathVar: string;
  NewPath: string;
begin
  // 读取当前系统PATH
  if not RegQueryStringValue(HKLM, 'SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment', 'Path', PathVar) then
  begin
    // 如果无法读取系统PATH，尝试用户PATH
    if not RegQueryStringValue(HKCU, 'Environment', 'Path', PathVar) then
    begin
      PathVar := '';
    end;
  end;

  // 检查是否已包含安装目录
  if (Pos(';' + InstallDir + ';', ';' + PathVar + ';') > 0) or
     (Pos(';' + InstallDir + '\;', ';' + PathVar + ';') > 0) then
  begin
    Log('安装目录已在PATH中: ' + InstallDir);
    Exit;
  end;

  // 添加到PATH
  NewPath := PathVar;
  if NewPath <> '' then
    NewPath := NewPath + ';';
  NewPath := NewPath + InstallDir;

  // 写回注册表
  if IsAdminLoggedOn then
  begin
    // 管理员权限：写入系统环境变量
    if RegWriteStringValue(HKLM, 'SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment', 'Path', NewPath) then
    begin
      Log('已添加安装目录到系统PATH: ' + InstallDir);
    end
    else
    begin
      Log('错误: 无法写入系统PATH注册表');
    end;
  end
  else
  begin
    // 非管理员：写入用户环境变量
    if RegWriteStringValue(HKCU, 'Environment', 'Path', NewPath) then
    begin
      Log('已添加安装目录到用户PATH: ' + InstallDir);
    end
    else
    begin
      Log('错误: 无法写入用户PATH注册表');
    end;
  end;
end;

// 函数：从PATH中移除安装目录
procedure RemoveFromPath(InstallDir: string);
var
  PathVar: string;
  NewPath: string;
  Parts: TArrayOfString;
  I: Integer;
begin
  // 读取当前系统PATH
  if not RegQueryStringValue(HKLM, 'SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment', 'Path', PathVar) then
  begin
    // 如果无法读取系统PATH，尝试用户PATH
    if not RegQueryStringValue(HKCU, 'Environment', 'Path', PathVar) then
    begin
      Exit;
    end;
  end;

  // 分割PATH并移除安装目录
  NewPath := '';
  StringChangeEx(PathVar, InstallDir, '', True);

  // 清理多余的分号
  Parts := SplitString(PathVar, ';');
  for I := 0 to GetArrayLength(Parts) - 1 do
  begin
    if Parts[I] <> '' then
    begin
      if NewPath <> '' then
        NewPath := NewPath + ';';
      NewPath := NewPath + Parts[I];
    end;
  end;

  // 写回注册表
  if IsAdminLoggedOn then
  begin
    RegWriteStringValue(HKLM, 'SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment', 'Path', NewPath);
  end
  else
  begin
    RegWriteStringValue(HKCU, 'Environment', 'Path', NewPath);
  end;
end;

// 初始化安装
function InitializeSetup(): Boolean;
begin
  Result := True;

  // 检查依赖
  if not CheckDependencies() then
  begin
    MsgBox('某些依赖未满足，但安装将继续进行。FPGABuilder可执行文件是自包含的。', mbInformation, MB_OK);
  end;

  // 检查Python是否安装（仅信息提示）
  if not IsPythonInstalled() then
  begin
    Log('未检测到系统Python安装，但FPGABuilder可执行文件是自包含的，无需Python。');
  end
  else
  begin
    Log('检测到系统Python安装。');
  end;
end;

// 安装完成后的处理
procedure CurStepChanged(CurStep: TSetupStep);
var
  InstallDir: string;
begin
  if CurStep = ssPostInstall then
  begin
    InstallDir := ExpandConstant('{{app}}');

    // 如果用户选择了"添加到PATH"任务
    if IsTaskSelected('addtopath') then
    begin
      AddToPath(InstallDir);
    end;
  end;
end;

// 卸载时的处理
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  InstallDir: string;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    InstallDir := ExpandConstant('{{app}}');

    // 从PATH中移除安装目录
    RemoveFromPath(InstallDir);
  end;
end;
"""
        # 写入ISS文件
        iss_file = self.project_root / "FPGABuilder-Offline.iss"
        with open(iss_file, "w", encoding="utf-8") as f:
            f.write(iss_content)

        # 运行Inno Setup编译器
        cmd = [str(inno_compiler), f"/O{self.output_dir}",
               f"/DOutputDir={self.output_dir}",
               f"/Dsrc={self.project_root}", str(iss_file)]

        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True, encoding='utf-8', errors='ignore')

        # 清理ISS文件（仅在成功时）
        if result.returncode == 0 and iss_file.exists():
            iss_file.unlink()
        elif iss_file.exists():
            print(f"ISS文件保留以供调试: {iss_file}")

        if result.returncode != 0:
            print(f"构建离线安装程序失败: {result.stderr}")
            return False

        print("Windows离线安装程序构建完成")
        return True

    def package_all(self):
        """打包所有格式"""
        print(f"FPGABuilder 打包工具 v{self.version}")
        print("=" * 50)

        # 清理
        self.clean()

        # 构建所有格式
        success = True

        print("\n1. 构建源代码分发包...")
        if not self.build_source_distribution():
            success = False
            print("  警告: 源代码分发包构建失败")

        print("\n2. 构建wheel包...")
        if not self.build_wheel():
            success = False
            print("  警告: wheel包构建失败")

        print("\n3. 构建独立可执行文件...")
        if not self.build_executable(onefile=True):
            success = False
            print("  警告: 可执行文件构建失败")

        if sys.platform == "win32":
            print("\n4. 构建Windows安装程序...")
            if not self.build_windows_installer():
                success = False
                print("  警告: Windows安装程序构建失败")

            print("\n5. 构建Windows离线安装程序...")
            if not self.build_windows_offline_installer():
                success = False
                print("  警告: Windows离线安装程序构建失败")

        # 显示输出文件
        print("\n" + "=" * 50)
        print("输出文件:")
        if self.output_dir.exists():
            for file in sorted(self.output_dir.glob("*")):
                size = file.stat().st_size if file.is_file() else 0
                size_str = f"{size / 1024 / 1024:.2f} MB" if size > 0 else ""
                print(f"  - {file.name} {size_str}")

        if success:
            print(f"\n[OK] 打包完成！文件保存在: {self.output_dir}")
        else:
            print(f"\n[WARN] 打包完成，但有警告。文件保存在: {self.output_dir}")

        return success


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="FPGABuilder打包工具")
    parser.add_argument("--clean", action="store_true", help="清理构建文件")
    parser.add_argument("--sdist", action="store_true", help="构建源代码分发包")
    parser.add_argument("--wheel", action="store_true", help="构建wheel包")
    parser.add_argument("--exe", action="store_true", help="构建独立可执行文件")
    parser.add_argument("--installer", action="store_true", help="构建Windows安装程序")
    parser.add_argument("--offline-installer", action="store_true", help="构建Windows离线安装程序（包含Python和所有依赖）")
    parser.add_argument("--all", action="store_true", help="打包所有格式")
    parser.add_argument("--output", "-o", help="输出目录", default="dist")
    parser.add_argument("--version", "-V", action="store_true", help="显示版本")

    args = parser.parse_args()

    if args.version:
        print(f"FPGABuilder v{__version__}")
        return

    packager = Packager(args.output)

    if args.clean:
        packager.clean()
        return

    if args.all:
        packager.package_all()
        return

    # 执行特定打包任务
    success = True

    if args.sdist:
        success = packager.build_source_distribution() and success

    if args.wheel:
        success = packager.build_wheel() and success

    if args.exe:
        success = packager.build_executable() and success

    if args.installer:
        success = packager.build_windows_installer() and success

    if args.offline_installer:
        success = packager.build_windows_offline_installer() and success

    # 如果没有指定任何选项，显示帮助
    if not any([args.clean, args.sdist, args.wheel, args.exe, args.installer, args.offline_installer, args.all]):
        parser.print_help()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()