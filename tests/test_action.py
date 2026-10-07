import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
STEP = next(
    step
    for step in yaml.safe_load((ROOT / "action.yml").read_text())["runs"]["steps"]
    if step.get("id") == "generate_version"
)


class ActionTests(unittest.TestCase):
    def run_action(self, changes="fix: example", old_tag="1.2.3", **inputs):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            action_path = workspace / "action with spaces"
            shutil.copytree(ROOT / "scripts", action_path / "scripts")
            output = workspace / "output"
            values = {
                "github.action_path": str(action_path),
                "inputs.changes": changes,
                "inputs.old-tag": old_tag,
                "inputs.prerelease-tag": inputs.get("prerelease_tag", ""),
                "inputs.major-release": inputs.get("major_release", ""),
            }

            def render(text):
                for name, value in values.items():
                    text = text.replace("${{ " + name + " }}", value)
                return text

            env = os.environ.copy()
            env.update({name: render(value) for name, value in STEP.get("env", {}).items()})
            env["GITHUB_OUTPUT"] = str(output)
            env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env["PATH"]
            result = subprocess.run(
                ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", render(STEP["run"])],
                cwd=workspace,
                env=env,
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertFalse((workspace / "marker").exists())
            return result, output.read_text() if output.exists() else ""

    def test_version_bumps(self):
        cases = [
            ({}, "1.2.4"),
            ({"changes": "fix: example\nfeat: example"}, "1.3.0"),
            ({"prerelease_tag": "alpha"}, "1.2.4-alpha.1"),
            ({"old_tag": "1.2.3-alpha.1"}, "1.2.3"),
            ({"major_release": "true"}, "2.0.0"),
        ]
        for inputs, expected in cases:
            with self.subTest(inputs=inputs):
                result, output = self.run_action(**inputs)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(output, f"new_tag={expected}\n")

    def test_changes_are_literal(self):
        for changes in [
            'fix: "quoted" $(touch marker)\nfix: `touch marker`',
            "--major_release=true",
        ]:
            with self.subTest(changes=changes):
                result, output = self.run_action(changes=changes)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(output, "new_tag=1.2.4\n")

    def test_major_release_is_literal(self):
        result, output = self.run_action(major_release="$(touch marker)")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output, "new_tag=2.0.0\n")

    def test_invalid_tags_do_not_write_outputs(self):
        for inputs in [
            {"old_tag": "1.2.3$(touch marker)"},
            {"prerelease_tag": "alpha$(touch marker)"},
            {"prerelease_tag": "alpha\nextra_output=value"},
        ]:
            with self.subTest(inputs=inputs):
                result, output = self.run_action(**inputs)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(output, "")


if __name__ == "__main__":
    unittest.main()
