# TermPlus

Windows Terminal `settings.json` 可视化编辑器，告别手动改 JSON。

## 预览

### 深色主题

主界面采用深色配色，Profile 列表与配置编辑区左右分栏布局。

<img width="1333" height="990" alt="image" src="https://github.com/user-attachments/assets/1fe6ac64-9d8f-4106-95fb-9be91dd2bd65" />


### 浅色主题

一键切换浅色模式，适合亮光环境使用。

<img width="1338" height="991" alt="image" src="https://github.com/user-attachments/assets/a3e5c806-8d61-4f5c-866a-cdeb418ba4f3" />


### 设置面板

在设置中管理命令行预设、主题切换、配置文件路径等全局选项。

<img width="778" height="791" alt="设置界面" src="https://github.com/user-attachments/assets/5b9cd876-7d14-40c0-bf17-1e1dfd112b40" />

### 应用效果

编辑保存后，Windows Terminal 即时生效。

<img width="2529" height="1509" alt="image" src="https://github.com/user-attachments/assets/4fb8d38f-27d4-4081-b9d9-b861949369f8" />


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
