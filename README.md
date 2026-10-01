# τ²-bench: can prompt engineering alone improve an agent?

A study on [τ²-bench](https://github.com/sierra-research/tau2-bench) (airline customer support, 50 tasks) with the model held fixed and only the system prompt allowed to change: no fine-tuning, no second model, no extra tools. Agent and simulated customer are both `gemini-3.5-flash-lite` at `temperature=0`. Six prompt versions were built by reading failed conversations turn by turn, each change registered as a prediction before the run, and the final version was run four times.

**Result.** The final version passes about 80% of tasks (mean of four runs) against 68% for the benchmark's default agent (one run). The gap is smaller than it looks, because the two figures do not have the same reliability: the same agent scores between 74% and 86% across runs, and where both agents have two runs the difference is 78% against 74%, with equal consistency. Details in the last section.

**A defect found in the benchmark.** The database comparison hashes with `json.dumps(..., sort_keys=True)`, which sorts dict keys but not list elements, so two identical bookings with payments listed in a different order are judged different. Reported as [sierra-research/tau2-bench#514](https://github.com/sierra-research/tau2-bench/issues/514), write-up in [`docs/segnalazione-bug.md`](docs/segnalazione-bug.md); a leaderboard submission of the final agent is open as [#518](https://github.com/sierra-research/tau2-bench/pull/518).

## Try it

```bash
python scripts/riepilogo.py     # recomputes every number in this README from results/esiti-per-task.json, no API calls
```

Running the agent needs a Gemini key (a 50-task run costs about $2):

```bash
git clone https://github.com/sierra-research/tau2-bench.git
git -C tau2-bench checkout 672227c
git -C tau2-bench apply ../patches/tau2-infra.patch ../patches/tau2-custom-agent.patch
cd tau2-bench && uv sync && cd ..
cp .env.example tau2-bench/.env       # add GEMINI_API_KEY and the Langfuse keys
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 tau2-bench/.venv/Scripts/python.exe scripts/s6_worker.py \
    --key-var GEMINI_API_KEY --agent custom_agent --tasks 0,1,2 --prefix myrun
```

`.venv/bin/python` on macOS and Linux; `--agent llm_agent` runs the default agent. Results land in `tau2-bench/data/simulations/myrun_custom_agent_t<id>/results.json`, and `scripts/s6_publish.py myrun` pushes them to Langfuse. The patches apply to upstream commit `672227c` and to the current `main`. There is no unit-test suite: `riepilogo.py` is the check.

## What the work shows

- **Look before fixing.** Every conversation traced on Langfuse, the reward split into its two parts (database state, information communicated), per-action metrics (unrequested writes, wrong arguments), and each failure read turn by turn and grouped by cause.
- **Adding rules made it worse.** Three consecutive versions that added clauses lost ground: past about twenty instructions small models start ignoring them silently ([arXiv:2608.02639](https://arxiv.org/abs/2608.02639)). The final version was built by subtraction: removing a worked example that taught the wrong behaviour and replacing ten lines of case law with one principle.
- **Repeat before believing.** Re-running an early version moved its gap against the default from +2 tasks to −1, which is why the final version was run four times.
- **Failures that are not the agent's.** Tasks 7 and 39 have an inconsistent ground truth, and the hash defect above explains 4 of 7 failures on tasks 14 and 23 (the issue first said both failed for this reason alone; it was corrected with a comment after an adversarial review).

## Limits

One model, one domain, one simulated-user model: nothing here says the prompt transfers. The default agent has a single full run, so the headline compares one run with a mean of four. Leaderboard entries above 80% used models with reasoning or a second model; this work has neither. Only the final prompt is in the repository as code (`patches/tau2-custom-agent.patch`); earlier versions are described in `docs/`. The failure-family judge (`scripts/judge.py`) agrees with reference labels on 43 of 48 traces, but 37 are passing tasks, it was tuned on the 11 failures it is scored on, and the labels come from a frontier model, not a person. Total API spend about $25.

## Where things are

| path | |
|---|---|
| `results/esiti-per-task.json` | reward of every task in every run (12 runs) |
| `patches/` | our changes to `tau2-bench`: tracing and rate limiter, the agent, a simulator guideline **not** active in the published numbers |
| `scripts/` | run workers, Langfuse publishing, statistics, the judge |
| `docs/` | failure analysis, prompt design rationale, the benchmark bug report |
| `report/` | the write-up for the portfolio site (Italian), with figures |
| `DIARIO.md`, `s*.log` | full working diary (Italian, including wrong hypotheses) and raw run logs |

## The numbers

`python scripts/riepilogo.py` prints these. All runs: 50 tasks, pass^1 = share of tasks passed in one run; *p* is McNemar's exact test against the default agent's single run, with no correction for multiple comparisons.

| agent | full runs | pass^1 | *p* |
|---|---|---|---|
| default `llm_agent` | 1 | 68.0% (34/50) | |
| v1, rules from 10 failed tasks | 1 | 78.0% | 0.125 |
| v2, two clauses changed | 1 | 76.0% | 0.289 |
| v3, one clause | 1 | 70.0% | 1.000 |
| v4, prompt restructured | 1 | 74.0% | 0.453 |
| v5, one confirmation per request | 1 | 76.0% | 0.289 |
| **v6, final** | **4** | **80.5%** mean of 82 / 74 / 80 / 86% | 0.039 / 0.508 / 0.031 / 0.004 |

Trials 1, 3 and 4 reach *p* < 0.05, trial 2 does not. On the 37 tasks where both agents have two runs: pass^1 is 78.4% for v6 and 74.3% for the default, pass^2 (passes in both runs) 67.6% for each, so the gain is on the average score, not on consistency. Five tasks were never solved in four trials (7, 23, 32, 35, 39).

MIT, see [`LICENSE`](LICENSE).
