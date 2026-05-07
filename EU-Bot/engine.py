import joblib
import chromadb
from sentence_transformers import SentenceTransformer
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os

# 1. 자원 로드 (서버 시작 시 한 번만 실행)
# NB 모델 및 벡터라이저 (test_model.py에서 학습 후 저장한 파일들)
nb_model = joblib.load("./models/intent_model.pkl") 
tfidf = joblib.load("./models/tfidf_vectorizer.pkl")

# 임베딩 모델 (NB/RF 비교 시 사용한 것과 동일한 모델)
embed_model = SentenceTransformer("jhgan/ko-sroberta-multitask")

# Chroma DB 연결
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection(name="eubot_knowledge")

# 줄임말 사전 (trans)
slang_dict = {
    "의아": "의료IT학과",
    "빅인": "빅데이터인공지능학과",
    "빅융": "빅데이터의료융합학부",
    "을지대": "을지대학교",
    "전기": "전공기초",
    "전필": "전공필수",
    "전선": "전공선택",
    "교필": "교양필수",
    "교선": "교양선택",
    "핵교": "핵심교양",
    "일교": "일반교양",
    "지클": "G-CLASS",
    "구클": "GOOGLE-CLASS",
    "LMS": "을지대학교 사이퍼캠퍼스",
    "뉴밀": "뉴밀레니엄센터",
    "인대생": "인성과대학생활",
    "인미설": "인성과미래설계",
    "공강": "강의 사이의 공백",
    "개총": "개강총회",
    "종총": "종강총회",
    "새터": "새내기 배움터",
    "과대": "과 대표",
    "과방": "학과방",
    "동방": "동아리방",
    "과사": "학과 사무실",
    "학식": "학생식당",
    "밥약": "밥 약속",
    "팀플": "팀 프로젝트",
    "복전": "복수전공",
    "중도": "중앙도서관",
    "강평": "강의 평가",
    "학고": "학사 경고",
    "과잠": "학과 점퍼",
    "과탑": "학과 성적 1등",
    "국장": "국가장학금",
    "중동": "중앙 동아리",
}

# LLM 설정 (OpenAI)
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# 2. 전처리 함수
def preprocess_text(text):
    for short, full in slang_dict.items():
        text = text.replace(short, full)
    return text

# 3. 메인 파이프라인 함수
def get_eu_bot_response(user_query):
    # STEP 1: 줄임말 변환
    clean_query = preprocess_text(user_query)
    
    # STEP 2: 의도 분류 (NB)
    query_vec = tfidf.transform([clean_query])
    category = nb_model.predict(query_vec)[0]
    prob = max(nb_model.predict_proba(query_vec)[0])
    
    # STEP 3: Vector DB 검색 (필터링 적용)
    query_embedding = embed_model.encode([clean_query]).tolist()
    
    # 분류 확률이 높을 경우 해당 카테고리 내에서만 검색
    if prob >= 0.5:
        search_results = collection.query(
            query_embeddings=query_embedding,
            n_results=3,
            where={"category": category} 
        )
    else:
        # 분류가 모호하면 전체 검색
        search_results = collection.query(
            query_embeddings=query_embedding,
            n_results=3
        )
    
    # STEP 4: 답변 생성 (RAG)
    context = "\n".join(search_results['documents'][0])
    
    template = """당신은 을지대학교 학사정보 스마트 비서 'EU-Bot'입니다. 
    제공된 [컨텍스트]를 바탕으로 학생의 질문에 친절하고 정확하게 답하세요.
    [컨텍스트]: {context}
    [질문]: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
    
    response = chain.invoke({"context": context, "question": clean_query})
    
    return {
        "answer": response.content,
        "intent": category,
        "sources": search_results['metadatas'][0]
    }

# 테스트 코딩임
if __name__ == "__main__":
    # 테스트 질문 (줄임말 포함)
    test_query = "의아 1학년 1학기 과목 알려줘" 
    
    print(f"--- 테스트 시작: {test_query} ---")
    response = get_eu_bot_response(test_query)
    
    print(f"분류된 카테고리: {response['intent']}")
    print(f"답변: {response['answer']}")