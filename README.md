# MSYS2 项目专属环境生成器

这是一个 Python 脚本，用于为任何项目创建一套独立的、便携的 MSYS2 开发环境。它解决了在多个项目间管理不同依赖项时可能出现的冲突和混乱问题。通过此脚本，每个项目都将拥有自己专属的 `pacman` 包管理器、软件库、数据库和缓存，所有这些都存储在项目根目录下的 `msys2` 文件夹内，从而与全局 MSYS2 环境完全隔离。

## 核心功能

- **环境隔离**: 为每个项目创建独立的 MSYS2 环境，`pacman` 的所有操作（安装、更新、卸载）都仅限于项目内部。
- **便携性**: 整个 MSYS2 环境（包括所有已安装的工具链和库）都包含在项目目录中，方便迁移和共享。
- **多环境支持**: 支持生成多种 MSYS2 环境，包括 `MINGW64`, `UCRT64`, `CLANG64` 等。
- **自动化配置**: 自动生成启动脚本 (`msys2.ps1`) 和 Bash 配置文件 (`.msys2_bash_profile`)。
- **智能初始化**: 首次设置时，脚本会自动运行 `pacman -Sy` 来同步初始的软件包数据库。

## 工作原理

该脚本通过以下步骤实现环境隔离：

1.  **创建目录结构**: 在指定的项目根目录下，创建 `msys2/msys2_root`, `msys2/msys2_db`, `msys2/msys2_cache` 等目录。
2.  **生成 Bash 配置文件 (`.msys2_bash_profile`)**: 这个文件会在启动专属的 Bash Shell 时被加载。其核心是定义了一个自定义的 `pacman` 函数，该函数会覆盖原始的 `pacman` 命令，并自动为其添加 `--root`, `--dbpath`, `--cachedir` 参数，强制其使用项目内的专属路径。
3.  **生成 PowerShell 启动器 (`msys2.ps1`)**: 这是进入项目专属环境的入口。它负责设置必要的环境变量，然后调用系统中的 MSYS2 启动程序（如 `mingw64.cmd`），并指示它使用我们生成的 `.msys2_bash_profile` 文件来初始化 Shell。

## 使用前提

在运行此脚本之前，请确保满足以下条件：

1.  **Python 3**: 已安装 Python 3 环境。
2.  **MSYS2 安装**: 系统中必须已安装 MSYS2。**强烈建议**通过 [Scoop](https://scoop.sh/) (`scoop install msys2`) 来安装，因为 Scoop 会自动将 MSYS2 的各种环境启动器（如 `mingw64.cmd`, `ucrt64.cmd` 等）添加到系统的 `PATH` 环境变量中，这是本脚本正常运行的必要条件。

## 使用步骤

1.  **运行初始化脚本**:
    在任意位置打开终端，运行 `main.py` 脚本。
    ```shell
    python main.py
    ```

2.  **输入项目路径**:
    根据提示，输入你希望创建专属环境的**项目根目录的绝对路径**。
    ```
    请输入您的项目根目录地址: C:\path\to\your\project
    ```

3.  **选择 MSYS2 环境**:
    从列表中选择你需要的 MSYS2 环境类型（例如，选择 `1` 代表 `mingw64`）。
    ```
    --- 请选择要创建的 MSYS2 环境 ---
    1: mingw64
    2: ucrt64
    3: clang64
    ...
    请输入选项编号 (1-5): 1
    ```

4.  **等待脚本执行**:
    脚本将自动创建目录、生成配置文件，并在需要时执行 `pacman -Sy` 进行初始化。

5.  **启动专属环境**:
    初始化完成后，进入你的项目根目录，并运行新生成的 `msys2.ps1` 脚本。
    ```powershell
    cd C:\path\to\your\project
    .\msys2.ps1
    ```

    执行后，你将进入一个全新的、隔离的 MSYS2 终端环境。提示符会清晰地显示当前所处的环境类型（如 `MINGW64`）。

## 验证隔离效果

进入专属环境后，你可以尝试使用 `pacman` 安装任意软件包，例如 `make`：

```bash
# 在专属的 MSYS2 环境中运行
pacman -S mingw-w64-x86_64-make
```

安装完成后，你可以检查：
- `make.exe` 是否被安装到了 `C:\path\to\your\project\msys2\msys2_root\mingw64\bin` 目录下。
- 软件包的数据库文件是否位于 `C:\path\to\your\project\msys2\msys2_db` 中。
- 软件包的压缩包是否缓存在 `C:\path\to\your\project\msys2\msys2_cache` 中。

这证明了所有操作都成功地被限制在了项目目录内，未对全局 MSYS2 环境造成任何影响。

```