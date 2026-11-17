## 1. IDENTIFY THE MECHANISM

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

## 1. REUSE SCOPE

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

## 2. ROLE OF THE MECHANISM

-   **CORE** --- The information-handling mechanism appears in the
    paper's own statement of its contributions: the contribution list,
    or the abstract's "we propose / introduce / present ...".
-   **COMPONENT** --- The mechanism is part of a system whose stated
    contribution is something else (e.g. a new agent, a multi-agent
    workflow, a tool, a benchmark result). Decide from the paper's own
    claims, not from how important the mechanism seems to you.

## 3. SE ACTIVITY (Hou et al., ACM TOSEM)

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

## STEP 4. TARGET

The main language or artefact the tasks produce, as stated in the paper
(e.g. Python, Java, Verilog, SQL, multiple). Use "unspecified" if the
paper does not say.

## OUTPUT


``` json
{
  "mechanism": "<one short phrase naming the mechanism>",
  "scope": "WITHIN | CROSS | EXTERNAL | NOT_APPLICABLE",
  "na_reason": "NO_MECHANISM | PARAMETRIC | CONTEXT_FILES | null",
  "sources": ["within" | "cross" | "external", ...],
  "cross_origin": "own_trajectories | others_tasks | both | null",
  "role": "CORE | COMPONENT | null",
  "activity": "<one of the six> | null",
  "target": "<language or artefact>",
  "evidence_scope": "<verbatim quote, under 100 words, that decides scope>",
  "evidence_role": "<verbatim quote, under 100 words, that decides role>"
}
```
