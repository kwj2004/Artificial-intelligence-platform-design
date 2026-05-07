import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, accuracy_score, f1_score
import numpy as np

# ==========================================
# 1. 한글 폰트 설정 (중요!)
# ==========================================
from matplotlib import rc
import matplotlib.font_manager as fm

# 윈도우 Malgun Gothic 기준. 맥 사용 시 'AppleGothic' 등으로 변경 필요
font_path = "C:/Windows/Fonts/malgun.ttf" 
font_name = fm.FontProperties(fname=font_path).get_name()
rc('font', family=font_name)

# 음수 부호 깨짐 방지
plt.rcParams['axes.unicode_minus'] = False 

# ==========================================
# 2. 데이터 준비 및 모델 학습
# ==========================================
# (데이터 로드 및 분할 코드는 이전과 동일)
df = pd.read_csv("EU-Bot_통합_학습데이터.csv")
X_train, X_test, y_train, y_test = train_test_split(
    df['question'], df['category'], test_size=0.2, random_state=42, stratify=df['category']
)

# 카테고리 순서를 보내주신 이미지와 동일하게 정렬
category_order = ['기타', '수강 신청', '일정', '장학금', '졸업 요건', '학사 경고', '학칙/규정 일반']
# 데이터셋에 존재하는 카테고리만 필터링
existing_categories = [cat for cat in category_order if cat in df['category'].unique()]

# 피처 추출
vectorizer = TfidfVectorizer()
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# NB 학습
nb_model = MultinomialNB(alpha=0.1)
nb_model.fit(X_train_vec, y_train)
y_pred_nb = nb_model.predict(X_test_vec)

# RF 학습
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train_vec, y_train)
y_pred_rf = rf_model.predict(X_test_vec)

# ==========================================
# 3. 전체 시각화 (1행 3열 구성)
# ==========================================
fig, axes = plt.subplots(1, 3, figsize=(22, 7)) # 1행 3열 subplot 생성

# --- (1) NB vs RF 성능 비교 (Bar Chart) ---
metrics = ['Accuracy', 'F1 (macro)', 'F1 (weighted)']
nb_scores = [
    accuracy_score(y_test, y_pred_nb),
    f1_score(y_test, y_pred_nb, average='macro'),
    f1_score(y_test, y_pred_nb, average='weighted')
]
rf_scores = [
    accuracy_score(y_test, y_pred_rf),
    f1_score(y_test, y_pred_rf, average='macro'),
    f1_score(y_test, y_pred_rf, average='weighted')
]

x = np.arange(len(metrics))
width = 0.35

rects1 = axes[0].bar(x - width/2, nb_scores, width, label='Naive Bayes', color='#3274A1') # 파란색 계열
rects2 = axes[0].bar(x + width/2, rf_scores, width, label='Random Forest', color='#3A923A') # 초록색 계열

axes[0].set_title('NB vs RF Performance Comparison')
axes[0].set_xticks(x)
axes[0].set_xticklabels(metrics)
axes[0].set_ylim(0, 1.1) # Y축 범위 설정 (라벨 표기를 위해 1.1까지)
axes[0].legend()

# 바 위에 점수 표기 함수
def autolabel(rects, ax):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.3f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3), # 3pt vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)

autolabel(rects1, axes[0])
autolabel(rects2, axes[0])


# --- (2) NB Confusion Matrix ---
cm_nb = confusion_matrix(y_test, y_pred_nb, labels=existing_categories)
sns.heatmap(cm_nb, annot=True, fmt='d', cmap='Blues', ax=axes[1],
            xticklabels=existing_categories, yticklabels=existing_categories)
axes[1].set_title(f'Naive Bayes Confusion Matrix (Acc: {nb_scores[0]:.3f})')
axes[1].set_ylabel('Actual')
axes[1].set_xlabel('Predicted')
axes[1].tick_params(axis='x', rotation=45) # X축 라벨 회전

# --- (3) RF Confusion Matrix ---
cm_rf = confusion_matrix(y_test, y_pred_rf, labels=existing_categories)
sns.heatmap(cm_rf, annot=True, fmt='d', cmap='Greens', ax=axes[2],
            xticklabels=existing_categories, yticklabels=existing_categories)
axes[2].set_title(f'Random Forest Confusion Matrix (Acc: {rf_scores[0]:.3f})')
axes[2].set_ylabel('Actual')
axes[2].set_xlabel('Predicted')
axes[2].tick_params(axis='x', rotation=45) # X축 라벨 회전

plt.tight_layout() # 그래프 간격 자동 조정
plt.show()

import joblib
import os

# 모델을 저장할 폴더 생성
os.makedirs('models', exist_ok=True)

# 학습된 모델과 벡터라이저 저장
joblib.dump(nb_model, './models/intent_model.pkl')
joblib.dump(vectorizer, './models/tfidf_vectorizer.pkl')
print("모델 저장 완료!")
