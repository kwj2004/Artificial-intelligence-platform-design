import streamlit as st
import base64
import time
import requests
import os
import subprocess
import sys

from streamlit.runtime.scriptrunner import get_script_run_ctx


if get_script_run_ctx() is None:
    subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])
    sys.exit()

# =========================================================
# 1. 페이지 설정
# =========================================================
st.set_page_config(page_title="EU-Bot: 을지대 스마트 비서", layout="wide")


# =========================================================
# 2. 로고 파일 Base64 인코딩 함수
# =========================================================
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None


# =========================================================
# 3. 커스텀 CSS
# =========================================================
st.markdown(
    """
    <style>
    .main {
        background-color: #ffffff;
    }

    [data-testid="stSidebar"] {
        background-color: #f0f4f9 !important;
        width: 300px !important;
    }

    .sidebar-title {
        font-size: 1.6rem;
        font-weight: 800;
        color: #1E3A8A !important;
        margin-bottom: 20px;
        margin-top: -30px;
    }

    .history-item {
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 5px;
        cursor: pointer;
        font-size: 0.9rem;
        color: #444746;
    }

    .history-item:hover {
        background-color: #e1e5ea;
    }

    .centered-box {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding-top: 10vh;
    }

    .logo-text-container {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 20px;
        gap: 15px;
    }

    .circular-logo {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        border: 2px solid #1E3A8A;
        background-color: white;
    }

    .main-title {
        margin: 0;
        color: #1E3A8A;
        font-size: 2.8rem;
        font-weight: bold;
    }

    .example-text {
        color: #70757a;
        font-size: 0.9rem;
        text-align: center;
        margin-top: 15px;
    }

    .source-box {
        font-size: 0.85rem;
        color: #555;
    }

    div[data-testid="stDialog"] div[role="dialog"] {
        border-radius: 20px;
        padding: 10px 12px;
        max-width: 625px;
    }

    div[data-testid="stDialog"] h2 {
        color: #111827;
        font-size: 1.7rem;
        font-weight: 800;
    }

    div[data-testid="stDialog"] h3 {
        color: #111827;
        font-size: 1.15rem;
        font-weight: 800;
    }
    /* 💡 도움말 박스 (라이트모드 기준) */
    .help-box { 
        background-color: rgba(30, 58, 138, 0.1); 
        color: #1E3A8A; 
        padding: 15px; 
        border-radius: 10px; 
        font-size: 0.85rem; 
        line-height: 1.5; 
    }

    /* ⚙️ 사이드바 설정 버튼 투명화 & 좌측 정렬 */
    [data-testid="stSidebar"] .stButton > button {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        justify-content: flex-start !important; 
        padding: 0.375rem 0.5rem !important;
        border-radius: 0.5rem !important;
        min-height: auto !important; 
        height: auto !important;
        margin-top: 0px !important;
    }
    [data-testid="stSidebar"] .stButton > button > div {
        justify-content: flex-start !important; 
        width: 100% !important;
        gap: 0.5rem !important;
    }
    [data-testid="stSidebar"] .stButton > button p {
        font-size: 1rem !important;
        text-align: left !important; 
        margin: 0 !important;
    }
    /* 라이트모드 버튼 호버 효과 */
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(151, 166, 195, 0.15) !important;
        color: #1E3A8A !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 4. 세션 상태 초기화
# =========================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        "2학년 1학기 전필 과목",
        "졸업 이수 학점 문의",
        "장학금 신청 방법",
    ]

if "model_type" not in st.session_state:
    st.session_state.model_type = "Naive Bayes (NB)"

if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Light"

if "word" not in st.session_state:
    st.session_state.word = ""

if "settings_open" not in st.session_state:
    st.session_state.settings_open = False

API_URL = os.getenv("EU_BOT_API_URL", "http://127.0.0.1:8000")

if st.session_state.theme_mode == "Dark":
    st.markdown(
        """
        <style>
        .stApp, [data-testid="stHeader"] { background-color: #0E1117 !important; color: #E0E0E0 !important; }
        
        /* 하단 바 전체 배경 (메인 배경과 동일하게) */
        [data-testid="stBottom"], [data-testid="stBottom"] > div { background-color: #0E1117 !important; }
        
        [data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid #30363d; }
        [data-testid="stSidebar"] * { color: #E0E0E0 !important; }
        .sidebar-title { color: #58A6FF !important; }
        .history-item { color: #C9D1D9 !important; background-color: #21262d; border: 1px solid #30363d; }
        
        /* 다크모드 도움말 박스 */
        .help-box { background-color: #1F2937 !important; color: #D1D5DB !important; border: 1px solid #374151; }
        
        /* 🔥 다크모드 채팅창 진짜 해결 CSS 🔥 */
        div[data-testid="stChatInput"] { background-color: #0E1117 !important; }
        
        div[data-testid="stChatInput"] > div { 
            background-color: #0E1117 !important; 
            border-radius: 15px !important; 
            border: 2px solid #58A6FF !important; 
            box-shadow: 0 0 10px rgba(88, 166, 255, 0.15) !important; 
        }
        
        div[data-testid="stChatInput"] div[data-baseweb="base-input"],
        div[data-testid="stChatInput"] div[data-baseweb="base-input"] > div {
            background-color: transparent !important;
        }
        
        div[data-testid="stChatInput"] textarea { 
            background-color: #0E1117 !important; 
            -webkit-text-fill-color: #FFFFFF !important; 
            color: #FFFFFF !important; 
            font-weight: 600 !important; 
            font-size: 1.05rem !important; 
        }
        
        div[data-testid="stChatInput"] textarea::placeholder { 
            color: #8B949E !important; 
            -webkit-text-fill-color: #8B949E !important;
            font-weight: normal !important; 
        }
        /* 🔥 전공 선택(Selectbox) 글자 강조 및 다크모드 최적화 🔥 */
        div[data-baseweb="select"] > div {
            background-color: #161B22 !important; /* 배경을 어둡게 */
            border: 1px solid #30363d !important; /* 테두리 색상 */
            border-radius: 8px !important;
        }
        
        /* 선택된 글자 강조 */
        div[data-baseweb="select"] span {
            color: #58A6FF !important; /* 글자색을 밝은 파란색으로 강조 */
            font-weight: 800 !important; /* 글자를 아주 굵게 */
            font-size: 1.05rem !important; /* 글자 크기 약간 키움 */
        }
        
        /* 드롭다운 메뉴(클릭 시 열리는 목록) 다크모드 처리 */
        ul[data-baseweb="menu"] {
            background-color: #161B22 !important;
        }
        ul[data-baseweb="menu"] li {
            color: #E0E0E0 !important;
        }
        ul[data-baseweb="menu"] li:hover {
            background-color: rgba(88, 166, 255, 0.15) !important;
            color: #FFFFFF !important;
        }
        
        div[data-testid="stChatInput"] button { background-color: transparent !important; color: #58A6FF !important; }
        div[data-testid="stChatInput"] button:hover { background-color: rgba(255, 255, 255, 0.1) !important; }
        
        .main-title { color: #58A6FF !important; }
        .example-text { color: #e5e7eb !important; }
        
        /* 다크모드 사이드바 설정 버튼 호버 */
        [data-testid="stSidebar"] .stButton > button:hover {
            background-color: rgba(255, 255, 255, 0.1) !important;
            color: #E0E0E0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def lookup_abbreviations(word=""):
    try:
        response = requests.get(
            f"{API_URL}/abbreviations",
            params={"word": word},
            timeout=5,
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        return []

    return []


def render_settings_panel():
    st.markdown("### 🎨 화면 테마")
    st.session_state.theme_mode = st.radio(
        "화면 테마",
        ["Light", "Dark"],
        key="theme_mode_radio",
        index=["Light", "Dark"].index(st.session_state.theme_mode),
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("### 📖 줄임말 사전 조회")
    st.session_state.word = st.text_input(
        "줄임말 입력",
        value=st.session_state.word,
        placeholder="예: 학고, 전필 등",
        key="word_input",
    ).strip()

    matches = lookup_abbreviations(st.session_state.word)
    if st.session_state.word:
        if matches:
            for item in matches[:8]:
                st.info(f"{item['abbr']} = {item['full_name']}")
        else:
            st.warning("일치하는 줄임말을 찾지 못했습니다.")

    with st.expander("›  전체 목록 보기"):
        all_words = lookup_abbreviations("")
        if all_words:
            for item in all_words:
                st.write(f"- **{item['abbr']}** = {item['full_name']}")
        else:
            st.write("API 서버를 먼저 실행해주세요.")

    if st.button("저장 및 닫기", use_container_width=True):
        st.session_state.theme_mode = st.session_state.theme_mode_radio
        st.session_state.settings_open = False
        st.rerun()


dialog = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)

if dialog:
    @dialog("⚙️ 환경 설정")
    def show_settings_dialog():
        render_settings_panel()


# =========================================================
# 5. 왼쪽 사이드바 구성
# =========================================================
with st.sidebar:
    st.markdown('<div class="sidebar-title">EU-Bot</div>', unsafe_allow_html=True)

    try:
        health = requests.get(f"{API_URL}/health", timeout=2).json()
        gemini_status = "Gemini ON" if health.get("gemini_enabled") else "로컬 DB"
        st.success(f"API 연결됨 ({gemini_status})")
    except Exception:
        st.warning("API 서버 대기 중")

    if st.button("🔄 대화 초기화"):
        st.session_state.messages = []
        st.session_state.chat_history = [
            "2학년 1학기 전필 과목",
            "졸업 이수 학점 문의",
            "장학금 신청 방법",
        ]
        st.rerun()

    st.markdown("**전공 선택**")
    dept = st.selectbox(
        "",
        ["빅데이터인공지능전공", "빅데이터의료융합학과", "의료IT학과", "첨단학부"],
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown("**최근 대화**")
    for chat in st.session_state.chat_history[:10]:
        st.markdown(f'<div class="history-item">💬 {chat}</div>', unsafe_allow_html=True)

    st.divider()

    # 💡 도움말 위젯 추가 구역
    st.markdown("**💡 도움말**")
    st.markdown('<div class="help-box"><b>EU-Bot 사용 가이드</b><br>• 학사 규정, 장학금 등을 질문하세요.<br>• 줄임말도 자동으로 인식합니다.</div>', unsafe_allow_html=True)
    
    st.markdown('<div style="height: 14px;"></div>', unsafe_allow_html=True)

    st.page_link("https://www.eulji.ac.kr", label="학교 홈페이지", icon="🏠")
    st.page_link("https://potal.eulji.ac.kr", label="을지대 포털", icon="🌐")
    st.page_link("https://lib.eulji.ac.kr", label="학술정보원(도서관)", icon="📚")

    st.write("")
    # 버튼에 type="tertiary" 인자를 추가하여 CSS가 정상적으로 스타일을 잡을 수 있게 바꿉니다.
    if st.button("⚙️ 설정", type="tertiary", use_container_width=True):
        st.session_state.settings_open = True

if st.session_state.settings_open:
    if dialog:
        show_settings_dialog()
    else:
        st.warning("현재 Streamlit 버전은 팝업 설정창을 지원하지 않아 아래에 설정을 표시합니다.")
        render_settings_panel()


# =========================================================
# 7. 메인 화면 출력
# =========================================================
if not st.session_state.messages:
    st.markdown('<div class="centered-box">', unsafe_allow_html=True)

    logo_base64 = get_base64_of_bin_file("을지대 로고.jpg")

    if logo_base64:
        logo_tag = f'<img src="data:image/jpeg;base64,{logo_base64}" class="circular-logo">'
    else:
        logo_tag = '<span style="font-size: 60px;">🎓</span>'

    st.markdown(
        f"""
        <div class="logo-text-container">
            {logo_tag}
            <h1 class="main-title">무엇을 도와드릴까요?</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="example-text">
            💡 <b>질문 예시:</b>
            "빅인 2학년 1학기 전필 과목" |
            "졸업 학점" |
            "장학금 신청"
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)

else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if "sources" in message and message["sources"]:
                with st.expander("📚 참고 출처 보기"):
                    for src in message["sources"]:
                        st.write(f"- {src}")


# =========================================================
# 8. 채팅 입력창
# =========================================================
prompt = st.chat_input("메시지를 입력하세요...")


# =========================================================
# 9. 메시지 처리 로직
# =========================================================
if prompt and isinstance(prompt, str) and prompt.strip() != "":
    prompt = prompt.strip()

    # 최근 대화 기록 업데이트
    if prompt not in st.session_state.chat_history:
        st.session_state.chat_history.insert(0, prompt)

    # 사용자 메시지 저장
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    # 사용자 메시지 바로 출력
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        res = requests.post(
            f"{API_URL}/chat",
            json={
                "question": prompt,
                "dept": dept,
                "model_type": st.session_state.model_type,
                "word": st.session_state.word,
            },
            timeout=300,
        )

        if res.status_code == 200:
            api_data = res.json()
            bot_response = api_data.get("answer", "답변을 불러오지 못했습니다.")
            sources = api_data.get("sources", [])
        else:
            bot_response = f"API 서버 오류가 발생했습니다. 상태 코드: {res.status_code}"
            sources = []

    except requests.exceptions.ConnectionError:
        bot_response = "API 서버에 연결할 수 없습니다. 먼저 FastAPI 서버를 실행해주세요."
        sources = []

    except requests.exceptions.Timeout:
        bot_response = "API 서버 응답 시간이 초과되었습니다. 다시 시도해주세요."
        sources = []

    except Exception as e:
        bot_response = f"오류가 발생했습니다: {e}"
        sources = []

    # AI 답변 출력
    full_response = bot_response

    with st.chat_message("assistant"):
        st.markdown(full_response)

        if sources:
            with st.expander("📚 참고 출처 보기"):
                for src in sources:
                    st.write(f"- {src}")

    # AI 답변 저장
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": full_response,
            "sources": sources,
        }
    )

    st.rerun()
