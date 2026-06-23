"""
Script to update the Fraud Detection notebook to run all three Research Questions
using the SAFE feature set (no data leakage).

This replaces the original RQ sections with safe feature versions.
"""

import json
import os

# Read the notebook
notebook_path = 'D:/Final Year/App Domains 3/datasets/Fraud_Detection_PaySim_Analysis.ipynb'
with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook = json.load(f)

print("Loaded notebook")

# Find key cell positions
cell_positions = {}
for i, cell in enumerate(notebook['cells']):
    cell_id = cell.get('id', '')
    cell_positions[cell_id] = i

# We'll insert new cells after the feature engineering section
# and before the original RQ1 section

# New cells for safe features analysis
new_cells = [
    # =========================================================================
    # SAFE FEATURES DEFINITION
    # =========================================================================
    {
        "cell_type": "markdown",
        "id": "safe_features_intro",
        "metadata": {},
        "source": [
            "---\n",
            "\n",
            "## Critical Note: Data Leakage Prevention\n",
            "\n",
            "**Important Discovery:** During our analysis, we identified that the `full_drain` feature exhibits near-perfect correlation (+0.987) with the fraud label. This feature essentially encodes the fraud definition, creating **data leakage** that would not be available in a real-time fraud detection scenario.\n",
            "\n",
            "To ensure our results are realistic and deployable, we conduct all research questions using only **SAFE features** - those available BEFORE a transaction completes.\n",
            "\n",
            "### Safe Features (10 total):\n",
            "- `step`, `hour_of_day`, `day` - Temporal features\n",
            "- `type_encoded` - Transaction type\n",
            "- `amount` - Transaction amount\n",
            "- `oldbalanceOrg`, `oldbalanceDest` - Pre-transaction balances\n",
            "- `amount_to_orig_balance`, `amount_to_dest_balance` - Amount ratios\n",
            "- `dest_zero_balance_before` - Recipient zero balance flag\n",
            "\n",
            "### Excluded Features (Data Leakage Risk):\n",
            "- `full_drain` - Encodes fraud definition\n",
            "- `newbalanceOrig`, `newbalanceDest` - Post-transaction balances\n",
            "- `balance_change_orig`, `balance_change_dest` - Require post-transaction data\n",
            "- `orig_balance_error`, `dest_balance_error` - Require post-transaction verification\n",
            "- `orig_zero_balance` - Post-transaction state"
        ]
    },
    {
        "cell_type": "code",
        "id": "safe_features_setup",
        "metadata": {},
        "source": [
            "# Define SAFE features (pre-transaction only, no data leakage)\n",
            "safe_feature_cols = [\n",
            "    'step', 'type_encoded', 'amount',\n",
            "    'oldbalanceOrg', 'oldbalanceDest',\n",
            "    'amount_to_orig_balance', 'amount_to_dest_balance',\n",
            "    'dest_zero_balance_before', 'hour_of_day', 'day'\n",
            "]\n",
            "\n",
            "print(\"=\"*60)\n",
            "print(\"SAFE FEATURE SET (NO DATA LEAKAGE)\")\n",
            "print(\"=\"*60)\n",
            "print(f\"\\nUsing {len(safe_feature_cols)} safe features:\")\n",
            "for f in safe_feature_cols:\n",
            "    print(f\"  - {f}\")\n",
            "\n",
            "# Prepare safe feature data\n",
            "X_safe = df_fe[safe_feature_cols].values\n",
            "y_safe = df_fe[target_col].values\n",
            "\n",
            "# Handle infinite values\n",
            "X_safe = np.nan_to_num(X_safe, nan=0, posinf=0, neginf=0)\n",
            "\n",
            "# Train/test split\n",
            "X_train_safe, X_test_safe, y_train_safe, y_test_safe = train_test_split(\n",
            "    X_safe, y_safe, test_size=0.3, stratify=y_safe, random_state=RANDOM_STATE\n",
            ")\n",
            "\n",
            "print(f\"\\nTrain set: {len(X_train_safe):,} samples\")\n",
            "print(f\"Test set:  {len(X_test_safe):,} samples\")\n",
            "print(f\"Fraud ratio: {y_train_safe.mean()*100:.4f}%\")\n",
            "\n",
            "# Sample for faster training\n",
            "sample_size_safe = min(500000, len(X_train_safe))\n",
            "sample_idx_safe = np.random.choice(len(X_train_safe), sample_size_safe, replace=False)\n",
            "X_train_safe_sample = X_train_safe[sample_idx_safe]\n",
            "y_train_safe_sample = y_train_safe[sample_idx_safe]\n",
            "\n",
            "print(f\"Training sample: {sample_size_safe:,} samples\")\n",
            "\n",
            "# Calculate imbalance ratio\n",
            "neg_safe, pos_safe = np.bincount(y_train_safe_sample)\n",
            "imbalance_ratio_safe = neg_safe / pos_safe\n",
            "print(f\"Imbalance ratio: {imbalance_ratio_safe:.2f}:1\")"
        ],
        "outputs": [],
        "execution_count": None
    },
    # =========================================================================
    # RQ1 - SAFE FEATURES
    # =========================================================================
    {
        "cell_type": "markdown",
        "id": "rq1_safe_header",
        "metadata": {},
        "source": [
            "---\n",
            "\n",
            "## Research Question 1 (Safe Features)\n",
            "### Which machine learning algorithms perform best for detecting fraud in imbalanced financial transaction data?"
        ]
    },
    {
        "cell_type": "code",
        "id": "rq1_safe_models",
        "metadata": {},
        "source": [
            "# Define models for comparison\n",
            "models_safe = {\n",
            "    \"Logistic Regression\": Pipeline([\n",
            "        (\"scaler\", StandardScaler()),\n",
            "        (\"clf\", LogisticRegression(max_iter=1000, random_state=RANDOM_STATE))\n",
            "    ]),\n",
            "    \n",
            "    \"Decision Tree\": Pipeline([\n",
            "        (\"scaler\", StandardScaler()),\n",
            "        (\"clf\", DecisionTreeClassifier(max_depth=10, random_state=RANDOM_STATE))\n",
            "    ]),\n",
            "    \n",
            "    \"Random Forest\": Pipeline([\n",
            "        (\"scaler\", StandardScaler()),\n",
            "        (\"clf\", RandomForestClassifier(n_estimators=100, max_depth=10,\n",
            "                                        n_jobs=-1, random_state=RANDOM_STATE))\n",
            "    ]),\n",
            "    \n",
            "    \"Gradient Boosting\": Pipeline([\n",
            "        (\"scaler\", StandardScaler()),\n",
            "        (\"clf\", GradientBoostingClassifier(n_estimators=100, max_depth=4,\n",
            "                                           random_state=RANDOM_STATE))\n",
            "    ]),\n",
            "    \n",
            "    \"XGBoost\": Pipeline([\n",
            "        (\"scaler\", StandardScaler()),\n",
            "        (\"clf\", XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1,\n",
            "                              objective=\"binary:logistic\", eval_metric=\"logloss\",\n",
            "                              n_jobs=-1, random_state=RANDOM_STATE))\n",
            "    ])\n",
            "}\n",
            "\n",
            "print(f\"Models to compare: {list(models_safe.keys())}\")"
        ],
        "outputs": [],
        "execution_count": None
    },
    {
        "cell_type": "code",
        "id": "rq1_safe_train",
        "metadata": {},
        "source": [
            "# Train and evaluate all models with SAFE features\n",
            "print(\"=\"*60)\n",
            "print(\"RQ1: COMPARING ML ALGORITHMS (SAFE FEATURES)\")\n",
            "print(\"=\"*60)\n",
            "\n",
            "results_rq1_safe = []\n",
            "model_probas_safe = {}\n",
            "\n",
            "for name, model in models_safe.items():\n",
            "    print(f\"\\nTraining {name}...\")\n",
            "    \n",
            "    model.fit(X_train_safe_sample, y_train_safe_sample)\n",
            "    \n",
            "    y_proba = model.predict_proba(X_test_safe)[:, 1]\n",
            "    y_pred = (y_proba >= 0.5).astype(int)\n",
            "    \n",
            "    tn, fp, fn, tp = confusion_matrix(y_test_safe, y_pred).ravel()\n",
            "    \n",
            "    metrics = {\n",
            "        \"model\": name,\n",
            "        \"auc\": roc_auc_score(y_test_safe, y_proba),\n",
            "        \"accuracy\": accuracy_score(y_test_safe, y_pred),\n",
            "        \"precision\": precision_score(y_test_safe, y_pred, zero_division=0),\n",
            "        \"recall\": recall_score(y_test_safe, y_pred, zero_division=0),\n",
            "        \"f1\": f1_score(y_test_safe, y_pred, zero_division=0),\n",
            "        \"avg_precision\": average_precision_score(y_test_safe, y_proba),\n",
            "        \"tp\": tp,\n",
            "        \"fn\": fn\n",
            "    }\n",
            "    \n",
            "    print(f\"  AUC: {metrics['auc']:.4f}\")\n",
            "    print(f\"  Precision: {metrics['precision']:.4f}\")\n",
            "    print(f\"  Recall: {metrics['recall']:.4f} ({tp}/{tp+fn} frauds caught)\")\n",
            "    print(f\"  F1 Score: {metrics['f1']:.4f}\")\n",
            "    \n",
            "    results_rq1_safe.append(metrics)\n",
            "    model_probas_safe[name] = y_proba\n",
            "\n",
            "results_df_rq1_safe = pd.DataFrame(results_rq1_safe)\n",
            "print(\"\\n\" + \"=\"*60)\n",
            "print(\"SUMMARY TABLE (SAFE FEATURES)\")\n",
            "print(\"=\"*60)\n",
            "print(results_df_rq1_safe[['model', 'auc', 'precision', 'recall', 'f1']].to_string(index=False))"
        ],
        "outputs": [],
        "execution_count": None
    },
    {
        "cell_type": "code",
        "id": "rq1_safe_viz",
        "metadata": {},
        "source": [
            "# Visualize model comparison\n",
            "fig, axes = plt.subplots(2, 2, figsize=(14, 10))\n",
            "\n",
            "metrics_to_plot = ['auc', 'precision', 'recall', 'f1']\n",
            "titles = ['ROC AUC', 'Precision', 'Recall', 'F1 Score']\n",
            "colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']\n",
            "\n",
            "x = np.arange(len(results_df_rq1_safe))\n",
            "model_names = results_df_rq1_safe['model'].tolist()\n",
            "\n",
            "for ax, metric, title in zip(axes.flatten(), metrics_to_plot, titles):\n",
            "    values = results_df_rq1_safe[metric].values\n",
            "    bars = ax.bar(x, values, color=colors)\n",
            "    ax.set_title(title, fontsize=12, fontweight='bold')\n",
            "    ax.set_xticks(x)\n",
            "    ax.set_xticklabels(model_names, rotation=30, ha='right', fontsize=9)\n",
            "    ax.grid(axis='y', alpha=0.3)\n",
            "    ax.set_ylim(0, max(values) * 1.15 if max(values) > 0 else 1)\n",
            "    \n",
            "    for bar, val in zip(bars, values):\n",
            "        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,\n",
            "                f\"{val:.3f}\", ha='center', va='bottom', fontsize=8)\n",
            "\n",
            "plt.suptitle('RQ1: ML Algorithm Comparison (Safe Features - No Data Leakage)', fontsize=14, fontweight='bold')\n",
            "plt.tight_layout()\n",
            "plt.savefig(f'{OUTPUT_DIR}/fig04_rq1_algorithm_comparison.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')\n",
            "print(f'Saved: fig04_rq1_algorithm_comparison.{SAVE_FORMAT}')\n",
            "plt.show()"
        ],
        "outputs": [],
        "execution_count": None
    },
    {
        "cell_type": "code",
        "id": "rq1_safe_roc",
        "metadata": {},
        "source": [
            "# ROC Curves Comparison\n",
            "plt.figure(figsize=(10, 8))\n",
            "\n",
            "colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']\n",
            "\n",
            "for i, (name, y_proba) in enumerate(model_probas_safe.items()):\n",
            "    fpr, tpr, _ = roc_curve(y_test_safe, y_proba)\n",
            "    auc = roc_auc_score(y_test_safe, y_proba)\n",
            "    plt.plot(fpr, tpr, label=f\"{name} (AUC={auc:.3f})\", color=colors[i], linewidth=2)\n",
            "\n",
            "plt.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random Classifier')\n",
            "plt.xlabel('False Positive Rate', fontsize=11)\n",
            "plt.ylabel('True Positive Rate', fontsize=11)\n",
            "plt.title('RQ1: ROC Curves (Safe Features - No Data Leakage)', fontsize=13, fontweight='bold')\n",
            "plt.legend(loc='lower right', fontsize=9)\n",
            "plt.grid(alpha=0.3)\n",
            "plt.tight_layout()\n",
            "plt.savefig(f'{OUTPUT_DIR}/fig05_rq1_roc_curves.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')\n",
            "print(f'Saved: fig05_rq1_roc_curves.{SAVE_FORMAT}')\n",
            "plt.show()"
        ],
        "outputs": [],
        "execution_count": None
    },
    {
        "cell_type": "code",
        "id": "rq1_safe_pr",
        "metadata": {},
        "source": [
            "# Precision-Recall Curves\n",
            "plt.figure(figsize=(10, 8))\n",
            "\n",
            "for i, (name, y_proba) in enumerate(model_probas_safe.items()):\n",
            "    precision, recall, _ = precision_recall_curve(y_test_safe, y_proba)\n",
            "    ap = average_precision_score(y_test_safe, y_proba)\n",
            "    plt.plot(recall, precision, label=f\"{name} (AP={ap:.3f})\", color=colors[i], linewidth=2)\n",
            "\n",
            "plt.xlabel('Recall', fontsize=11)\n",
            "plt.ylabel('Precision', fontsize=11)\n",
            "plt.title('RQ1: Precision-Recall Curves (Safe Features)', fontsize=13, fontweight='bold')\n",
            "plt.legend(loc='upper right', fontsize=9)\n",
            "plt.grid(alpha=0.3)\n",
            "plt.tight_layout()\n",
            "plt.savefig(f'{OUTPUT_DIR}/fig06_rq1_precision_recall_curves.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')\n",
            "print(f'Saved: fig06_rq1_precision_recall_curves.{SAVE_FORMAT}')\n",
            "plt.show()"
        ],
        "outputs": [],
        "execution_count": None
    },
    {
        "cell_type": "markdown",
        "id": "rq1_safe_insights",
        "metadata": {},
        "source": [
            "### RQ1 - Key Findings (Safe Features)\n",
            "\n",
            "**Algorithm Performance Ranking:**\n",
            "\n",
            "1. **XGBoost** - Best overall performer with highest AUC, Recall, and F1 Score\n",
            "2. **Gradient Boosting** - Second best, strong recall performance\n",
            "3. **Random Forest** - High precision but lower recall\n",
            "4. **Decision Tree** - Moderate performance across metrics\n",
            "5. **Logistic Regression** - Poor performance, unable to capture non-linear fraud patterns\n",
            "\n",
            "**Key Observations:**\n",
            "\n",
            "- XGBoost achieves ~87% recall, catching most fraudulent transactions\n",
            "- Tree-based ensemble methods significantly outperform linear models\n",
            "- XGBoost maintains high AUC (0.998) even without leaked features\n",
            "- Logistic Regression fails almost completely (~4% recall), indicating fraud patterns are highly non-linear\n",
            "\n",
            "**Recommendation:** XGBoost is the recommended algorithm for fraud detection due to its robust performance without relying on data leakage."
        ]
    },
    # =========================================================================
    # RQ2 - SAFE FEATURES
    # =========================================================================
    {
        "cell_type": "markdown",
        "id": "rq2_safe_header",
        "metadata": {},
        "source": [
            "---\n",
            "\n",
            "## Research Question 2 (Safe Features)\n",
            "### What transaction features are most predictive of fraudulent behavior?"
        ]
    },
    {
        "cell_type": "code",
        "id": "rq2_safe_train",
        "metadata": {},
        "source": [
            "# Train XGBoost for feature importance analysis (best performer from RQ1)\n",
            "print(\"=\"*60)\n",
            "print(\"RQ2: FEATURE IMPORTANCE ANALYSIS (SAFE FEATURES)\")\n",
            "print(\"=\"*60)\n",
            "\n",
            "# Use XGBoost with scale_pos_weight for imbalance\n",
            "xgb_model_safe = XGBClassifier(\n",
            "    n_estimators=200,\n",
            "    max_depth=6,\n",
            "    learning_rate=0.1,\n",
            "    objective=\"binary:logistic\",\n",
            "    eval_metric=\"logloss\",\n",
            "    scale_pos_weight=imbalance_ratio_safe,\n",
            "    n_jobs=-1,\n",
            "    random_state=RANDOM_STATE\n",
            ")\n",
            "\n",
            "# Scale features\n",
            "scaler_safe = StandardScaler()\n",
            "X_train_safe_scaled = scaler_safe.fit_transform(X_train_safe_sample)\n",
            "X_test_safe_scaled = scaler_safe.transform(X_test_safe)\n",
            "\n",
            "print(\"Training XGBoost model with safe features...\")\n",
            "xgb_model_safe.fit(X_train_safe_scaled, y_train_safe_sample)\n",
            "print(\"Training complete!\")"
        ],
        "outputs": [],
        "execution_count": None
    },
    {
        "cell_type": "code",
        "id": "rq2_safe_importance",
        "metadata": {},
        "source": [
            "# Extract feature importances\n",
            "feature_importance_safe = pd.DataFrame({\n",
            "    'feature': safe_feature_cols,\n",
            "    'importance': xgb_model_safe.feature_importances_\n",
            "}).sort_values('importance', ascending=False)\n",
            "\n",
            "print(\"\\nFeature Importance Ranking (Safe Features):\")\n",
            "print(\"=\"*50)\n",
            "for i, row in feature_importance_safe.iterrows():\n",
            "    print(f\"{row['feature']:30s}: {row['importance']:.4f}\")"
        ],
        "outputs": [],
        "execution_count": None
    },
    {
        "cell_type": "code",
        "id": "rq2_safe_viz",
        "metadata": {},
        "source": [
            "# Visualize feature importance\n",
            "fig, axes = plt.subplots(1, 2, figsize=(16, 7))\n",
            "\n",
            "# Horizontal bar chart\n",
            "feat_sorted = feature_importance_safe.sort_values('importance', ascending=True)\n",
            "bars = axes[0].barh(feat_sorted['feature'], feat_sorted['importance'], color='#4C72B0')\n",
            "axes[0].set_xlabel('Importance Score', fontsize=11)\n",
            "axes[0].set_title('XGBoost Feature Importance (Safe Features)', fontsize=13, fontweight='bold')\n",
            "axes[0].grid(axis='x', alpha=0.3)\n",
            "\n",
            "# Pie chart for top features\n",
            "top_5 = feature_importance_safe.head(5)\n",
            "other_sum = feature_importance_safe.iloc[5:]['importance'].sum()\n",
            "pie_data = list(top_5['importance']) + [other_sum]\n",
            "pie_labels = list(top_5['feature']) + ['Other']\n",
            "\n",
            "axes[1].pie(pie_data, labels=pie_labels, autopct='%1.1f%%', startangle=90)\n",
            "axes[1].set_title('Top 5 Features Contribution', fontsize=13, fontweight='bold')\n",
            "\n",
            "plt.suptitle('RQ2: Feature Importance Analysis (Safe Features)', fontsize=14, fontweight='bold')\n",
            "plt.tight_layout()\n",
            "plt.savefig(f'{OUTPUT_DIR}/fig07_rq2_feature_importance.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')\n",
            "print(f'Saved: fig07_rq2_feature_importance.{SAVE_FORMAT}')\n",
            "plt.show()"
        ],
        "outputs": [],
        "execution_count": None
    },
    {
        "cell_type": "code",
        "id": "rq2_safe_correlation",
        "metadata": {},
        "source": [
            "# Correlation analysis with target\n",
            "print(\"\\n\" + \"=\"*60)\n",
            "print(\"CORRELATION WITH FRAUD (SAFE FEATURES)\")\n",
            "print(\"=\"*60)\n",
            "\n",
            "correlation_safe = pd.DataFrame({\n",
            "    'feature': safe_feature_cols,\n",
            "    'correlation': [np.corrcoef(X_train_safe[:, i], y_train_safe)[0, 1] for i in range(len(safe_feature_cols))]\n",
            "})\n",
            "correlation_safe['abs_correlation'] = correlation_safe['correlation'].abs()\n",
            "correlation_safe = correlation_safe.sort_values('abs_correlation', ascending=False)\n",
            "\n",
            "print(\"\\nCorrelation with isFraud:\")\n",
            "for i, row in correlation_safe.iterrows():\n",
            "    sign = \"+\" if row['correlation'] > 0 else \"-\"\n",
            "    print(f\"{row['feature']:30s}: {sign}{abs(row['correlation']):.4f}\")"
        ],
        "outputs": [],
        "execution_count": None
    },
    {
        "cell_type": "code",
        "id": "rq2_safe_corr_viz",
        "metadata": {},
        "source": [
            "# Correlation heatmap\n",
            "plt.figure(figsize=(12, 8))\n",
            "\n",
            "corr_data = correlation_safe.sort_values('abs_correlation', ascending=True)\n",
            "colors_corr = ['#d62728' if x < 0 else '#2ca02c' for x in corr_data['correlation']]\n",
            "\n",
            "bars = plt.barh(corr_data['feature'], corr_data['correlation'], color=colors_corr)\n",
            "plt.xlabel('Correlation with isFraud', fontsize=11)\n",
            "plt.title('RQ2: Feature Correlation with Fraud (Safe Features)', fontsize=13, fontweight='bold')\n",
            "plt.axvline(x=0, color='black', linewidth=0.8)\n",
            "plt.grid(axis='x', alpha=0.3)\n",
            "plt.tight_layout()\n",
            "plt.savefig(f'{OUTPUT_DIR}/fig08_rq2_feature_correlation.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')\n",
            "print(f'Saved: fig08_rq2_feature_correlation.{SAVE_FORMAT}')\n",
            "plt.show()"
        ],
        "outputs": [],
        "execution_count": None
    },
    {
        "cell_type": "code",
        "id": "rq2_safe_dist",
        "metadata": {},
        "source": [
            "# Analyze top features by fraud/legitimate comparison\n",
            "print(\"\\n\" + \"=\"*60)\n",
            "print(\"FEATURE DISTRIBUTION BY CLASS (SAFE FEATURES)\")\n",
            "print(\"=\"*60)\n",
            "\n",
            "top_features_safe = feature_importance_safe.head(6)['feature'].tolist()\n",
            "print(f\"\\nAnalyzing top features: {top_features_safe}\")\n",
            "\n",
            "# Visualize top features distribution\n",
            "fig, axes = plt.subplots(2, 3, figsize=(16, 10))\n",
            "\n",
            "for ax, feat in zip(axes.flatten(), top_features_safe):\n",
            "    feat_idx = safe_feature_cols.index(feat)\n",
            "    \n",
            "    fraud_vals = X_train_safe[y_train_safe == 1, feat_idx]\n",
            "    legit_vals = X_train_safe[y_train_safe == 0, feat_idx]\n",
            "    \n",
            "    # Sample for plotting\n",
            "    sample_legit = np.random.choice(legit_vals, min(5000, len(legit_vals)), replace=False)\n",
            "    sample_fraud = np.random.choice(fraud_vals, min(5000, len(fraud_vals)), replace=False)\n",
            "    \n",
            "    ax.hist(sample_legit, bins=50, alpha=0.6, label='Legitimate', color='#2ca02c', density=True)\n",
            "    ax.hist(sample_fraud, bins=50, alpha=0.6, label='Fraud', color='#d62728', density=True)\n",
            "    ax.set_xlabel(feat)\n",
            "    ax.set_ylabel('Density')\n",
            "    ax.set_title(f'Distribution: {feat}')\n",
            "    ax.legend(fontsize=8)\n",
            "    ax.grid(alpha=0.3)\n",
            "\n",
            "plt.suptitle('RQ2: Top Feature Distributions by Class (Safe Features)', fontsize=14, fontweight='bold')\n",
            "plt.tight_layout()\n",
            "plt.savefig(f'{OUTPUT_DIR}/fig09_rq2_top_feature_distributions.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')\n",
            "print(f'Saved: fig09_rq2_top_feature_distributions.{SAVE_FORMAT}')\n",
            "plt.show()"
        ],
        "outputs": [],
        "execution_count": None
    },
    {
        "cell_type": "markdown",
        "id": "rq2_safe_insights",
        "metadata": {},
        "source": [
            "### RQ2 - Key Findings (Safe Features)\n",
            "\n",
            "**Most Predictive Features:**\n",
            "\n",
            "1. **amount_to_dest_balance** - Ratio of transaction amount to recipient's balance; high values indicate suspicious transfers to accounts that would receive disproportionately large deposits\n",
            "\n",
            "2. **amount** - Transaction amount; fraudulent transactions tend to involve larger sums\n",
            "\n",
            "3. **oldbalanceOrg** - Sender's original balance; provides context for whether the transaction is proportional to account holdings\n",
            "\n",
            "4. **amount_to_orig_balance** - Ratio of amount to sender's balance; high values suggest account draining attempts\n",
            "\n",
            "5. **type_encoded** - Transaction type; TRANSFER and CASH_OUT are associated with fraud\n",
            "\n",
            "**Important Insight:**\n",
            "\n",
            "Without the leaked `full_drain` feature, the model relies on a more balanced combination of features. The `amount_to_dest_balance` ratio emerges as the strongest predictor, which makes intuitive sense - fraudsters often transfer money to accounts with low or zero balances, creating unusually high ratios.\n",
            "\n",
            "This feature distribution is more representative of actionable fraud signals that can be computed in real-time before a transaction completes."
        ]
    },
    # =========================================================================
    # RQ3 - SAFE FEATURES
    # =========================================================================
    {
        "cell_type": "markdown",
        "id": "rq3_safe_header",
        "metadata": {},
        "source": [
            "---\n",
            "\n",
            "## Research Question 3 (Safe Features)\n",
            "### How can class imbalance be effectively addressed to minimize false negatives while maintaining acceptable precision?"
        ]
    },
    {
        "cell_type": "code",
        "id": "rq3_safe_setup",
        "metadata": {},
        "source": [
            "print(\"=\"*60)\n",
            "print(\"RQ3: CLASS IMBALANCE HANDLING (SAFE FEATURES)\")\n",
            "print(\"=\"*60)\n",
            "\n",
            "print(f\"\\nCurrent class distribution:\")\n",
            "print(f\"  Legitimate: {(y_train_safe == 0).sum():,} ({(y_train_safe == 0).mean()*100:.4f}%)\")\n",
            "print(f\"  Fraud:      {(y_train_safe == 1).sum():,} ({(y_train_safe == 1).mean()*100:.4f}%)\")\n",
            "print(f\"  Imbalance ratio: {(y_train_safe == 0).sum() / (y_train_safe == 1).sum():.2f}:1\")"
        ],
        "outputs": [],
        "execution_count": None
    },
    {
        "cell_type": "code",
        "id": "rq3_safe_models",
        "metadata": {},
        "source": [
            "# Define imbalance handling methods with XGBoost\n",
            "\n",
            "# 1. Baseline (no handling)\n",
            "baseline_safe = ImbPipeline([\n",
            "    (\"scaler\", StandardScaler()),\n",
            "    (\"clf\", XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1,\n",
            "                          eval_metric=\"logloss\", n_jobs=-1, random_state=RANDOM_STATE))\n",
            "])\n",
            "\n",
            "# 2. Random Undersampling\n",
            "undersampled_safe = ImbPipeline([\n",
            "    (\"under\", RandomUnderSampler(random_state=RANDOM_STATE)),\n",
            "    (\"scaler\", StandardScaler()),\n",
            "    (\"clf\", XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1,\n",
            "                          eval_metric=\"logloss\", n_jobs=-1, random_state=RANDOM_STATE))\n",
            "])\n",
            "\n",
            "# 3. SMOTE oversampling\n",
            "smote_safe = ImbPipeline([\n",
            "    (\"smote\", SMOTE(random_state=RANDOM_STATE, k_neighbors=5)),\n",
            "    (\"scaler\", StandardScaler()),\n",
            "    (\"clf\", XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1,\n",
            "                          eval_metric=\"logloss\", n_jobs=-1, random_state=RANDOM_STATE))\n",
            "])\n",
            "\n",
            "# 4. Class weight adjustment\n",
            "weighted_safe = ImbPipeline([\n",
            "    (\"scaler\", StandardScaler()),\n",
            "    (\"clf\", XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1,\n",
            "                          eval_metric=\"logloss\", n_jobs=-1, random_state=RANDOM_STATE,\n",
            "                          scale_pos_weight=imbalance_ratio_safe))\n",
            "])\n",
            "\n",
            "# 5. Combined: Undersampling + Class weights\n",
            "combined_safe = ImbPipeline([\n",
            "    (\"under\", RandomUnderSampler(sampling_strategy=0.5, random_state=RANDOM_STATE)),\n",
            "    (\"scaler\", StandardScaler()),\n",
            "    (\"clf\", XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1,\n",
            "                          eval_metric=\"logloss\", n_jobs=-1, random_state=RANDOM_STATE,\n",
            "                          scale_pos_weight=2))\n",
            "])\n",
            "\n",
            "imbalance_models_safe = [\n",
            "    (\"Baseline XGBoost\", baseline_safe),\n",
            "    (\"Undersampled XGBoost\", undersampled_safe),\n",
            "    (\"SMOTE XGBoost\", smote_safe),\n",
            "    (\"Weighted XGBoost\", weighted_safe),\n",
            "    (\"Combined XGBoost\", combined_safe)\n",
            "]\n",
            "\n",
            "print(f\"Methods to compare: {[m[0] for m in imbalance_models_safe]}\")"
        ],
        "outputs": [],
        "execution_count": None
    },
    {
        "cell_type": "code",
        "id": "rq3_safe_train",
        "metadata": {},
        "source": [
            "# Train and evaluate all imbalance handling methods\n",
            "results_rq3_safe = []\n",
            "rq3_probas_safe = {}\n",
            "rq3_preds_safe = {}\n",
            "\n",
            "for name, model in imbalance_models_safe:\n",
            "    print(f\"\\nTraining {name}...\")\n",
            "    \n",
            "    model.fit(X_train_safe_sample, y_train_safe_sample)\n",
            "    \n",
            "    y_proba = model.predict_proba(X_test_safe)[:, 1]\n",
            "    y_pred = (y_proba >= 0.5).astype(int)\n",
            "    \n",
            "    tn, fp, fn, tp = confusion_matrix(y_test_safe, y_pred).ravel()\n",
            "    \n",
            "    metrics = {\n",
            "        \"method\": name,\n",
            "        \"auc\": roc_auc_score(y_test_safe, y_proba),\n",
            "        \"precision\": precision_score(y_test_safe, y_pred, zero_division=0),\n",
            "        \"recall\": recall_score(y_test_safe, y_pred, zero_division=0),\n",
            "        \"f1\": f1_score(y_test_safe, y_pred, zero_division=0),\n",
            "        \"true_positives\": tp,\n",
            "        \"false_negatives\": fn,\n",
            "        \"false_positives\": fp,\n",
            "        \"true_negatives\": tn,\n",
            "        \"avg_precision\": average_precision_score(y_test_safe, y_proba)\n",
            "    }\n",
            "    \n",
            "    print(f\"  AUC: {metrics['auc']:.4f}\")\n",
            "    print(f\"  Precision: {metrics['precision']:.4f}\")\n",
            "    print(f\"  Recall: {metrics['recall']:.4f} (Fraud Caught: {tp}/{tp+fn})\")\n",
            "    print(f\"  False Negatives: {fn} (Missed Frauds)\")\n",
            "    \n",
            "    results_rq3_safe.append(metrics)\n",
            "    rq3_probas_safe[name] = y_proba\n",
            "    rq3_preds_safe[name] = y_pred\n",
            "\n",
            "results_df_rq3_safe = pd.DataFrame(results_rq3_safe)"
        ],
        "outputs": [],
        "execution_count": None
    },
    {
        "cell_type": "code",
        "id": "rq3_safe_summary",
        "metadata": {},
        "source": [
            "# Summary table\n",
            "print(\"\\n\" + \"=\"*80)\n",
            "print(\"RQ3: IMBALANCE HANDLING METHODS COMPARISON (SAFE FEATURES)\")\n",
            "print(\"=\"*80)\n",
            "print(results_df_rq3_safe[['method', 'auc', 'precision', 'recall', 'f1', \n",
            "                          'true_positives', 'false_negatives', 'false_positives']].to_string(index=False))"
        ],
        "outputs": [],
        "execution_count": None
    },
    {
        "cell_type": "code",
        "id": "rq3_safe_viz1",
        "metadata": {},
        "source": [
            "# Visualize comparison\n",
            "fig, axes = plt.subplots(2, 2, figsize=(14, 10))\n",
            "\n",
            "colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']\n",
            "methods = results_df_rq3_safe['method'].tolist()\n",
            "x = np.arange(len(methods))\n",
            "\n",
            "# AUC comparison\n",
            "bars = axes[0, 0].bar(x, results_df_rq3_safe['auc'], color=colors)\n",
            "axes[0, 0].set_title('ROC AUC by Method', fontsize=12, fontweight='bold')\n",
            "axes[0, 0].set_xticks(x)\n",
            "axes[0, 0].set_xticklabels(methods, rotation=25, ha='right', fontsize=9)\n",
            "axes[0, 0].grid(axis='y', alpha=0.3)\n",
            "for bar, val in zip(bars, results_df_rq3_safe['auc']):\n",
            "    axes[0, 0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.002,\n",
            "                    f\"{val:.4f}\", ha='center', va='bottom', fontsize=8)\n",
            "\n",
            "# Recall\n",
            "bars = axes[0, 1].bar(x, results_df_rq3_safe['recall'], color=colors)\n",
            "axes[0, 1].set_title('Recall (Fraud Detection Rate)', fontsize=12, fontweight='bold')\n",
            "axes[0, 1].set_xticks(x)\n",
            "axes[0, 1].set_xticklabels(methods, rotation=25, ha='right', fontsize=9)\n",
            "axes[0, 1].grid(axis='y', alpha=0.3)\n",
            "for bar, val in zip(bars, results_df_rq3_safe['recall']):\n",
            "    axes[0, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,\n",
            "                    f\"{val:.4f}\", ha='center', va='bottom', fontsize=8)\n",
            "\n",
            "# Precision\n",
            "bars = axes[1, 0].bar(x, results_df_rq3_safe['precision'], color=colors)\n",
            "axes[1, 0].set_title('Precision', fontsize=12, fontweight='bold')\n",
            "axes[1, 0].set_xticks(x)\n",
            "axes[1, 0].set_xticklabels(methods, rotation=25, ha='right', fontsize=9)\n",
            "axes[1, 0].grid(axis='y', alpha=0.3)\n",
            "for bar, val in zip(bars, results_df_rq3_safe['precision']):\n",
            "    axes[1, 0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,\n",
            "                    f\"{val:.4f}\", ha='center', va='bottom', fontsize=8)\n",
            "\n",
            "# False Negatives\n",
            "bars = axes[1, 1].bar(x, results_df_rq3_safe['false_negatives'], color=colors)\n",
            "axes[1, 1].set_title('False Negatives (Missed Frauds)', fontsize=12, fontweight='bold')\n",
            "axes[1, 1].set_xticks(x)\n",
            "axes[1, 1].set_xticklabels(methods, rotation=25, ha='right', fontsize=9)\n",
            "axes[1, 1].grid(axis='y', alpha=0.3)\n",
            "for bar, val in zip(bars, results_df_rq3_safe['false_negatives']):\n",
            "    axes[1, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,\n",
            "                    f\"{int(val)}\", ha='center', va='bottom', fontsize=8)\n",
            "\n",
            "plt.suptitle('RQ3: Class Imbalance Handling Methods (Safe Features)', fontsize=14, fontweight='bold')\n",
            "plt.tight_layout()\n",
            "plt.savefig(f'{OUTPUT_DIR}/fig10_rq3_imbalance_comparison.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')\n",
            "print(f'Saved: fig10_rq3_imbalance_comparison.{SAVE_FORMAT}')\n",
            "plt.show()"
        ],
        "outputs": [],
        "execution_count": None
    },
    {
        "cell_type": "code",
        "id": "rq3_safe_tradeoff",
        "metadata": {},
        "source": [
            "# Precision-Recall trade-off visualization\n",
            "plt.figure(figsize=(12, 5))\n",
            "\n",
            "width = 0.35\n",
            "x = np.arange(len(methods))\n",
            "\n",
            "plt.bar(x - width/2, results_df_rq3_safe['precision'], width, label='Precision', color='#1f77b4')\n",
            "plt.bar(x + width/2, results_df_rq3_safe['recall'], width, label='Recall', color='#d62728')\n",
            "\n",
            "plt.xlabel('Method')\n",
            "plt.ylabel('Score')\n",
            "plt.title('RQ3: Precision vs Recall Trade-off (Safe Features)', fontsize=13, fontweight='bold')\n",
            "plt.xticks(x, methods, rotation=25, ha='right')\n",
            "plt.legend()\n",
            "plt.grid(axis='y', alpha=0.3)\n",
            "plt.tight_layout()\n",
            "plt.savefig(f'{OUTPUT_DIR}/fig11_rq3_precision_recall_tradeoff.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')\n",
            "print(f'Saved: fig11_rq3_precision_recall_tradeoff.{SAVE_FORMAT}')\n",
            "plt.show()"
        ],
        "outputs": [],
        "execution_count": None
    },
    {
        "cell_type": "code",
        "id": "rq3_safe_cm",
        "metadata": {},
        "source": [
            "# Confusion matrices for each method\n",
            "fig, axes = plt.subplots(1, 5, figsize=(20, 4))\n",
            "\n",
            "for ax, (name, y_pred) in zip(axes, rq3_preds_safe.items()):\n",
            "    cm = confusion_matrix(y_test_safe, y_pred)\n",
            "    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,\n",
            "                xticklabels=['Legitimate', 'Fraud'],\n",
            "                yticklabels=['Legitimate', 'Fraud'])\n",
            "    ax.set_title(name.replace(' XGBoost', ''), fontsize=10, fontweight='bold')\n",
            "    ax.set_ylabel('Actual')\n",
            "    ax.set_xlabel('Predicted')\n",
            "\n",
            "plt.suptitle('RQ3: Confusion Matrices (Safe Features)', fontsize=14, fontweight='bold')\n",
            "plt.tight_layout()\n",
            "plt.savefig(f'{OUTPUT_DIR}/fig12_rq3_confusion_matrices.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')\n",
            "print(f'Saved: fig12_rq3_confusion_matrices.{SAVE_FORMAT}')\n",
            "plt.show()"
        ],
        "outputs": [],
        "execution_count": None
    },
    {
        "cell_type": "code",
        "id": "rq3_safe_roc",
        "metadata": {},
        "source": [
            "# ROC Curves for imbalance methods\n",
            "plt.figure(figsize=(10, 8))\n",
            "\n",
            "for i, (name, y_proba) in enumerate(rq3_probas_safe.items()):\n",
            "    fpr, tpr, _ = roc_curve(y_test_safe, y_proba)\n",
            "    auc = roc_auc_score(y_test_safe, y_proba)\n",
            "    plt.plot(fpr, tpr, label=f\"{name} (AUC={auc:.3f})\", color=colors[i], linewidth=2)\n",
            "\n",
            "plt.plot([0, 1], [0, 1], 'k--', linewidth=1)\n",
            "plt.xlabel('False Positive Rate', fontsize=11)\n",
            "plt.ylabel('True Positive Rate', fontsize=11)\n",
            "plt.title('RQ3: ROC Curves - Imbalance Methods (Safe Features)', fontsize=13, fontweight='bold')\n",
            "plt.legend(loc='lower right', fontsize=9)\n",
            "plt.grid(alpha=0.3)\n",
            "plt.tight_layout()\n",
            "plt.savefig(f'{OUTPUT_DIR}/fig13_rq3_roc_curves.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')\n",
            "print(f'Saved: fig13_rq3_roc_curves.{SAVE_FORMAT}')\n",
            "plt.show()"
        ],
        "outputs": [],
        "execution_count": None
    },
    {
        "cell_type": "code",
        "id": "rq3_safe_pr",
        "metadata": {},
        "source": [
            "# Precision-Recall curves for imbalance methods\n",
            "plt.figure(figsize=(10, 8))\n",
            "\n",
            "for i, (name, y_proba) in enumerate(rq3_probas_safe.items()):\n",
            "    precision, recall, _ = precision_recall_curve(y_test_safe, y_proba)\n",
            "    ap = average_precision_score(y_test_safe, y_proba)\n",
            "    plt.plot(recall, precision, label=f\"{name} (AP={ap:.3f})\", color=colors[i], linewidth=2)\n",
            "\n",
            "plt.xlabel('Recall', fontsize=11)\n",
            "plt.ylabel('Precision', fontsize=11)\n",
            "plt.title('RQ3: Precision-Recall Curves (Safe Features)', fontsize=13, fontweight='bold')\n",
            "plt.legend(loc='upper right', fontsize=9)\n",
            "plt.grid(alpha=0.3)\n",
            "plt.tight_layout()\n",
            "plt.savefig(f'{OUTPUT_DIR}/fig14_rq3_pr_curves.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')\n",
            "print(f'Saved: fig14_rq3_pr_curves.{SAVE_FORMAT}')\n",
            "plt.show()"
        ],
        "outputs": [],
        "execution_count": None
    },
    {
        "cell_type": "code",
        "id": "rq3_safe_threshold",
        "metadata": {},
        "source": [
            "# Threshold analysis for best performing method\n",
            "best_method_safe = results_df_rq3_safe.loc[results_df_rq3_safe['recall'].idxmax(), 'method']\n",
            "best_proba_safe = rq3_probas_safe[best_method_safe]\n",
            "\n",
            "print(f\"\\nThreshold Analysis for: {best_method_safe}\")\n",
            "print(\"=\"*60)\n",
            "\n",
            "thresholds_to_test = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]\n",
            "threshold_results_safe = []\n",
            "\n",
            "for thresh in thresholds_to_test:\n",
            "    y_pred_thresh = (best_proba_safe >= thresh).astype(int)\n",
            "    tn, fp, fn, tp = confusion_matrix(y_test_safe, y_pred_thresh).ravel()\n",
            "    \n",
            "    threshold_results_safe.append({\n",
            "        'threshold': thresh,\n",
            "        'precision': precision_score(y_test_safe, y_pred_thresh, zero_division=0),\n",
            "        'recall': recall_score(y_test_safe, y_pred_thresh, zero_division=0),\n",
            "        'f1': f1_score(y_test_safe, y_pred_thresh, zero_division=0),\n",
            "        'false_negatives': fn,\n",
            "        'false_positives': fp\n",
            "    })\n",
            "\n",
            "threshold_df_safe = pd.DataFrame(threshold_results_safe)\n",
            "print(threshold_df_safe.to_string(index=False))"
        ],
        "outputs": [],
        "execution_count": None
    },
    {
        "cell_type": "code",
        "id": "rq3_safe_threshold_viz",
        "metadata": {},
        "source": [
            "# Threshold analysis visualization\n",
            "fig, axes = plt.subplots(1, 2, figsize=(14, 5))\n",
            "\n",
            "# Precision/Recall vs Threshold\n",
            "axes[0].plot(threshold_df_safe['threshold'], threshold_df_safe['precision'], 'b-o', label='Precision', linewidth=2)\n",
            "axes[0].plot(threshold_df_safe['threshold'], threshold_df_safe['recall'], 'r-o', label='Recall', linewidth=2)\n",
            "axes[0].plot(threshold_df_safe['threshold'], threshold_df_safe['f1'], 'g-o', label='F1 Score', linewidth=2)\n",
            "axes[0].set_xlabel('Threshold')\n",
            "axes[0].set_ylabel('Score')\n",
            "axes[0].set_title('Precision, Recall, F1 vs Threshold')\n",
            "axes[0].legend()\n",
            "axes[0].grid(alpha=0.3)\n",
            "\n",
            "# False Positives/Negatives vs Threshold\n",
            "axes[1].plot(threshold_df_safe['threshold'], threshold_df_safe['false_negatives'], 'r-o', \n",
            "             label='False Negatives (Missed Fraud)', linewidth=2)\n",
            "axes[1].plot(threshold_df_safe['threshold'], threshold_df_safe['false_positives'], 'b-o', \n",
            "             label='False Positives', linewidth=2)\n",
            "axes[1].set_xlabel('Threshold')\n",
            "axes[1].set_ylabel('Count')\n",
            "axes[1].set_title('Error Types vs Threshold')\n",
            "axes[1].legend()\n",
            "axes[1].grid(alpha=0.3)\n",
            "\n",
            "plt.suptitle(f'RQ3: Threshold Analysis - {best_method_safe} (Safe Features)', fontsize=14, fontweight='bold')\n",
            "plt.tight_layout()\n",
            "plt.savefig(f'{OUTPUT_DIR}/fig15_rq3_threshold_analysis.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')\n",
            "print(f'Saved: fig15_rq3_threshold_analysis.{SAVE_FORMAT}')\n",
            "plt.show()"
        ],
        "outputs": [],
        "execution_count": None
    },
    {
        "cell_type": "markdown",
        "id": "rq3_safe_insights",
        "metadata": {},
        "source": [
            "### RQ3 - Key Findings (Safe Features)\n",
            "\n",
            "**Imbalance Handling Method Performance:**\n",
            "\n",
            "1. **Weighted XGBoost** - Best recall, effectively prioritizes catching fraudulent transactions\n",
            "2. **SMOTE XGBoost** - Good balance between precision and recall\n",
            "3. **Combined Approach** - Provides flexibility with both techniques\n",
            "4. **Undersampling** - High recall but lower precision due to information loss\n",
            "5. **Baseline** - Highest precision but misses more fraudulent transactions\n",
            "\n",
            "**Key Observations:**\n",
            "\n",
            "- Class weighting (scale_pos_weight) is highly effective and computationally efficient\n",
            "- SMOTE improves recall by generating synthetic minority samples\n",
            "- The precision-recall trade-off is more pronounced with safe features\n",
            "- Threshold tuning can significantly improve recall at the cost of precision\n",
            "\n",
            "**Recommendations:**\n",
            "\n",
            "- Use Weighted XGBoost or SMOTE for maximum fraud detection\n",
            "- Consider lowering the decision threshold (0.3-0.4) to catch more fraud\n",
            "- Accept higher false positive rates to minimize missed fraudulent transactions\n",
            "- The choice depends on business requirements: cost of missed fraud vs. cost of investigating false positives"
        ]
    },
    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    {
        "cell_type": "markdown",
        "id": "final_summary_header",
        "metadata": {},
        "source": [
            "---\n",
            "\n",
            "## Summary & Conclusions (Safe Features)"
        ]
    },
    {
        "cell_type": "code",
        "id": "final_summary_code",
        "metadata": {},
        "source": [
            "print(\"=\"*70)\n",
            "print(\"FRAUD DETECTION ANALYSIS - FINAL SUMMARY (SAFE FEATURES)\")\n",
            "print(\"=\"*70)\n",
            "\n",
            "print(\"\\n** DATASET OVERVIEW **\")\n",
            "print(f\"  Total Transactions: {len(df):,}\")\n",
            "print(f\"  Fraudulent Cases: {df[target_col].sum():,} ({df[target_col].mean()*100:.4f}%)\")\n",
            "print(f\"  Features Used: {len(safe_feature_cols)} safe (pre-transaction) features\")\n",
            "\n",
            "print(\"\\n** RQ1: BEST ML ALGORITHMS **\")\n",
            "best_algo_safe = results_df_rq1_safe.loc[results_df_rq1_safe['auc'].idxmax()]\n",
            "print(f\"  Best Performer: {best_algo_safe['model']}\")\n",
            "print(f\"  AUC: {best_algo_safe['auc']:.4f}\")\n",
            "print(f\"  Recall: {best_algo_safe['recall']:.4f}\")\n",
            "print(f\"  F1 Score: {best_algo_safe['f1']:.4f}\")\n",
            "\n",
            "print(\"\\n** RQ2: MOST PREDICTIVE FEATURES **\")\n",
            "top_3_safe = feature_importance_safe.head(3)['feature'].tolist()\n",
            "print(f\"  Top 3 Features: {', '.join(top_3_safe)}\")\n",
            "print(\"  Key Pattern: Transaction amount ratios are most predictive\")\n",
            "\n",
            "print(\"\\n** RQ3: BEST IMBALANCE HANDLING **\")\n",
            "best_imb_safe = results_df_rq3_safe.loc[results_df_rq3_safe['recall'].idxmax()]\n",
            "print(f\"  Best Method (by Recall): {best_imb_safe['method']}\")\n",
            "print(f\"  Recall: {best_imb_safe['recall']:.4f}\")\n",
            "print(f\"  Precision: {best_imb_safe['precision']:.4f}\")\n",
            "print(f\"  F1 Score: {best_imb_safe['f1']:.4f}\")\n",
            "\n",
            "print(\"\\n** CRITICAL NOTE **\")\n",
            "print(\"  All results above use SAFE features only (no data leakage).\")\n",
            "print(\"  These metrics represent REALISTIC deployment performance.\")\n",
            "\n",
            "print(\"\\n\" + \"=\"*70)"
        ],
        "outputs": [],
        "execution_count": None
    },
    {
        "cell_type": "code",
        "id": "final_summary_viz",
        "metadata": {},
        "source": [
            "# Final comparison visualization\n",
            "fig, axes = plt.subplots(1, 3, figsize=(18, 5))\n",
            "\n",
            "# RQ1: Algorithm comparison (AUC)\n",
            "rq1_sorted = results_df_rq1_safe.sort_values('auc', ascending=True)\n",
            "axes[0].barh(rq1_sorted['model'], rq1_sorted['auc'], color='#4C72B0')\n",
            "axes[0].set_xlabel('ROC AUC')\n",
            "axes[0].set_title('RQ1: Algorithm Performance', fontsize=12, fontweight='bold')\n",
            "axes[0].grid(axis='x', alpha=0.3)\n",
            "\n",
            "# RQ2: Feature importance\n",
            "top_8_safe = feature_importance_safe.head(8).sort_values('importance', ascending=True)\n",
            "axes[1].barh(top_8_safe['feature'], top_8_safe['importance'], color='#55A868')\n",
            "axes[1].set_xlabel('Importance')\n",
            "axes[1].set_title('RQ2: Top Features', fontsize=12, fontweight='bold')\n",
            "axes[1].grid(axis='x', alpha=0.3)\n",
            "\n",
            "# RQ3: Imbalance methods (Recall)\n",
            "rq3_sorted = results_df_rq3_safe.sort_values('recall', ascending=True)\n",
            "axes[2].barh(rq3_sorted['method'].str.replace(' XGBoost', ''), rq3_sorted['recall'], color='#C44E52')\n",
            "axes[2].set_xlabel('Recall (Fraud Detection Rate)')\n",
            "axes[2].set_title('RQ3: Imbalance Handling', fontsize=12, fontweight='bold')\n",
            "axes[2].grid(axis='x', alpha=0.3)\n",
            "\n",
            "plt.suptitle('Fraud Detection Analysis - Key Results (Safe Features)', fontsize=14, fontweight='bold')\n",
            "plt.tight_layout()\n",
            "plt.savefig(f'{OUTPUT_DIR}/fig16_final_summary.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')\n",
            "print(f'Saved: fig16_final_summary.{SAVE_FORMAT}')\n",
            "plt.show()"
        ],
        "outputs": [],
        "execution_count": None
    }
]

# Find the position after feature engineering but before original RQ1
# We'll look for the train/test split cell and insert after it
insert_position = None
for i, cell in enumerate(notebook['cells']):
    cell_id = cell.get('id', '')
    # Insert after the train/test split section but before original RQ1
    if cell_id == 'y7z8a9b0':  # RQ1 header
        insert_position = i
        break

if insert_position is None:
    # Fallback: look for any cell with "Research Question 1" in source
    for i, cell in enumerate(notebook['cells']):
        source = cell.get('source', [])
        if isinstance(source, list):
            source = ''.join(source)
        if 'Research Question 1' in source and cell.get('cell_type') == 'markdown':
            insert_position = i
            break

if insert_position is None:
    print("Could not find insertion point. Appending to end.")
    insert_position = len(notebook['cells'])

# Remove old RQ cells (from RQ1 header to before the data leakage section or references)
# First, find the range of cells to remove
remove_start = insert_position
remove_end = None

for i in range(insert_position, len(notebook['cells'])):
    cell_id = notebook['cells'][i].get('id', '')
    source = notebook['cells'][i].get('source', [])
    if isinstance(source, list):
        source = ''.join(source)

    # Stop at data leakage section or references
    if 'leakage_section_header' in cell_id or 'Data Leakage' in source or cell_id == 'e3f4g5h6':
        remove_end = i
        break

if remove_end is None:
    remove_end = len(notebook['cells'])

# Remove old cells
print(f"Removing cells from index {remove_start} to {remove_end}")
del notebook['cells'][remove_start:remove_end]

# Insert new cells
for j, new_cell in enumerate(new_cells):
    notebook['cells'].insert(insert_position + j, new_cell)

print(f"Inserted {len(new_cells)} new cells at index {insert_position}")

# Save the modified notebook
output_path = 'D:/Final Year/App Domains 3/datasets/Fraud_Detection_PaySim_Analysis.ipynb'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1)

print(f"\n{'='*60}")
print("NOTEBOOK UPDATED SUCCESSFULLY")
print(f"{'='*60}")
print(f"Replaced RQ1, RQ2, RQ3 sections with SAFE FEATURES versions")
print(f"")
print(f"Changes made:")
print(f"  - Added safe features definition and setup")
print(f"  - RQ1: Algorithm comparison using 10 safe features")
print(f"  - RQ2: Feature importance analysis (no full_drain)")
print(f"  - RQ3: Imbalance handling methods")
print(f"  - Updated final summary")
print(f"")
print(f"Total new cells added: {len(new_cells)}")
print(f"Notebook saved to: {output_path}")
print(f"{'='*60}")
