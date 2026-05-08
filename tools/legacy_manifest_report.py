"""Print the legacy FastXAFS tool/dependency manifest without hardware imports."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastxafs_app.legacy_manifest import LEGACY_TOOLS


def main() -> int:
    for tool in LEGACY_TOOLS.values():
        print(f"{tool.key}: {tool.title}")
        print(f"  file: {tool.path}")
        print(f"  role: {tool.role}")
        print(f"  third-party: {', '.join(tool.third_party_dependencies) or '-'}")
        print(f"  local: {', '.join(tool.local_dependencies) or '-'}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
