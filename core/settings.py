import json
import os
import shutil
from pathlib import Path
from typing import Optional
from .models import TerminalSettings


class SettingsManager:
    def __init__(self, settings_path: str = None):
        if settings_path:
            self.settings_path = Path(settings_path)
        else:
            self.settings_path = Path(
                os.getenv("LOCALAPPDATA"),
                "Packages",
                "Microsoft.WindowsTerminal_8wekyb3d8bbwe",
                "LocalState",
                "settings.json"
            )

    def load(self) -> Optional[TerminalSettings]:
        if not self.settings_path.exists():
            return None
        try:
            with open(self.settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return TerminalSettings.from_dict(data)
        except Exception as e:
            raise ValueError(f"Failed to load settings: {e}")

    def save(self, settings: TerminalSettings, backup: bool = True) -> bool:
        try:
            if backup and self.settings_path.exists():
                shutil.copy2(self.settings_path, self.settings_path.with_suffix(".json.bak"))
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(settings.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            raise ValueError(f"Failed to save settings: {e}")

    def exists(self) -> bool:
        return self.settings_path.exists()
