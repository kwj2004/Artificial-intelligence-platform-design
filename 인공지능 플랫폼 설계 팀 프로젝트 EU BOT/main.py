import json
import os
import re
import sys
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer


# =========================================================
# 0. 파일 경로 설정
# =========================================================
# 이 파이썬 파일과 같은 폴더에 아래 두 파일을 넣어두면 됩니다.
# JSON 파일 후보는 위에서부터 순서대로 찾습니다.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

JSON_CANDIDATES = [
    "EU-Bot_청크_데이터.json",
    
]

CSV_CANDIDATES = [
    "EU-Bot_통합_학습데이터.csv",
]


def find_file(candidates):
    for name in candidates:
        path = os.path.join(BASE_DIR, name)
        if os.path.exists(path):
            return path
    return ""


JSON_PATH = find_file(JSON_CANDIDATES)
CSV_PATH = find_file(CSV_CANDIDATES)

if not JSON_PATH:
    raise FileNotFoundError(
        "JSON 파일을 찾지 못했습니다. 파이썬 파일과 같은 폴더에 "
        "'EU-Bot_청크_데이터 수정.json' 또는 '붙여넣은 텍스트 (1)(5).txt'를 넣어주세요."
    )

if not CSV_PATH:
    raise FileNotFoundError(
        "CSV 파일을 찾지 못했습니다. 파이썬 파일과 같은 폴더에 "
        "'EU-Bot_통합_학습데이터.csv'를 넣어주세요."
    )


# =========================================================
# 1. 데이터 로드
# =========================================================
def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_csv(path):
    # 엑셀에서 저장한 CSV까지 고려합니다.
    for enc in ["utf-8-sig", "utf-8", "cp949"]:
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)


data = read_json(JSON_PATH)
chunks = data.get("chunks", [])

if not chunks:
    raise ValueError("JSON 안에 chunks 배열이 없습니다.")

train_df = read_csv(CSV_PATH)
required_cols = {"question", "category", "sub_intent"}
missing = required_cols - set(train_df.columns)
if missing:
    raise ValueError(f"CSV에 필요한 컬럼이 없습니다: {missing}. 현재 컬럼: {list(train_df.columns)}")

train_df = train_df.dropna(subset=["question", "category"]).copy()
train_df["question"] = train_df["question"].astype(str)
train_df["category"] = train_df["category"].astype(str)
train_df["sub_intent"] = train_df["sub_intent"].astype(str)


# =========================================================
# 2. 공통 유틸
# =========================================================
def clean_text(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def compact(value):
    return re.sub(r"\s+", "", clean_text(value).lower())


def contains_any(text, words):
    return any(w in text for w in words)


# 줄임말/별칭 사전
ALIAS_MAP = {
    "의아": "의료IT학과",
    "의아이": "의료IT학과",
    "의료아이티": "의료IT학과",
    "의료IT": "의료IT학과",
    "의료it": "의료IT학과",
    "빅융": "빅데이터의료융합학과",
    "빅데이터의료융합": "빅데이터의료융합학과",
    "빅데이터의료융합학부": "빅데이터의료융합학과",
    "빅인": "빅데이터인공지능전공",
    "빅데이터인공지능": "빅데이터인공지능전공",
    "빅데이터인공지능학과": "빅데이터인공지능전공",
    "첨단": "빅데이터인공지능전공",
    "첨단학부": "빅데이터인공지능전공",
    "스의정": "스마트의료정보학부",
    "스마트의료정보": "스마트의료정보학부",
}

# JSON 안에 줄임말 사전 chunk가 있으면 자동 반영
for c in chunks:
    if c.get("document") == "줄임말 사전" or c.get("subcategory") == "줄임말 사전":
        abbr = clean_text(c.get("abbr") or c.get("article"))
        full = clean_text(c.get("full_name"))
        if abbr and full:
            ALIAS_MAP[abbr] = full


def expand_aliases(question):
    q = clean_text(question)
    expanded = q
    for alias, full in sorted(ALIAS_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        if alias in expanded and full not in expanded:
            expanded = expanded.replace(alias, f"{alias} {full}")
    return expanded


def normalize_category_name(category):
    category = clean_text(category)
    # CSV와 JSON category가 같도록 유지합니다.
    return category


def infer_curriculum_category(question):
    q = expand_aliases(question)
    q_low = q.lower()

    # 교육과정/학번 기준 우선
    if "22교육과정" in q or "22학번" in q:
        if contains_any(q, ["의아", "의료IT", "의료아이티", "의료IT학과"]):
            return "교육과정_의아"
        return "교육과정_빅융"

    if "24교육과정" in q or "24학번" in q or contains_any(q, ["스의정", "스마트의료정보"]):
        return "교육과정_스의정"

    if "26교육과정" in q or "25학번" in q or "현행" in q or "지금" in q or "첨단" in q:
        return "교육과정_첨단"

    # 학과 별칭 기준
    if contains_any(q, ["의아", "의료IT", "의료아이티", "의료IT학과"]):
        return "교육과정_의아"

    if contains_any(q, ["빅융", "빅데이터의료융합"]):
        return "교육과정_빅융"

    if contains_any(q, ["스의정", "스마트의료정보"]):
        return "교육과정_스의정"

    if contains_any(q, ["빅인", "빅데이터인공지능", "첨단학부"]):
        return "교육과정_첨단"

    return ""


def extract_grade_semester_course_type(question):
    q = clean_text(question)
    grade = ""
    semester = ""
    course_type = ""

    gm = re.search(r"(\d+)\s*학년", q)
    if gm:
        grade = gm.group(1)

    sm = re.search(r"(\d+)\s*학기", q)
    if sm:
        semester = sm.group(1)

    # 3-1, 3/1 형태
    cm = re.search(r"\b(\d)\s*[-/]\s*(\d)\b", q)
    if cm:
        grade = grade or cm.group(1)
        semester = semester or cm.group(2)

    for ct in ["전공기초", "전공필수", "전공선택", "전필", "전선", "교양필수", "교양선택"]:
        if ct in q:
            course_type = ct
            break

    if course_type == "전필":
        course_type = "전공필수"
    elif course_type == "전선":
        course_type = "전공선택"

    return grade, semester, course_type


def extract_subjects_from_text(text):
    # 작은따옴표 안 과목명 추출
    names = re.findall(r"'([^']+)'", text)
    return names


# =========================================================
# 3. JSON 인덱스 생성
# =========================================================
chunk_records = []
category_to_chunks = {}
source_to_chunk = {}

for c in chunks:
    category = clean_text(c.get("category"))
    text = clean_text(c.get("text"))
    title = clean_text(c.get("title"))
    article = clean_text(c.get("article"))
    source_id = clean_text(c.get("source_id"))

    search_text = " | ".join([
        category,
        clean_text(c.get("document")),
        clean_text(c.get("document_date")),
        source_id,
        article,
        title,
        text,
    ])

    rec = {
        "chunk": c,
        "category": category,
        "source_id": source_id,
        "title": title,
        "article": article,
        "text": text,
        "search_text": search_text,
    }
    chunk_records.append(rec)
    category_to_chunks.setdefault(category, []).append(rec)
    if source_id:
        source_to_chunk[source_id] = rec


# 교육과정 요약 인덱스
curriculum_summaries = []
for rec in chunk_records:
    c = rec["chunk"]
    if clean_text(c.get("document")) != "교육과정":
        continue
    if not clean_text(c.get("source_id")).startswith("교육과정_"):
        continue

    grade, semester, course_type = extract_grade_semester_course_type(c.get("article", ""))
    if not grade:
        continue

    curriculum_summaries.append({
        "category": rec["category"],
        "grade": grade,
        "semester": semester,
        "course_type": course_type,
        "text": rec["text"],
        "title": rec["title"],
        "article": rec["article"],
    })

CURRICULUM_TYPE_ORDER = {
    "전공기초": 1,
    "전공필수": 2,
    "전공선택": 3,
    "교양필수": 4,
    "교양선택": 5,
    "": 9,
}

# 대체과목 인덱스
replacement_chunks = [rec for rec in chunk_records if rec["category"] == "대체과목"]
replacement_by_subject = {}
for rec in replacement_chunks:
    subjects = extract_subjects_from_text(rec["text"])
    # 보통 첫 번째가 폐지 과목, 두 번째가 대체 과목입니다.
    if subjects:
        replacement_by_subject[subjects[0]] = rec
    # title/article에서도 화살표 앞부분 추출
    m = re.search(r"대체과목:\s*(.+?)\s*→", rec["title"] or rec["article"])
    if m:
        replacement_by_subject[m.group(1).strip()] = rec

# 일정 인덱스
schedule_chunks = category_to_chunks.get("일정", [])

# 학과정보 인덱스
info_chunks = category_to_chunks.get("학과정보", [])


# =========================================================
# 4. CSV 질문 리스트 기반 카테고리 분류 모델
# =========================================================
train_questions = [expand_aliases(q) for q in train_df["question"].tolist()]
train_categories = [normalize_category_name(c) for c in train_df["category"].tolist()]

category_vectorizer = CountVectorizer(token_pattern=r"(?u)\b\w+\b", ngram_range=(1, 2))
X_cat = category_vectorizer.fit_transform(train_questions)
category_nb = MultinomialNB(alpha=0.1)
category_nb.fit(X_cat, train_categories)

# CSV 질문 transformer 검색용
model = SentenceTransformer("jhgan/ko-sroberta-multitask")
question_embeddings = model.encode(train_questions, convert_to_numpy=True, show_progress_bar=False)

# JSON chunk transformer 검색용
chunk_search_texts = [rec["search_text"] for rec in chunk_records]
chunk_embeddings = model.encode(chunk_search_texts, convert_to_numpy=True, show_progress_bar=False)


# =========================================================
# 5. 카테고리/의도 판별
# =========================================================
def predict_category(question):
    q = expand_aliases(question)

    # 규칙 기반 우선 판별
    if contains_any(q, ["대체", "폐강", "폐지", "없어졌", "없어진", "복학생", "미이수", "대신"]):
        return "대체과목", 1.0, "rule"

    if contains_any(q, ["언제", "날짜", "일정", "기간", "어디", "장소", "몇월", "며칠", "캘린더"]):
        # 교육과정 질문의 "몇 학기"는 일정으로 오해하지 않도록 보정
        if not contains_any(q, ["교육과정", "커리큘럼", "과목", "전공"]):
            return "일정", 1.0, "rule"

    if contains_any(q, ["졸업인증", "인증", "심폐소생술", "사회봉사", "토익", "오픽", "ITQ", "MOS", "정보처리"]):
        return "졸업인증", 1.0, "rule"

    if contains_any(q, ["교수", "교수님", "연구실", "이메일", "연락처", "전화", "뜻", "줄임말", "뭐야"]):
        # 과목 뭐야는 교육과정으로 갈 수 있으니 과목명 직접 검색 전에만 사용
        if not contains_any(q, ["교육과정", "과목", "수업", "전공필수", "전공선택"]):
            return "학과정보", 1.0, "rule"

    cur_cat = infer_curriculum_category(q)
    if cur_cat:
        return cur_cat, 1.0, "rule"

    # NB 분류
    x = category_vectorizer.transform([q])
    pred = category_nb.predict(x)[0]
    prob = float(max(category_nb.predict_proba(x)[0]))

    # NB가 애매하면 CSV 질문 transformer로 보조
    if prob < 0.35:
        emb = model.encode([q], convert_to_numpy=True, show_progress_bar=False)
        sims = cosine_similarity(emb, question_embeddings)[0]
        idx = int(np.argmax(sims))
        return train_categories[idx], float(sims[idx]), "csv-transformer"

    return pred, prob, "csv-nb"


# =========================================================
# 6. 카테고리별 답변 함수
# =========================================================
def answer_curriculum(question, category):
    q = expand_aliases(question)
    category = category or infer_curriculum_category(q)
    grade, semester, course_type = extract_grade_semester_course_type(q)

    matched = []
    for row in curriculum_summaries:
        if row["category"] != category:
            continue
        if grade and row["grade"] != grade:
            continue
        if semester and row["semester"] != semester:
            continue
        if course_type and row["course_type"] != course_type:
            continue
        matched.append(row)

    # 전공필수/전공선택을 묻지 않고 학년만 물으면 해당 학년 전체 출력
    if matched:
        matched.sort(key=lambda r: (
            int(r["semester"] or 9),
            CURRICULUM_TYPE_ORDER.get(r["course_type"], 99),
            r["course_type"],
        ))

        label_map = {
            "교육과정_의아": "의료IT학과 22교육과정",
            "교육과정_빅융": "빅데이터의료융합학과 22교육과정",
            "교육과정_스의정": "스마트의료정보학부 24교육과정",
            "교육과정_첨단": "빅데이터인공지능전공 현행 26교육과정",
        }
        head = label_map.get(category, category)
        detail = []
        if grade:
            detail.append(f"{grade}학년")
        if semester:
            detail.append(f"{semester}학기")
        if course_type:
            detail.append(course_type)

        lines = [f"[{head} {' '.join(detail)} 교육과정]"]
        for row in matched:
            lines.append(f"- {row['semester']}학기 {row['course_type']}: {row['text']}")
        return "\n".join(lines)

    # 요약 매칭 실패 시 해당 category 내 semantic 검색
    return semantic_chunk_answer(q, category_filter=category)


def answer_replacement(question):
    q = expand_aliases(question)
    cq = compact(q)

    # 특정 폐지과목명이 질문에 있으면 해당 chunk 우선
    for subject, rec in replacement_by_subject.items():
        if compact(subject) in cq:
            return rec["text"]

    # 전체 목록 질문이면 전체목록 chunk 우선
    for rec in replacement_chunks:
        if "전체목록" in rec["source_id"] or "전체 목록" in rec["title"]:
            if contains_any(q, ["전체", "목록", "뭐", "알려"]):
                return rec["text"]

    return semantic_chunk_answer(q, category_filter="대체과목")


def answer_schedule(question):
    q = expand_aliases(question)
    cq = compact(q)

    # 제목/행사명 직접 포함 시 우선
    best = None
    best_len = 0
    for rec in schedule_chunks:
        names = [rec["title"], rec["article"]]
        for name in names:
            cn = compact(name)
            if cn and cn in cq and len(cn) > best_len:
                best = rec
                best_len = len(cn)

    if best:
        c = best["chunk"]
        title = clean_text(c.get("title"))
        start = clean_text(c.get("start_date"))
        end = clean_text(c.get("end_date"))
        place = clean_text(c.get("place"))
        event_cat = clean_text(c.get("event_category"))

        if contains_any(q, ["어디", "장소", "어디서"]):
            return f"{title} 장소는 {place}입니다."
        if contains_any(q, ["언제", "날짜", "기간", "며칠", "몇월"]):
            if start and end and start != end:
                return f"{title} 일정은 {start}부터 {end}까지이며, 장소는 {place}입니다."
            return f"{title} 일정은 {start}이며, 장소는 {place}입니다."
        return best["text"]

    return semantic_chunk_answer(q, category_filter="일정")


def answer_department_info(question):
    q = expand_aliases(question)
    cq = compact(q)

    # 줄임말 답변
    for alias, full in ALIAS_MAP.items():
        if compact(alias) in cq and contains_any(q, ["뜻", "줄임말", "뭐야", "무슨", "정식"]):
            return f"{alias}은(는) {full}을 의미하는 줄임말입니다."

    # 교수명/연락처 직접 검색
    return semantic_chunk_answer(q, category_filter="학과정보")


def answer_graduation(question):
    return semantic_chunk_answer(question, category_filter="졸업인증")


def semantic_chunk_answer(question, category_filter=""):
    q = expand_aliases(question)

    indices = list(range(len(chunk_records)))
    if category_filter:
        indices = [i for i, rec in enumerate(chunk_records) if rec["category"] == category_filter]

    if not indices:
        indices = list(range(len(chunk_records)))

    emb = model.encode([q], convert_to_numpy=True, show_progress_bar=False)
    sims = cosine_similarity(emb, chunk_embeddings[indices])[0]
    local_best = int(np.argmax(sims))
    best_i = indices[local_best]
    score = float(sims[local_best])
    rec = chunk_records[best_i]

    if score < 0.32:
        return "질문이 너무 모호합니다. 학과명, 학년/학기, 과목명, 일정명 등을 조금 더 구체적으로 입력해주세요."

    return rec["text"]


def answer_question(question):
    category, score, method = predict_category(question)

    if category.startswith("교육과정_"):
        answer = answer_curriculum(question, category)
    elif category == "대체과목":
        answer = answer_replacement(question)
    elif category == "일정":
        answer = answer_schedule(question)
    elif category == "학과정보":
        answer = answer_department_info(question)
    elif category == "졸업인증":
        answer = answer_graduation(question)
    else:
        answer = semantic_chunk_answer(question, category_filter=category)

    return {
        "category": category,
        "score": score,
        "method": method,
        "answer": answer,
    }

def strip_keyword_tag(text):
    """키워드 태그 제거"""
    return re.sub(r'\[키워드:.*?\]\s*', '', text)


# =========================================================
# 7. 실행
# =========================================================
if __name__ == "__main__":
    print("JSON 파일:", os.path.basename(JSON_PATH))
    print("CSV 파일:", os.path.basename(CSV_PATH))
    print("총 JSON chunk 수:", len(chunks))
    print("총 CSV 학습 질문 수:", len(train_df))
    print("CSV 카테고리 분포:", dict(Counter(train_categories)))
    print("을지대 CSV + JSON 기반 챗봇입니다.")
    print("종료하려면 '종료'를 입력하세요.")

    while True:
        try:
            user_question = input("\n질문 입력: ").strip()
        except KeyboardInterrupt:
            print("\n프로그램을 종료합니다.")
            break

        if user_question == "종료":
            print("프로그램을 종료합니다.")
            break

        if not user_question:
            print("질문을 입력해주세요.")
            continue

        result = answer_question(user_question)

        print("예측 category:", result["category"])
        print("판별 방식:", result["method"], "/ 점수:", round(result["score"], 4))
        print("답변:")
        print(strip_keyword_tag(result["answer"]))
