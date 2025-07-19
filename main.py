import os
import subprocess
import sys
from pathlib import Path

# ==============================================================================
# 模板: Bash 启动配置文件 (.msys2_bash_profile)
# ==============================================================================
# 此文件定义了进入项目专属 bash 环境后需要执行的所有命令。
# 它与具体环境(mingw64, clang64等)无关，因此无需修改。
# ==============================================================================
BASH_PROFILE_TEMPLATE = r'''
# 清理终端，提供一个干净的启动界面
clear

# 打印环境信息，帮助用户确认当前所在环境
# $MSYSTEM 变量会由 msys2_shell.cmd 根据启动方式自动设置为 MINGW64, CLANG64 等
echo '========================================================================'
echo "已进入项目专属的 MSYS2 环境 ($MSYSTEM)"
echo "MSYS2 Root   : $PROJECT_MSYS2_ROOT_PATH"
echo "MSYS2 DB     : $PROJECT_MSYS2_DB_PATH"
echo "MSYS2 Cache  : $PROJECT_MSYS2_CACHE_PATH"
echo '------------------------------------------------------------------------'
echo '`pacman` 命令已被封装，将自动使用本项目的路径。'
echo '环境已就绪。'
echo '========================================================================'

# 定义 pacman 函数来封装原始命令，使其自动附加必要的路径参数。
pacman() {
    command pacman --root="$PROJECT_MSYS2_ROOT_PATH" \
                   --dbpath="$PROJECT_MSYS2_DB_PATH" \
                   --cachedir="$PROJECT_MSYS2_CACHE_PATH" \
                   "$@"
}

# 使用 `export -f` 将该函数导出，使其在子 Shell 中也同样生效。
export -f pacman

# 自定义命令行提示符 (PS1)，以清晰地展示当前用户、主机和 MSYS2 环境类型。
export PS1='\[\e]0;\w\a\]\n\[\e[32m\]\u@\h \[\e[35m\]$MSYSTEM \[\e[33m\]\w\[\e[0m\]\n\$ '
'''

# ==============================================================================
# 模板: PowerShell 启动脚本 (msys2.ps1)
# ==============================================================================
# 此模板现在包含占位符 {env_name} 和 {env_name_upper}，
# Python 脚本将根据用户的选择填充它们。
# ==============================================================================
POWERSHELL_SCRIPT_TEMPLATE = r'''
# 获取此脚本所在的目录，该目录即为项目根目录
$projectRoot = $PSScriptRoot

# 根据项目根目录，构建 MSYS2 相关子目录的绝对路径
$msys2BaseDir = Join-Path -Path $projectRoot -ChildPath "msys2"
$msys2RootDir = Join-Path -Path $msys2BaseDir -ChildPath "msys2_root"
$msys2DbDir = Join-Path -Path $msys2BaseDir -ChildPath "msys2_db"
$msys2CacheDir = Join-Path -Path $msys2BaseDir -ChildPath "msys2_cache"

# 验证必要的目录和配置文件是否存在，确保环境已被正确初始化
$bashProfile = Join-Path -Path $projectRoot -ChildPath ".msys2_bash_profile"
if (-not (Test-Path -Path $msys2RootDir -PathType Container)) {{
    Write-Error "错误: MSYS2 根目录未找到于 '$msys2RootDir'。请先运行 Python 初始化脚本。"
    exit 1
}}
if (-not (Test-Path -Path $bashProfile -PathType Leaf)) {{
    Write-Error "错误: Bash 启动配置文件 '.msys2_bash_profile' 未找到。请重新运行 Python 初始化脚本。"
    exit 1
}}

# --- 辅助函数: 将 Windows 路径转换为 MSYS2/bash 兼容的路径格式 ---
Function ConvertTo-Msys2Path {{
    param(
        [string]$WindowsPath
    )
    $fullPath = (Get-Item -Path $WindowsPath).FullName
    $msysPath = $fullPath -replace '\\', '/' -replace '^([A-Z]):', '/$1'
    return $msysPath.ToLower()
}}

# 设置环境变量，这些变量将被传递给 bash 进程，并由 .msys2_bash_profile 文件使用
$env:PROJECT_MSYS2_ROOT_PATH = ConvertTo-Msys2Path -WindowsPath $msys2RootDir
$env:PROJECT_MSYS2_DB_PATH = ConvertTo-Msys2Path -WindowsPath $msys2DbDir
$env:PROJECT_MSYS2_CACHE_PATH = ConvertTo-Msys2Path -WindowsPath $msys2CacheDir

# 获取 bash 启动配置文件的 MSYS2 格式路径
$bashProfileMsys = ConvertTo-Msys2Path -WindowsPath $bashProfile

Write-Host "正在启动项目专属的 MSYS2 {env_name_upper} 环境..."

# --- 启动 MSYS2 环境 ---
# 使用选择的环境启动器 ({env_name}.cmd) 来稳定地启动环境。
# 引号内的 `bash --rcfile '...'` 指令会加载指定的配置文件并启动一个交互式 Shell。
{env_name}.cmd -defterm -here -c "bash --rcfile '$bashProfileMsys'"
'''

def convert_to_msys_path(windows_path: Path) -> str:
    """辅助函数，将 Windows Path 对象转换为 MSYS2/bash 风格的路径字符串。"""
    path_str = windows_path.resolve().as_posix()
    drive, tail = os.path.splitdrive(path_str)
    drive_letter = drive.replace(":", "").lower()
    return f"/{drive_letter}{tail}"

def select_environment() -> str:
    """提供菜单让用户选择MSYS2环境，并返回选择结果的小写字符串。"""
    environments = ["mingw64", "ucrt64", "clang64", "clangarm64", "mingw32"]
    
    print("\n--- 请选择要创建的 MSYS2 环境 ---")
    for i, env in enumerate(environments, 1):
        print(f"{i}: {env}")
    
    while True:
        try:
            choice = int(input(f"请输入选项编号 (1-{len(environments)}): "))
            if 1 <= choice <= len(environments):
                return environments[choice - 1]
            else:
                print("输入无效，请输入列表中的编号。")
        except ValueError:
            print("输入无效，请输入一个数字。")

def main():
    """主执行函数，负责整个初始化流程。"""
    print("--- MSYS2 项目环境初始化脚本 ---")

    try:
        project_dir_str = input("请输入您的项目根目录地址: ")
        project_dir = Path(project_dir_str).resolve()
        if not project_dir.is_dir():
            print(f"错误: 提供的路径 '{project_dir}' 不是一个有效的目录。")
            sys.exit(1)
    except Exception as e:
        print(f"错误: 读取路径时发生问题: {e}")
        sys.exit(1)

    # 新增：让用户选择环境
    selected_env = select_environment()
    print(f"\n已选择环境: {selected_env.upper()}")

    print(f"将在 '{project_dir}' 中为 {selected_env.upper()} 环境进行设置。")

    msys2_base_dir = project_dir / "msys2"
    msys2_root_dir = msys2_base_dir / "msys2_root"
    msys2_cache_dir = msys2_base_dir / "msys2_cache"
    msys2_db_dir = msys2_base_dir / "msys2_db"

    print("正在创建/验证目录结构...")
    try:
        # 这些目录对于所有环境都是共享的
        os.makedirs(msys2_root_dir, exist_ok=True)
        os.makedirs(msys2_cache_dir, exist_ok=True)
        os.makedirs(msys2_db_dir, exist_ok=True)
    except OSError as e:
        print(f"错误: 创建目录时失败: {e}")
        sys.exit(1)

    bash_profile_path = project_dir / ".msys2_bash_profile"
    print(f"正在生成/更新 Bash 启动配置文件: {bash_profile_path}")
    try:
        with open(bash_profile_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(BASH_PROFILE_TEMPLATE)
    except IOError as e:
        print(f"错误: 写入 Bash 启动配置文件时失败: {e}")
        sys.exit(1)

    ps1_script_path = project_dir / "msys2.ps1"
    print(f"正在生成/更新 PowerShell 启动脚本: {ps1_script_path}")
    try:
        # 填充模板中的占位符
        ps1_content = POWERSHELL_SCRIPT_TEMPLATE.format(
            env_name=selected_env,
            env_name_upper=selected_env.upper()
        )
        with open(ps1_script_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(ps1_content)
    except IOError as e:
        print(f"错误: 写入 PowerShell 脚本时失败: {e}")
        sys.exit(1)
        
    if not any(os.scandir(msys2_db_dir)):
        print(f"\n检测到环境未初始化，正在为 {selected_env.upper()} 执行一次性初始化 (pacman -Sy)...")
        print("该过程将同步软件包数据库到项目的专属目录中，可能需要一些时间。")
        
        root_path_msys = convert_to_msys_path(msys2_root_dir)
        db_path_msys = convert_to_msys_path(msys2_db_dir)
        cache_path_msys = convert_to_msys_path(msys2_cache_dir)
        
        pacman_command = (
            f"pacman -Sy --noconfirm "
            f"--root='{root_path_msys}' "
            f"--dbpath='{db_path_msys}' "
            f"--cachedir='{cache_path_msys}'"
        )
        
        # 使用选择的环境启动器
        launcher_cmd = f"{selected_env}.cmd"
        full_command = [launcher_cmd, '-c', pacman_command]

        try:
            result = subprocess.run(
                full_command, check=True, capture_output=True, text=True, 
                encoding='utf-8', shell=True
            )
            print("--- 初始化成功 ---")
        except FileNotFoundError:
            print(f"\n错误: '{launcher_cmd}' 未找到。请确保 scoop shims 目录在系统 PATH 中，且对应的 MSYS2 环境已安装。")
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            print(f"\n错误: pacman 初始化命令执行失败，返回码: {e.returncode}")
            print(f"--- STDERR ---\n{e.stderr}\n--- STDOUT ---\n{e.stdout}")
            sys.exit(1)
    else:
        print("\n检测到环境已初始化，跳过 `pacman -Sy` 步骤。")
        
    print("\n========================================================")
    print("✅ 设置完成！")
    print(f"\n现在您可以进入 '{project_dir}' 目录，")
    print(f"通过运行 'msys2.ps1' 来启动本项目的专属 {selected_env.upper()} 环境。")
    print("========================================================")

if __name__ == "__main__":
    main()