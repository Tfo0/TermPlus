from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any


@dataclass
class Profile:
    guid: str
    name: str
    hidden: bool = False
    commandline: str = ""
    startingDirectory: str = ""
    icon: Optional[str] = None
    tabTitle: Optional[str] = None
    tabColor: Optional[str] = None
    suppressApplicationTitle: bool = False
    foreground: Optional[str] = None
    background: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        data = asdict(self)
        data.pop("extra", None)
        data.update(self.extra)
        return {k: v for k, v in data.items() if v is not None and v is not False}

    @staticmethod
    def from_dict(data: dict) -> "Profile":
        known_fields = {
            "guid", "name", "hidden", "commandline", "startingDirectory",
            "icon", "tabTitle", "tabColor", "suppressApplicationTitle",
            "foreground", "background"
        }
        known = {k: v for k, v in data.items() if k in known_fields}
        extra = {k: v for k, v in data.items() if k not in known_fields}
        return Profile(**known, extra=extra)


@dataclass
class TerminalSettings:
    profiles: List[Profile] = field(default_factory=list)
    defaultProfile: str = ""
    schemes: List[Dict[str, Any]] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "$schema": "https://raw.githubusercontent.com/microsoft/terminal/main/doc/cascadia/SettingsSchema.json",
            "defaultProfile": self.defaultProfile,
            "profiles": {
                "defaults": {},
                "list": [p.to_dict() for p in self.profiles]
            },
            "schemes": self.schemes,
            **self.extra
        }

    @staticmethod
    def from_dict(data: dict) -> "TerminalSettings":
        profiles_data = data.get("profiles", {})
        profile_list = profiles_data.get("list", [])
        profiles = [Profile.from_dict(p) for p in profile_list]
        schemes = data.get("schemes", [])
        extra = {k: v for k, v in data.items()
                 if k not in {"profiles", "defaultProfile", "schemes", "$schema"}}
        return TerminalSettings(
            profiles=profiles,
            defaultProfile=data.get("defaultProfile", ""),
            schemes=schemes,
            extra=extra
        )
