import json
import numpy as np

from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from sentence_transformers import SentenceTransformer


with open("EU-Bot_청크_데이터.json", "r", encoding="utf-8") as file:
    data = json.load(file)

kb = data["knowledge_base"]

texts = []
labels = []
answers = {}


def add_train(label, answer, question_list):
    for q in question_list:
        texts.append(q)
        labels.append(label)
    answers[label] = answer


# 1. 커리큘럼 요약 학습 데이터
for item in kb["function_1_curriculum_summaries"]:
    label = item["id"]

    dept = item["dept"]
    year = item["curriculum_year"]
    grade = item["grade"]
    semester = item["semester"]
    content = item["content"]

    short_dept = "의아" if dept == "의료IT학과" else "빅융"

    questions = [
        f"{dept} {grade}학년 {semester}학기 과목",
        f"{dept} {grade}학년 {semester}학기 교육과정",
        f"{dept} {grade}학년 {semester}학기 커리큘럼",
        f"{dept} {grade}학년 {semester}학기 전공필수",
        f"{dept} {grade}학년 {semester}학기 전공선택",
        f"{dept} {year} {grade}학년 {semester}학기",
        f"{short_dept} {grade}학년 {semester}학기 과목",
        f"{short_dept} {grade}-{semester} 과목",
        f"{short_dept} {grade}학년 {semester}학기 뭐 배워",
        f"{grade}학년 {semester}학기 {dept} 과목 알려줘",
        f"{grade}학년 {semester}학기 {short_dept} 교육과정 알려줘",
        f"{dept} {grade}학년 {semester}학기 전필 전선",
        content
    ]

    add_train(label, content, questions)


# 2. 과목 상세정보 학습 데이터
for item in kb["function_2_subject_details"]:
    dept = item["dept"]
    year = item["year"]
    subject = item["subject_name"]
    full = item["full_data"]

    label = f"{dept}_{year}_{subject}"

    answer = (
        f"[과목 상세정보]\n"
        f"학과: {dept}\n"
        f"교육과정: {year}\n"
        f"과목명: {subject}\n"
        f"코드: {full['코드']}\n"
        f"이수구분: {full['이수구분']}\n"
        f"학년/학기: {full['학년_학기']}\n"
        f"학점: {full['학점']}\n"
        f"이론/실습: {full['이론_실습']}\n"
        f"성적방식: {full['성적방식']}"
    )

    short_dept = "의아" if dept == "의료IT학과" else "빅융"

    questions = [
        f"{subject}",
        f"{subject} 정보",
        f"{subject} 알려줘",
        f"{subject} 과목 정보",
        f"{subject} 상세정보",
        f"{subject} 몇 학점",
        f"{subject} 학점",
        f"{subject} 이수구분",
        f"{subject} 전공필수야",
        f"{subject} 전공선택이야",
        f"{subject} 몇 학년",
        f"{subject} 몇 학기",
        f"{subject} 학년 학기",
        f"{subject} 코드",
        f"{subject} 과목코드",
        f"{subject} 성적방식",
        f"{subject} grade",
        f"{subject} 이론 실습",
        f"{subject} 실습 있어",
        f"{subject} 수업시간",
        f"{dept} {subject}",
        f"{dept} {subject} 정보",
        f"{short_dept} {subject}",
        f"{short_dept} {subject} 몇 학점",
        f"{short_dept} {subject} 이수구분",
        f"{short_dept} {subject} 몇 학년",
    ]

    add_train(label, answer, questions)


# =========================
# NB 모델 학습
# =========================
vectorizer = CountVectorizer(
    token_pattern=r"(?u)\b\w+\b",
    ngram_range=(1, 2)
)

X = vectorizer.fit_transform(texts)

nb_model = MultinomialNB(alpha=0.1)
nb_model.fit(X, labels)


# =========================
# Transformer 모델 준비
# =========================
transformer_model = SentenceTransformer("jhgan/ko-sroberta-multitask")

transformer_embeddings = transformer_model.encode(
    texts,
    convert_to_numpy=True
)


print("총 학습 문장 수:", len(texts))
print("총 label 수:", len(set(labels)))
print("을지대 NB + Transformer 챗봇입니다.")
print("종료하려면 '종료' 입력하세요.")


while True:
    user_question = input("\n질문 입력: ")

    if user_question == "종료":
        print("프로그램을 종료합니다.")
        break

    # =========================
    # 1차: NB 모델 예측
    # =========================
    test_X = vectorizer.transform([user_question])

    nb_predicted_label = nb_model.predict(test_X)[0]
    nb_probabilities = nb_model.predict_proba(test_X)[0]
    nb_max_probability = max(nb_probabilities)

    print("NB 예측 label:", nb_predicted_label)
    print("NB 확률:", nb_max_probability)

    # NB가 확신하면 바로 답변
    if nb_max_probability >= 0.40:
        print("답변:")
        print(answers[nb_predicted_label])
        continue

    # =========================
    # 2차: Transformer 유사도 검색
    # =========================
    question_embedding = transformer_model.encode(
        [user_question],
        convert_to_numpy=True
    )

    similarities = cosine_similarity(
        question_embedding,
        transformer_embeddings
    )[0]

    best_index = np.argmax(similarities)
    transformer_score = similarities[best_index]
    transformer_label = labels[best_index]

    print("Transformer 예측 label:", transformer_label)
    print("Transformer 유사도:", transformer_score)

    if transformer_score >= 0.55:
        print("답변:")
        print(answers[transformer_label])
    else:
        print("질문이 너무 모호합니다.")
        print("학과명, 과목명, 학년/학기 등을 구체적으로 입력해주세요.")