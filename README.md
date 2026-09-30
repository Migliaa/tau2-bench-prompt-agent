# τ²-bench: can prompt engineering alone improve an agent?

A study on [τ²-bench](https://github.com/sierra-research/tau2-bench) (airline domain, 50 tasks) with the model held fixed and only the system prompt allowed to change: no fine-tuning, no second model, no extra tools. Agent and simulated customer are both `gemini-3.5-flash-lite` at `temperature=0`. Six prompt versions were built by reading failed conversations turn by turn, each change registered as a prediction before the run, and the final version was run four times.

| agent | full runs | pass^1 | McNemar *p* vs default |
|---|---|---|---|
| default `llm_agent` (benchmark's own) | 1 | 68.0% (34/50) | |
| our v6 | 4 | **80.5%** mean of 82 / 74 / 80 / 86% (200 simulations) | 0.039 / 0.508 / 0.031 / 0.004 |

The two numbers do not have the same reliability: 68.0% is one run, 80.5% is the mean of four, and the same v6 scores anywhere from 74% to 86% with nothing changed. On the 37 tasks where both agents have two runs, pass^1 is 78.4% for v6 and 74.3% for the default, and pass^2 (succeeds in both runs) is 67.6% for each: the gain is on the average score, not on consistency. Trials 1, 3 and 4 reach *p* < 0.05 and trial 2 does not; no correction for multiple comparisons is applied across the four.

```bash
python scripts/riepilogo.py     # recomputes every number above from results/esiti-per-task.json, no API calls
```

```
esecuzione    superati   pass^1  vinti  persi  p (McNemar)
baseline_1       34/50    68.0%
v6_trial1        41/50    82.0%      8      1        0.039
v6_trial2        37/50    74.0%      6      3        0.508
v6_trial3        40/50    80.0%      6      0        0.031
v6_trial4        43/50    86.0%      9      0        0.004

v6, quattro trial: pass^1 medio 80.5%, pass^4 64.0% (50 task)
```

The script needs only Python 3.10+ and the standard library; the output is in Italian, like the rest of the working notes.

## What it is, who it is for, what goes in and out

Companies deploy small, cheap models for customer support, where a 40-page policy has to be followed in every conversation; the question is how much a prompt alone can buy on such a model. The study is meant for people who build or evaluate conversational agents. Input: the benchmark's airline domain (a database of reservations, a policy, 50 tasks with a simulated customer) and a system prompt. Output: per task, a reward that is 1 only if the final database state matches the expected one and the required information was communicated, otherwise 0; per-action metrics (unrequested writes, wrong arguments); every conversation traced on Langfuse.

## What the evaluation showed

All versions below run the same 50 tasks; only v6 has more than one full run.

| version | full runs | pass^1 | vs default (*p*) |
|---|---|---|---|
| default | 1 | 34/50 | |
| v1, rules from 10 failed tasks | 1 | 39/50 | 0.125 |
| v2, two clauses changed | 1 | 38/50 | 0.289 |
| v3, one clause | 1 | 35/50 | 1.000 |
| v4, prompt restructured | 1 | 37/50 | 0.453 |
| v5, one confirmation per request, search discipline | 1 | 38/50 | 0.289 |
| v6 | 4 | 80.5% mean | see above |

- **Adding rules made it worse.** Three consecutive versions that added clauses lost ground; v1 alone stacks about 21 constraints on top of the domain's roughly 40, past the point (about 20) where small models start ignoring instructions silently ([arXiv:2608.02639](https://arxiv.org/abs/2608.02639)). v6 was built by subtraction instead: removing a worked example that taught the wrong behaviour, and replacing ten lines of case law with one principle.
- **Single runs mislead.** Re-running v1 against the default on the 36 tasks both completed moved the gap from +2 to −1 tasks; at `temperature=0` 5 of 36 tasks changed outcome for the default and 8 of 36 for v1.
- **Five tasks were never solved in four trials** (7, 23, 32, 35, 39). Tasks 7 and 39 have an inconsistent ground truth, 23 is affected by the defect below, 32 and 35 are flight-selection tasks (a fixed budget, the second cheapest) that the model gets wrong.
- **A defect in the benchmark.** The database comparison hashes with `json.dumps(..., sort_keys=True)`, which sorts dict keys but not list elements, so two identical bookings with payments listed in a different order are judged different. Shown on two runs of task 14 differing only in the order of two gift cards. It explains 4 of 7 failures on tasks 14 and 23 (the other 3 are real agent failures; the issue first said both tasks failed for this reason alone and was corrected with a comment). Reported as [sierra-research/tau2-bench#514](https://github.com/sierra-research/tau2-bench/issues/514), open at the time of writing, write-up in [`docs/segnalazione-bug.md`](docs/segnalazione-bug.md).
- **A leaderboard submission** of v6 is open as [sierra-research/tau2-bench#518](https://github.com/sierra-research/tau2-bench/pull/518).

## Limits

One model, one domain, one simulated-user model: nothing here says the v6 prompt transfers to another model or domain. The default agent has a single full run (a second one stopped at 37 tasks), so the headline gap compares one run with the mean of four. Submissions above 80% on the public leaderboard used models with reasoning enabled or a second model; this work has neither. Only the v6 prompt is in the repository as code (`patches/tau2-custom-agent.patch`); v1 to v5 are described in `docs/s5-correzioni.md` and `docs/v4-bozza-prompt.md` but not stored as files. The automatic judge that assigns a failure family to a trace (`scripts/judge.py`, `docs/giudice/`) agrees with the reference label on 43 of 48 traces, but 37 of those are passing tasks, only 8 of the 11 failures match, it was tuned on those same 11, and the reference labels come from a frontier model, not from a person. Total API spend: about $25.

## Reproducing a run

`tau2-bench/` is a third-party clone and is not committed. The patches apply cleanly to upstream commit `672227c` (the one the work started from) and to the current `main`.

```bash
git clone https://github.com/sierra-research/tau2-bench.git
git -C tau2-bench checkout 672227c
git -C tau2-bench apply ../patches/tau2-infra.patch ../patches/tau2-custom-agent.patch
cd tau2-bench && uv sync && cd ..
cp .env.example tau2-bench/.env       # add GEMINI_API_KEY and the Langfuse keys
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 tau2-bench/.venv/Scripts/python.exe scripts/s6_worker.py \
    --key-var GEMINI_API_KEY --agent custom_agent --tasks 0,1,2 --prefix myrun
```

`.venv/bin/python` on macOS and Linux. Results land in `tau2-bench/data/simulations/myrun_custom_agent_t<id>/results.json`; `--agent llm_agent` runs the default agent. `scripts/s6_publish.py myrun` pushes them to Langfuse, `scripts/estrai_esiti.py` rebuilds `results/esiti-per-task.json` from local simulations. A full 50-task run costs about $2. There is no unit-test suite: `scripts/riepilogo.py` is the check, and the real runs are the tests.

## Where things are

| path | |
|---|---|
| `results/esiti-per-task.json` | reward of every task in every run (12 runs, 50 tasks each except two interrupted ones) |
| `patches/` | our changes to `tau2-bench`: tracing and rate limiter, the agent, and a simulator guideline that is **not** active in the published numbers |
| `scripts/` | run workers, Langfuse publishing, statistics (McNemar, pass^k), the judge |
| `docs/` | failure analysis (`s5-correzioni.md`), prompt design rationale, the benchmark bug report, research notes |
| `report/` | the write-up prepared for the portfolio site (Italian), with figures |
| `DIARIO.md` | full working diary, in Italian, including the wrong hypotheses |

MIT, see [`LICENSE`](LICENSE).
