# Rater guide: 30-paper agreement check

You classify 30 randomly chosen papers yourself, from the paper's own text. Your answers are later compared with the AI classification (Cohen's kappa). Please do not look at `PSK_labelled_30.csv` until you have finished.

## How to do it

1. Open `index.html` in a browser (double-click it). The page shows one paper at a time.
2. Press **Open paper (PDF)** and read it. The PDFs are in the `papers/` folder, so this works offline and is the exact file PSK read. **Online** opens the paper's arXiv or DOI page instead.
3. Answer three things: **1. Reuse scope**, **2. Role**, **3. SE activity**. Mechanism and reasoning are optional; one line of reasoning is enough.
4. Press **Save & next**. It saves your answer and opens the next paper in a new tab. If something required is missing it tells you what.
5. Back, Jump to # and Open paper again are under the form. Your answers stay in the browser; **Download decisions** saves them as a CSV (it also downloads by itself after the 30th paper). **Import decisions** loads a CSV on another device.

The sample is a simple random sample of 30 of the 289 papers (seed 20261103, `make_sample.py`).

## The task in plain words

Every paper here proposes or tests some way an LLM coding agent handles information: it stores it, keeps it, removes it, compresses it, retrieves it or supplies it to the model. First find the one such mechanism the paper presents as its contribution, then answer:

- **Reuse scope.** Where does the information that mechanism gives the agent come from?
  - **WITHIN**: it is made during this one task and no later, separate task gets it. Compressing, summarising or note-taking over the current work, and retries or reflection on the same task, are WITHIN.
  - **CROSS**: it was made by earlier, separate tasks and is given to the agent in a later task. Those tasks may have been done by this agent, other agents or humans (past issues with their fixes, past commits, earlier trajectories, lessons, skills).
  - **EXTERNAL**: it is stored but was not made by running tasks: documentation, a fixed knowledge base, web search, a code index not updated from task outcomes.
  - **NOT APPLICABLE**, with a reason: **NO_MECHANISM** (nothing to identify), **PARAMETRIC** (it works by changing the model's weights) or **CONTEXT_FILES** (the paper is about human-written instruction files such as AGENTS.md).
  - If several sources are present: CROSS if any part is CROSS, else EXTERNAL if any part is EXTERNAL, else WITHIN. For CROSS, also say whose earlier tasks: the system's own, other people's or agents', or both.
  - Words like "memory", "experience", "knowledge" or "long-term" decide nothing. Look at what is stored, when it is made and when it is used.
- **Role.** **CORE** if the mechanism appears in the paper's own statement of contributions (the contribution list, or the abstract's "we propose / introduce / present"). **COMPONENT** if it is part of a system whose stated contribution is something else, such as a new agent, workflow, tool or benchmark. Go by the paper's claims, not by how important the mechanism seems. No role when there is no mechanism.
- **SE activity.** Pick the one kind of task the mechanism is tested on (list below).
Use only the paper's text, not what you know about the system.

## Exact criteria (unchanged from the prompt)

The text below is copied word for word from `prompt.md`, Steps 0 to 4. It is also in the page, in the box "Criteria (exact text from the prompt)".

## STEP 0. IDENTIFY THE MECHANISM

Find the information-handling mechanism this paper proposes or
evaluates. An information- handling mechanism is any part of an
LLM-based agent system that decides what information is stored, kept,
removed, compressed, retrieved or supplied to the model across steps or
tasks. Examples: trajectory compression or pruning, summarisation,
context folding, scratchpads, notes, experience stores, skill libraries,
retrieval over prior work or documentation, repository indexes. If the
paper describes more than one, classify the one it presents as its
contribution. If none is identifiable, set scope = NOT_APPLICABLE with
reason NO_MECHANISM and skip Steps 1 and 2.

## STEP 1. REUSE SCOPE

The unit is the TASK: one problem instance with a defined start and end,
such as one issue, one benchmark instance or one user request. Classify
by where the information that the mechanism supplies to the agent comes
from. The three sources follow Zhang et al. (ACM TOIS), adapted from
trials to tasks.

-   **WITHIN** --- The information is produced during the current task
    and is not available to any later, separate task. This covers
    compression, pruning, folding, summarising or note-taking over the
    current trajectory, even if it is written to disk. It also covers
    retries, reflection or best-of-n across attempts at the SAME task
    instance. (Zhang et al. call repeated attempts "cross-trial"; we
    count them as WITHIN, because the information never reaches a
    different task.)
-   **CROSS** --- The information was produced by executing EARLIER,
    SEPARATE tasks and is supplied to the agent during a later task. The
    earlier tasks may have been solved by this agent, other agents or
    human developers (e.g. past issues with their fixes, past commits,
    earlier trajectories, distilled lessons, skills learned from earlier
    tasks). A repository index that is updated from task outcomes and
    reused across tasks is CROSS.
-   **EXTERNAL** --- The information is persistent but was NOT produced
    by executing tasks: API or library documentation, a fixed knowledge
    base, web search, or a code index built from the repository that is
    not updated from task outcomes. It does not change as the agent
    works.
-   **NOT_APPLICABLE**, with exactly one reason:
    -   **NO_MECHANISM** - no identifiable information-handling
        mechanism (see Step 0)
    -   **PARAMETRIC** - the mechanism works by changing model weights
        (training, fine-tuning or reinforcement learning on
        trajectories)
    -   **CONTEXT_FILES**- the object of study is human-written
        repository instruction files (AGENTS.md, CLAUDE.md, READMEs
        written for agents)

If the mechanism draws on several sources, assign CROSS if any part is
CROSS, otherwise EXTERNAL if any part is EXTERNAL, otherwise WITHIN.
List every source present in "sources". Words such as "memory",
"experience", "knowledge" or "long-term" decide nothing on their own.
Decide from what is stored, when it is produced, and when it is used.

## STEP 2. ROLE OF THE MECHANISM

-   **CORE** --- The information-handling mechanism appears in the
    paper's own statement of its contributions: the contribution list,
    or the abstract's "we propose / introduce / present ...".
-   **COMPONENT** --- The mechanism is part of a system whose stated
    contribution is something else (e.g. a new agent, a multi-agent
    workflow, a tool, a benchmark result). Decide from the paper's own
    claims, not from how important the mechanism seems to you.

## STEP 3. SE ACTIVITY (Hou et al., ACM TOSEM)

Assign the activity of the tasks the mechanism is evaluated on. Choose
one, the dominant one if several apply:

-   REQUIREMENTS_ENGINEERING
-   SOFTWARE_DESIGN
-   SOFTWARE_DEVELOPMENT (e.g. code generation, completion, translation)
-   QUALITY_ASSURANCE (e.g. testing, fault localisation, vulnerability
    detection)
-   SOFTWARE_MAINTENANCE (e.g. issue resolution, program repair,
    refactoring)
-   SOFTWARE_MANAGEMENT

## After you finish

Run `uv run kappa_review/compare_ratings.py path/to/class_decisions_30_*.csv`. It prints agreement and kappa for scope, CROSS vs the rest, role and activity, and writes `kappa_comparison.xlsx` with the two classifications side by side.
