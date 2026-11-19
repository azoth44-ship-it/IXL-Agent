# IXL Agent

A Codex skill for permitted, self-directed IXL mathematics practice. It keeps one browser session open, checks exact answers independently, verifies the entered answer, and stops at the requested SmartScore or the first incorrect/unknown result.

This is an independent project, not affiliated with or endorsed by IXL. Use it only where automated practice is permitted. It does not bypass authentication, CAPTCHAs, or platform protections, and is not intended for prohibited graded or proctored work.

## Supported formats

| IXL skill | Implemented format |
| --- | --- |
| Identify probability distributions | Exact probability bounds and sum checks |
| Chain rule | Function and derivative lookup tables |
| Make a piecewise function continuous | Supported two-branch continuity problems |
| Find tangent lines using implicit differentiation | Rational slopes, three-field point-slope form, and a full tangent equation |

For a new or changed question format, Codex can add a workspace adapter, check it against the current editor without submitting, and resume the same goal in the open browser. Success depends on verifying the actual problem, input and score. Automatic browser crash recovery is not implemented.

## Install in Codex

Clone this repository and copy the `ixl-agent` folder into your Codex skills directory, normally `~/.codex/skills/`. Preserve any existing installation before replacing it. Start a new Codex chat if the skill is not yet listed.

Invoke it with a permitted practice URL and goal:

```text
$ixl-agent
Use https://www.ixl.com/math/algebra-2/identify-probability-distributions
for permitted practice until SmartScore reaches 90. Stop immediately if an answer is wrong.
```

The bundled installer and operating examples currently target Windows with Python 3.11+ and installed Chrome or Edge. The user signs in manually when needed. Browser profiles stay local. The host needs no separate model API key.

See [the operating reference](ixl-agent/references/operation.md) for dependency installation, the persistent host, JSON commands, and cancellation. Keep the host and its stdin alive to retain the browser window. During practice, create `STOP` in the session workspace to block the next submission.

## Local tests

From the repository root with Python 3.11+:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\ixl-agent\scripts\requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
$env:PYTHONPATH="$PWD\ixl-agent\scripts\runtime;$PWD\ixl-agent\scripts;$PWD\ixl-agent\scripts\adapters"
.\.venv\Scripts\python.exe -m pytest .\ixl-agent\scripts\tests -q
```

Tests use local fixtures and do not submit answers to IXL. The initial package passed 59 local tests. Prior live sessions demonstrated positive score progress on the three supported formats; [the evidence reference](ixl-agent/references/evidence.md) records timings, earlier failures, and limitations. Active practice timings exclude preparation and are not general speed or accuracy guarantees.

An optional [GitHub Actions template](examples/github-actions-tests.yml.example) is included. It is not enabled automatically; a maintainer can copy it to `.github/workflows/tests.yml` using an account with workflow-write permission.

## Privacy and contributions

Never commit browser profiles, cookies, credentials, screenshots, or personal practice reports. The repository includes source code, tests, and documentation only. Contributions should include a reproducible local fixture; real-account submissions require the account holder's explicit authorization.

Licensed under the [MIT License](LICENSE). Third-party dependencies retain their own licenses.

## 中文说明

在 Codex 中输入 `/ixl agent <练习链接> 目标90分`，也可以选择 `$ixl-agent`。已验证的题型走内置流程。遇到新题型，Codex 在同一浏览器里检查题面，完成适配和回读验证后接着原目标运行。达到目标、答错或无法确认反馈时暂停提交。需要登录时由用户手动完成。
