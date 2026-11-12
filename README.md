# IXL Agent

A Codex skill for permitted, self-directed IXL mathematics practice. It keeps one browser session open, checks exact answers independently, verifies the entered answer, and stops at the requested SmartScore or the first incorrect/unknown result.

This is an independent project, not affiliated with or endorsed by IXL. Use it only where automated practice is permitted. It does not bypass authentication, CAPTCHAs, or platform protections, and is not intended for prohibited graded or proctored work.

## Supported formats

| IXL skill | Implemented format |
| --- | --- |
| Identify probability distributions | Exact probability bounds and sum checks |
| Chain rule | Function and derivative lookup tables |
| Make a piecewise function continuous | Supported two-branch continuity problems |

Other question formats require adaptation and verification before submission. General quotient-rule practice, model inference, and automatic crash recovery are not validated capabilities.

## Install in Codex

Clone this repository and copy the `ixl-agent` folder into your Codex skills directory, normally `~/.codex/skills/`. Preserve any existing installation before replacing it. Start a new Codex chat if the skill is not yet listed.

Invoke it with a permitted practice URL and goal:

```text
$ixl-agent
Use https://www.ixl.com/math/algebra-2/identify-probability-distributions
for permitted practice until SmartScore reaches 90. Stop immediately if an answer is wrong.
```

The bundled installer and operating examples currently target Windows with Python 3.11+ and installed Chrome or Edge. The user signs in manually; browser profiles stay local. No API key or paid model service is required.

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

这是用于获准自主练习的 Codex 技能：保持浏览器常驻、精确计算和独立验算、回读输入、读取真实 SmartScore，达到目标或出现错题/未知反馈立即停止。当前仅支持上表中的三种已验证题型，不保证支持同名技能下的所有变化。安装时将 `ixl-agent` 文件夹复制到 `~/.codex/skills/`，在新聊天中用 `$ixl-agent` 加练习链接和目标分数调用。登录由用户手动完成，账户资料不会随技能发布。
