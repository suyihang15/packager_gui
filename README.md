# Python 打包器 (GUI)

这是一个用于把 Python 脚本打包成可执行文件的可视化工具（基于 PyInstaller）。

主要特性：
- 支持单文件（--onefile）和目录打包
- 可选使用临时虚拟环境进行构建，避免本地环境污染
- 可添加资源/文件夹、可选依赖 `requirements.txt`（会作为 `--add-data` 打包）
- 简洁 GUI（基于 PySide6），若未安装 PySide6 会回退到 Tkinter 界面或提示安装

快速开始：

1. 安装依赖（推荐在干净的虚拟环境中）

```bash
pip install -r requirements.txt
```

2. 启动工具

```bash
python packager_gui.py
```

使用说明：
- 在界面中选择主脚本（.py），设置输出目录、是否单文件、是否隐藏控制台等。
- 若勾选“使用隔离虚拟环境构建”，工具会创建临时 venv、在其中安装 PyInstaller（和可选的 requirements），然后进行打包，最后清理临时目录。
- 添加的资源/文件夹会作为 `--add-data` 加入，Windows 下路径分隔为 `;`。

文件说明：

- `packager_gui.py`
  - 程序入口文件。
  - 运行后会导入 `src.ui.run_app()` 并启动打包器界面。

- `src/ui.py`
  - GUI 前端逻辑。
  - 提供选择主脚本、输出目录、图标、依赖文件、资源列表等界面控件。
  - 处理用户操作并调用 `src.core.run_packaging()` 执行打包。

- `src/core.py`
  - 打包后端逻辑。
  - 负责创建临时虚拟环境、安装 PyInstaller、安装可选依赖、生成 `PyInstaller` 命令并运行。
  - 支持 `--onefile`、`--windowed`、`--icon`、`--add-data` 等参数。

- `main.spec`
  - `PyInstaller` 的静态配置文件。
  - 定义了 `Analysis`、`PYZ`、`EXE` 等打包步骤。
  - 通过 `console=False` 控制生成的 exe 是否隐藏命令行窗口。

- `README.md`
  - 当前项目说明文档。
  - 记录安装、运行和打包说明。

- `requirements.txt`
  - 列出本工具运行所需的 Python 包依赖。

- `build/`
  - 记录历史打包产物和中间文件。
  - 不属于源代码逻辑，主要是 `PyInstaller` 打包后的输出结果。

把本工具本身打包为 exe：

1. 在项目根运行（示例）

```bash
python -m PyInstaller --onefile packager_gui.py
```

注意事项：
- 打包目标程序时，外部依赖会被 PyInstaller 扫描并包含，但某些第三方包（如使用动态插件）可能需要额外的 hook 或手动 `--add-data`。
- 图标需为 Windows 下的 `.ico` 文件。
- 其本身是基于pyinstaller对python文件进行打包，如果一点看不懂上面的内容，可以直接用本人打包好的exe文件，

软件示例：
<img width="1502" height="1065" alt="屏幕截图 2026-05-21 164625" src="https://github.com/user-attachments/assets/09393cc2-208c-4440-aada-2df71b521fb0" />
