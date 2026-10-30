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
class MenuFolder:
    """A folder entry in the Windows Terminal newTabMenu."""

    name: str
    icon: Optional[str] = None
    entries: List[str] = field(default_factory=list)
    inlining: str = "never"
    allow_empty: bool = False

    def to_dict(self) -> dict:
        data = {
            "type": "folder",
            "name": self.name,
            "inlining": self.inlining,
            "entries": [{"type": "profile", "profile": guid} for guid in self.entries],
        }
        if self.icon:
            data["icon"] = self.icon
        if self.allow_empty:
            data["allowEmpty"] = True
        return data


def _resolve_profile_ref(ref: str, profiles: List[Profile]) -> Optional[str]:
    if not ref:
        return None
    ref_lower = ref.lower()
    for p in profiles:
        if p.guid.lower() == ref_lower:
            return p.guid
    for p in profiles:
        if p.name.lower() == ref_lower:
            return p.guid
    return None


@dataclass
class TerminalSettings:
    profiles: List[Profile] = field(default_factory=list)
    defaultProfile: str = ""
    schemes: List[Dict[str, Any]] = field(default_factory=list)
    profileDefaults: Dict[str, Any] = field(default_factory=dict)
    menu_folders: List[MenuFolder] = field(default_factory=list)
    menu_loose: List[str] = field(default_factory=list)
    menu_tail: List[Dict[str, Any]] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        data = {
            "$schema": "https://raw.githubusercontent.com/microsoft/terminal/main/doc/cascadia/SettingsSchema.json",
            "defaultProfile": self.defaultProfile,
            "profiles": {
                "defaults": self.profileDefaults,
                "list": [p.to_dict() for p in self.profiles]
            },
            "schemes": self.schemes,
            **self.extra
        }
        menu = self._serialize_menu()
        if menu is not None:
            data["newTabMenu"] = menu
        return data

    def _serialize_menu(self) -> Optional[List[Dict[str, Any]]]:
        if not self.menu_folders and not self.menu_loose and not self.menu_tail:
            return None
        entries: List[Dict[str, Any]] = []
        entries.extend(folder.to_dict() for folder in self.menu_folders)
        entries.extend({"type": "profile", "profile": guid} for guid in self.menu_loose)
        entries.extend(self.menu_tail)
        return entries

    @staticmethod
    def from_dict(data: dict) -> "TerminalSettings":
        profiles_data = data.get("profiles", {})
        profile_list = profiles_data.get("list", [])
        profile_defaults = profiles_data.get("defaults", {})
        profiles = [Profile.from_dict(p) for p in profile_list]
        schemes = data.get("schemes", [])
        extra = {k: v for k, v in data.items()
                 if k not in {"profiles", "defaultProfile", "schemes", "$schema"}}
        raw_menu = extra.pop("newTabMenu", None)
        settings = TerminalSettings(
            profiles=profiles,
            defaultProfile=data.get("defaultProfile", ""),
            schemes=schemes,
            profileDefaults=profile_defaults,
            extra=extra
        )
        settings._parse_menu(raw_menu)
        return settings

    def _parse_menu(self, raw_menu):
        if not isinstance(raw_menu, list):
            return
        hidden_guids = {p.guid for p in self.profiles if p.hidden}
        for entry in raw_menu:
            if not isinstance(entry, dict):
                self.menu_tail.append(entry)
                continue
            entry_type = entry.get("type")
            if entry_type == "folder":
                folder = MenuFolder(
                    name=entry.get("name", ""),
                    icon=entry.get("icon"),
                    inlining=entry.get("inlining", "never"),
                    allow_empty=bool(entry.get("allowEmpty", False)),
                )
                for child in entry.get("entries", []):
                    if not isinstance(child, dict) or child.get("type") != "profile":
                        continue
                    guid = _resolve_profile_ref(child.get("profile", ""), self.profiles)
                    if guid and guid not in hidden_guids:
                        folder.entries.append(guid)
                self.menu_folders.append(folder)
            elif entry_type == "profile":
                guid = _resolve_profile_ref(entry.get("profile", ""), self.profiles)
                if guid and guid not in hidden_guids:
                    self.menu_loose.append(guid)
            else:
                self.menu_tail.append(entry)

    @property
    def has_remaining_profiles_entry(self) -> bool:
        return any(
            isinstance(e, dict) and e.get("type") in ("remainingProfiles", "matchProfiles")
            for e in self.menu_tail
        )
