from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OfficialTextParseResult:
    roles: list[dict[str, object]]
    majors: list[dict[str, object]]


def parse_official_text(path: Path) -> OfficialTextParseResult:
    """Parse a local, normalized public catalog text file without any network access."""

    roles: list[dict[str, object]] = []
    majors: list[dict[str, object]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "：" not in line:
            continue
        prefix, content = line.split("：", 1)
        values = [part.strip() for part in content.split("|")]
        if len(values) < 2 or not values[0] or not values[1]:
            continue
        aliases = _split_aliases(values[2] if len(values) > 2 else "")
        if prefix == "职业":
            roles.append(
                {
                    "role_name": values[0],
                    "family": values[1],
                    "aliases": aliases,
                }
            )
        elif prefix == "专业":
            majors.append(
                {
                    "major_name": values[0],
                    "category": values[1],
                    "aliases": aliases,
                }
            )
    return OfficialTextParseResult(roles=roles, majors=majors)


def _split_aliases(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]
