"""
Fix remaining reference issues in the corrected paper.
"""

from docx import Document

doc = Document('D:/Final Year/App Domains 3/datasets/CSC1112 - Fraud Detection Paper - CORRECTED.docx')

changes = []

# Fix [4][5] to just [4] - since [5] is the LightGBM reference
for para in doc.paragraphs:
    if '[4][5]' in para.text:
        new_text = para.text.replace('[4][5]', '[4]')
        for run in para.runs:
            run.text = ""
        if para.runs:
            para.runs[0].text = new_text
        changes.append("Changed '[4][5]' to '[4]' (removed LightGBM reference)")

# Save
output_path = 'D:/Final Year/App Domains 3/datasets/CSC1112 - Fraud Detection Paper - CORRECTED.docx'
doc.save(output_path)

print("Additional fixes applied:")
for change in changes:
    print(f"  - {change}")

print(f"\nDocument saved to: {output_path}")
