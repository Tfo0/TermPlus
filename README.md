# TermPlus

Windows Terminal `settings.json` 可视化编辑器，告别手动改 JSON。

## 预览

### 深色主题

主界面采用深色配色，Profile 列表与配置编辑区左右分栏布局。

<img width="1284" height="780" alt="深色主题" src="https://github.com/user-attachments/assets/81ee7754-aba7-49ea-b87d-8d5f9b695990" />

### 浅色主题

一键切换浅色模式，适合亮光环境使用。

<img width="1289" height="788" alt="浅色主题" src="https://github.com/user-attachments/assets/c2876676-2f3e-4ec3-81b8-207858cf4004" />

### 设置面板

在设置中管理命令行预设、主题切换、配置文件路径等全局选项。

<img width="778" height="791" alt="设置界面" src="https://github.com/user-attachments/assets/5b9cd876-7d14-40c0-bf17-1e1dfd112b40" />

### 应用效果

编辑保存后，Windows Terminal 即时生效。

<img width="2528" height="1505" alt="最终效果" src="https://github.com/user-attachments/assets/1b54a542-5e26-4b02-9465-4c05bb452399" />

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

## 配置文件位置

```
%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json
```

TermPlus 会自动检测该路径，也可在 ⚙ 设置中手动指定。
