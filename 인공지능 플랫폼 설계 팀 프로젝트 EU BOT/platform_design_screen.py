import streamlit as st
import base64
import time
import requests  # FastAPI 통신을 위해 반드시 필요
import streamlit.components.v1 as components
import pandas as pd

# 0. 줄임말 사전 로드 함수 (기존 로직 유지)
@st.cache_data
def load_slang_dict(file_path):
    try:
        df = pd.read_csv(file_path, encoding='utf-8') 
        return dict(zip(df['줄임말'], df['뜻']))
    except Exception as e:
        return {}

# 사전 파일 경로
SLANG_FILE = "EU-BOT Abbreviation dataset.csv"
slang_dict = load_slang_dict(SLANG_FILE)

# 1. 페이지 설정
st.set_page_config(page_title="EU-Bot: 을지대 스마트 비서", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = ["2학년 1학기 전필 과목", "졸업 이수 학점 문의", "장학금 신청 방법"]

# 2. 로고 인코딩 및 커스텀 CSS
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #f0f4f9 !important; width: 300px !important; }
    .sidebar-title { font-size: 1.6rem; font-weight: 800; color: #1E3A8A !important; margin-bottom: 20px; margin-top: -30px; }
    .history-item { padding: 10px 15px; border-radius: 10px; margin-bottom: 5px; cursor: pointer; font-size: 0.9rem; color: #444746; }
    .history-item:hover { background-color: #e1e5ea; }
    .centered-box { display: flex; flex-direction: column; align-items: center; justify-content: center; padding-top: 10vh; }
    .logo-text-container { display: flex; align-items: center; justify-content: center; margin-bottom: 20px; gap: 15px; }
    .circular-logo { width: 80px; height: 80px; border-radius: 50%; border: 2px solid #1E3A8A; background-color: white; }
    .main-title { margin: 0; color: #1E3A8A; font-size: 2.8rem; font-weight: bold; }
    .example-text { color: #70757a; font-size: 0.85rem; text-align: center; margin-top: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 3. 사이드바 구성
with st.sidebar:
    st.markdown('<div class="sidebar-title">EU-Bot</div>', unsafe_allow_html=True)
    st.markdown("**전공 선택**")
    dept = st.selectbox("", ["빅데이터인공지능전공", "빅데이터의료융합학과", "의료IT학과", "첨단학부"], label_visibility="collapsed")
    st.divider()
    st.markdown("**최근 대화**")
    for chat in st.session_state.chat_history:
        st.markdown(f'<div class="history-item">{chat}</div>', unsafe_allow_html=True)
    st.divider()
    st.page_link("https://www.eulji.ac.kr", label="을지대학교 홈페이지", icon="🏠")
    st.page_link("https://eis.eu.ac.kr", label="을지대학교 eis", icon="🌐")
    st.page_link("https://lib.eulji.ac.kr", label="학술정보원(도서관)", icon="📚")

# 4. 설정 팝업창 (Dialog)
@st.dialog("⚙️ 환경 설정")
def show_settings():
    st.write("챗봇의 동작 모델을 설정합니다.")
    st.session_state.model_type = st.radio("모델 선택", ["Naive Bayes (NB)", "Random Forest (RF)"])
    if st.button("설정 저장"):
        st.rerun()

col_empty, col_setup = st.columns([0.94, 0.06])
with col_setup:
    if st.button("⚙️"):
        show_settings()

# 5. 커스텀 입력창 렌더링
def render_custom_input():
    chat_html = """
    <style>
        @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');
        .input-wrapper {
            display: flex; align-items: center; background: #ffffff;
            border: 1px solid #dfe1e5; border-radius: 32px;
            padding: 8px 18px; box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            width: 100%; max-width: 750px; margin: 0 auto;
        }
        .chat-input { flex: 1; border: none; outline: none; padding: 12px; font-size: 16px; background: transparent; }
        .icon-btn { color: #5f6368; cursor: pointer; padding: 8px; font-size: 19px; }
        .send-btn {
            background: #e8eaed; color: #5f6368; border-radius: 50%;
            width: 38px; height: 38px; display: flex; align-items: center; justify-content: center;
            transition: all 0.3s; margin-left: 5px;
        }
        .send-btn.active { background: #1E3A8A; color: white; cursor: pointer; }
    </style>
    <div class="input-wrapper">
        <i class="fa-solid fa-plus icon-btn"></i>
        <input type="text" id="userInput" class="chat-input" placeholder="메시지를 입력하세요..." oninput="onInp(this)" onkeypress="onKey(event)">
        <i class="fa-solid fa-microphone icon-btn" style="margin-right:8px;"></i>
        <div id="sendBtn" class="send-btn"><i class="fa-solid fa-arrow-up"></i></div>
    </div>
    <script>
        function onInp(el) {
            const b = document.getElementById('sendBtn');
            if(el.value.trim().length > 0) b.classList.add('active');
            else b.classList.remove('active');
        }
        function onKey(e) {
            if (e.key === 'Enter' && e.target.value.trim() !== "") {
                window.parent.postMessage({type: 'streamlit:setComponentValue', value: e.target.value}, '*');
                e.target.value = "";
            }
        }
    </script>
    """
    return components.html(chat_html, height=90)

# 6. 메인 화면 로직
if not st.session_state.messages:
    st.markdown('<div class="centered-box">', unsafe_allow_html=True)
    logo_base64 = get_base64_of_bin_file('을지대 로고.jpg')
    logo_tag = f'<img src="data:image/jpeg;base64,{logo_base64}" class="circular-logo">' if logo_base64 else '🎓'
    st.markdown(f'<div class="logo-text-container">{logo_tag}<h1 class="main-title">무엇을 도와드릴까요?</h1></div>', unsafe_allow_html=True)
    prompt = render_custom_input()
    st.markdown('<div class="example-text">💡 <b>질문 예시:</b> "빅인 2학년 1학기 전필 과목" | "졸업 학점" | "장학금 신청"</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message:
                with st.expander("📚 참고 출처 보기"):
                    for src in message["sources"]:
                        st.write(f"- {src}")
    
    st.markdown('<div style="height: 120px;"></div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div style="position: fixed; bottom: 30px; width: 60%; left: 33%; z-index: 100;">', unsafe_allow_html=True)
        prompt = render_custom_input()
        st.markdown('</div>', unsafe_allow_html=True)

# 7. 메시지 처리 및 FastAPI 연동 로직
if prompt and isinstance(prompt, str) and prompt.strip() != "":
    processed_prompt = prompt
    for slang, full_name in slang_dict.items():
        if slang in processed_prompt:
            processed_prompt = processed_prompt.replace(slang, full_name)
    
    if prompt not in st.session_state.chat_history:
        st.session_state.chat_history.insert(0, prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # FastAPI 통신 설정
        api_url = "http://127.0.0.1:8000/chat"
        payload = {
            "question": processed_prompt,
            "dept": dept,
            "model_type": st.session_state.get('model_type', "Naive Bayes (NB)")
        }
        
        try:
            # 팀원분이 설계한 API로 요청 전송
            response = requests.post(api_url, json=payload, timeout=15)
            response.raise_for_status()
            result = response.json()
            
            # API 응답 데이터 매핑
            full_response = result.get("answer", "답변을 생성할 수 없습니다.")
            sources = result.get("sources", [])
            score = result.get("score", 0.0)
            
            # 타이핑 효과
            typed_text = ""
            for chunk in full_response.split(" "):
                typed_text += chunk + " "
                time.sleep(0.04)
                message_placeholder.markdown(typed_text + "▌")
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            full_response = f"⚠️ 서버 연결 에러: {str(e)}"
            sources = ["FastAPI 서버 상태를 확인해주세요."]
            message_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response, "sources": sources})
    st.rerun()