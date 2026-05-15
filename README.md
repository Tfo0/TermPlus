# TermPlus

Windows Terminal `settings.json` 可视化编辑器，告别手动改 JSON。

> 截图待更新

## 功能

- 左侧侧边栏浏览和编辑所有 Profile
- 命令行预设（PowerShell、CMD、WSL、Git Bash……）可在设置中自定义管理
- Tab 颜色选择器，实时预览效果
- 拖拽调整 Profile 排序
- 归档（隐藏）Profile，无需删除
- 深色 / 浅色主题
- 保存时自动备份（`settings.json.bak`）
- 关闭前有未保存更改时弹出提示

## 下载

从 [Releases](../../releases) 下载最新版 **TermPlus.exe**，无需安装 Python，开箱即用。

## 从源码运行

```bash
pip install -r requirements.txt
python main.py
```

## 打包 exe

```bash
build.bat
# 输出：dist/TermPlus.exe
```

## 项目结构

```
TermPlus/
├── core/
│   ├── app_config.py      # 应用级配置（路径、主题、预设）
│   ├── models.py          # Profile / TerminalSettings 数据模型
│   ├── settings.py        # settings.json 读写
│   └── theme.py           # 深色 / 浅色主题
├── ui/
│   ├── main_window.py     # 主窗口
│   ├── profile_list.py    # 侧边栏列表（常用 / 归档分区）
│   ├── profile_form.py    # Profile 编辑表单
│   └── settings_dialog.py # 设置对话框
├── assets/
│   └── icon.ico
├── main.py
├── build.spec             # PyInstaller 配置
├── build.bat
└── requirements.txt
```

## 配置文件位置

```
%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json
```

TermPlus 会自动检测该路径，也可在 ⚙ 设置中手动指定。
