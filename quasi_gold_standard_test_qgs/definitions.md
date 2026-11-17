# Quasi-Gold Standard: Definitions

This file defines the criteria and labels used to build the quasi-gold standard (QGS) in `qgs.csv`. The QGS was used to measure the recall of the search (Section "Quasi-Gold Standard" in the paper).

- Inclusion criteria IC1, IC2 and EC1: fixed on 2 August 2026, together with the search string. They are the criteria applied in relevance screening (`2_relevance_check_and_bucketing/`).
- QGS labelling: 27 October 2026, by the first author.
- The final classification of the 289 papers with an available implementation uses a later, more detailed guideline: `4_classification/guidelines.md`. The QGS scope labels were assigned before that guideline was written. Under the final guideline, 15 of the 16 QGS primary studies with an available implementation keep their label; Prometheus (2507.19942), labelled WITHIN here, is classified EXTERNAL there.

## Candidates

39 candidate papers were assembled independently of the search string, from prior reading and from backward and forward snowballing on two seed papers (Live-SWE-agent, 2511.13646; SWE-MeM, 2606.28434). All were posted on arXiv before the search date (2 August 2026). No candidate was added after the corpus was retrieved.

## Inclusion and exclusion criteria (verbatim, fixed 2 August 2026)

**IC1:** the record proposes, evaluates, studies, or benchmarks a memory or information-handling mechanism for an LLM-based agent. Information handling includes context compression, pruning, summarisation, context folding, scratchpads, retrieval over prior work, experience stores, skill libraries, self-evolving or self-improving behaviour, and cross-task knowledge capture or reuse. Whether the mechanism is the paper's central contribution or a prominent part of its system is a bucketing question, not an exclusion question.

**IC2:** it is applied to, or evaluated on, code generation or software engineering tasks. Repository navigation, issue resolution, program repair, code completion, and long-horizon SWE agent work all count.

**EC1:** exclude only if the evaluation is purely conversational, QA, or a general-domain / non-code task with no code or software engineering component at all.

## Additional exclusions used in QGS labelling

These two were applied when labelling the QGS. In the final classification they are not exclusion criteria but reasons for the label NOT_APPLICABLE (see `4_classification/guidelines.md`).

**EC2:** the mechanism works by changing model parameters (training or fine-tuning on trajectories, or other weight updates). Final classification: NOT_APPLICABLE, PARAMETRIC.

**EC3:** the object of study is human-authored repository context files (AGENTS.md, CLAUDE.md, READMEs written for agents). Final classification: NOT_APPLICABLE, CONTEXT_FILES.

A candidate is IN if IC1 and IC2 hold and none of EC1, EC2, EC3 applies. Otherwise it is OUT, with the failing criterion recorded in `out_reason`.

## Bucket (IN candidates only)

- **PRIMARY:** proposes or evaluates a mechanism.
- **BENCHMARK:** a dataset or benchmark for evaluating memory or information handling.
- **SURVEY:** a survey or review.

## Scope (PRIMARY only)

A task is one problem instance with a defined start and end (one issue, one benchmark instance, one session).

- **CROSS:** the mechanism keeps information after a task ends and supplies it to the agent during a later, separate task. The information may come from the agent's own earlier tasks or from tasks solved by others, such as past issues with their human fixes.
- **WITHIN:** the information the mechanism handles is produced during the current task and is not available to a later task. This covers compression, pruning, folding or summarising of the current trajectory, even when written to disk, and retries or reflection across attempts at the same task instance.

Benchmarks and surveys receive no scope label.

**Memory source (CROSS only):** `own-trajectories`, `external-task-records`, `codebase` or `other`. Several values are separated by a semicolon.

## Columns of `qgs.csv`

|Column|Content|
|---|---|
|`arxiv_id`|arXiv identifier|
|`name`|system or paper name|
|`arxiv_title`, `first_author`, `first_posted_date`|metadata retrieved from the arXiv API by identifier|
|`assembly_route`|how the candidate was found: prior reading, backward/forward snowballing, forward snowballing|
|`IC1`, `IC2`, `EC1`, `EC2`, `EC3`|Y/N for each criterion|
|`status`|IN or OUT|
|`out_reason`|criterion and reason, for OUT candidates|
|`bucket`|PRIMARY, BENCHMARK or SURVEY, for IN candidates|
|`scope`|CROSS or WITHIN, for PRIMARY candidates|
|`source`|memory source, for CROSS candidates|
|`evidence`|quote from the paper that decides the scope label or the OUT reason|

## Outcome

25 candidates are IN: 21 primary studies (11 CROSS, 10 WITHIN), 3 benchmarks and 1 survey. 14 are OUT: 5 on IC1, 5 on EC1, 1 on EC2, 3 on EC3.

The merged corpus (2,411 records) contains 24 of the 25 IN papers (recall 96.0%, Wilson 95% interval 80.5% to 99.3%). The paper not retrieved is AMA-Bench (2602.22769), a multi-domain memory benchmark whose title and abstract contain no code or software engineering term. Part of the QGS was used to revise the search string once before it was fixed, so this recall is an upper bound.