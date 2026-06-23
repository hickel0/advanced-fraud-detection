"""
Script to modify the Fraud Detection notebook to save all visualizations to an outputs directory.
"""

import json
import os

# Read the notebook
notebook_path = 'D:/Final Year/App Domains 3/datasets/Fraud_Detection_PaySim_Analysis.ipynb'
with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook = json.load(f)

# Mapping of cell IDs to figure names
figure_names = {
    'y5z6a7b8': 'fig01_class_distribution',
    'g3h4i5j6': 'fig02_fraud_by_transaction_type',
    's5t6u7v8': 'fig03_amount_distribution',
    's7t8u9v0': 'fig04_rq1_algorithm_comparison',
    'w1x2y3z4': 'fig05_rq1_roc_curves',
    'a5b6c7d8': 'fig06_rq1_precision_recall_curves',
    'u5v6w7x8': 'fig07_rq2_feature_importance',
    'c3d4e5f6': 'fig08_rq2_feature_correlation',
    'k1l2m3n4': 'fig09_rq2_top_feature_distributions',
    'm9n0o1p2': 'fig10_rq3_imbalance_comparison',
    'q3r4s5t6': 'fig11_rq3_precision_recall_tradeoff',
    'u7v8w9x0': 'fig12_rq3_confusion_matrices',
    'y1z2a3b4': 'fig13_rq3_roc_curves',
    'c5d6e7f8': 'fig14_rq3_pr_curves',
    'k3l4m5n6': 'fig15_rq3_threshold_analysis',
    'a9b0c1d2': 'fig16_final_summary'
}

# Create the output directory setup cell
output_setup_cell = {
    "cell_type": "code",
    "id": "output_setup",
    "metadata": {},
    "source": [
        "# Setup output directory for saving figures\n",
        "import os\n",
        "\n",
        "OUTPUT_DIR = 'D:/Final Year/App Domains 3/datasets/outputs'\n",
        "os.makedirs(OUTPUT_DIR, exist_ok=True)\n",
        "print(f'Output directory created: {OUTPUT_DIR}')\n",
        "\n",
        "# Set high DPI for better quality figures\n",
        "SAVE_DPI = 300\n",
        "SAVE_FORMAT = 'png'  # Can also use 'pdf', 'svg', etc."
    ],
    "outputs": [],
    "execution_count": None
}

# Find the imports cell index and insert after it
imports_idx = None
for i, cell in enumerate(notebook['cells']):
    cell_id = cell.get('id', '')
    if cell_id == 'i9j0k1l2':  # The imports cell
        imports_idx = i
        break

if imports_idx is not None:
    # Insert the output setup cell after imports
    notebook['cells'].insert(imports_idx + 1, output_setup_cell)
    print(f"Inserted output setup cell after index {imports_idx}")

# Now modify each visualization cell
modified_count = 0
for cell in notebook['cells']:
    if cell['cell_type'] != 'code':
        continue

    cell_id = cell.get('id', '')

    # Get source as string
    if isinstance(cell['source'], list):
        source = ''.join(cell['source'])
    else:
        source = cell['source']

    # Skip if already modified or no plt.show()
    if 'savefig' in source or 'plt.show()' not in source:
        continue

    # Get figure name
    fig_name = figure_names.get(cell_id, f'figure_{cell_id}')

    # Create the savefig line
    savefig_line = f"plt.savefig(f'{{OUTPUT_DIR}}/{fig_name}.{{SAVE_FORMAT}}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')\nprint(f'Saved: {fig_name}.{{SAVE_FORMAT}}')\n"

    # Replace plt.show() with savefig + plt.show()
    new_source = source.replace(
        'plt.show()',
        savefig_line + 'plt.show()'
    )

    # Update cell source
    cell['source'] = new_source.split('\n')
    # Add newlines back except for last line
    cell['source'] = [line + '\n' for line in cell['source'][:-1]] + [cell['source'][-1]]

    modified_count += 1
    print(f"Modified cell: {cell_id} -> {fig_name}")

# Save the modified notebook
output_notebook_path = 'D:/Final Year/App Domains 3/datasets/Fraud_Detection_PaySim_Analysis.ipynb'
with open(output_notebook_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1)

print(f"\n{'='*60}")
print(f"Modified {modified_count} cells")
print(f"Notebook saved to: {output_notebook_path}")
print(f"Figures will be saved to: D:/Final Year/App Domains 3/datasets/outputs/")
print(f"{'='*60}")
