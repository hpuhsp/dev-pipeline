# Review Evals · 审查评测用例

Sample diffs with **seeded, known defects** for verifying that the dev-pipeline review phase (1A parallel agents or 1B serial fallback) actually catches what it claims to catch. Each defect is marked with an `EXPECTED:` comment in the fixture.

含**已知植入缺陷**的样例 diff，用于验证审查阶段（1A 并行 / 1B 串行）真能抓出宣称能抓的问题。每个缺陷在 fixture 中以 `EXPECTED:` 注释标记。

## How to Run · 运行方式

1. In any AI agent with the dev-pipeline skill installed, paste a fixture's diff content and ask: *"Review this diff using the dev-pipeline code review checklist"* (or apply the diff in a scratch git repo and run the Review Only mode).
2. Compare the findings against the expected table below.
3. **Pass bar**: every expected finding is reported (severity may differ by ±1 level; confidence ≥ 5).

## Expected Findings · 预期发现

### `fixtures/js-defects.diff` (TypeScript)

| Location | Expected finding | Reviewer | Severity |
|----------|-----------------|----------|----------|
| `API_KEY` constant | Hardcoded secret | Agent 1 / Pass 1 | BLOCKER |
| `searchUsers` | SQL injection via string concatenation | Agent 1 / Pass 1 | BLOCKER |
| `notifyAll` loop | N+1 query + sequential awaits (missed `Promise.all`) | Agent 2 / Pass 2 | WARNING+ |
| `isAdult` | `==` instead of `===`; type coercion bug | Agent 1+3 / Pass 1+3 | WARNING |
| `getName` | Missing null check on `user.profile` | Agent 1 / Pass 1 | WARNING+ |

### `fixtures/python-defects.diff` (Python)

| Location | Expected finding | Reviewer | Severity |
|----------|-----------------|----------|----------|
| `PASSWORD` constant | Hardcoded credential | Agent 1 / Pass 1 | BLOCKER |
| `add_tag` | Mutable default argument | Agent 1+3 / Pass 1+3 | WARNING+ |
| `get_timeout` | `dict[key]` without `.get()` — KeyError risk | Agent 1 / Pass 1 | WARNING |
| `run_backup` | Shell injection via `os.system` + concatenation | Agent 1 / Pass 1 | BLOCKER |
| `load_session` | Unsafe `pickle.loads` on untrusted input | Agent 1 / Pass 1 | BLOCKER |
| `read_all` | Unclosed file handle (no `with`); `except: pass` swallows errors | Agent 1+3 / Pass 1+3 | WARNING |

### `fixtures/java-defects.diff` (Java)

| Location | Expected finding | Reviewer | Severity |
|----------|-----------------|----------|----------|
| `FORMAT` field | `SimpleDateFormat` is thread-unsafe; P3C mandates `java.time` | Agent 3 / Pass 3 | BLOCKER |
| `name()` | Missing `@Override` (P3C mandatory) | Agent 3 / Pass 3 | BLOCKER |
| `formatIds` | String concatenation in loop — use `StringBuilder` (P3C) | Agent 2+3 / Pass 2+3 | WARNING |
| `sameOwner` | NPE risk: `equals` on possibly-null; constant-first convention | Agent 1 / Pass 1 | WARNING+ |
| `parse` | Empty catch block swallows exception | Agent 3 / Pass 3 | WARNING+ |

## Notes

- Fixtures are diffs (not live code) on purpose — the review phase consumes `git diff` output.
- `Severity WARNING+` means WARNING or BLOCKER are both acceptable.
- False positives beyond the expected list are acceptable if confidence-gated correctly (low-confidence → appendix).
