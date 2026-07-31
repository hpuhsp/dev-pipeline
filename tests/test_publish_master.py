import pathlib
import subprocess
import unittest
from unittest import mock

from scripts import publish_master


class PublishMasterTests(unittest.TestCase):
    def test_dry_run_does_not_invoke_mutating_commands(self):
        with mock.patch.object(publish_master, "output", return_value="main"), mock.patch.object(
            publish_master, "run"
        ) as run, mock.patch.object(
            publish_master, "parse_args",
            return_value=type(
                "Args",
                (),
                {
                    "main_branch": "main",
                    "master_branch": "master",
                    "main_remote": "origin2",
                    "master_remote": "origin",
                    "dry_run": True,
                },
            )(),
        ):
            self.assertEqual(0, publish_master.main())

        run.assert_not_called()

    def test_fast_forward_check_rejects_remote_divergence(self):
        with mock.patch.object(
            publish_master.subprocess,
            "run",
            return_value=subprocess.CompletedProcess([], 1),
        ):
            with self.assertRaisesRegex(RuntimeError, "not an ancestor"):
                publish_master.ensure_fast_forward("origin/master")

    def test_fast_forward_check_accepts_ancestor(self):
        with mock.patch.object(
            publish_master.subprocess,
            "run",
            return_value=subprocess.CompletedProcess([], 0),
        ):
            publish_master.ensure_fast_forward("origin/master")


if __name__ == "__main__":
    unittest.main()
