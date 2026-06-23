"""
Run complete fraud detection analysis with SAFE features (no data leakage).
Memory-optimized version.
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')
import os
import gc

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
import seaborn as sns

from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from imblearn.pipeline import Pipeline as ImbPipeline

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

# Output settings
OUTPUT_DIR = 'D:/Final Year/App Domains 3/datasets/outputs'
os.makedirs(OUTPUT_DIR, exist_ok=True)
SAVE_DPI = 300
SAVE_FORMAT = 'png'

print("="*70)
print("FRAUD DETECTION ANALYSIS - SAFE FEATURES (NO DATA LEAKAGE)")
print("="*70)

# =============================================================================
# LOAD AND PREPARE DATA (MEMORY OPTIMIZED)
# =============================================================================
print("\n[1/6] Loading dataset...")
path = "D:/Final Year/App Domains 3/datasets/Synthetic_Financial_Dataset.csv"

# Load only needed columns with optimized dtypes
df = pd.read_csv(path, usecols=['step', 'type', 'amount', 'oldbalanceOrg',
                                 'oldbalanceDest', 'isFraud'])
print(f"Dataset loaded: {df.shape[0]:,} transactions")

# Sample the dataset FIRST to save memory
SAMPLE_FRAC = 0.15  # Use 15% of data
df = df.sample(frac=SAMPLE_FRAC, random_state=RANDOM_STATE).reset_index(drop=True)
print(f"Sampled to: {df.shape[0]:,} transactions ({SAMPLE_FRAC*100:.0f}%)")
gc.collect()

target_col = "isFraud"

# Feature engineering
le = LabelEncoder()
df['type_encoded'] = le.fit_transform(df['type'])
df['amount_to_orig_balance'] = df['amount'] / (df['oldbalanceOrg'] + 1)
df['amount_to_dest_balance'] = df['amount'] / (df['oldbalanceDest'] + 1)
df['dest_zero_balance_before'] = (df['oldbalanceDest'] == 0).astype(np.int8)
df['hour_of_day'] = (df['step'] % 24).astype(np.int8)
df['day'] = (df['step'] // 24).astype(np.int16)

# Drop original type column
df.drop('type', axis=1, inplace=True)
gc.collect()

# SAFE features only
safe_feature_cols = [
    'step', 'type_encoded', 'amount',
    'oldbalanceOrg', 'oldbalanceDest',
    'amount_to_orig_balance', 'amount_to_dest_balance',
    'dest_zero_balance_before', 'hour_of_day', 'day'
]

print(f"Using {len(safe_feature_cols)} SAFE features (no data leakage)")

# Prepare arrays
X_safe = df[safe_feature_cols].values.astype(np.float32)
y_safe = df[target_col].values.astype(np.int8)

# Handle inf/nan
X_safe = np.where(np.isfinite(X_safe), X_safe, 0)

# Free dataframe memory
del df
gc.collect()

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X_safe, y_safe, test_size=0.3, stratify=y_safe, random_state=RANDOM_STATE
)

del X_safe, y_safe
gc.collect()

# Sample for faster training
train_sample_size = min(100000, len(X_train))
train_idx = np.random.choice(len(X_train), train_sample_size, replace=False)
X_train_sample = X_train[train_idx]
y_train_sample = y_train[train_idx]

test_sample_size = min(100000, len(X_test))
test_idx = np.random.choice(len(X_test), test_sample_size, replace=False)
X_test_sample = X_test[test_idx]
y_test_sample = y_test[test_idx]

del X_train, y_train, X_test, y_test
gc.collect()

neg, pos = np.bincount(y_train_sample)
imbalance_ratio = neg / pos
fraud_count = y_test_sample.sum()
print(f"Train: {len(X_train_sample):,} | Test: {len(X_test_sample):,}")
print(f"Test frauds: {fraud_count} | Imbalance: {imbalance_ratio:.0f}:1")

# =============================================================================
# RQ1: ALGORITHM COMPARISON
# =============================================================================
print("\n[2/6] RQ1: Comparing ML Algorithms...")
print("-"*50)

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
        ("clf", RandomForestClassifier(n_estimators=50, max_depth=10, n_jobs=-1, random_state=RANDOM_STATE))
    ]),
    "Gradient Boosting": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", GradientBoostingClassifier(n_estimators=50, max_depth=3, random_state=RANDOM_STATE))
    ]),
    "XGBoost": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1,
                              eval_metric="logloss", n_jobs=-1, random_state=RANDOM_STATE))
    ])
}

results_rq1 = []
model_probas = {}
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

for name, model in models.items():
    print(f"  Training {name}...", end=" ")
    model.fit(X_train_sample, y_train_sample)
    y_proba = model.predict_proba(X_test_sample)[:, 1]
    y_pred = (y_proba >= 0.5).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_test_sample, y_pred).ravel()
    metrics = {
        "model": name,
        "auc": roc_auc_score(y_test_sample, y_proba),
        "precision": precision_score(y_test_sample, y_pred, zero_division=0),
        "recall": recall_score(y_test_sample, y_pred, zero_division=0),
        "f1": f1_score(y_test_sample, y_pred, zero_division=0),
        "avg_precision": average_precision_score(y_test_sample, y_proba),
        "tp": tp, "fn": fn
    }
    results_rq1.append(metrics)
    model_probas[name] = y_proba
    print(f"AUC={metrics['auc']:.4f}, Recall={metrics['recall']:.4f} ({tp}/{tp+fn})")
    gc.collect()

results_df_rq1 = pd.DataFrame(results_rq1)

# RQ1 Visualizations
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
for ax, metric, title in zip(axes.flatten(), ['auc', 'precision', 'recall', 'f1'],
                              ['ROC AUC', 'Precision', 'Recall', 'F1 Score']):
    values = results_df_rq1[metric].values
    bars = ax.bar(range(len(results_df_rq1)), values, color=colors)
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.set_xticks(range(len(results_df_rq1)))
    ax.set_xticklabels(results_df_rq1['model'], rotation=30, ha='right', fontsize=9)
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim(0, max(values) * 1.15 if max(values) > 0 else 1)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f"{val:.3f}", ha='center', va='bottom', fontsize=8)
plt.suptitle('RQ1: ML Algorithm Comparison (Safe Features)', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig04_rq1_algorithm_comparison.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')
plt.close()

# ROC Curves
plt.figure(figsize=(10, 8))
for i, (name, y_proba) in enumerate(model_probas.items()):
    fpr, tpr, _ = roc_curve(y_test_sample, y_proba)
    auc = roc_auc_score(y_test_sample, y_proba)
    plt.plot(fpr, tpr, label=f"{name} (AUC={auc:.3f})", color=colors[i], linewidth=2)
plt.plot([0, 1], [0, 1], 'k--', linewidth=1)
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('RQ1: ROC Curves (Safe Features)', fontsize=13, fontweight='bold')
plt.legend(loc='lower right')
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig05_rq1_roc_curves.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')
plt.close()

# PR Curves
plt.figure(figsize=(10, 8))
for i, (name, y_proba) in enumerate(model_probas.items()):
    prec, rec, _ = precision_recall_curve(y_test_sample, y_proba)
    ap = average_precision_score(y_test_sample, y_proba)
    plt.plot(rec, prec, label=f"{name} (AP={ap:.3f})", color=colors[i], linewidth=2)
plt.xlabel('Recall')
plt.ylabel('Precision')
plt.title('RQ1: Precision-Recall Curves (Safe Features)', fontsize=13, fontweight='bold')
plt.legend(loc='upper right')
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig06_rq1_precision_recall_curves.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')
plt.close()

print("  Saved: fig04, fig05, fig06")

# =============================================================================
# RQ2: FEATURE IMPORTANCE
# =============================================================================
print("\n[3/6] RQ2: Feature Importance Analysis...")
print("-"*50)

xgb_model = XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1,
                          scale_pos_weight=imbalance_ratio, eval_metric="logloss",
                          n_jobs=-1, random_state=RANDOM_STATE)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_sample)
xgb_model.fit(X_train_scaled, y_train_sample)

feature_importance = pd.DataFrame({
    'feature': safe_feature_cols,
    'importance': xgb_model.feature_importances_
}).sort_values('importance', ascending=False)

print("  Feature Importance Ranking:")
for _, row in feature_importance.iterrows():
    print(f"    {row['feature']:30s}: {row['importance']:.4f}")

# Correlation
correlation = pd.DataFrame({
    'feature': safe_feature_cols,
    'correlation': [np.corrcoef(X_train_sample[:, i], y_train_sample)[0, 1] for i in range(len(safe_feature_cols))]
})
correlation['abs_correlation'] = correlation['correlation'].abs()
correlation = correlation.sort_values('abs_correlation', ascending=False)

# Feature importance visualization
fig, axes = plt.subplots(1, 2, figsize=(16, 7))
feat_sorted = feature_importance.sort_values('importance', ascending=True)
axes[0].barh(feat_sorted['feature'], feat_sorted['importance'], color='#4C72B0')
axes[0].set_xlabel('Importance Score')
axes[0].set_title('XGBoost Feature Importance', fontsize=13, fontweight='bold')
axes[0].grid(axis='x', alpha=0.3)

top_5 = feature_importance.head(5)
other_sum = feature_importance.iloc[5:]['importance'].sum()
pie_data = list(top_5['importance']) + [other_sum]
pie_labels = list(top_5['feature']) + ['Other']
axes[1].pie(pie_data, labels=pie_labels, autopct='%1.1f%%', startangle=90)
axes[1].set_title('Top 5 Features Contribution', fontsize=13, fontweight='bold')
plt.suptitle('RQ2: Feature Importance Analysis (Safe Features)', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig07_rq2_feature_importance.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')
plt.close()

# Correlation plot
plt.figure(figsize=(12, 8))
corr_sorted = correlation.sort_values('abs_correlation', ascending=True)
colors_corr = ['#d62728' if x < 0 else '#2ca02c' for x in corr_sorted['correlation']]
plt.barh(corr_sorted['feature'], corr_sorted['correlation'], color=colors_corr)
plt.xlabel('Correlation with isFraud')
plt.title('RQ2: Feature Correlation with Fraud (Safe Features)', fontsize=13, fontweight='bold')
plt.axvline(x=0, color='black', linewidth=0.8)
plt.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig08_rq2_feature_correlation.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')
plt.close()

# Top feature distributions
top_features = feature_importance.head(6)['feature'].tolist()
fig, axes = plt.subplots(2, 3, figsize=(16, 10))
for ax, feat in zip(axes.flatten(), top_features):
    feat_idx = safe_feature_cols.index(feat)
    fraud_vals = X_train_sample[y_train_sample == 1, feat_idx]
    legit_vals = X_train_sample[y_train_sample == 0, feat_idx]
    sample_legit = np.random.choice(legit_vals, min(3000, len(legit_vals)), replace=False)
    sample_fraud = np.random.choice(fraud_vals, min(3000, len(fraud_vals)), replace=False) if len(fraud_vals) > 0 else fraud_vals
    ax.hist(sample_legit, bins=50, alpha=0.6, label='Legitimate', color='#2ca02c', density=True)
    if len(sample_fraud) > 0:
        ax.hist(sample_fraud, bins=50, alpha=0.6, label='Fraud', color='#d62728', density=True)
    ax.set_xlabel(feat)
    ax.set_ylabel('Density')
    ax.set_title(f'Distribution: {feat}')
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
plt.suptitle('RQ2: Top Feature Distributions by Class', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig09_rq2_top_feature_distributions.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')
plt.close()

print("  Saved: fig07, fig08, fig09")

# =============================================================================
# RQ3: IMBALANCE HANDLING
# =============================================================================
print("\n[4/6] RQ3: Class Imbalance Handling...")
print("-"*50)

imbalance_models = [
    ("Baseline XGBoost", ImbPipeline([
        ("scaler", StandardScaler()),
        ("clf", XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1,
                              eval_metric="logloss", n_jobs=-1, random_state=RANDOM_STATE))
    ])),
    ("Undersampled XGBoost", ImbPipeline([
        ("under", RandomUnderSampler(random_state=RANDOM_STATE)),
        ("scaler", StandardScaler()),
        ("clf", XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1,
                              eval_metric="logloss", n_jobs=-1, random_state=RANDOM_STATE))
    ])),
    ("SMOTE XGBoost", ImbPipeline([
        ("smote", SMOTE(random_state=RANDOM_STATE, k_neighbors=5)),
        ("scaler", StandardScaler()),
        ("clf", XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1,
                              eval_metric="logloss", n_jobs=-1, random_state=RANDOM_STATE))
    ])),
    ("Weighted XGBoost", ImbPipeline([
        ("scaler", StandardScaler()),
        ("clf", XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1,
                              eval_metric="logloss", n_jobs=-1, random_state=RANDOM_STATE,
                              scale_pos_weight=imbalance_ratio))
    ])),
    ("Combined XGBoost", ImbPipeline([
        ("under", RandomUnderSampler(sampling_strategy=0.5, random_state=RANDOM_STATE)),
        ("scaler", StandardScaler()),
        ("clf", XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1,
                              eval_metric="logloss", n_jobs=-1, random_state=RANDOM_STATE,
                              scale_pos_weight=2))
    ]))
]

results_rq3 = []
rq3_probas = {}
rq3_preds = {}

for name, model in imbalance_models:
    print(f"  Training {name}...", end=" ")
    model.fit(X_train_sample, y_train_sample)
    y_proba = model.predict_proba(X_test_sample)[:, 1]
    y_pred = (y_proba >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test_sample, y_pred).ravel()

    metrics = {
        "method": name,
        "auc": roc_auc_score(y_test_sample, y_proba),
        "precision": precision_score(y_test_sample, y_pred, zero_division=0),
        "recall": recall_score(y_test_sample, y_pred, zero_division=0),
        "f1": f1_score(y_test_sample, y_pred, zero_division=0),
        "tp": tp, "fn": fn, "fp": fp, "tn": tn,
        "avg_precision": average_precision_score(y_test_sample, y_proba)
    }
    results_rq3.append(metrics)
    rq3_probas[name] = y_proba
    rq3_preds[name] = y_pred
    print(f"Recall={metrics['recall']:.4f} ({tp}/{tp+fn}), Prec={metrics['precision']:.4f}")
    gc.collect()

results_df_rq3 = pd.DataFrame(results_rq3)

# RQ3 Visualizations
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
methods = results_df_rq3['method'].tolist()
x = np.arange(len(methods))

for ax, metric, title in zip([axes[0,0], axes[0,1], axes[1,0], axes[1,1]],
                              ['auc', 'recall', 'precision', 'fn'],
                              ['ROC AUC', 'Recall (Fraud Detection)', 'Precision', 'False Negatives']):
    values = results_df_rq3[metric].values if metric != 'fn' else results_df_rq3['fn'].values
    bars = ax.bar(x, values, color=colors)
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=25, ha='right', fontsize=9)
    ax.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars, values):
        label = f"{val:.4f}" if metric != 'fn' else f"{int(val)}"
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                label, ha='center', va='bottom', fontsize=8)
plt.suptitle('RQ3: Class Imbalance Handling (Safe Features)', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig10_rq3_imbalance_comparison.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')
plt.close()

# Precision-Recall tradeoff
plt.figure(figsize=(12, 5))
width = 0.35
plt.bar(x - width/2, results_df_rq3['precision'], width, label='Precision', color='#1f77b4')
plt.bar(x + width/2, results_df_rq3['recall'], width, label='Recall', color='#d62728')
plt.xlabel('Method')
plt.ylabel('Score')
plt.title('RQ3: Precision vs Recall Trade-off (Safe Features)', fontsize=13, fontweight='bold')
plt.xticks(x, methods, rotation=25, ha='right')
plt.legend()
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig11_rq3_precision_recall_tradeoff.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')
plt.close()

# Confusion matrices
fig, axes = plt.subplots(1, 5, figsize=(20, 4))
for ax, (name, y_pred) in zip(axes, rq3_preds.items()):
    cm = confusion_matrix(y_test_sample, y_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                xticklabels=['Legit', 'Fraud'], yticklabels=['Legit', 'Fraud'])
    ax.set_title(name.replace(' XGBoost', ''), fontsize=10, fontweight='bold')
    ax.set_ylabel('Actual')
    ax.set_xlabel('Predicted')
plt.suptitle('RQ3: Confusion Matrices (Safe Features)', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig12_rq3_confusion_matrices.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')
plt.close()

# ROC curves
plt.figure(figsize=(10, 8))
for i, (name, y_proba) in enumerate(rq3_probas.items()):
    fpr, tpr, _ = roc_curve(y_test_sample, y_proba)
    auc = roc_auc_score(y_test_sample, y_proba)
    plt.plot(fpr, tpr, label=f"{name} (AUC={auc:.3f})", color=colors[i], linewidth=2)
plt.plot([0, 1], [0, 1], 'k--', linewidth=1)
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('RQ3: ROC Curves - Imbalance Methods (Safe Features)', fontsize=13, fontweight='bold')
plt.legend(loc='lower right', fontsize=9)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig13_rq3_roc_curves.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')
plt.close()

# PR curves
plt.figure(figsize=(10, 8))
for i, (name, y_proba) in enumerate(rq3_probas.items()):
    prec, rec, _ = precision_recall_curve(y_test_sample, y_proba)
    ap = average_precision_score(y_test_sample, y_proba)
    plt.plot(rec, prec, label=f"{name} (AP={ap:.3f})", color=colors[i], linewidth=2)
plt.xlabel('Recall')
plt.ylabel('Precision')
plt.title('RQ3: Precision-Recall Curves (Safe Features)', fontsize=13, fontweight='bold')
plt.legend(loc='upper right', fontsize=9)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig14_rq3_pr_curves.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')
plt.close()

# Threshold analysis
best_method = results_df_rq3.loc[results_df_rq3['recall'].idxmax(), 'method']
best_proba = rq3_probas[best_method]
thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
threshold_results = []
for thresh in thresholds:
    y_pred_t = (best_proba >= thresh).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test_sample, y_pred_t).ravel()
    threshold_results.append({
        'threshold': thresh,
        'precision': precision_score(y_test_sample, y_pred_t, zero_division=0),
        'recall': recall_score(y_test_sample, y_pred_t, zero_division=0),
        'f1': f1_score(y_test_sample, y_pred_t, zero_division=0),
        'fn': fn, 'fp': fp
    })
threshold_df = pd.DataFrame(threshold_results)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].plot(threshold_df['threshold'], threshold_df['precision'], 'b-o', label='Precision', linewidth=2)
axes[0].plot(threshold_df['threshold'], threshold_df['recall'], 'r-o', label='Recall', linewidth=2)
axes[0].plot(threshold_df['threshold'], threshold_df['f1'], 'g-o', label='F1 Score', linewidth=2)
axes[0].set_xlabel('Threshold')
axes[0].set_ylabel('Score')
axes[0].set_title('Metrics vs Threshold')
axes[0].legend()
axes[0].grid(alpha=0.3)

axes[1].plot(threshold_df['threshold'], threshold_df['fn'], 'r-o', label='False Negatives', linewidth=2)
axes[1].plot(threshold_df['threshold'], threshold_df['fp'], 'b-o', label='False Positives', linewidth=2)
axes[1].set_xlabel('Threshold')
axes[1].set_ylabel('Count')
axes[1].set_title('Errors vs Threshold')
axes[1].legend()
axes[1].grid(alpha=0.3)
plt.suptitle(f'RQ3: Threshold Analysis - {best_method}', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig15_rq3_threshold_analysis.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')
plt.close()

print("  Saved: fig10, fig11, fig12, fig13, fig14, fig15")

# =============================================================================
# FINAL SUMMARY
# =============================================================================
print("\n[5/6] Generating Final Summary...")
print("-"*50)

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# RQ1
rq1_sorted = results_df_rq1.sort_values('auc', ascending=True)
axes[0].barh(rq1_sorted['model'], rq1_sorted['auc'], color='#4C72B0')
axes[0].set_xlabel('ROC AUC')
axes[0].set_title('RQ1: Algorithm Performance', fontsize=12, fontweight='bold')
axes[0].grid(axis='x', alpha=0.3)

# RQ2
top_8 = feature_importance.head(8).sort_values('importance', ascending=True)
axes[1].barh(top_8['feature'], top_8['importance'], color='#55A868')
axes[1].set_xlabel('Importance')
axes[1].set_title('RQ2: Top Features', fontsize=12, fontweight='bold')
axes[1].grid(axis='x', alpha=0.3)

# RQ3
rq3_sorted = results_df_rq3.sort_values('recall', ascending=True)
axes[2].barh(rq3_sorted['method'].str.replace(' XGBoost', ''), rq3_sorted['recall'], color='#C44E52')
axes[2].set_xlabel('Recall')
axes[2].set_title('RQ3: Imbalance Handling', fontsize=12, fontweight='bold')
axes[2].grid(axis='x', alpha=0.3)

plt.suptitle('Fraud Detection Analysis - Key Results (Safe Features)', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig16_final_summary.{SAVE_FORMAT}', dpi=SAVE_DPI, bbox_inches='tight', facecolor='white')
plt.close()

print("  Saved: fig16")

# =============================================================================
# PRINT FINAL RESULTS
# =============================================================================
print("\n[6/6] FINAL RESULTS")
print("="*70)

print("\n** RQ1: ALGORITHM COMPARISON **")
print(results_df_rq1[['model', 'auc', 'precision', 'recall', 'f1']].to_string(index=False))

print("\n** RQ2: TOP FEATURES **")
print(feature_importance.to_string(index=False))

print("\n** RQ3: IMBALANCE HANDLING **")
print(results_df_rq3[['method', 'auc', 'precision', 'recall', 'f1', 'tp', 'fn']].to_string(index=False))

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
best_rq1 = results_df_rq1.loc[results_df_rq1['auc'].idxmax()]
best_rq3 = results_df_rq3.loc[results_df_rq3['recall'].idxmax()]
print(f"\nBest Algorithm: {best_rq1['model']}")
print(f"  AUC: {best_rq1['auc']:.4f}, Recall: {best_rq1['recall']:.4f}, F1: {best_rq1['f1']:.4f}")
print(f"\nTop Feature: {feature_importance.iloc[0]['feature']} ({feature_importance.iloc[0]['importance']:.4f})")
print(f"\nBest Imbalance Method: {best_rq3['method']}")
print(f"  Recall: {best_rq3['recall']:.4f}, Precision: {best_rq3['precision']:.4f}")

print(f"\nAll figures saved to: {OUTPUT_DIR}")
print("="*70)
