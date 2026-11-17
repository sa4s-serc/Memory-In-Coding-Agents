# RQ3 Extraction Form: Reported Limitations

Version 1.1, fixed 16 November 2026.

This form records which kinds of limitations the authors of each within-task and cross-task paper (95 + 56 = 151) report about their own work.

**Origin.** Derived from a pilot on 30 randomly selected papers (seed 20261114). Limitation statements in the pilot papers were extracted and open-coded with LLM assistance (Claude) into 14 provisional themes; the first and second author consolidated these into 11 fields in three groups.

**Changes.** 1.1 (2026-11-16): rules clarified after a calibration run of both LLMs on the 30 pilot papers, before any non-pilot paper was extracted and before the human evaluation. Added rules on framing (including when a cost counts), where to look, boilerplate, future work, one field per statement, field boundaries and doubt. Sharpened two include items (F2 repeated runs, F3 benchmark ceiling). No field was added, removed or renamed.

Two LLMs fill in the form independently for all 151 papers, from the full text, using the prompt in `prompt_extraction.md`. Where they disagree, the first author decides from the paper. A human evaluator fills in the form for a stratified random sample of 30 non-pilot papers, without seeing the LLM output. The rules and fields below are the same text the LLMs receive: both are generated from `extraction_form_v1.json`.

## How to fill in the form

For each field, record **1** if the authors state at least one limitation of that kind about their own work, otherwise **0**. Support every 1 with a verbatim quote and its page number.

For each statement that might be a limitation, check in order:
1. Is it about the authors' own approach, system or evaluation? (rule 1)
2. Do the authors present it as a weakness, shortfall, cost, risk, open problem or untested condition? A neutral description of the design, a measurement given without being called a drawback, or a result presented as an advantage is not a limitation. (rule 2)
3. Is it specific to this study, or is it boilerplate? (rule 4)
4. If it is future work, does it name a specific thing the current work does not do, have or test? (rule 6)
5. Which single field fits best? (rules 7 and 8)

If the answer to 1, 2 or 4 is no, or 3 is boilerplate, skip the statement. If you are unsure, skip it (rule 9).

Two special cases:
- If the only limitation statements are boilerplate, record **only boilerplate**.
- If there is no limitation statement at all, record **no limitation**.

In both cases every field is 0.

## Rules

1. Own work only. Record limitations the authors state about their own approach, system or evaluation. Ignore statements about prior work, background, baselines or other systems, the authors' prompt texts or examples, and weaknesses of LLMs in general that the authors do not tie to their own approach.
2. Framing. A statement counts only if the authors present it as a weakness, shortfall, cost, risk, open problem or untested condition of their own work. Do not count: neutral descriptions of the design or setup ('we evaluate on CrossCodeEval', 'the token budget B is fixed'); measurements reported without being presented as a drawback; results presented as an advantage ('the maintenance cost is small'); or speculation about what a stronger model might add. Costs: an extra cost of the approach counts if the authors present it as a cost or overhead of their approach, even if they call it acceptable or reasonable. It does not count if they describe it as small, modest, negligible, imperceptible or amortised, or if they mention it to show that the approach saves cost or time overall.
3. Where to look. Read the sections on limitations, threats to validity, discussion, conclusion and future work in full. Statements elsewhere in the paper (including results and appendices) count only if they meet rule 2 on their own; cue words such as limitation, drawback, overhead, cannot, does not, not yet, only, fails, future work and beyond the scope help to find them.
4. Boilerplate. A statement is boilerplate if it would be equally true of any other paper: it names no specific model, benchmark, metric, component, setting or number of this study ('results may not generalise', 'as with any empirical study', 'our work has some limitations'). Boilerplate fills no field. A threat to validity that names a specific aspect of this study counts, even if the authors describe a mitigation, unless they state that the threat was ruled out.
5. LLM judges. An LLM judge used to evaluate the paper's results belongs to F3 Evaluation quality; an LLM judge or other signal used inside the mechanism belongs to F4 Memory quality.
6. Future work. A future-work item counts only if it names a specific thing the current work does not do, have or test, and is recorded under the gap it implies ('extend to other programming languages' is F1; 'transfer skills across models' is F5; 'we have not built a reduce operator' is F11). Vague directions ('explore further', 'richer policies', 'a promising extension', 'improve efficiency') do not count.
7. One field per statement. Record a statement under the single field that best matches what the authors say is limited. Use a second field only if the statement contains two distinct limitations.
8. Field boundaries. Missing or irrelevant accumulated experience or memory is F5; restriction to some tasks, models, languages or benchmarks is F1. Few tasks, items or problems is F1; too few runs, no seeds, variance or significance testing is F2; a benchmark that measures the wrong thing, is contaminated, capped or saturated is F3. A memory or retrieval design acknowledged as simple is F6; other functionality not yet built is F11. Wrong content that the mechanism stores or acts on is F4; errors in the agent's outputs or actions are F10. Pressure on the context window is F7; tokens, money, time or hardware is F8.
9. Doubt. If you are unsure whether a statement meets rules 1 to 4, do not count it.
10. A field is filled if the paper states at least one limitation of that kind; how often it is stated does not matter.
11. Every filled field needs at least one verbatim quote from the paper, with its page. Quote the sentence that states the limitation, not the surrounding description.

## Fields

| Group | Field | Definition |
|---|---|---|
| Evaluation | F1 Generalizability | The approach was evaluated on few models, languages, tasks, benchmarks, settings or small samples, or is inherently restricted to some tasks or dependent on the underlying model or agent. |
| Evaluation | F2 Weak experimental validation | Analyses that would support the claims were not done: ablations, sensitivity, baselines, quantitative evaluation, cost measurement, repeated runs, causal or statistical support. |
| Evaluation | F3 Evaluation quality | The metrics, judges, oracles or benchmarks used to evaluate the approach may not measure what is intended. |
| Memory and context | F4 Memory quality | The information or signals the mechanism stores or acts on may be wrong: noisy or LLM-judged feedback, missing ground truth, polluted entries. |
| Memory and context | F5 Limited experience | Benefits depend on the availability, order, relevance or reach of accumulated experience or captured knowledge: cold start, no similar past tasks, plateauing gains, bounded by sources, no transfer across projects or models. |
| Memory and context | F6 Memory representation | The memory or knowledge design is acknowledged as simple: similarity-only retrieval, flat or minimal representation, static knowledge. |
| Memory and context | F7 Context limitation | Problems caused by the finite context window: budget pressure, instruction decay, loss through compression or summarisation. |
| Engineering | F8 Resource overhead | The approach costs extra tokens, money, training compute, latency, memory or special hardware. |
| Engineering | F9 Manual configuration | Templates, prompts, thresholds or hyperparameters are hand-crafted or hand-tuned and may need recalibration. |
| Engineering | F10 Agent reliability and safety | The agent produces imperfect artefacts or actions, or running it poses safety or security risks. |
| Engineering | F11 Incomplete implementation | Functionality the authors consider needed is not yet supported, including integration with model training. |

### F1 Generalizability (Evaluation)

The approach was evaluated on few models, languages, tasks, benchmarks, settings or small samples, or is inherently restricted to some tasks or dependent on the underlying model or agent.

Includes:

- **Few LLMs evaluated.** Only a small number of LLMs, or a single model family, were evaluated. *Example from the pilot:* "Nothing in the design is model-specific, and every LLM role is bound fromaconfigurationtable,butwehavenotrunacross-family replication and cannot claim one."
- **Single programming language.** Evaluation is restricted to one (or few) programming languages. *Example from the pilot:* "First, MemOp is evaluated across four benchmarks, three programming languages, and eleven SE activity categories (§4.4, §F.1). Extending this evaluation to further programming languages and SE activities is a natural next step."
- **Narrow task domain.** Evidence comes from one task type, domain or benchmark family. *Example from the pilot:* "Future work will explore extending this framework beyond code generation to broader reasoning tasks and dynamic agentic workflows."
- **Untested frameworks or settings.** The approach was not tested in other agent frameworks, harnesses or deployment settings (e.g. streaming, distribution shift). *Example from the pilot:* "Future work could extend this framework to strictly streaming task settings"
- **Small evaluation sample.** Few tasks, items, problems, competitions or corpora were used, including a benchmark with few items. *Example from the pilot:* "Ten items is few"
- **Restricted to task types.** The mechanism suits only some tasks, inputs or failure types. *Example from the pilot:* "It buys least where they are semantic"
- **Depends on model or agent.** Benefits depend on the underlying LLM/agent, or are limited to homogeneous models, or may vanish with stronger models. *Example from the pilot:* "We acknowledge that the case for architectural control flow may diminish as LLM capabilities in- crease."

### F2 Weak experimental validation (Evaluation)

Analyses that would support the claims were not done: ablations, sensitivity, baselines, quantitative evaluation, cost measurement, repeated runs, causal or statistical support.

Includes:

- **Missing ablation or sensitivity analysis.** Components, variants or hyperparameters were not isolated or varied. *Example from the pilot:* "Results suggest stability at λ = 0.5; broader sensitivity remains unquantified."
- **Missing baseline comparison.** No or limited comparison against baselines or alternative designs. *Example from the pilot:* "The Leviathan results demonstrate absolute capability but do not include a controlled comparison against a baseline agent without SOMA’s memory architecture."
- **No quantitative evaluation.** The paper lacks systematic quantitative evaluation. *Example from the pilot:* "This paper documents architectural decisions and design rationale but lacks systematic quantitative evaluation."
- **Weak causal or statistical support.** The analysis cannot establish causality, uses single runs without seeds, variance or significance testing, or uses optimistic/pooled statistics or post-hoc designed instruments. *Example from the pilot:* "These proportions describe usage rather than independently establish each source’s causal contribution."
- **Cost not measured.** End-to-end cost of the mechanism was not evaluated. *Example from the pilot:* "evaluate the end-to-end cost of skill acquisition, maintenance, and use."

### F3 Evaluation quality (Evaluation)

The metrics, judges, oracles or benchmarks used to evaluate the approach may not measure what is intended.

Includes:

- **Inadequate metric.** Metrics are proxies or miss quality dimensions. *Example from the pilot:* "Answer-sufficiency is a proxy for task help, not task completion."
- **LLM-as-judge in evaluation.** The evaluation relies on LLM judges that may be biased or differ from humans. *Example from the pilot:* "the question-quality evaluation in RQ3 relies on LLM-as-a-judge"
- **No evaluation oracle.** Correctness of outputs is hard to verify automatically. *Example from the pilot:* "Secondly, unlike traditional function-level code generation approach, automating the evalua- tion of general-purpose software is exceptionally challenging. Though recent efforts aimed to em- ploy Human Revision Cost (Hong et al., 2024), manual verification is still impractical."
- **Benchmark contamination.** Models may have seen benchmark data in training. *Example from the pilot:* "Our de- contamination procedure relies on structured reason- ing traces to detect memorization, which were not available for the harness-free model outputs."
- **Benchmark ceiling.** The benchmark is capped or saturated for the setting. (A benchmark with few items is F1 Small evaluation sample.) *Example from the pilot:* "The current OOLONG suite caps at 1M tokens, a ceiling that the raw Opus 4.6 context window already exceeds. Keeping evaluation meaningful as context lengths grow will require benchmarks that scale with them."

### F4 Memory quality (Memory and context)

The information or signals the mechanism stores or acts on may be wrong: noisy or LLM-judged feedback, missing ground truth, polluted entries.

Includes:

- **Noisy or LLM-judged feedback.** Signals used by the mechanism (success/failure, quality, utility) come from LLM judges or stochastic estimates and may be wrong. *Example from the pilot:* "This agreement supports consistency with human judgment, but does not establish whether scores predict repair gains on unseen CVEs."
- **Needs ground truth or oracle.** The mechanism needs ground-truth labels, anchors or verifiers that may be unavailable. *Example from the pilot:* "With no anchor the loop optimizes noise"
- **Memory pollution.** Stored knowledge may be contaminated across contexts or by bad entries. *Example from the pilot:* "A global L3 improves cross-project transfer but may introduce cross- project contamination if not managed carefully."

### F5 Limited experience (Memory and context)

Benefits depend on the availability, order, relevance or reach of accumulated experience or captured knowledge: cold start, no similar past tasks, plateauing gains, bounded by sources, no transfer across projects or models.

Includes:

- **No relevant past experience.** Effectiveness drops when no similar prior experience exists (novel tasks). *Example from the pilot:* "issues solved exclusively by DARS highlight a limitation of ExpeRepair: its effectiveness drops when relevant prior experience is unavailable."
- **Cold start and order sensitivity.** Early-phase instability, sparse evidence or dependence on task order. *Example from the pilot:* "As shown in Figure 7, all repositories exhibit high volatility during the early phase."
- **Bounded by captured knowledge.** Usefulness is limited by what is captured in documentation, history or interactions. *Example from the pilot:* "The binding constraint is capture."
- **Diminishing returns.** Gains from accumulated memory plateau. *Example from the pilot:* "Django’s cumulative resolution rate stabi- lizes around issue 80 at approximately 60%, which may be attributable to diminishing returns from repeated memory and the increasing heterogeneity of the remaining issues."
- **No cross-context transfer.** Knowledge is not transferred across projects, models or deployments. *Example from the pilot:* "The ACE playbook currently operates per-project with effectiveness scoring and semantic retrieval."

### F6 Memory representation (Memory and context)

The memory or knowledge design is acknowledged as simple: similarity-only retrieval, flat or minimal representation, static knowledge.

Includes:

- **Simple retrieval.** Retrieval is similarity/embedding based only. *Example from the pilot:* "We intentionally adopt simple embedding- based retrieval and straightforward consolidation to better isolate the effect of content quality."
- **Unstructured or minimal memory.** Memory is flat, non-compositional, minimal, or modelled in a simplified way. *Example from the pilot:* "Our current system design is intentionally minimal"
- **Static knowledge.** Knowledge is injected once and not refreshed during execution. *Example from the pilot:* "However, dynamic acquisition would inevitably introduce additional cost; explor- ing how to balance knowledge freshness and computational cost remains an open challenge."

### F7 Context limitation (Memory and context)

Problems caused by the finite context window: budget pressure, instruction decay, loss through compression or summarisation.

Includes:

- **Context budget pressure.** Content competes for a finite context window; token accounting is unreliable. *Example from the pilot:* "Loading all MCP tool schemas at startup consumed 40% of the context budget before the agent processed its first user message."
- **Instruction decay.** Instructions lose influence as conversations grow. *Example from the pilot:* "3.2 Steering Behavior Over Long Horizons System prompt influence decays as conversations grow. Instructions that reliably govern the agent’s first few turns are routinely violated after 30 or more tool calls, when the instruction is far from the model’s attention window and buried under dozens of tool results."
- **Compression information loss.** Summarising/compressing context loses or distorts information. *Example from the pilot:* "A subtlety: iteratively summarizing a summary accumulates distortion over multiple rounds."

### F8 Resource overhead (Engineering)

The approach costs extra tokens, money, training compute, latency, memory or special hardware.

Includes:

- **Extra token or API cost.** The approach consumes more tokens/API cost. *Example from the pilot:* "The native Bayesian rows spend more tokens"
- **Training compute overhead.** Training requires more compute/time/memory. *Example from the pilot:* "Training overhead. The K-step unrolling training pipeline requires K+1 sequential forward passes through the backbone per training iteration (one warmup pass plus K unrolled steps), compared to a single for- ward pass in standard dLLM training. This multiplicative increase in computation directly raises wall-clock training time and GPU memory consumption, as intermediate activations must be retained across steps for backpropagation through the unrolled computation graph, although the recurrent modules themselves are lightweight (∼0.6% of backbone parame- ters)."
- **Runtime latency or memory.** Inference adds latency or memory. *Example from the pilot:* "In this study, sam- pling functions and class methods based on rel- evance required the use of a text embedding model. When the number of code files in the repository is excessive, this may reduce the sampling rate, leading to increased completion latency."
- **Hardware requirements.** Requires special hardware (e.g. local GPU). *Example from the pilot:* "The SGLang integration requires a GPU with sufficient VRAM (24GB+) and is not applicable to API-only deployments."

### F9 Manual configuration (Engineering)

Templates, prompts, thresholds or hyperparameters are hand-crafted or hand-tuned and may need recalibration.

Includes:

- **Hand-crafted templates or prompts.** Templates, categories or prompts were designed manually and may lack coverage. *Example from the pilot:* "The 24-template reminder catalog and its injection timing were manually engineered based on observed failure modes."
- **Hand-tuned parameters.** Thresholds/hyperparameters are fixed or empirically tuned and may need recalibration. *Example from the pilot:* "Current parameters - the 70% compaction threshold, 3 nudge attempts, 6 thinking depth levels - are globally fixed."

### F10 Agent reliability and safety (Engineering)

The agent produces imperfect artefacts or actions, or running it poses safety or security risks.

Includes:

- **Imperfect generated artefacts.** Generated code or systems are simplistic or contain residual errors. *Example from the pilot:* "The chess engine has a known 13-node error at depth 5, consistent with an en-passant-discovers-check edge case."
- **Agent action errors.** Agents take imprecise or suboptimal actions (edits, tool choice). *Example from the pilot:* "Agents default to text search (grep) for nearly every lookup, even when a more precise tool exists. This wastes iterations and floods the context with false positives."
- **Unsafe code execution.** Generated code runs without isolation, posing security risks. *Example from the pilot:* "While challenges such as execution security remain"

### F11 Incomplete implementation (Engineering)

Functionality the authors consider needed is not yet supported, including integration with model training.

Includes:

- **Unsupported functionality.** Functionality the authors consider needed is not supported yet. *Example from the pilot:* "First, we plan to extend OpenSage to support AI-generated workflows."
- **Not integrated with training.** The approach is not integrated with model training (distillation, RL) or has a training-inference gap. *Example from the pilot:* "help close the training-to-inference extrapolation gap"
