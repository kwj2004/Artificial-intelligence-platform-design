import streamlit as st
import base64
import time
import streamlit.components.v1 as components

import pandas as pd

# 0. 줄임말 사전 로드 함수
@st.cache_data # 매번 파일을 읽지 않도록 캐싱 처리
def load_slang_dict(file_path):
    try:
        # 을지대 관련 데이터인 만큼 UTF-8 또는 CP949 인코딩 확인 필요
        df = pd.read_csv(file_path, encoding='utf-8') 
        # { '학고': '학사 경고', '교필': '교양 필수' } 형태로 변환
        return dict(zip(df['줄임말'], df['뜻']))
    except Exception as e:
        st.error(f"사전 로드 실패: {e}")
        return {}

# 사전 파일 경로 (프로젝트 폴더 내 위치)
SLANG_FILE = "EU-BOT Abbreviation dataset.csv"
slang_dict = load_slang_dict(SLANG_FILE)
# 1. 페이지 설정
st.set_page_config(page_title="EU-Bot: 을지대 스마트 비서", layout="wide")

# 로고 파일을 Base64로 인코딩하는 함수
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

# 2. 커스텀 CSS
st.markdown("""
    <style>
         /* 우측 상단 버튼 배치 보정 */
div[data-testid="column"]:nth-child(2) button {
    background-color: transparent !important;
    border: none !important;
    font-size: 24px !important;
    padding: 0 !important;
    float: right;
}   
    .main { background-color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #f0f4f9 !important; width: 300px !important; }
    .sidebar-title { font-size: 1.6rem; font-weight: 800; color: #1E3A8A !important; margin-bottom: 20px; margin-top: -30px; }
    .history-item { padding: 10px; border-radius: 10px; margin-bottom: 5px; cursor: pointer; font-size: 0.9rem; color: #444746; }
    .history-item:hover { background-color: #e1e5ea; }
    .centered-box { display: flex; flex-direction: column; align-items: center; justify-content: center; padding-top: 10vh; }
    .logo-text-container { display: flex; align-items: center; justify-content: center; margin-bottom: 20px; gap: 15px; }
    .circular-logo { width: 80px; height: 80px; border-radius: 50%; border: 2px solid #1E3A8A; background-color: white; }
    .main-title { margin: 0; color: #1E3A8A; font-size: 2.8rem; font-weight: bold; }
    .example-text { color: #70757a; font-size: 0.85rem; text-align: center; margin-top: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = ["2학년 1학기 전필 과목", "졸업 이수 학점 문의", "장학금 신청 방법"]

# 3. 왼쪽 사이드바 구성
with st.sidebar:
    st.markdown('<div class="sidebar-title">EU-Bot</div>', unsafe_allow_html=True)
    st.markdown("**전공 선택**")
    dept = st.selectbox("", ["빅데이터인공지능전공", "빅데이터의료융합학과", "의료IT학과", "첨단학부"], label_visibility="collapsed")
    st.divider()
    st.markdown("**최근 대화**")
    for chat in st.session_state.chat_history:
        st.markdown(f'<div class="history-item"> {chat}</div>', unsafe_allow_html=True)
    for _ in range(3):
        st.write("")
    st.divider()
    st.page_link("https://www.eulji.ac.kr", label="을지대학교 홈페이지", icon="🏠")
    st.page_link("https://eis.eu.ac.kr", label="을지대학교 eis", icon="🌐")
    st.page_link("https://lib.eulji.ac.kr", label="학술정보원(도서관)", icon="📚") 

# 4-1. 설정 팝업창 함수 정의 (에러 수정본)
@st.dialog("⚙️ 환경 설정")
def show_settings():
    st.write("챗봇의 동작 모델과 사전을 설정합니다.")
    st.divider()
    
    # 1. 모델 선택 (세션 상태 유지)
    current_model = st.session_state.get('model_type', "Naive Bayes (NB)")
    model_idx = 0 if current_model == "Naive Bayes (NB)" else 1
    
    st.session_state.model_type = st.radio(
        "모델 선택", 
        ["Naive Bayes (NB)", "Random Forest (RF)"],
        index=model_idx
    )
    
    # 2. 줄임말 사전 검색 (에러가 발생했던 부분 수정)
    # 따옴표와 괄호가 정확히 닫히도록 한 줄로 작성하는 것이 안전합니다.
    st.session_state.word_input = st.text_input(
        "줄임말 사전 검색", 
        placeholder="학고, 교필 등",
        value=st.session_state.get('word_input', "")
    )
    
    st.divider()
    if st.button("설정 저장"):
        st.rerun()

# 4-2. 우측 상단 설정 아이콘 배치 (기존 영역)
col_empty, col_setup = st.columns([0.94, 0.06])
with col_setup:
    # 배경 투명 버튼 스타일 적용
    if st.button("⚙️"):
        show_settings()

# 5. 커스텀 채팅창 렌더링 함수
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

# 6. 메인 화면 및 채팅 시스템 통합
if not st.session_state.messages:
    st.markdown('<div class="centered-box">', unsafe_allow_html=True)
    logo_base64 = get_base64_of_bin_file('을지대 로고.jpg')
    logo_tag = f'<img src="data:image/jpeg;base64,{logo_base64}" class="circular-logo">' if logo_base64 else '<span style="font-size: 60px;">🎓</span>'
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

# 7. 메시지 처리 로직 (줄임말 변환 추가 버전)
if prompt and isinstance(prompt, str) and prompt.strip() != "":
    
    # [데이터 전처리] 줄임말 -> 정식 명칭 변환
    processed_prompt = prompt
    for 줄임말, 뜻 in slang_dict.items():
        if 줄임말 in processed_prompt:
            processed_prompt = processed_prompt.replace(줄임말, 뜻)
    
    # 1. 채팅 기록 업데이트 및 유저 메시지 저장
    if prompt not in st.session_state.chat_history:
        st.session_state.chat_history.insert(0, prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 2. AI 답변 생성 (변환된 processed_prompt를 기반으로 분석)
    # 나중에 RandomForest나 Naive Bayes 모델이 이 변환된 문장을 받게 됩니다.
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # 모델에게는 '학사 경고'로 변환된 문장을 전달하여 정확도를 높임
        mock_response = f"[{dept}] {model_type} 모델 분석: '{processed_prompt}'에 대한 정보입니다."
        
        for chunk in mock_response.split():
            full_response += chunk + " "
            time.sleep(0.05)
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    
    # 3. 답변 저장 및 갱신
    st.session_state.messages.append({
        "role": "assistant", 
        "content": full_response, 
        "sources": ["을지대 학사 사전", "CSV 데이터베이스"]
    })
    st.rerun()