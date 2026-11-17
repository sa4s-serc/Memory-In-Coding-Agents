# Relevance Screening stage with Bucketing

Stage 1 screening of the 2,411 merged records by title and abstract, followed by human validation of the LLM decisions.

## Contents

| File | Description |
|---|---|
| `screen.py` | Screening script, including the full prompt with IC1, IC2 and EC1 |
| `screened_qwen3.5_397b_r1.jsonl` | One line per record: `id`, `title`, `include` (probability 0 to 1), `bucket` (PRIMARY / SURVEY / BENCHMARK / EXCLUDE), `reason`, `abstract_chars` |
| `cohens_kappa/` | Human validation sample and rater sheets |

## Procedure

- **Model:** qwen3.5:397b via Ollama Cloud, temperature 0, batches of 10 records.
- **Records scored:** 2,408. Three records with no abstract (R01835, R02226, R02242) were screened manually.
- **Cutoff:** records with `include` >= 0.70 were retained, giving 1,048 records: 860 PRIMARY, 104 SURVEY and 84 BENCHMARK. The prompt defines 0.3 to 0.7 as the band for borderline records. Every quasi-gold-standard paper in the corpus scored >= 0.90.
- **Next stage:** the 860 PRIMARY records go on to the implementation screen.

## Validation (`cohens_kappa/`)

- **Sample:** 60 records drawn at random, 20 from each score band:
  - high: >= 0.70
  - mid: 0.50 to 0.69
  - low: < 0.50
- **Raters:** two raters (PSK, AG) labelled each record INCLUDE or EXCLUDE against IC1, IC2 and EC1, independently and without seeing the model's output.
- **Disagreements:** the two disagreements were resolved by discussion to form the consensus labels.

| Measure | Value |
|---|---|
| Inter-rater agreement (PSK vs AG) | κ = 0.921, 96.7% observed agreement |
| Model vs consensus | κ = 0.692, 86.7% observed agreement |
