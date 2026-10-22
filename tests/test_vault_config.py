from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "career-evidence-miner" / "scripts"))

from vault_config import resolve_vaults  # noqa: E402


class VaultConfigTests(unittest.TestCase):
    def test_resolves_yaml_vaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "career-vault.yaml"
            config.write_text(
                f"vaults:\n  - path: {root / 'vault-a'}\n  - path: {root / 'vault-b'}\n"
                "ignore_globs:\n  - '.obsidian/**'\n"
                "resume:\n  language: zh-CN\n  max_pages: 1\n",
                encoding="utf-8",
            )
            vaults, data = resolve_vaults(None, str(config))
            self.assertEqual(len(vaults), 2)
            self.assertEqual(data["resume"]["language"], "zh-CN")


if __name__ == "__main__":
    unittest.main()
