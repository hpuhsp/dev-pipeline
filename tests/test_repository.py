import pathlib
import unittest
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / ".claude" / "skills" / "dev-pipeline"


class RepositoryContractTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
