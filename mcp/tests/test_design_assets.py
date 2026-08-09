import unittest
from pathlib import Path

from knowb_org_index.design_assets import DesignAssetError, DesignAssetOperations
from knowb_org_index.models import DesignAssetConfig


class _FakeDrive:
    def __init__(self, permissions):
        self._permissions = permissions

    def permissions(self, _file_id):
        return self._permissions


class DesignAssetPolicyTests(unittest.TestCase):
    def setUp(self):
        repo_root = Path(__file__).resolve().parents[2]
        self.config = DesignAssetConfig(
            enabled=True,
            google_drive_folder_id="folder-id",
            allowed_google_email="owner@example.com",
            allowed_github_logins=("owner",),
            allowed_upload_roots=(repo_root / "static/design-system",),
        )
        self.operations = DesignAssetOperations(self.config, object())

    def test_user_acl_is_private(self):
        self.operations.drive = _FakeDrive([{"type": "user", "role": "owner"}])
        result = self.operations._private_permissions("folder-id")
        self.assertTrue(result["private"])

    def test_public_acl_is_rejected(self):
        self.operations.drive = _FakeDrive([{"type": "anyone", "role": "reader"}])
        with self.assertRaises(DesignAssetError):
            self.operations._private_permissions("folder-id")

    def test_upload_source_must_be_allowlisted_and_an_asset(self):
        asset = (
            Path(__file__).resolve().parents[2]
            / "static/design-system/knowb-autumn-palette.png"
        )
        result = self.operations._local_upload(str(asset))
        self.assertEqual(result["name"], asset.name)
        self.assertGreater(result["bytes"], 0)

        with self.assertRaises(DesignAssetError):
            self.operations._local_upload(str(Path(__file__).resolve().parents[2] / "README.md"))


if __name__ == "__main__":
    unittest.main()
