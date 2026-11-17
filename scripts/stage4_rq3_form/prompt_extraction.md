You will fill in a data extraction form for one research paper, record {record_id}. The full text of the paper comes first, divided into pages marked "[p. N]". The form, its rules and the output format follow after it.

<paper id="{record_id}">
{text}
</paper>

## Task

The form records which kinds of limitations the authors report about their own work. Record only what the authors state. Do not add limitations you notice yourself, and do not judge whether a stated limitation is real or important. A human expert fills in the same form for some papers using exactly these rules; record what they would record.

For each statement that might be a limitation, check in order:
1. Is it about the authors' own approach, system or evaluation? (rule 1)
2. Do the authors present it as a weakness, shortfall, cost, risk, open problem or untested condition? A neutral description of the design, a measurement given without being called a drawback, or a result presented as an advantage is not a limitation. (rule 2)
3. Is it specific to this study, or is it boilerplate? (rule 4)
4. If it is future work, does it name a specific thing the current work does not do, have or test? (rule 6)
5. Which single field fits best? (rules 7 and 8)

If the answer to 1, 2 or 4 is no, or 3 is boilerplate, skip the statement. If you are unsure, skip it (rule 9).

## Rules

{rules}

## Fields

{fields}

## Output

Return only a JSON object, with no text before or after it. For every field F1 to F11, give "present" (true or false) and, when true, one to three verbatim quotes from the paper with their page numbers. Copy each quote exactly as it appears in the text above, including hyphenation and spacing.

{{"record_id": "{record_id}",
 "fields": {{
  "F1": {{"present": true, "evidence": [{{"quote": "<verbatim text>", "page": 9}}]}},
  "F2": {{"present": false, "evidence": []}},
  ...
  "F11": {{"present": false, "evidence": []}}
 }},
 "only_boilerplate": false,
 "no_limitation": false}}

Set "only_boilerplate" to true if the only limitation statements are boilerplate, and "no_limitation" to true if the paper states no limitation at all; in both cases every field is false.
