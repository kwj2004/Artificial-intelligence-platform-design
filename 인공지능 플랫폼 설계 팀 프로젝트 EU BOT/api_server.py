from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import importlib.util
import os

# 🌟 1. 제미나이 라이브러리 추가
import google.generativeai as genai

# =========================================================
# 1. 모델 파이썬 파일 불러오기
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(BASE_DIR, "main.py")

spec = importlib.util.spec_from_file_location("eu_bot_model", MODEL_FILE)
eu_bot_model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eu_bot_model)


# =========================================================
# 2. FastAPI 및 제미나이 API 설정
# =========================================================
app = FastAPI(title="EU-Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🌟 2. 제미나이 API 키 및 모델 초기화
# 주의: 여기에 발급받은 실제 API 키를 넣으세요!
GEMINI_API_KEY = ""
genai.configure(api_key=GEMINI_API_KEY)
# 가장 빠르고 가벼운 1.5 Flash 모델 사용
llm_model = genai.GenerativeModel('gemini-2.5-flash') 


# =========================================================
# 3. 요청/응답 데이터 형식 (기존과 동일)
# =========================================================
class ChatRequest(BaseModel):
    question: str
    dept: str | None = None
    model_type: str | None = None

class ChatResponse(BaseModel):
    answer: str
    category: str
    score: float
    method: str
    sources: list[str]


@app.get("/")
def root():
    return {"message": "EU-Bot API 서버가 실행 중입니다.", "status": "ok"}


# =========================================================
# 5. 챗봇 답변 API (핵심 연동 부분)
# =========================================================
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    question = req.question.strip()

    if not question:
        return ChatResponse(
            answer="질문을 입력해주세요.", category="", score=0.0, method="empty", sources=[]
        )

    # 🌟 3. 자체 모델(main.py)에서 1차로 정확한 데이터베이스 텍스트 추출
    result = eu_bot_model.answer_question(question)
    raw_answer = result.get("answer", "")

    # 🌟 4. 제미나이 API를 호출하여 답변을 부드럽게 다듬기
    try:
        # 프롬프트(명령어) 작성: 챗봇의 페르소나와 제약사항 부여
        prompt = f"""
        당신은 을지대학교 학생들의 질문에 답변해주는 친절한 학사 지원 스마트 비서 'EU-Bot'입니다.
        아래 [검색된 정보]를 바탕으로 [사용자 질문]에 대한 답변을 자연스럽고 예의 바른 문장으로 작성해주세요.
        
        조건:
        1. [검색된 정보]에 없는 내용은 절대 지어내지 마세요.
        2. 가독성을 위해 적절히 줄바꿈이나 글머리 기호를 사용해주세요.
        3. 학생에게 도움이 될 만한 따뜻한 인사말이나 맺음말을 가볍게 덧붙여주세요.

        [사용자 질문]: {question}
        [검색된 정보]: {raw_answer}
        """
        
        # API 호출
        response = llm_model.generate_content(prompt)
        final_answer = response.text
        method_used = result.get("method", "") + " + Gemini_API" # 메소드 명시
        
    except Exception as e:
        # 만약 인터넷 연결 오류나 API 오류가 나면, 예비용으로 원본 텍스트를 그대로 반환 (안전장치)
        final_answer = raw_answer + "\n\n(⚠️ AI 응답 생성 지연으로 원본 데이터를 출력합니다.)"
        method_used = result.get("method", "")

    # 🌟 5. 최종 결과 반환
    return ChatResponse(
        answer=final_answer,
        category=result.get("category", ""),
        score=float(result.get("score", 0.0)),
        method=method_used,
        sources=[
            "EU-Bot_청크_데이터 수정.json",
            "EU-Bot_통합_학습데이터.csv"
        ]
    )