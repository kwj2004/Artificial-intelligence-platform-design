"""
EU-Bot NB vs RF 의도 분류 모델 학습 및 비교
=============================================
통합 학습데이터(380건)로 Naive Bayes / Random Forest 학습 후 성능 비교

필요 패키지:
  pip install scikit-learn pandas matplotlib seaborn joblib

실행:
  python EU-Bot_모델_학습_비교.py
"""

import pandas as pd
import numpy as np
import json
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, f1_score, classification_report,
    confusion_matrix
)
from sklearn.pipeline import Pipeline
import joblib
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("🚀 EU-Bot NB vs RF 의도 분류 모델 학습 및 비교")
print("=" * 60)

# ===== 1. 데이터 로드 =====
print("\n📄 Step 1: 데이터 로드")

df = pd.read_csv("EU-Bot_통합_학습데이터.csv", encoding="utf-8-sig")
print(f"  총 데이터: {len(df)}건")
print(f"\n  카테고리 분포:")
print(df["category"].value_counts().to_string(header=False))

X = df["question"].values
y = df["category"].values

# ===== 2. Train/Test 분할 (8:2) =====
print(f"\n📄 Step 2: Train/Test 분할 (8:2)")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"  Train: {len(X_train)}건")
print(f"  Test:  {len(X_test)}건")

# ===== 3. TF-IDF 벡터라이저 설정 =====
print(f"\n📄 Step 3: TF-IDF 피처 추출")

tfidf = TfidfVectorizer(
    max_features=5000,
    ngram_range=(1, 2),     # unigram + bigram
    min_df=1,
    max_df=0.95,
    sublinear_tf=True,      # 로그 스케일 TF
)

X_train_tfidf = tfidf.fit_transform(X_train)
X_test_tfidf = tfidf.transform(X_test)

print(f"  피처 수: {X_train_tfidf.shape[1]}개")
print(f"  Train 행렬: {X_train_tfidf.shape}")
print(f"  Test 행렬:  {X_test_tfidf.shape}")

# ===== 4. 모델 A: Naive Bayes =====
print(f"\n{'=' * 60}")
print(f"🤖 모델 A: Multinomial Naive Bayes")
print(f"{'=' * 60}")

nb_model = MultinomialNB(alpha=0.1)
nb_model.fit(X_train_tfidf, y_train)

nb_pred = nb_model.predict(X_test_tfidf)
nb_accuracy = accuracy_score(y_test, nb_pred)
nb_f1_macro = f1_score(y_test, nb_pred, average='macro')
nb_f1_weighted = f1_score(y_test, nb_pred, average='weighted')

# 교차 검증
nb_cv_scores = cross_val_score(nb_model, X_train_tfidf, y_train, cv=5, scoring='accuracy')

print(f"\n  📊 성능 결과:")
print(f"  Accuracy:         {nb_accuracy:.4f} ({nb_accuracy*100:.1f}%)")
print(f"  F1-Score (macro):  {nb_f1_macro:.4f}")
print(f"  F1-Score (weighted): {nb_f1_weighted:.4f}")
print(f"  교차검증 평균 Accuracy: {nb_cv_scores.mean():.4f} (±{nb_cv_scores.std():.4f})")

print(f"\n  📋 카테고리별 성능:")
print(classification_report(y_test, nb_pred, zero_division=0))

# ===== 5. 모델 B: Random Forest =====
print(f"{'=' * 60}")
print(f"🌲 모델 B: Random Forest Classifier")
print(f"{'=' * 60}")

rf_model = RandomForestClassifier(
    n_estimators=200,
    max_depth=None,
    min_samples_split=2,
    min_samples_leaf=1,
    random_state=42,
    n_jobs=-1,
)
rf_model.fit(X_train_tfidf, y_train)

rf_pred = rf_model.predict(X_test_tfidf)
rf_accuracy = accuracy_score(y_test, rf_pred)
rf_f1_macro = f1_score(y_test, rf_pred, average='macro')
rf_f1_weighted = f1_score(y_test, rf_pred, average='weighted')

# 교차 검증
rf_cv_scores = cross_val_score(rf_model, X_train_tfidf, y_train, cv=5, scoring='accuracy')

print(f"\n  📊 성능 결과:")
print(f"  Accuracy:         {rf_accuracy:.4f} ({rf_accuracy*100:.1f}%)")
print(f"  F1-Score (macro):  {rf_f1_macro:.4f}")
print(f"  F1-Score (weighted): {rf_f1_weighted:.4f}")
print(f"  교차검증 평균 Accuracy: {rf_cv_scores.mean():.4f} (±{rf_cv_scores.std():.4f})")

print(f"\n  📋 카테고리별 성능:")
print(classification_report(y_test, rf_pred, zero_division=0))

# ===== 6. 모델 비교 =====
print(f"{'=' * 60}")
print(f"⚡ NB vs RF 성능 비교")
print(f"{'=' * 60}")

comparison = {
    "지표": ["Accuracy", "F1 (macro)", "F1 (weighted)", "교차검증 평균", "교차검증 표준편차"],
    "Naive Bayes": [
        f"{nb_accuracy:.4f}", f"{nb_f1_macro:.4f}", f"{nb_f1_weighted:.4f}",
        f"{nb_cv_scores.mean():.4f}", f"{nb_cv_scores.std():.4f}"
    ],
    "Random Forest": [
        f"{rf_accuracy:.4f}", f"{rf_f1_macro:.4f}", f"{rf_f1_weighted:.4f}",
        f"{rf_cv_scores.mean():.4f}", f"{rf_cv_scores.std():.4f}"
    ],
}

comp_df = pd.DataFrame(comparison)
print(f"\n{comp_df.to_string(index=False)}")

# 승자 판정
if nb_accuracy > rf_accuracy:
    winner = "Naive Bayes"
    winner_accuracy = nb_accuracy
elif rf_accuracy > nb_accuracy:
    winner = "Random Forest"
    winner_accuracy = rf_accuracy
else:
    winner = "동점"
    winner_accuracy = nb_accuracy

print(f"\n  🏆 Accuracy 기준 승자: {winner} ({winner_accuracy*100:.1f}%)")

if nb_f1_weighted > rf_f1_weighted:
    f1_winner = "Naive Bayes"
elif rf_f1_weighted > nb_f1_weighted:
    f1_winner = "Random Forest"
else:
    f1_winner = "동점"

print(f"  🏆 F1(weighted) 기준 승자: {f1_winner}")

# ===== 7. Confusion Matrix 저장 =====
categories = sorted(list(set(y_test)))

nb_cm = confusion_matrix(y_test, nb_pred, labels=categories)
rf_cm = confusion_matrix(y_test, rf_pred, labels=categories)

print(f"\n  📊 Naive Bayes Confusion Matrix:")
cm_df = pd.DataFrame(nb_cm, index=categories, columns=categories)
print(cm_df.to_string())

print(f"\n  📊 Random Forest Confusion Matrix:")
cm_df2 = pd.DataFrame(rf_cm, index=categories, columns=categories)
print(cm_df2.to_string())

# ===== 8. 시각화 저장 =====
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    
    # 한글 폰트 설정
    font_candidates = ['Malgun Gothic', 'NanumGothic', 'AppleGothic', 'DejaVu Sans']
    font_set = False
    for font_name in font_candidates:
        if any(font_name in f.name for f in fm.fontManager.ttflist):
            plt.rcParams['font.family'] = font_name
            plt.rcParams['axes.unicode_minus'] = False
            font_set = True
            break
    
    if not font_set:
        plt.rcParams['axes.unicode_minus'] = False

    # --- 그래프 1: 성능 비교 막대 그래프 ---
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    
    metrics = ['Accuracy', 'F1 (macro)', 'F1 (weighted)']
    nb_scores = [nb_accuracy, nb_f1_macro, nb_f1_weighted]
    rf_scores = [rf_accuracy, rf_f1_macro, rf_f1_weighted]
    
    x = np.arange(len(metrics))
    width = 0.35
    
    axes[0].bar(x - width/2, nb_scores, width, label='Naive Bayes', color='#2E75B6')
    axes[0].bar(x + width/2, rf_scores, width, label='Random Forest', color='#27AE60')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(metrics)
    axes[0].set_ylim(0, 1.1)
    axes[0].set_title('NB vs RF Performance')
    axes[0].legend()
    
    for i, (nb_s, rf_s) in enumerate(zip(nb_scores, rf_scores)):
        axes[0].text(i - width/2, nb_s + 0.02, f'{nb_s:.3f}', ha='center', fontsize=9)
        axes[0].text(i + width/2, rf_s + 0.02, f'{rf_s:.3f}', ha='center', fontsize=9)
    
    # --- 그래프 2: NB Confusion Matrix ---
    im1 = axes[1].imshow(nb_cm, cmap='Blues', aspect='auto')
    axes[1].set_xticks(range(len(categories)))
    axes[1].set_yticks(range(len(categories)))
    axes[1].set_xticklabels(categories, rotation=45, ha='right', fontsize=8)
    axes[1].set_yticklabels(categories, fontsize=8)
    axes[1].set_title('NB Confusion Matrix')
    axes[1].set_xlabel('Predicted')
    axes[1].set_ylabel('Actual')
    
    for i in range(len(categories)):
        for j in range(len(categories)):
            axes[1].text(j, i, str(nb_cm[i, j]), ha='center', va='center',
                        color='white' if nb_cm[i, j] > nb_cm.max()/2 else 'black', fontsize=10)
    
    # --- 그래프 3: RF Confusion Matrix ---
    im2 = axes[2].imshow(rf_cm, cmap='Greens', aspect='auto')
    axes[2].set_xticks(range(len(categories)))
    axes[2].set_yticks(range(len(categories)))
    axes[2].set_xticklabels(categories, rotation=45, ha='right', fontsize=8)
    axes[2].set_yticklabels(categories, fontsize=8)
    axes[2].set_title('RF Confusion Matrix')
    axes[2].set_xlabel('Predicted')
    axes[2].set_ylabel('Actual')
    
    for i in range(len(categories)):
        for j in range(len(categories)):
            axes[2].text(j, i, str(rf_cm[i, j]), ha='center', va='center',
                        color='white' if rf_cm[i, j] > rf_cm.max()/2 else 'black', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('모델_비교_결과.png', dpi=150, bbox_inches='tight')
    print(f"\n  ✅ 시각화 저장: 모델_비교_결과.png")

except Exception as e:
    print(f"\n  ⚠️ 시각화 생성 실패 (matplotlib 필요): {e}")

# ===== 9. 모델 저장 =====
os.makedirs("models", exist_ok=True)

# TF-IDF 벡터라이저 저장
joblib.dump(tfidf, "models/tfidf_vectorizer.pkl")

# 두 모델 모두 저장
joblib.dump(nb_model, "models/naive_bayes_model.pkl")
joblib.dump(rf_model, "models/random_forest_model.pkl")

# 최종 채택 모델 저장 (Accuracy 기준)
if nb_accuracy >= rf_accuracy:
    best_model = nb_model
    best_name = "Naive Bayes"
else:
    best_model = rf_model
    best_name = "Random Forest"

joblib.dump(best_model, "models/best_intent_classifier.pkl")

print(f"\n  ✅ 모델 저장 완료:")
print(f"    models/tfidf_vectorizer.pkl")
print(f"    models/naive_bayes_model.pkl")
print(f"    models/random_forest_model.pkl")
print(f"    models/best_intent_classifier.pkl ({best_name})")

# ===== 10. 비교 결과 JSON 저장 =====
result_json = {
    "project": "EU-Bot",
    "experiment": "NB vs RF 의도 분류 모델 비교",
    "data": {
        "total_samples": len(df),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "categories": list(df["category"].unique()),
        "num_categories": len(df["category"].unique()),
        "tfidf_features": X_train_tfidf.shape[1],
    },
    "model_a_naive_bayes": {
        "algorithm": "Multinomial Naive Bayes",
        "hyperparameters": {"alpha": 0.1},
        "accuracy": round(nb_accuracy, 4),
        "f1_macro": round(nb_f1_macro, 4),
        "f1_weighted": round(nb_f1_weighted, 4),
        "cv_mean": round(nb_cv_scores.mean(), 4),
        "cv_std": round(nb_cv_scores.std(), 4),
        "confusion_matrix": nb_cm.tolist(),
    },
    "model_b_random_forest": {
        "algorithm": "Random Forest Classifier",
        "hyperparameters": {"n_estimators": 200, "max_depth": "None"},
        "accuracy": round(rf_accuracy, 4),
        "f1_macro": round(rf_f1_macro, 4),
        "f1_weighted": round(rf_f1_weighted, 4),
        "cv_mean": round(rf_cv_scores.mean(), 4),
        "cv_std": round(rf_cv_scores.std(), 4),
        "confusion_matrix": rf_cm.tolist(),
    },
    "conclusion": {
        "accuracy_winner": winner,
        "f1_winner": f1_winner,
        "selected_model": best_name,
        "reason": f"{best_name}이(가) Accuracy 기준으로 더 높은 성능을 보여 최종 시스템에 채택"
    }
}

with open("모델_비교_결과.json", "w", encoding="utf-8") as f:
    json.dump(result_json, f, ensure_ascii=False, indent=2)

print(f"  ✅ 비교 결과 저장: 모델_비교_결과.json")

# ===== 11. 실제 테스트 =====
print(f"\n{'=' * 60}")
print(f"🔍 실제 질문 분류 테스트")
print(f"{'=' * 60}")

test_questions = [
    "졸업인증제 필수 분야가 뭐야?",
    "MT 언제야?",
    "장학금 신청 어떻게 해?",
    "학사 경고 기준이 뭐야?",
    "수강신청 기간이 언제야?",
    "이사회 구성은 어떻게 돼?",
    "중간고사 언제 시작해?",
    "토익 몇 점이면 인증돼?",
]

test_tfidf = tfidf.transform(test_questions)
nb_test_pred = nb_model.predict(test_tfidf)
rf_test_pred = rf_model.predict(test_tfidf)

print(f"\n  {'질문':<30} {'NB 예측':<18} {'RF 예측':<18}")
print(f"  {'-'*66}")
for q, nb_p, rf_p in zip(test_questions, nb_test_pred, rf_test_pred):
    match = "✅" if nb_p == rf_p else "❌"
    print(f"  {q:<30} {nb_p:<18} {rf_p:<18} {match}")

print(f"\n{'=' * 60}")
print(f"✅ 모델 학습 및 비교 완료!")
print(f"  최종 채택 모델: {best_name}")
print(f"  다음 단계: FastAPI 백엔드에서 이 모델을 로드하여 사용")
print(f"{'=' * 60}")
