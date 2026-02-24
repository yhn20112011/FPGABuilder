@echo off
REM FPGABuilder包装脚本 - 解决PATH问题
REM 作者: Claude Opus 4.6
REM 日期: 2026-02-24

setlocal

REM 设置UTF-8编码以支持中文输出
set PYTHONUTF8=1

REM 设置Python Scripts目录路径
set SCRIPTS_DIR=C:\Users\NUC\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\Scripts

REM 检查可执行文件是否存在
if not exist "%SCRIPTS_DIR%\FPGABuilder.exe" (
    echo 错误: 未找到 FPGABuilder.exe
    echo 请检查路径: %SCRIPTS_DIR%
    exit /b 1
)

REM 执行命令
"%SCRIPTS_DIR%\FPGABuilder.exe" %*

endlocal