# Running the persistent host

Use a full Windows Python 3.11+ interpreter, Playwright and SymPy. Reuse the project interpreter if it can import `playwright.sync_api` and `sympy`. Otherwise `scripts/install.ps1` probes the Python launcher and the installed Codex runtime, and returns the path of the project venv interpreter. A broken venv is left intact and the installer creates a clean sibling. Chrome is the default channel. Use `--channel msedge` for installed Edge.

Example (replace absolute paths with this installed skill and the user's chosen workspace):

```powershell
$ixlPython = & '<skill>\scripts\install.ps1' -Workspace '<workspace>' | Select-Object -Last 1
& $ixlPython -u '<skill>\scripts\session.py' --workspace '<workspace>' --url 'https://www.ixl.com/math/algebra-2/identify-probability-distributions'
```

Use a stable workspace folder for the host so local adapters and the profile are available on the next invocation. Keep the subprocess and stdin session alive. Retain its session identifier in the chat's working notes. `--profile` can point to a previously authorized application profile; do not open it concurrently in two hosts. It remains local and is not copied into the skill. Existing authenticated browser sessions cannot be attached merely by launching another process; reuse their actual host or close it only when the user intends to switch hosts.

Wait for `ready`, then allow manual login if necessary. Send one JSON command per line through the existing session stdin:

```json
{"action":"inspect"}
{"action":"practice","target_score":90,"strict":false,"max_seconds":180,"permitted_practice":true,"submission_authorized":true}
```

Set authorization flags only when the user actually requested permitted practice. These flags are a guard, not a source of permission. A packaging/installation/test request alone does not permit submitting to a real account.

After a goal, pause or exception, continue using the same host. To switch skills:

```json
{"action":"navigate","url":"https://www.ixl.com/math/calculus/chain-rule"}
{"action":"inspect"}
{"action":"practice","target_score":80,"strict":true,"max_seconds":180,"permitted_practice":true,"submission_authorized":true}
```

`strict:true` means greater than the target. When the built-in adapter does not match the active format, prepare a [local adapter](adaptation.md) in the same host, verify the live input and resend the original goal with its `adapter` name.

For a built-in adapter error, inspect the latest result and the live page before resuming. A last row without confirmed feedback, a click error or a page transition can mean the previous answer was submitted. Resume adaptation only after establishing that the failure happened before submission or that the previous submission succeeded.

## Pause and cancellation

During an active practice call, create an empty file named `STOP` in the host workspace using the filesystem tool. Each adapter checks it before every submission; an already-clicked submission may still receive feedback, but the next one is blocked. Do not rely on queued stdin pause/close being processed in the middle of a synchronous run.

Remove pending tool-side commands on cancellation. For an idle host, `{"action":"pause"}` sets STOP. After an explicit user resume, send a new authorized practice command with `"resume":true`; otherwise the host refuses to clear STOP. An incorrect/unknown feedback result returns to idle; inspect it before deciding whether the user's existing authorization still permits continuation. Never clear a user cancellation just because time passed.

Close only on explicit user intent to exit: `{"action":"close"}`. EOF/host termination also releases the browser, so keep the stdin session alive while the user wants the window retained. Browser operation timeouts can delay cancellation of an operation already in progress.

## Local verification

```powershell
$env:PYTHONPATH='<skill>\scripts\runtime;<skill>\scripts'
& '<workspace>\.venv\Scripts\python.exe' -m pytest '<skill>\scripts\tests' -q
```

These tests are local only. Do not run archived real-account reports as tests. The skill package deliberately excludes the old live-test harnesses, user screenshots, browser profiles and Codex credentials.

Outputs go to workspace `reports/chain`, `reports/probability`, or `reports/piecewise`. Save/rename result.json before starting another run of the same adapter, because the next run replaces that report. Keep a final score screenshot and measured times. Logs distinguish positive score progress from explicitly captured Correct text.
