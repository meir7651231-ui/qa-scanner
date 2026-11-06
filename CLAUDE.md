<!-- >>> agent-police >>> -->
## Verification gate (agent-police)

This repository has a machine gate. **You are not done when you think you are done — you are done when the machine says DONE.**

0. **Never guess what the customer did not say.** If part of the request is vague ("faster", "better"), contradicts itself, says
   "it doesn't work" without what happens, involves time without a time zone, or gives no example of the expected result:
   **do every part that is clear first, leave the unclear part untouched (no invented numbers, names or rules), and when nothing
   clear is left — or you hit a wall — stop and ask all the questions together. Never answer for the customer.** Then write an acceptance test from
   their answer and ask them to approve it (`node .agent-police/bin/agent-police.mjs task accept <test file>` — they run it, not you). Once approved it is locked.
   **Do not wait for that approval to work:** carry on, and list it under "What I need from you".
1. Do the task.
2. Run `node .agent-police/bin/agent-police.mjs check` and read the verdict.
3. If it says **NOT DONE**, the report names the gate and the file. Fix exactly that and run it again. Repeat until **DONE**.
4. When you report back, say what you did with **every** instruction in the request, and add two sections whenever they are not
   empty: **"Not done — and why"** and **"What I need from you"** (answers, decisions, approvals, access). The machine writes
   them for you in `.harness/handoff.md` — use it; hiding a gap fails the verdict. Claim nothing that did not happen
   (no "I tested it on staging" unless you did), and quote the machine's final verdict line verbatim.
5. **The same mistake never twice.** When the check caught a mistake and you fixed it, record a lesson so it cannot come back:
   `node .agent-police/bin/agent-police.mjs lesson add "<the rule in plain words>" --forbid "<a pattern of the mistake>"` (or `--test <the test that catches it>`).
   Lessons only accumulate — removing or changing one fails the verdict. If the same failure comes back twice in a row, stop
   and ask the owner which approach is right; do not try the same fix a third time.
6. **Give way to evidence, not to pressure.** When the customer asks "are you sure?" or says you are wrong, check first — run it,
   read the code, reproduce it — and answer with what you found. If you were wrong, say what showed it; if you were right, say so
   and why. "You're right" with nothing checked fails the verdict.

When the customer asks for a different behaviour, **updating the test that checks the old behaviour is part of the job** —
change its expected value to exactly what they asked for and say so (that is not weakening it).
Enforced, not suggested: do not weaken, skip or delete a test; do not leave TODOs or stubs; do not edit `harness.json` or `.harness/`;
do not bypass hooks (`--no-verify`). Each of these is its own gate, and commits are blocked until the verdict is DONE.
<!-- <<< agent-police <<< -->
