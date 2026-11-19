# Verified adapters and new-format preparation

| URL path | Verified format | Mathematical check | Input |
|---|---|---|---|
| /math/calculus/make-a-piecewise-function-continuous | Two branches, common boundary, one included endpoint, finite rational solutions of linear/quadratic parameter equations | Exact equation solve, directional limits after substituting each root, and the included branch's actual boundary value | Plain input.fillIn, comma-separated all-solutions list, exact field readback |
| /math/calculus/chain-rule | Function/derivative value tables with a requested composition derivative at a point | Correct inner/outer lookup plus automatic differentiation of a Hermite-interpolated composition matching every provided value and derivative | Plain numeric input.fillIn, exact field readback |
| /math/algebra-2/identify-probability-distributions | Table of probabilities with yes/no validity question | Every probability in [0,1] and exact sum 1; SymPy Rational cross-checked with Fraction | Unique scoped role=radio yes/no; aria-checked must be true before Submit |
| /math/calculus/find-tangent-lines-using-implicit-differentiation | Rational slope and tangent equation at a specified point | Implicit partial derivatives checked by substituting the tangent into the original equation and testing the first-order term | One slope editor, three point-slope editors, or a single full-equation editor |

## Preparation for a new skill

Navigate and inspect without submitting. Read active visible DOM, not hidden app state or private APIs. Capture a question-only screenshot if layout is material. Determine the real mathematical schema and input widget. Do not assume a named calculus skill shares another skill's formula parser. In the live chain-rule skill the useful representation was a numeric table.

Separate recognition from reasoning. Preserve fraction numerator/denominator, exponent base/power, unary minus, composition order, all requested roots, endpoint inclusion and units. If extraction drops a sign or table column, abstain before reasoning. For formula math, the IXL expression DOM uses `.vFrac`, `.wholeExp`, `.contractedTimes` and specialized function elements; flat innerText can collapse x^3 to x3 or merge a worked example with the active problem.

Implement only the observed format first, with a local regression for ambiguity, missing data and an appropriate independent mathematical check. Validate the answer format before the first live submission. Normal text/radio inputs are fast; symbolic proxy inputs need careful keyboard state. After typing an exponent, ArrowRight exits it. Trigonometric functions should use their symbol buttons, not plain product letters. Read back the editor DOM and prove the resulting expression equivalent; checking the intended string alone is insufficient. Block submission on mismatch.

Only then run continuously inside one browser. Do not recover a Good job/score animation by reopening the browser. Wait for changed active-question content and a visible changed score stable for 300 ms. A full navigation may destroy an execution context: pause and inspect the live page, never blindly resubmit the previous answer. Check the actual displayed score after any uncertain result.

## Resume the original goal with a workspace adapter

1. Send `{"action":"inspect","capture":true}` to save the active question fragment and screenshot. The capture includes widget structure and is for inspection, not execution. Use it to build a minimal offline fixture. Write a local adapter at `<workspace>/local_adapters/<name>.py`. Reuse an existing local adapter if its local fixtures and current widget still match. Use a lowercase name with digits or underscores.
2. Implement the contract below. The exact path is required. Return JSON-compatible question data containing every value and option that affects the answer. Extract only the problem and choices, excluding editable values so readback does not change the question identity.

   | Interface | Responsibility |
   |---|---|
   | `SKILL_PATH` | Exact IXL practice URL path without a trailing slash |
   | `extract(question)` | Read the current Playwright question locator. Raise on unsupported or ambiguous layout |
   | `solve(data)` | Compute the intended exact answer |
   | `verify(data, answer)` | Independently verify the math and return a boolean |
   | `fill(question, answer)` | Set only the answer widget, through ordinary user-facing interactions. Do not press Enter or Submit |
   | `read(question)` | Read the actual selected choice or rendered answer |
   | `equivalent(data, answer, actual)` | Return a boolean based on exact answer equivalence |

3. Run local checks on the observed format, at least one edge case, and rejection of ambiguous input. Send `{"action":"verify_input","adapter":"<name>"}` in the still-open host. This fills and reads the current editor without submitting. Fix mismatches locally and repeat. Once it returns `input_verified`, send the original practice command with `"adapter":"<name>"`. The host reloads the workspace file on each command, so it needs no browser restart. It repeats the checks on each question, then submits and waits for the platform result.
4. If the next variant returns `pre_submit_blocked`, inspect and extend the same adapter, run the relevant local checks and repeat the readback before continuing. `incorrect` stops the run. On `unknown_feedback`, use `review_submission` to confirm a delayed positive result without clicking. Continue only when that command confirms success and the original authorization still applies.

The bundled runtime includes polynomial/rational derivative and editor utilities from development, but no advertised fresh-host adapter for that skill. General trigonometric quotient-rule input did not complete its integration test; adapting it remains separate work. Do not route unsupported tasks through a nearby supported skill just to achieve a score.
