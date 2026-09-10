import json
import os
import select
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from knowb_org_index.okf import diagnostics


@unittest.skipUnless(diagnostics()["available"], "build mcp/okf-bridge for stdio acceptance")
class StdioAcceptanceTests(unittest.TestCase):
    def test_installed_command_can_initialize_list_search_and_read(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            source = root / "docs" / "one.md"
            source.write_text("# One\nstdio-needle\n", encoding="utf-8")
            config = root / "registry.yml"
            config.write_text(
                yaml.safe_dump(
                    {
                        "version": 1,
                        "organization": "knowb-ai",
                        "strict_manifests": False,
                        "allowed_roots": [str(root)],
                        "state_dir": str(root / "state"),
                        "projects": [
                            {
                                "id": "project",
                                "path": str(root),
                                "knowledge": {"roots": [{"path": "docs"}]},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            environment = {
                key: value
                for key, value in os.environ.items()
                if key not in {"KNOWB_ORG_ROOT", "KNOWB_ORG_CONFIG", "PYTHONPATH"}
            }
            if os.environ.get("KNOWB_PORTABLE_PYTHON"):
                environment.pop("PYTHONPATH", None)
            else:
                environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
            process = subprocess.Popen(
                [sys.executable, "-m", "knowb_org_index.server", "--config", str(config)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=environment,
            )
            def stop_process() -> None:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=3)
                for stream in (process.stdin, process.stdout, process.stderr):
                    if stream is not None:
                        stream.close()

            self.addCleanup(stop_process)

            def notify(message: dict[str, object]) -> None:
                assert process.stdin is not None
                process.stdin.write(json.dumps(message) + "\n")
                process.stdin.flush()

            def request(message: dict[str, object]) -> dict[str, object]:
                assert process.stdin is not None
                assert process.stdout is not None
                process.stdin.write(json.dumps(message) + "\n")
                process.stdin.flush()
                ready, _, _ = select.select([process.stdout], [], [], 20)
                self.assertTrue(ready, "MCP stdio response timed out")
                line = process.stdout.readline()
                self.assertTrue(line, "MCP stdio process exited without a response")
                return json.loads(line)

            initialized = request(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "p6-test", "version": "1"},
                    },
                }
            )
            self.assertEqual(initialized["result"]["serverInfo"]["version"], "0.2.0")
            notify({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
            tools = request({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
            names = {item["name"] for item in tools["result"]["tools"]}
            self.assertTrue({"search_knowledge", "read_project_doc", "get_project_context"} <= names)
            search = request(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "search_knowledge",
                        "arguments": {"query": "stdio-needle", "projects": ["project"], "limit": 1},
                    },
                }
            )
            hit = search["result"]["structuredContent"]["results"][0]
            self.assertEqual(hit["path"], "docs/one.md")
            read = request(
                {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {
                        "name": "read_project_doc",
                        "arguments": {"project": "project", "path": hit["path"]},
                    },
                }
            )
            self.assertIn("stdio-needle", read["result"]["structuredContent"]["content"])


if __name__ == "__main__":
    unittest.main()
