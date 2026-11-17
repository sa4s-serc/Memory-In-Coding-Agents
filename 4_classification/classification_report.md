# Classification Report

Input: the 289 papers that passed the implementation review (`implementation_screen/outcome_screening.md`). Output: one classification per paper on four attributes, recorded in `results/<record_id>.json` and joined to the rated sheet in `classification_joined.xlsx`.

## What was classified

Each paper was classified from its full PDF, using the guidelines in `guidelines.md`, on four attributes:

| Attribute             | Values                                                                                                                                                |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Reuse scope           | WITHIN, CROSS, EXTERNAL, or NOT_APPLICABLE with one reason: NO_MECHANISM, PARAMETRIC, CONTEXT_FILES                                                   |
| Role of the mechanism | CORE (the mechanism is in the paper's own statement of contributions), COMPONENT (it is part of a system whose stated contribution is something else) |
| SE activity           | one of six: requirements engineering, software design, software development, quality assurance, software maintenance, software management             |
| Target                | language or artefact, or "unspecified"                                                                                                                |

Scope is decided by where the information the mechanism supplies comes from. WITHIN is information produced during the current task. CROSS is information produced by executing earlier, separate tasks (by this agent, other agents or human developers). EXTERNAL is persistent information not produced by executing tasks (documentation, a fixed knowledge base, web search, a code index not updated from task outcomes). If a mechanism draws on several sources, the scope is CROSS if any part is CROSS, otherwise EXTERNAL if any part is EXTERNAL, otherwise WITHIN. Each result also holds the mechanism as a short phrase, the sources, the origin of CROSS information (`own_trajectories`, `others_tasks` or `both`), and two verbatim evidence quotes (one for scope, one for role).

**Validation:** `join_results.py` checks every result against the manifest: the filename and `record_id` match a manifest row; `pdf_sha256` matches the PDF. The final run classifies all 289 papers obtained from the previous step of the study.
**Join key:** `record_id` only. Titles are never used to join, because some PDFs are retitled versions of the same paper.

## Results

### Scope by role (289 papers)

| Scope                         |  Papers |    CORE | COMPONENT | No role |
| ----------------------------- | ------: | ------: | --------: | ------: |
| WITHIN                        |      95 |      52 |        43 |         |
| EXTERNAL                      |      50 |      20 |        30 |         |
| CROSS                         |      56 |      39 |        17 |         |
| NOT_APPLICABLE, PARAMETRIC    |      54 |      51 |         3 |         |
| NOT_APPLICABLE, NO_MECHANISM  |      32 |         |           |      32 |
| NOT_APPLICABLE, CONTEXT_FILES |       2 |       2 |           |         |
| **Total**                     | **289** | **164** |    **93** |  **32** |


### SE activity

| Activity | Papers |
|---|---:|
| Software development | 174 |
| Software maintenance | 92 |
| Quality assurance | 16 |
| Requirements engineering | 2 |
| Software design | 2 |
| Software management | 2 |
| Not assigned | 1 |

The 56 CROSS papers: software development 41, software maintenance 14, requirements engineering 1.

### Papers whose mechanism draws on more than one source

46 of the 201 papers with a WITHIN, EXTERNAL or CROSS mechanism list more than one source: within + external 26, cross + within 12, cross + external 5, all three 3.


### The 16 passing QGS papers

All 16 QGS primary studies with a passing implementation are among the 289. Their classification: CROSS 8 (ExpeRepair, SWE-Exp, EET, MemGovern, Memory Transfer Learning, MemRepair, EvoRepair, ReasoningBank), WITHIN 7 (Git-Context-Controller, Context-Folding, CAT, SWE-Pruner, ContextSniper, ACQUIRE, SWE-Pruner Pro), EXTERNAL 1 (Prometheus). All 16 have role CORE. 15 of the 16 keep the scope the QGS gave them; Prometheus differs (QGS: within-task; classified EXTERNAL because it indexes the repository as a knowledge graph).


## Files

| File | Purpose |
|---|---|
| `guidelines.md` | The classification guideline used |
| `manifest.csv` | One row per paper, in review order, with the PDF hash and the title check |
| `join_results.py` | Validates the results and writes the joined sheet; run with `uv run join_results.py` |
| `classification_joined.xlsx` | One row per paper: record id, PDF hash, classification fields, then the rated-sheet columns |
| `rationale.md` | Per-paper reasoning |
| `notes.txt` | PDFs whose title differs from the manifest |

The per-paper result files are in `results/<record_id>.json`, 289. The PDFs are not redistributed; the manifest carries the DOI or arXiv id and the SHA-256 of each.
