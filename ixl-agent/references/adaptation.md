# Verified adapters and new-format preparation

| URL path | Verified format | Mathematical check | Input |
|---|---|---|---|
| /math/calculus/make-a-piecewise-function-continuous | Two branches, common boundary, one included endpoint, finite rational solutions of linear/quadratic parameter equations | Exact equation solve, directional limits after substituting each root, and the included branch's actual boundary value | Plain input.fillIn, comma-separated all-solutions list, exact field readback |
| /math/calculus/chain-rule | Function/derivative value tables with a requested composition derivative at a point | Correct inner/outer lookup plus automatic differentiation of a Hermite-interpolated composition matching every provided value and derivative | Plain numeric input.fillIn, exact field readback |
| /math/algebra-2/identify-probability-distributions | Table of probabilities with yes/no validity question | Every probability in [0,1] and exact sum 1; SymPy Rational cross-checked with Fraction | Unique scoped role=radio yes/no; aria-checked must be true before Submit |

## Preparation for a new skill

Navigate and inspect without submitting. Read active visible DOM, not hidden app state or private APIs. Capture a question-only screenshot if layout is material. Determine the real mathematical schema and input widget. Do not assume a named calculus skill shares another skill's formula parser. In the live chain-rule skill the useful representation was a numeric table.

Separate recognition from reasoning. Preserve fraction numerator/denominator, exponent base/power, unary minus, composition order, all requested roots, endpoint inclusion and units. If extraction drops a sign or table column, abstain before reasoning. For formula math, the IXL expression DOM uses `.vFrac`, `.wholeExp`, `.contractedTimes` and specialized function elements; flat innerText can collapse x^3 to x3 or merge a worked example with the active problem.

Implement only the observed format first, with a local regression for ambiguity, missing data and an appropriate independent mathematical check. Validate the answer format before the first live submission. Normal text/radio inputs are fast; symbolic proxy inputs need careful keyboard state. After typing an exponent, ArrowRight exits it. Trigonometric functions should use their symbol buttons, not plain product letters. Read back the editor DOM and prove the resulting expression equivalent; checking the intended string alone is insufficient. Block submission on mismatch.

Only then run continuously inside one browser. Do not recover a Good job/score animation by reopening the browser. Wait for changed active-question content and a visible changed score stable for 300 ms. A full navigation may destroy an execution context: pause and inspect the live page, never blindly resubmit the previous answer. Check the actual displayed score after any uncertain result.

The bundled runtime includes polynomial/rational derivative and editor utilities from development, but no advertised fresh-host adapter for that skill. General trigonometric quotient-rule input did not complete its integration test; adapting it remains separate work. Do not route unsupported tasks through a nearby supported skill just to achieve a score.
