import importlib.util
import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
GATE_PATH = (
    ROOT / ".claude" / "skills" / "dev-pipeline" / "scripts" / "codegraph_gate.py"
)
SPEC = importlib.util.spec_from_file_location("codegraph_gate", GATE_PATH)
assert SPEC and SPEC.loader
codegraph_gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(codegraph_gate)


def completed(command, code=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(command, code, stdout, stderr)


class CodeGraphGateTests(unittest.TestCase):
    def make_repository(self, directory: pathlib.Path) -> pathlib.Path:
        repository = directory / "repository"
        (repository / ".codegraph").mkdir(parents=True)
        (repository / ".codegraph" / "codegraph.db").write_text("index")
        return repository

    def test_missing_index_is_not_required_and_never_invokes_cli(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            codegraph_gate.shutil, "which"
        ) as which:
            report = codegraph_gate.build_report(pathlib.Path(directory))

        self.assertFalse(report["codegraph"]["available"])
        self.assertEqual("index-missing", report["codegraph"]["reason"])
        self.assertEqual("not-required", report["affected"]["state"])
        which.assert_not_called()

    def test_wasm_backend_stays_available_with_a_performance_warning(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = self.make_repository(pathlib.Path(directory))
            responses = [
                completed(["codegraph", "status", "--json"], stdout='{"backend":"wasm"}'),
                completed(["git", "diff", "HEAD", "--name-only"], stdout="src/auth.ts\n"),
                completed(
                    ["codegraph", "affected", "--stdin", "--json"],
                    stdout='["tests/auth.test.ts"]',
                ),
            ]
            with mock.patch.object(
                codegraph_gate.shutil, "which", return_value="codegraph"
            ), mock.patch.object(codegraph_gate, "run", side_effect=responses):
                report = codegraph_gate.build_report(repository)

        self.assertTrue(report["codegraph"]["available"])
        self.assertIn("wasm-backend", report["codegraph"]["warnings"])
        self.assertEqual("executed", report["affected"]["state"])
        self.assertEqual(["tests/auth.test.ts"], report["affected"]["tests"])
        self.assertTrue(report["evidence_complete"])

    def test_empty_affected_result_is_recorded_as_execution_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = self.make_repository(pathlib.Path(directory))
            responses = [
                completed(["codegraph", "status", "--json"], stdout="{}"),
                completed(["git", "diff", "HEAD", "--name-only"], stdout="src/auth.ts\n"),
                completed(
                    ["codegraph", "affected", "--stdin", "--json"], stdout="[]"
                ),
            ]
            with mock.patch.object(
                codegraph_gate.shutil, "which", return_value="codegraph"
            ), mock.patch.object(codegraph_gate, "run", side_effect=responses):
                report = codegraph_gate.build_report(repository)

        self.assertEqual("empty", report["affected"]["state"])
        self.assertEqual("no-affected-tests", report["affected"]["reason"])
        self.assertTrue(report["evidence_complete"])

    def test_affected_failure_is_recorded_for_repository_local_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = self.make_repository(pathlib.Path(directory))
            responses = [
                completed(["codegraph", "status", "--json"], stdout="{}"),
                completed(["git", "diff", "HEAD", "--name-only"], stdout="src/auth.ts\n"),
                completed(
                    ["codegraph", "affected", "--stdin", "--json"],
                    code=2,
                    stderr="index temporarily locked",
                ),
            ]
            with mock.patch.object(
                codegraph_gate.shutil, "which", return_value="codegraph"
            ), mock.patch.object(codegraph_gate, "run", side_effect=responses):
                report = codegraph_gate.build_report(repository)

        self.assertEqual("failed", report["affected"]["state"])
        self.assertEqual("affected-failed", report["affected"]["reason"])
        self.assertEqual(2, report["affected"]["affected"]["exit_code"])


if __name__ == "__main__":
    unittest.main()
