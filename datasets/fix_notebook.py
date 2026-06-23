"""
Fix the notebook by removing outdated data leakage comparison cells
that reference variables from the old (leaked) analysis.
"""

import json

notebook_path = 'D:/Final Year/App Domains 3/datasets/Fraud_Detection_PaySim_Analysis.ipynb'

with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook = json.load(f)

print(f"Total cells before: {len(notebook['cells'])}")

# Find and remove cells that reference old variables or are part of the
# outdated leakage comparison section
cells_to_remove = []
outdated_ids = [
    'leakage_section_header',
    'leakage_analysis',
    'safe_features_header',
    'safe_features_model',
    'safe_model_training',
    'leakage_comparison',
    'leakage_comparison_viz',
    'safe_feature_importance',
    'leakage_conclusion'
]

for i, cell in enumerate(notebook['cells']):
    cell_id = cell.get('id', '')

    # Check if this is one of the outdated cells
    if cell_id in outdated_ids:
        cells_to_remove.append(i)
        print(f"Marking for removal: {cell_id}")
        continue

    # Also check source for references to old variables
    source = cell.get('source', [])
    if isinstance(source, list):
        source = ''.join(source)

    # Check for cells referencing old variable names that no longer exist
    if 'results_df_rq3[' in source and 'results_df_rq3_safe' not in source:
        # This cell uses the old variable name
        cells_to_remove.append(i)
        print(f"Marking for removal (old var): cell at index {i}")

# Remove cells in reverse order to preserve indices
for idx in sorted(cells_to_remove, reverse=True):
    del notebook['cells'][idx]

print(f"\nRemoved {len(cells_to_remove)} outdated cells")
print(f"Total cells after: {len(notebook['cells'])}")

# Save the fixed notebook
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1)

print(f"\nNotebook saved to: {notebook_path}")
print("The notebook should now run without NameError")
