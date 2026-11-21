# Implementation Review Outcome

All 598 ratings: `rated_implementations_final_598.xlsx`.

## Final ratings (598 papers)

| Rating | Papers | Share |
|---|---:|---:|
| GREEN | 277 | 46.3% |
| ORANGE | 12 | 2.0% |
| RED | 309 | 51.7% |
| **Pass (GREEN+ORANGE)** | **289** | **48.3%** |

| Evidence | Papers | GREEN | ORANGE | RED | Pass rate |
|---|---:|---:|---:|---:|---:|
| Strong | 455 | 246 | 10 | 199 | 56.3% |
| Medium | 68 | 26 | 1 | 41 | 39.7% |
| Weak | 75 | 5 | 1 | 69 | 8.0% |

## Inter-rater agreement

Two reviewers rated a simple random sample of 50 of the 598 papers (seed 20261030). The 4 disagreements were resolved by consensus.

| Comparison | Cohen's kappa | 95% CI | Agreement | PABAK |
|---|---:|---:|---:|---:|
| GREEN+ORANGE vs RED | 0.88 | 0.72–1.00 | 94% | 0.88 |
| GREEN / ORANGE / RED | 0.84 | 0.68–0.96 | 92% | 0.88 |
| GREEN vs ORANGE+RED | 0.84 | 0.68–0.96 | 92% | 0.84 |

| Result | Reviewer 1 | Reviewer 2 | Papers |
|---|---|---|---:|
| Agreed | GREEN | GREEN | 25 |
| Agreed | RED | RED | 21 |
| **Total agreed** | | | **46** |
| Disagreed | RED | GREEN | 2 |
| Disagreed | ORANGE | GREEN | 1 |
| Disagreed | GREEN | RED | 1 |
| **Total disagreed** | | | **4** |

## QGS

**16 of 21 primary studies have a passing implementation (76%), all GREEN.** The rate for all reviewed papers is 48.3%.

| Scope | Primaries | GREEN | RED | Not reviewed |
|---|---:|---:|---:|---:|
| Cross-task | 11 | 8 | 1 | 2 |
| Within-task | 10 | 8 | 2 | 0 |
| **Total** | **21** | **16** | **3** | **2** |

| Paper | Outcome | Reason |
|---|---|---|
| SWE-Mem | RED | Link is an unrelated repo |
| AgentDiet | RED | Links are unrelated to the paper |
| Feedback-Normalized Memory | RED | Repo failed the rating criteria |
| MemCoder | Not reviewed | Only a third-party repo was found |
| Subtask-Level Memory | Not reviewed | Only a third-party repo was found |

**Why the QGS rate is below 100%:** the QGS was selected for relevance to the topic, not for having released code. A QGS paper can be a correct primary study and still have no usable implementation.