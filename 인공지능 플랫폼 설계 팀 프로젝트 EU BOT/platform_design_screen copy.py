import streamlit as st
import base64
import time

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

# 2. 커스텀 CSS (제미나이 스타일 내비게이션 및 레이아웃)
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background-color: #f0f4f9 !important;
        width: 300px !important;
    }
    
    /* 사이드바 텍스트 가독성 */
    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {
        color: #1f1f1f !important;
        font-weight: 500;
    }

    .sidebar-title {
        font-size: 1.6rem;
        font-weight: 800;
        color: #1E3A8A !important;
        margin-bottom: 20px;
        margin-top: -30px;
    }

    /* 채팅 기록 스타일 (Gemini 스타일) */
    .history-item {
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 5px;
        cursor: pointer;
        font-size: 0.9rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        color: #444746;
    }
    .history-item:hover {
        background-color: #e1e5ea;
    }

    /* 하단 고정 바로가기 스타일 */
    .sidebar-bottom {
        position: absolute;
        bottom: 20px;
        width: 100%;
    }

    /* 메인 타이틀 디자인 */
    .logo-text-container { 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        margin-bottom: 10px; 
        gap: 15px;
    }
    .circular-logo {
        width: 60px; height: 60px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #1E3A8A;
        background-color: white;
    }
    .main-title {
        margin: 0; color: #1E3A8A; 
        font-size: 2.5rem; font-weight: bold;
    }
    .example-text { 
        color: #70757a; font-size: 0.85rem; 
        text-align: center; margin-top: 10px; 
    }
    </style>
    """, unsafe_allow_html=True)

# 세션 상태 초기화 (메시지 및 대화 기록)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    # 예시 기록 (실제로는 질문 시 여기에 추가됨)
    st.session_state.chat_history = ["2학년 1학기 전필 과목", "졸업 이수 학점 문의", "장학금 신청 방법"]

# 3. 왼쪽 사이드바 구성
with st.sidebar:
    st.markdown('<div class="sidebar-title">EU-Bot</div>', unsafe_allow_html=True)
    
    # 3-1. 전공 선택
    st.markdown("**전공 선택**")
    dept = st.selectbox("", ["빅데이터인공지능전공", "빅데이터의료융합학과", "의료IT학과", "첨단학부"], label_visibility="collapsed")
    
    st.divider()

    # 3-2. 채팅 기록 영역 (Gemini처럼 위쪽에 배치)
    st.markdown("**최근 대화**")
    for chat in st.session_state.chat_history:
        st.markdown(f'<div class="history-item">💬 {chat}</div>', unsafe_allow_html=True)

    # 3-3. 하단 바로가기 영역 (가장 아래로 이동)
    # Streamlit은 상단부터 쌓이므로 공간을 띄워 하단 느낌을 줍니다.
    st.write("") # 간격 조절용
    st.write("") 
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")


    st.divider()
    st.markdown("### 🔗 바로가기")
    st.page_link("https://www.eulji.ac.kr", label="학교 홈페이지", icon="🏠")
    st.page_link("https://potal.eulji.ac.kr", label="을지대 포털", icon="🌐")
    # 사용자가 추가할 수 있는 한 줄 공간 (예시)
    st.page_link("https://lib.eulji.ac.kr", label="학술정보원(도서관)", icon="📚") 

# 4. 우측 상단 설정창 (모델 및 줄임말 사전)
col_title, col_setup = st.columns([0.88, 0.12])

with col_setup:
    with st.expander("⚙️ 설정"):
        st.markdown("**🤖 모델 선택**")
        model_type = st.radio("", ["Naive Bayes (NB)", "Random Forest (RF)"], label_visibility="collapsed")
        
        st.divider()
        st.markdown("**🔍 줄임말 사전**")
        word = st.text_input("", placeholder="학고, 교필 등", label_visibility="collapsed", key="slang_input")
        if word == "학고":
            st.info("✅ 학사 경고")
        elif word == "교필":
            st.info("✅ 교양 필수")

# 5. 메인 타이틀 영역
with col_title:
    logo_base64 = get_base64_of_bin_file('을지대 로고.jpg')
    if logo_base64:
        logo_html = f'<img src="data:image/jpeg;base64,{logo_base64}" class="circular-logo">'
    else:
        logo_html = '<span style="font-size: 45px;">🎓</span>' 

    st.markdown(
        f"""
        <div class="logo-text-container">
            {logo_html}
            <h1 class="main-title">학생을 위한 EU챗봇</h1>
        </div>
        """, 
        unsafe_allow_html=True
    )

# 6. 채팅 시스템
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message:
            with st.expander("📚 참고 출처 보기"):
                for src in message["sources"]:
                    st.write(f"- {src}")

if prompt := st.chat_input("질문을 입력하세요..."):
    # 1. 채팅 기록(History) 리스트 맨 앞에 추가
    if prompt not in st.session_state.chat_history:
        st.session_state.chat_history.insert(0, prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        mock_response = f"[{dept}] {model_type} 모델로 분석 중입니다. '{prompt}'에 대한 정보입니다."
        
        for chunk in mock_response.split():
            full_response += chunk + " "
            time.sleep(0.05)
            message_placeholder.markdown(full_response + "▌")
        
        sources = ["을지대학교 학사관리규정", "2026 교육과정 가이드"]
        message_placeholder.markdown(full_response)
        with st.expander("📚 참고 출처 보기"):
            for src in sources:
                st.write(f"- {src}")
        
    st.session_state.messages.append({"role": "assistant", "content": full_response, "sources": sources})

st.markdown("""
    <div class="example-text">
        💡 <b>질문 예시:</b> "빅인 2학년 1학기 전필 과목" | "졸업 학점이 몇 점이야?" | "장학금 종류 알려줘"
    </div>
    """, unsafe_allow_html=True)