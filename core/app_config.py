import json
import os
from pathlib import Path


DEFAULT_PRESETS = [
    {"name": "PowerShell",   "command": r"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe -nologo"},
    {"name": "CMD",          "command": "cmd.exe"},
    {"name": "WSL",          "command": "wsl.exe"},
    {"name": "Git Bash",     "command": r"C:\Program Files\Git\bin\bash.exe --login -i"},
]


class AppConfig:
    _CONFIG_FILE = Path.home() / ".terminalconfig_editor.json"
    DEFAULT_PATH = str(Path(
        os.getenv("LOCALAPPDATA", ""),
        "Packages",
        "Microsoft.WindowsTerminal_8wekyb3d8bbwe",
        "LocalState",
        "settings.json"
    ))

    def __init__(self):
        self.settings_json_path = self.DEFAULT_PATH
        self.theme = "dark"
        self.presets: list[dict] = list(DEFAULT_PRESETS)
        self._load()

    def _load(self):
        if self._CONFIG_FILE.exists():
            try:
                with open(self._CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.settings_json_path = data.get("settings_json_path", self.DEFAULT_PATH)
                theme = data.get("theme", "dark")
                self.theme = "dark" if theme not in ("dark", "light") else theme
                if "presets" in data:
                    self.presets = data["presets"]
                elif "custom_presets" in data:
                    self.presets = list(DEFAULT_PRESETS) + data["custom_presets"]
            except Exception:
                pass

    def save(self):
        with open(self._CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "settings_json_path": self.settings_json_path,
                "theme": self.theme,
                "presets": self.presets,
            }, f, indent=2)
