"""Small dependency-free config loader for career vaults."""

from __future__ import annotations

import fnmatch
import json
import os
from pathlib import Path

DEFAULT_IGNORE_GLOBS = [".obsidian/**", ".git/**", "node_modules/**", ".tmp/**"]
DEFAULT_PRIVATE_GLOBS = ["private/**", "*.private.md", "**/*.private.md"]


def _strip_comment(line: str) -> str:
    quote = None
    out = []
    for char in line:
        if char in ("'", '"'):
            quote = None if quote == char else (char if quote is None else quote)
        if char == "#" and quote is None:
            break
        out.append(char)
    return "".join(out).rstrip()


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def _scalar(value: str):
    value = _unquote(value)
    low = value.lower()
    if low in {"true", "false"}:
        return low == "true"
    if low in {"null", "none", "~"}:
        return None
    try:
        return int(value)
    except ValueError:
        return value


def load_config(path: str | Path | None) -> dict:
    if not path:
        return {}
    p = Path(path).expanduser()
    if not p.exists():
        return {}
    if p.suffix.lower() == ".json":
        return json.loads(p.read_text(encoding="utf-8"))
    config: dict = {}
    current = None
    for raw in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = _strip_comment(raw)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        text = line.strip()
        if indent == 0:
            key, sep, value = text.partition(":")
            if not sep:
                continue
            key = key.strip()
            if value.strip():
                config[key] = _scalar(value)
                current = None
            else:
                current = key
                if key == "vaults":
                    config[key] = []
                elif key in ("ignore_globs", "private_globs"):
                    config[key] = []
                else:
                    config[key] = {}
            continue
        if current == "vaults" and isinstance(config.get("vaults"), list):
            if text.startswith("- "):
                item = text[2:].strip()
                if ":" in item:
                    key, value = item.split(":", 1)
                    config["vaults"].append({key.strip(): _scalar(value)})
                else:
                    config["vaults"].append(_scalar(item))
            elif ":" in text and config["vaults"] and isinstance(config["vaults"][-1], dict):
                key, value = text.split(":", 1)
                config["vaults"][-1][key.strip()] = _scalar(value)
        elif current in ("ignore_globs", "private_globs") and text.startswith("- "):
            config[current].append(_scalar(text[2:]))
        elif current == "resume" and isinstance(config.get("resume"), dict) and ":" in text:
            key, value = text.split(":", 1)
            config["resume"][key.strip()] = _scalar(value)
    return config


def discover_config(explicit: str | Path | None = None) -> dict:
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    env_config = os.environ.get("CAREER_VAULT_CONFIG")
    if env_config:
        candidates.append(Path(env_config))
    candidates.extend([Path.cwd() / "career-vault.yaml", Path.cwd() / "career-vault.yml", Path.cwd() / "career-vault.json"])
    for path in candidates:
        if path.exists():
            return load_config(path)
    return {}


def resolve_vaults(explicit_vaults: list[str] | None = None, config_path: str | None = None) -> tuple[list[Path], dict]:
    config = discover_config(config_path)
    explicit = [Path(item).expanduser() for item in (explicit_vaults or []) if item]
    if explicit:
        return explicit, config
    entries = config.get("vaults") or []
    resolved = []
    for item in entries:
        raw = item.get("path") if isinstance(item, dict) else item
        if raw:
            resolved.append(Path(str(raw)).expanduser())
    if resolved:
        return resolved, config
    env_vault = os.environ.get("CAREER_VAULT")
    if env_vault:
        return [Path(env_vault).expanduser()], config
    raise ValueError("No career vault configured. Pass --vault, set CAREER_VAULT, or provide career-vault.yaml.")


def ignored(relative_path: str, config: dict, include_private: bool = False) -> bool:
    patterns = list(config.get("ignore_globs") or DEFAULT_IGNORE_GLOBS)
    if not include_private:
        patterns += list(config.get("private_globs") or DEFAULT_PRIVATE_GLOBS)
    rel = relative_path.replace("\\", "/")
    return any(fnmatch.fnmatch(rel, pattern.replace("\\", "/")) for pattern in patterns)


def iter_markdown(vault: Path, config: dict, include_private: bool = False):
    for path in sorted(vault.rglob("*.md")):
        rel = path.relative_to(vault).as_posix()
        if not ignored(rel, config, include_private=include_private):
            yield path
