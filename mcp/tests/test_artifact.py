import unittest
import tempfile
import zipfile
from pathlib import Path

from knowb_org_index.artifacts import ArtifactError, audit_wheel
from knowb_org_index.build_targets import platform_tag_for_target


class ArtifactContractTests(unittest.TestCase):
    def test_supported_targets_have_conservative_platform_tags(self):
        self.assertEqual(platform_tag_for_target("aarch64-apple-darwin"), "macosx_11_0_arm64")
        self.assertEqual(platform_tag_for_target("x86_64-unknown-linux-gnu"), "manylinux_2_17_x86_64")
        self.assertEqual(platform_tag_for_target("x86_64-pc-windows-msvc"), "win_amd64")

    def test_unknown_target_is_rejected(self):
        with self.assertRaises(ValueError):
            platform_tag_for_target("mystery-target")

    def test_wheel_audit_requires_one_native_bridge_and_non_pure_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            wheel = Path(directory) / "connector.whl"
            with zipfile.ZipFile(wheel, "w") as archive:
                archive.writestr(
                    "knowb_org_index-0.1.0.dist-info/WHEEL",
                    "Root-Is-Purelib: false\nTag: py3-none-macosx_11_0_arm64\n",
                )
                archive.writestr(
                    "knowb_org_index/_bin/knowb-okf-bridge-aarch64-apple-darwin",
                    b"native",
                )
            result = audit_wheel(wheel)
            self.assertIn("knowb-okf-bridge", result["binary"])

            with zipfile.ZipFile(wheel, "a") as archive:
                archive.writestr("knowb_org_index/config/local-projects.yml", "secret")
            with self.assertRaises(ArtifactError):
                audit_wheel(wheel)


if __name__ == "__main__":
    unittest.main()
