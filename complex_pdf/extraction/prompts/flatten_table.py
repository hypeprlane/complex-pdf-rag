FLATTEN_TABLE_PROMPT = """
You are given a table in HTML format.

Your task:
- Flatten this table into a clear, human-readable paragraph.
- Include *every significant piece of data* from the table: titles, component names, values, units, material names, codes, and other properties.
- Preserve structure and associations, e.g. which material corresponds to which part.
- Do not omit or generalize any rows or key values. Include numeric values and special codes exactly as seen.
- Ensure no technical information from the table is lost.
- Do not return any HTML, code, or markup — just plain text.

Here is the table HTML:
---
{table_html}
---
Please return the flattened, lossless table description suitable for embedding.
"""
