import io
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from release_evidence import EvidenceError, generate


class ReleaseEvidenceTests(unittest.TestCase):
    def _wheel(self, path: Path, *, private: bool = False) -> None:
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(
                "knowb_org_index-0.2.0.dist-info/METADATA",
                "Name: knowb-org-index\nVersion: 0.2.0\nRequires-Dist: PyYAML>=6.0\n",
            )
            archive.writestr(
                "knowb_org_index-0.2.0.dist-info/WHEEL",
                "Root-Is-Purelib: false\nTag: py3-none-macosx_11_0_arm64\n",
            )
            archive.writestr(
                "knowb_org_index/_bin/knowb-okf-bridge-aarch64-apple-darwin",
                b"native",
            )
            if private:
                archive.writestr("knowb_org_index/.knowb-state/org-index.sqlite", b"private")

    def _root(self, root: Path) -> None:
        (root / "src/knowb_org_index").mkdir(parents=True)
        (root / "src/knowb_org_index/protocol.py").write_text(
            'OKF_RS_REVISION = "6d52cc7ad0b5afea2e0001779b4498e268905ddc"\n',
            encoding="utf-8",
        )
        (root / "uv.lock").write_text("version = 1\n", encoding="utf-8")

    def test_generates_hashes_sbom_and_license_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._root(root)
            artifacts = root / "artifacts"
            artifacts.mkdir()
            wheel = artifacts / "knowb_org_index-0.2.0-py3-none-macosx_11_0_arm64.whl"
            self._wheel(wheel)
            with tarfile.open(artifacts / "knowb_org_index-0.2.0.tar.gz", "w:gz") as archive:
                info = tarfile.TarInfo("knowb_org_index-0.2.0/README.md")
                info.size = 5
                archive.addfile(info, io.BytesIO(b"hello"))
            output = root / "evidence"
            manifest = generate(
                artifacts,
                output,
                source_commit="abc123",
                target="aarch64-apple-darwin",
                root=root,
            )
            self.assertEqual(manifest["version"], "0.2.0")
            self.assertEqual(len(manifest["artifacts"]), 2)
            self.assertTrue((output / "checksums.txt").is_file())
            self.assertTrue((output / "sbom.cdx.json").is_file())
            self.assertTrue((output / "licenses.json").is_file())

    def test_rejects_private_paths_before_writing_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._root(root)
            artifacts = root / "artifacts"
            artifacts.mkdir()
            self._wheel(
                artifacts / "knowb_org_index-0.2.0-py3-none-macosx_11_0_arm64.whl",
                private=True,
            )
            with self.assertRaisesRegex(EvidenceError, "private paths"):
                generate(
                    artifacts,
                    root / "evidence",
                    source_commit="abc123",
                    target="aarch64-apple-darwin",
                    root=root,
                )


if __name__ == "__main__":
    unittest.main()
