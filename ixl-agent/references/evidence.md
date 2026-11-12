# Observed evidence and honest reporting

These are single real practice sessions on 2026-11-12, not general accuracy guarantees:

| Skill | Displayed score progress | Submitted questions | Active continuous practice time |
|---|---|---|---|
| Piecewise continuity | 75 -> 80 -> 84 -> 88 -> 92 | 4 | 9.289 s |
| Chain-rule tables | 0 -> 15 -> 28 -> 39 -> 48 -> 56 -> 63 -> 69 -> 75 -> 80 -> 84 | 10 | 16.777 s |
| Probability distributions | 0 -> 15 -> 28 -> 39 -> 48 -> 56 -> 63 -> 69 -> 75 -> 80 -> 84 -> 88 -> 92 | 12 | 21.581 s |

Each row used one existing logged-in browser and showed positive platform score changes and new questions. Correctness was inferred from platform progress, not from a captured Correct banner for every question. Preparation, adapter development, local tests and tool orchestration are outside those active-loop timings. Never describe them as total request wall times or guaranteed throughput.

During earlier rational-derivative development, two incorrectly formatted editor submissions lowered SmartScore from 69 to 59. Exponent caret scope caused the problem. After symbolic editor readback was added, a separately authorized single retry advanced 59 to 66. This is why intended-answer correctness cannot replace rendered-input validation. Do not replay those failures on a real account as packaging tests.

Codex ChatGPT authentication/thread startup worked, but inference timed out; no completed model answer was scored. There is no paid API fallback. Browser profile persistence across normal restarts worked, but automatic crash reconnection and uncertain in-flight submission recovery were not implemented. Keep these limits visible rather than calling the entire project universally end-to-end verified.

The new portable host must pass local contract tests. That validates packaging and execution guards, not a new real-account session. Only run a live session when the user actually requests permitted practice.
