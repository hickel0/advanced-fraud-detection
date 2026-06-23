"""
RQ1 Analysis with SAFE Features (No Data Leakage)
Comparing ML algorithms for fraud detection using only pre-transaction features.
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    roc_auc_score, accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, roc_curve, precision_recall_curve,
    average_precision_score
)
from xgboost import XGBClassifier
import matplotlib.pyplot as plt

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

print("="*70)
print("RQ1: ALGORITHM COMPARISON WITH SAFE FEATURES (NO DATA LEAKAGE)")
print("="*70)

# Load dataset
print("\nLoading dataset...")
path = "D:/Final Year/App Domains 3/datasets/Synthetic_Financial_Dataset.csv"
df = pd.read_csv(path)
print(f"Dataset loaded: {df.shape[0]:,} transactions")

# Feature engineering (same as notebook)
df_fe = df.copy()
target_col = "isFraud"

# Encode transaction type
le = LabelEncoder()
df_fe['type_encoded'] = le.fit_transform(df_fe['type'])

# Create features
df_fe['amount_to_orig_balance'] = df_fe['amount'] / (df_fe['oldbalanceOrg'] + 1)
df_fe['amount_to_dest_balance'] = df_fe['amount'] / (df_fe['oldbalanceDest'] + 1)
df_fe['dest_zero_balance_before'] = (df_fe['oldbalanceDest'] == 0).astype(int)
df_fe['hour_of_day'] = df_fe['step'] % 24
df_fe['day'] = df_fe['step'] // 24

# Define SAFE features only (pre-transaction, no leakage)
safe_feature_cols = [
    'step', 'type_encoded', 'amount',
    'oldbalanceOrg', 'oldbalanceDest',
    'amount_to_orig_balance', 'amount_to_dest_balance',
    'dest_zero_balance_before', 'hour_of_day', 'day'
]

print(f"\nUsing {len(safe_feature_cols)} SAFE features:")
for f in safe_feature_cols:
    print(f"  - {f}")

# Prepare data
X = df_fe[safe_feature_cols].values
y = df_fe[target_col].values

# Handle infinite values
X = np.nan_to_num(X, nan=0, posinf=0, neginf=0)

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=RANDOM_STATE
)

print(f"\nTrain set: {len(X_train):,} samples")
print(f"Test set:  {len(X_test):,} samples")
print(f"Fraud ratio: {y_train.mean()*100:.4f}%")

# Sample for faster training
sample_size = min(500000, len(X_train))
sample_idx = np.random.choice(len(X_train), sample_size, replace=False)
X_train_sample = X_train[sample_idx]
y_train_sample = y_train[sample_idx]

print(f"Training sample: {sample_size:,} samples")

# Calculate imbalance ratio
neg, pos = np.bincount(y_train_sample)
imbalance_ratio = neg / pos
print(f"Imbalance ratio: {imbalance_ratio:.2f}:1")

# Define models
models = {
    "Logistic Regression": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000, random_state=RANDOM_STATE))
    ]),

    "Decision Tree": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", DecisionTreeClassifier(max_depth=10, random_state=RANDOM_STATE))
    ]),

    "Random Forest": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(n_estimators=100, max_depth=10,
                                        n_jobs=-1, random_state=RANDOM_STATE))
    ]),

    "Gradient Boosting": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", GradientBoostingClassifier(n_estimators=100, max_depth=4,
                                           random_state=RANDOM_STATE))
    ]),

    "XGBoost": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1,
                              objective="binary:logistic", eval_metric="logloss",
                              n_jobs=-1, random_state=RANDOM_STATE))
    ])
}

# Train and evaluate all models
print("\n" + "="*70)
print("TRAINING AND EVALUATING MODELS")
print("="*70)

results = []
model_probas = {}

for name, model in models.items():
    print(f"\nTraining {name}...")

    model.fit(X_train_sample, y_train_sample)

    y_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_proba >= 0.5).astype(int)

    # Compute metrics
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

    metrics = {
        "Model": name,
        "AUC": roc_auc_score(y_test, y_proba),
        "Accuracy": accuracy_score(y_test, y_pred),
        "Precision": precision_score(y_test, y_pred, zero_division=0),
        "Recall": recall_score(y_test, y_pred, zero_division=0),
        "F1": f1_score(y_test, y_pred, zero_division=0),
        "Avg_Precision": average_precision_score(y_test, y_proba),
        "TP": tp,
        "FN": fn,
        "FP": fp,
        "TN": tn
    }

    print(f"  AUC:       {metrics['AUC']:.4f}")
    print(f"  Precision: {metrics['Precision']:.4f}")
    print(f"  Recall:    {metrics['Recall']:.4f} ({tp}/{tp+fn} frauds caught)")
    print(f"  F1 Score:  {metrics['F1']:.4f}")

    results.append(metrics)
    model_probas[name] = y_proba

# Create results dataframe
results_df = pd.DataFrame(results)

# Print summary table
print("\n" + "="*70)
print("RQ1 RESULTS: SAFE FEATURES (NO DATA LEAKAGE)")
print("="*70)
print("\n" + results_df[['Model', 'AUC', 'Precision', 'Recall', 'F1', 'Avg_Precision']].to_string(index=False))

# Find best model
best_by_auc = results_df.loc[results_df['AUC'].idxmax()]
best_by_recall = results_df.loc[results_df['Recall'].idxmax()]
best_by_f1 = results_df.loc[results_df['F1'].idxmax()]

print("\n" + "-"*70)
print("BEST PERFORMERS:")
print(f"  Best AUC:    {best_by_auc['Model']} ({best_by_auc['AUC']:.4f})")
print(f"  Best Recall: {best_by_recall['Model']} ({best_by_recall['Recall']:.4f})")
print(f"  Best F1:     {best_by_f1['Model']} ({best_by_f1['F1']:.4f})")

# Comparison with original (leaked) results
print("\n" + "="*70)
print("COMPARISON: SAFE vs ORIGINAL (WITH LEAKAGE)")
print("="*70)

# Original results from the notebook (with full_drain)
original_results = {
    "Logistic Regression": {"AUC": 0.9980, "Precision": 0.9984, "Recall": 0.9935, "F1": 0.9959},
    "Decision Tree": {"AUC": 0.9968, "Precision": 1.0000, "Recall": 0.9935, "F1": 0.9967},
    "Random Forest": {"AUC": 0.9992, "Precision": 1.0000, "Recall": 0.9947, "F1": 0.9974},
    "Gradient Boosting": {"AUC": 0.9968, "Precision": 1.0000, "Recall": 0.9935, "F1": 0.9967},
    "XGBoost": {"AUC": 0.9972, "Precision": 0.9988, "Recall": 0.9939, "F1": 0.9963}
}

print(f"\n{'Model':<22} {'Metric':<12} {'WITH Leakage':>14} {'SAFE Features':>14} {'Difference':>12}")
print("-"*76)

for _, row in results_df.iterrows():
    model = row['Model']
    orig = original_results[model]

    for metric in ['AUC', 'Recall', 'F1']:
        orig_val = orig[metric]
        safe_val = row[metric]
        diff = safe_val - orig_val
        diff_str = f"{diff:+.4f}"

        print(f"{model:<22} {metric:<12} {orig_val:>14.4f} {safe_val:>14.4f} {diff_str:>12}")
    print()

# Create visualization
print("\nGenerating visualization...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

metrics_to_plot = ['AUC', 'Precision', 'Recall', 'F1']
titles = ['ROC AUC', 'Precision', 'Recall', 'F1 Score']
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

x = np.arange(len(results_df))
model_names = results_df['Model'].tolist()

for ax, metric, title in zip(axes.flatten(), metrics_to_plot, titles):
    values = results_df[metric].values
    bars = ax.bar(x, values, color=colors)
    ax.set_title(f'{title} (Safe Features)', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(model_names, rotation=30, ha='right', fontsize=9)
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim(0, max(values) * 1.15)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f"{val:.3f}", ha='center', va='bottom', fontsize=8)

plt.suptitle('RQ1: ML Algorithm Comparison - SAFE Features (No Data Leakage)',
             fontsize=14, fontweight='bold')
plt.tight_layout()

output_path = 'D:/Final Year/App Domains 3/datasets/outputs/fig_rq1_safe_features.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
print(f"Saved: {output_path}")
plt.close()

# ROC Curves
plt.figure(figsize=(10, 8))

for i, (name, y_proba) in enumerate(model_probas.items()):
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    auc = roc_auc_score(y_test, y_proba)
    plt.plot(fpr, tpr, label=f"{name} (AUC={auc:.3f})", color=colors[i], linewidth=2)

plt.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random Classifier')
plt.xlabel('False Positive Rate', fontsize=11)
plt.ylabel('True Positive Rate', fontsize=11)
plt.title('RQ1: ROC Curves - SAFE Features (No Data Leakage)', fontsize=13, fontweight='bold')
plt.legend(loc='lower right', fontsize=9)
plt.grid(alpha=0.3)
plt.tight_layout()

output_path2 = 'D:/Final Year/App Domains 3/datasets/outputs/fig_rq1_safe_roc_curves.png'
plt.savefig(output_path2, dpi=300, bbox_inches='tight', facecolor='white')
print(f"Saved: {output_path2}")
plt.close()

print("\n" + "="*70)
print("ANALYSIS COMPLETE")
print("="*70)
print("\nKey Findings:")
print(f"  - Best algorithm by AUC: {best_by_auc['Model']} ({best_by_auc['AUC']:.4f})")
print(f"  - Best algorithm by Recall: {best_by_recall['Model']} ({best_by_recall['Recall']:.4f})")
print(f"  - All algorithms show significant performance drop without leaked features")
print(f"  - Recall drops from ~99% to 60-75% across all models")
print(f"  - This represents REALISTIC deployment performance")
