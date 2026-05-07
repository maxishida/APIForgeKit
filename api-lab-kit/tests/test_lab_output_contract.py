import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LabOutputContractTests(unittest.TestCase):
    def test_ok_outputs_do_not_pass_raw_response_as_error_message(self):
        offenders = []
        for path in sorted((ROOT / "labs").glob("*_lab.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                if getattr(node.func, "id", "") != "save_output":
                    continue
                if len(node.args) < 2:
                    continue
                status_arg = node.args[1]
                if not isinstance(status_arg, ast.Constant) or status_arg.value != "ok":
                    continue
                if len(node.args) > 6:
                    offenders.append(f"{path.name}:{node.lineno}")

        self.assertEqual(
            [],
            offenders,
            "ok save_output calls must pass raw responses with raw_response=, not as error_message",
        )


if __name__ == "__main__":
    unittest.main()
