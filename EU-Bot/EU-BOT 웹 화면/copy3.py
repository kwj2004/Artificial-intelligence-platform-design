import streamlit as st
import base64
import time
import streamlit.components.v1 as components

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
        st.markdown(f'<div class="history-item">💬 {chat}</div>', unsafe_allow_html=True)
    st.divider()
    st.page_link("https://www.eulji.ac.kr", label="학교 홈페이지", icon="🏠")
    st.page_link("https://potal.eulji.ac.kr", label="을지대 포털", icon="🌐")
    st.page_link("https://lib.eulji.ac.kr", label="학술정보원(도서관)", icon="📚") 

# 4. 우측 상단 설정창
col_empty, col_setup = st.columns([0.88, 0.12])
with col_setup:
    with st.expander("⚙️ 설정"):
        model_type = st.radio("모델 선택", ["Naive Bayes (NB)", "Random Forest (RF)"])
        word = st.text_input("줄임말 사전", placeholder="학고, 교필 등")

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

# 7. 메시지 처리 로직 (완전 수정본)
if prompt and isinstance(prompt, str) and prompt.strip() != "":
    # 최근 대화 기록 업데이트
    if prompt not in st.session_state.chat_history:
        st.session_state.chat_history.insert(0, prompt)
    
    # 1. 유저 메시지 저장
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 2. AI 답변 생성 (이 블록 안에서 모든 것이 해결됩니다)
    mock_response = f"[{dept}] {model_type} 모델로 분석 중입니다. '{prompt}'에 대한 정보입니다."
    full_response = ""
    sources = ["을지대학교 학사관리규정", "2026 교육과정 가이드"]
    
    # 화면에 답변이 써지는 효과를 주기 위해 rerun 전에 한 번 출력
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        for chunk in mock_response.split():
            full_response += chunk + " "
            time.sleep(0.05)
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    
    # 3. 답변을 세션에 저장
    st.session_state.messages.append({
        "role": "assistant", 
        "content": full_response, 
        "sources": sources
    })
    
    # 4. 화면 갱신 (반드시 if문 안에서만!)
    st.rerun()