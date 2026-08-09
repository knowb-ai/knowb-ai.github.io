import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from knowb_org_index.env import load_dotenv


class EnvironmentLoaderTests(unittest.TestCase):
    def test_loads_values_without_overriding_shell_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text(
                "FROM_FILE=loaded\n"
                "QUOTED=\"quoted value\"\n"
                "export EXPORTED=also-loaded\n"
                "EXISTING=from-file\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"EXISTING": "from-shell"}, clear=False):
                load_dotenv(path)
                self.assertEqual(os.environ["FROM_FILE"], "loaded")
                self.assertEqual(os.environ["QUOTED"], "quoted value")
                self.assertEqual(os.environ["EXPORTED"], "also-loaded")
                self.assertEqual(os.environ["EXISTING"], "from-shell")


if __name__ == "__main__":
    unittest.main()
