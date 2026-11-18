# RQ3 Reported limitations: results

This report gives the results of the RQ3 data extraction: which kinds of limitations the authors of the 151 within-task and cross-task papers report about their own work. 

## Summary

- 144 (95%) of the 151 papers report at least one specific limitation of their own work; the median paper reports limitations in 3 of the 11 fields.
- The most frequent field by far is F1 Generalizability (116 papers, 77%), followed by F11 Incomplete implementation (62, 41%), F8 Resource overhead and F10 Agent reliability and safety (58 each, 38%).
- Cross-task papers report limitations of accumulated experience (F5) far more often than within-task papers (32% vs 9%); within-task papers report resource overhead (F8) more often (45% vs 27%).
- The two LLMs agreed with each other at Cohen's κ = 0.75 (1661 decisions). A blind human evaluation of 30 papers agreed with the final values at κ = 0.70 (95% CI 0.60–0.79).

## Method

**Population.** All 151 papers classified WITHIN (95) or CROSS (56) in the classification step; 91 CORE and 60 COMPONENT.

**Form.** `scripts/extraction_form_v1.json` (version 1.1), described for human raters in `scripts/extraction_guidelines.md`. It has 11 binary fields in three groups (Evaluation, Memory and context, Engineering) and 11 rules. A field is 1 if the authors state at least one limitation of that kind about their own work. Boilerplate statements that would be true of any paper fill no field.

**Origin of the form.** The fields were derived from a pilot on 30 randomly selected papers (seed 20261114). Limitation statements in the pilot papers were extracted and open-coded manually into 14 provisional themes, which the second author consolidated into 11 fields. Version 1.1 clarified the rules after a calibration run of both LLMs on the 30 pilot papers only, before any non-pilot paper was extracted and before the human evaluation. No field was added, removed or renamed.

**Text.** The full text of each PDF up to the references, plus appendix pages that carry a limitations-type heading (21 papers). Text length: median 41,830 characters.

**Extraction.** Two LLMs filled in the form independently for every paper with the prompt `scripts/prompt_extraction.md`: model A = deepseek-v4-pro:0813 and model B = glm-5.3, both through the Ollama API at temperature 0. Both runs used the same prompt and form (SHA-256 `0b9b0f76…`, recorded in `results/llm/<model>/_run.json`). Each filled field had to be supported by verbatim quotes with page numbers, which the script checked against the text.

**Adjudication.** Where the two LLMs agreed, their value is final. The 173 decisions on which they disagreed (in 99 papers) were decided by the first author from the paper, checking both models' quotes.

**Human evaluation.** A human filled in the form for a stratified random sample of 30 non-pilot papers (strata: scope × whether the LLMs disagreed on the paper; proportional allocation, seed 20261115), without seeing any LLM output. The rater used the same rules as the LLMs.

## 1. Limitations we find to be reported

Papers with at least one field: 144 (95%) overall, 90 (95%) within-task, 54 (96%) cross-task. The other 7 papers state no limitation or only boilerplate.

| Field | Group | All (N=151) | Within-task (N=95) | Cross-task (N=56) |
|---|---|---|---|---|
| F1 Generalizability | Evaluation | 116 (77%) | 74 (78%) | 42 (75%) |
| F2 Weak experimental validation | Evaluation | 46 (30%) | 24 (25%) | 22 (39%) |
| F3 Evaluation quality | Evaluation | 45 (30%) | 27 (28%) | 18 (32%) |
| F4 Memory quality | Memory and context | 43 (28%) | 24 (25%) | 19 (34%) |
| F5 Limited experience | Memory and context | 27 (18%) | 9 (9%) | 18 (32%) |
| F6 Memory representation | Memory and context | 14 (9%) | 5 (5%) | 9 (16%) |
| F7 Context limitation | Memory and context | 20 (13%) | 16 (17%) | 4 (7%) |
| F8 Resource overhead | Engineering | 58 (38%) | 43 (45%) | 15 (27%) |
| F9 Manual configuration | Engineering | 17 (11%) | 13 (14%) | 4 (7%) |
| F10 Agent reliability and safety | Engineering | 58 (38%) | 40 (42%) | 18 (32%) |
| F11 Incomplete implementation | Engineering | 62 (41%) | 42 (44%) | 20 (36%) |

Papers with at least one field in each group:

| Group | All (N=151) | Within-task (N=95) | Cross-task (N=56) |
|---|---|---|---|
| Evaluation | 128 (85%) | 78 (82%) | 50 (89%) |
| Memory and context | 78 (52%) | 45 (47%) | 33 (59%) |
| Engineering | 115 (76%) | 75 (79%) | 40 (71%) |

Median number of fields per paper (papers with any): 3 overall, 3 within-task, 3 cross-task.

## 2. Agreement between the two LLMs

151 papers × 11 fields = 1661 decisions. Pooled Cohen's κ = **0.749**, raw agreement 89.6%. 173 decisions differed, in 99 papers.

| Field | κ | Agreement | A: papers | B: papers |
|---|---|---|---|---|
| F1 Generalizability | 0.729 | 90% | 114 | 115 |
| F2 Weak experimental validation | 0.726 | 89% | 47 | 40 |
| F3 Evaluation quality | 0.767 | 91% | 46 | 36 |
| F4 Memory quality | 0.602 | 83% | 43 | 46 |
| F5 Limited experience | 0.579 | 87% | 31 | 24 |
| F6 Memory representation | 0.733 | 95% | 14 | 15 |
| F7 Context limitation | 0.634 | 93% | 20 | 10 |
| F8 Resource overhead | 0.740 | 88% | 59 | 47 |
| F9 Manual configuration | 0.762 | 95% | 17 | 16 |
| F10 Agent reliability and safety | 0.687 | 86% | 56 | 43 |
| F11 Incomplete implementation | 0.732 | 87% | 66 | 68 |

Model A filled more fields than model B (513 vs 460), most visibly in F7, F10, F8 and F3.

## 3. Adjudication

All disagreements were adjudicated; The decisions and notes are in `results/LLM_conflicts_manual_adjudication.xlsx`.

## 4. Human evaluation

30 papers × 11 fields = 330 decisions. Sample strata: CROSS/agree 4, CROSS/disagree 7, WITHIN/agree 5, WITHIN/disagree 14. The 95% confidence intervals come from a bootstrap over papers (5000 draws). Precision and recall treat the human values as the reference.

| Comparison | κ | 95% CI | Agreement | Precision | Recall | Fields set to 1 (human / other) |
|---|---|---|---|---|---|---|
| Human vs A (deepseek-v4-pro:0813) | 0.654 | 0.55–0.74 | 84.5% | 0.72 | 0.82 | 103 / 118 |
| Human vs B (glm-5.3) | 0.724 | 0.64–0.80 | 88.2% | 0.81 | 0.81 | 103 / 102 |
| Human vs final values | 0.701 | 0.60–0.79 | 86.7% | 0.75 | 0.85 | 103 / 117 |
## 5. Files

| File | Content |
|---|---|
| `results/papers.csv` | The 151 papers: record_id, scope, role, pilot (0/1) |
| `results/text_log.csv` | Text extraction per paper: characters, appendix pages kept |
| `results/llm/<model>/<record_id>.json` | Each model's filled form, with quotes, page numbers and verbatim checks |
| `results/llm/<model>/_run.json` | Model, host, temperature, thinking setting, prompt+form SHA-256, start time |
| `results/llm_agreement.json`, `results/disagreements.csv` | LLM–LLM agreement and the list of disagreements with both models' quotes |
| `results/LLM_conflicts_manual_adjudication.xlsx` | The adjudicated value for each disagreement |
| `results/human_sample.csv` | The human evaluation sample |
| `results/PSK_eval.xlsx`, `results/AG_eval.xlsx` | The two human raters' filled forms (PSK, AG) |
| `results/PSK_vs_AG_conflicts.xlsx` | Field-level conflicts between the two human raters, with notes and resolutions |
| `results/human_eval.json` | Human vs A, B and final: κ with CI, precision, recall, per-field counts |
| `results/paper_fields.csv` | Final values per paper (F1–F11), number of fields, status |
| `results/rq3_summary.json` | The counts in Section 1 |
