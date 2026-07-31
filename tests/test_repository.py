import pathlib
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / ".claude" / "skills" / "dev-pipeline"


class RepositoryContractTests(unittest.TestCase):
    def test_skill_frontmatter_contains_only_portable_trigger_metadata(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = skill.split("---", 2)[1].strip().splitlines()
        keys = {
            line.split(":", 1)[0]
            for line in frontmatter
            if line and not line.startswith((" ", "\t")) and ":" in line
        }

        self.assertEqual({"name", "description"}, keys)
        self.assertIn("name: dev-pipeline", skill)

    def test_skill_routes_user_intent_without_implicit_pipeline_fallthrough(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        routing = skill.split("## Intent Router", 1)[1].split("## Phase 0:", 1)[0]

        required_rules = (
            "Explicit user intent wins",
            "route_plan",
            "target_nodes",
            "supporting_nodes",
            "Do not fall through",
            "Full Pipeline",
            "Review Only",
            "Test Only",
            "Message Only",
            "Branch Only",
            "Commit Only",
        )
        for rule in required_rules:
            with self.subTest(rule=rule):
                self.assertIn(rule, routing)

        self.assertIn("Only explicit full-pipeline intent", routing)
        self.assertNotIn("Subsequent phases always run serially", skill)

    def test_ci_uses_change_aware_runner_and_publishes_reports(self):
        workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("python scripts/test_runner.py", workflow)
        self.assertIn("actions/upload-artifact@v4", workflow)
        self.assertIn("artifacts/test-results", workflow)

    def test_unit_test_phase_requires_decision_coverage_and_reports(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        test_section = skill.split("## Phase 2: Unit Test Generation", 1)[1].split(
            "## Phase 3:", 1
        )[0]

        for expected in (
            "test_decision",
            "pass rate",
            "requirement coverage",
            "scenario coverage",
            "JSON",
            "Markdown",
            "Agent evaluation",
            "token",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, test_section)

    def test_codegraph_commands_include_staged_changes(self):
        markdown = "\n".join(
            path.read_text(encoding="utf-8")
            for path in SKILL_ROOT.rglob("*.md")
        )
        self.assertNotIn(
            "git diff --name-only | codegraph affected",
            markdown,
            "CodeGraph must inspect staged as well as unstaged changes",
        )
        self.assertIn("git diff HEAD --name-only | codegraph affected", markdown)

    def test_codegraph_is_scoped_to_each_repository_context(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        detection = skill.split("**CodeGraph activation (optional, per repository)**", 1)[1].split(
            "Summarize:", 1
        )[0]

        self.assertIn("repository_contexts", skill)
        for rule in (
            "repository_context",
            "repository_context.codegraph.available",
            "<repository.root>/.codegraph/codegraph.db",
            "Never use a parent repository's `.codegraph` index for a submodule",
            "A subtree uses its parent context",
            "(cd \"<repository.root>\" && codegraph status --json)",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, detection)

    def test_codegraph_affected_runs_from_owning_repository(self):
        markdown = "\n".join(
            path.read_text(encoding="utf-8") for path in SKILL_ROOT.rglob("*.md")
        )

        self.assertIn(
            '(cd "<repository.root>" && git diff HEAD --name-only | codegraph affected --stdin --quiet)',
            markdown,
        )
        self.assertIn("Push-Location \"<repository.root>\"", markdown)
        self.assertNotIn("codegraph_available = true", markdown)

    def test_codegraph_requires_index_cli_and_healthy_status(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        detection = skill.split("**CodeGraph activation (optional, per repository)**", 1)[1].split(
            "Summarize:", 1
        )[0]

        required_rules = (
            ".codegraph/codegraph.db",
            "command -v codegraph",
            "Get-Command codegraph",
            "codegraph status --json",
            "all three checks pass",
            "repository_context.codegraph.available = true",
            "index-missing",
            "cli-missing",
            "status-unhealthy",
            "Do not install, initialize, or rebuild CodeGraph",
        )
        for rule in required_rules:
            with self.subTest(rule=rule):
                self.assertIn(rule, detection)

    def test_codegraph_wasm_backend_is_a_warning_not_an_availability_failure(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        tooling = (SKILL_ROOT / "references" / "tooling.md").read_text(encoding="utf-8")

        self.assertIn("`wasm` remains usable", skill)
        self.assertIn("wasm-backend", tooling)
        self.assertIn("do not classify it as `status-unhealthy`", tooling)

    def test_codegraph_execution_evidence_is_an_eligible_review_and_test_gate(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        review_reference = (SKILL_ROOT / "references" / "review-agents.md").read_text(
            encoding="utf-8"
        )
        test_reference = (SKILL_ROOT / "references" / "test-generation.md").read_text(
            encoding="utf-8"
        )

        for rule in (
            "### CodeGraph Execution Gate",
            "scripts/codegraph_gate.py",
            "Completion invariant",
            "Only an eligible `repository_context` runs",
            "`executed`, `empty`, or documented `failed` evidence",
            "Re-run the gate after any review fix",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, skill)

        self.assertIn("eligible, available context is `pending`", review_reference)
        self.assertIn("eligible context that resolves to `available = true`", skill)
        self.assertIn("Do not state that CodeGraph ran without this evidence", test_reference)

    def test_codegraph_is_skipped_for_ineligible_lightweight_work(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        tooling = (SKILL_ROOT / "references" / "tooling.md").read_text(encoding="utf-8")

        for rule in (
            "Do not check for CodeGraph here",
            "ordinary local changes, test-file-only changes, documentation/configuration-only changes",
            "do not run `status`, `affected`, graph exploration, or the gate script",
            "complete lightweight path, not a degraded result",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, skill)

        self.assertIn("For all other changes, record `not-needed` and make no CodeGraph call", tooling)

    def test_codegraph_complex_change_exploration_is_selective_and_bounded(self):
        tooling = (SKILL_ROOT / "references" / "tooling.md").read_text(encoding="utf-8")

        for rule in (
            "### Exploration gate for complex changes",
            'codegraph context "<task>" --max-nodes 30 --max-code 8 --format markdown',
            "codegraph query <symbol> --limit 10",
            "codegraph impact <symbol> --depth 2",
            "cross-module, affects a public API, route, core service, or unknown bug call chain",
            "do not add graph calls to trivial, local, or documentation-only changes",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, tooling)

    def test_branch_detection_checks_conventional_fix_prefix(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        detection_line = next(
            line for line in skill.splitlines() if "Auto-detect branch convention" in line
        )
        self.assertIn("'fix/*'", detection_line)

    def test_branch_selection_routes_to_repository_owning_changes(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        branch_section = skill.split("## Phase 4: Branch Selection", 1)[1].split(
            "## Phase 5:", 1
        )[0]

        required_rules = (
            "target_repo",
            "git -C \"<target_repo>\" rev-parse --abbrev-ref HEAD",
            "git -C \"<target_repo>\" checkout -b <branch-name>",
            "multiple repositories",
            "Git subtree",
            "git stash",
        )
        for rule in required_rules:
            with self.subTest(rule=rule):
                self.assertIn(rule, branch_section)

        self.assertIn("stop and ask the user to select", branch_section)
        self.assertNotIn("`git checkout -b <branch-name>`", branch_section)

        commit_section = skill.split("## Phase 5: Commit Execution", 1)[1]
        self.assertIn("inherit `target_repo`", commit_section)
        self.assertIn("git -C \"<target_repo>\"", commit_section)
        unscoped_commands = (
            "`git status --short`",
            "`git status --porcelain`",
            "`git add ",
            "`git reset --",
            "`git rm --cached",
            "`git commit ",
        )
        for command in unscoped_commands:
            with self.subTest(command=command):
                self.assertNotIn(command, commit_section)

    def test_packaged_skill_uses_portable_paths(self):
        with zipfile.ZipFile(ROOT / "dev-pipeline.skill") as package:
            invalid = [name for name in package.namelist() if "\\" in name]
        self.assertEqual([], invalid)

    def test_packaged_skill_matches_source_contents(self):
        expected = sorted(
            path.relative_to(SKILL_ROOT).as_posix()
            for path in SKILL_ROOT.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
        )
        with zipfile.ZipFile(ROOT / "dev-pipeline.skill") as package:
            actual = sorted(entry.filename for entry in package.infolist() if not entry.is_dir())
            self.assertEqual(expected, actual)
            for source in SKILL_ROOT.rglob("*"):
                if (
                    source.is_file()
                    and "__pycache__" not in source.parts
                    and source.suffix != ".pyc"
                ):
                    with self.subTest(path=source):
                        self.assertEqual(
                            source.read_bytes(),
                            package.read(source.relative_to(SKILL_ROOT).as_posix()),
                        )

    def test_sync_script_builds_a_portable_matching_package(self):
        with tempfile.TemporaryDirectory() as directory:
            package = pathlib.Path(directory) / "dev-pipeline.skill"
            installed = pathlib.Path(directory) / "installed"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "sync_skill.py"),
                    "--package",
                    str(package),
                    "--installed",
                    str(installed),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(0, result.returncode, result.stderr)
            check = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "sync_skill.py"),
                    "--package",
                    str(package),
                    "--installed",
                    str(installed),
                    "--check",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, check.returncode, check.stderr)


if __name__ == "__main__":
    unittest.main()
