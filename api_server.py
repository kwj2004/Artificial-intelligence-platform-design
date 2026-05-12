from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import importlib.util
import os


# =========================================================
# 1. 모델 파이썬 파일 불러오기
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(BASE_DIR, "eu_bot_csv_json_chatbot.py")

spec = importlib.util.spec_from_file_location("eu_bot_model", MODEL_FILE)
eu_bot_model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eu_bot_model)


# =========================================================
# 2. FastAPI 앱 생성
# =========================================================
app = FastAPI(title="EU-Bot API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# 3. 요청/응답 데이터 형식
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


# =========================================================
# 4. 상태 확인용 API
# =========================================================
@app.get("/")
def root():
    return {
        "message": "EU-Bot API 서버가 실행 중입니다.",
        "status": "ok"
    }


# =========================================================
# 5. 챗봇 답변 API
# =========================================================
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    question = req.question.strip()

    if not question:
        return ChatResponse(
            answer="질문을 입력해주세요.",
            category="",
            score=0.0,
            method="empty",
            sources=[]
        )

    result = eu_bot_model.answer_question(question)

    return ChatResponse(
        answer=result.get("answer", ""),
        category=result.get("category", ""),
        score=float(result.get("score", 0.0)),
        method=result.get("method", ""),
        sources=[
            "EU-Bot_청크_데이터 수정.json",
            "EU-Bot_통합_학습데이터.csv"
        ]
    )
