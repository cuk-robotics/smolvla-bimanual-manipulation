"""Catch workflow syntax errors before they prevent GitHub Actions from starting."""
from pathlib import Path
import unittest

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(yaml is None, "PyYAML unavailable")
class WorkflowTests(unittest.TestCase):
    def test_workflow_commands_are_valid_yaml_strings(self):
        paths = sorted((ROOT / ".github/workflows").glob("*.yml"))
        self.assertTrue(paths, "No workflows found")
        for path in paths:
            with self.subTest(workflow=path.name):
                workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
                self.assertIsInstance(workflow, dict)
                for job in workflow["jobs"].values():
                    for step in job["steps"]:
                        if "run" in step:
                            self.assertIsInstance(step["run"], str)
                            self.assertTrue(step["run"].strip())


if __name__ == "__main__":
    unittest.main()
