# rq3_form: reported limitations (RQ3)

Data extraction of the limitations that the authors of the 151 within-task and cross-task papers report about their own work. Two LLMs filled in an 11-field form for every paper; the first author adjudicated their disagreements; a human filled in the form blind for 30 papers to evaluate the result. The results are in `report.md`.

## Layout

```
rq3_form/
  report.md                     all results
  scripts/
    extraction_form_v1.json     the form: 11 fields and 11 rules (version 1.1)
    extraction_guidelines.md    the same form and rules, written for human raters
    prompt_extraction.md        the LLM prompt template (the form's rules and fields are inserted)
    pilot_sample.txt            the 30 pilot papers the form was calibrated on
    rq3_common.py               paths, model names, shared helpers
    rq3_01_fulltext.py          1. list the 151 papers, extract their text from the PDFs
    rq3_02_extract_llm.py       2. one LLM fills in the form for every paper
    rq3_03_agreement.py         3. LLM-LLM agreement, human sample, adjudication sheet
    rq3_04_finalize.py          4. final values per paper and counts per field
    rq3_05_human_eval.py        5. human vs LLM agreement
  results/                      everything the scripts produced (see the table at the end of report.md)
```

## Reproduce

Requires Python 3.11+ and `pip install pandas numpy openpyxl pymupdf requests`.

Steps 4 and 5 run on the files in `results/` alone:

```
cd scripts
python rq3_04_finalize.py
python rq3_05_human_eval.py
```

Re-running the extraction from scratch needs the PDFs and `classification_joined.xlsx` from the classification step (set `PATHS` in `rq3_common.py`) and an Ollama API key in the environment (`export OLLAMA_API_KEY=...`):

```
python rq3_01_fulltext.py                  # writes results/papers.csv and results/text/ (paper text, not included here)
python rq3_02_extract_llm.py --model A     # deepseek-v4-pro:0813
python rq3_02_extract_llm.py --model B     # glm-5.3
python rq3_03_agreement.py                 # writes human_eval.xlsx and adjudication.xlsx (does not overwrite existing ones); renamed in results/ to PSK_eval.xlsx and LLM_conflicts_manual_adjudication.xlsx
```

LLM output can vary between runs even at temperature 0, so a re-run may not reproduce `results/llm/` exactly. The prompt and form used are fixed by the SHA-256 recorded in `results/llm/<model>/_run.json`.

The extracted paper text (`results/text/`) is not included because the papers are under copyright; `rq3_01_fulltext.py` rebuilds it from the PDFs.
