import streamlit as st
import base64
import time
import requests
import pandas as pd
import os

# 0. 줄임말 사전 로드 함수 (캐싱 적용)
@st.cache_data
def load_slang_dict(file_path):
    try:
        # 파일 존재 여부 확인 후 로드
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, encoding='utf-8') 
            return dict(zip(df['줄임말'], df['뜻']))
        else:
            return {"학고": "학사 경고", "교필": "교양 필수"}
    except Exception as e:
        return {"학고": "학사 경고", "교필": "교양 필수"}

SLANG_FILE = "EU-BOT Abbreviation dataset.csv"
slang_dict = load_slang_dict(SLANG_FILE)

# 1. 페이지 설정
st.set_page_config(page_title="EU-Bot: 을지대 스마트 비서", layout="wide")

def get_base64_of_bin_file(bin_file):
    try:
        if os.path.exists(bin_file):
            with open(bin_file, 'rb') as f:
                data = f.read()
            return base64.b64encode(data).decode()
        return None
    except:
        return None

# 2. 커스텀 CSS (기본 레이아웃 및 테마 색상 유지)
st.markdown("""
    <style>
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
if "model_type" not in st.session_state:
    st.session_state.model_type = "Naive Bayes (NB)"

# 3. 왼쪽 사이드바 구성
with st.sidebar:
    st.markdown('<div class="sidebar-title">EU-Bot</div>', unsafe_allow_html=True)
    st.markdown("**전공 선택**")
    dept = st.selectbox("전공", ["빅데이터인공지능전공", "빅데이터의료융합학과", "의료IT학과", "첨단학부"], label_visibility="collapsed")
    st.divider()
    st.markdown("**최근 대화**")
    for chat in st.session_state.chat_history[:5]:
        st.markdown(f'<div class="history-item"> {chat}</div>', unsafe_allow_html=True)
    
    st.divider()
    st.page_link("https://www.eulji.ac.kr", label="을지대학교 홈페이지", icon="🏠")
    st.page_link("https://eis.eu.ac.kr", label="을지대학교 eis", icon="🌐")
    st.page_link("https://lib.eulji.ac.kr", label="학술정보원(도서관)", icon="📚") 

# 4. 설정 팝업창
@st.dialog("⚙️ 환경 설정")
def show_settings():
    st.write("챗봇의 동작 모델과 사전을 설정합니다.")
    st.divider()
    st.session_state.model_type = st.radio(
        "모델 선택", 
        ["Naive Bayes (NB)", "Random Forest (RF)"],
        index=0 if st.session_state.model_type == "Naive Bayes (NB)" else 1
    )
    st.session_state.word_input = st.text_input("줄임말 사전 검색", placeholder="학고, 교필 등")
    if st.button("설정 저장"):
        st.rerun()

col_empty, col_setup = st.columns([0.94, 0.06])
with col_setup:
    if st.button("⚙️"):
        show_settings()

# 5. 메인 화면 구성
if not st.session_state.messages:
    st.markdown('<div class="centered-box">', unsafe_allow_html=True)
    logo_base64 = get_base64_of_bin_file('을지대 로고.jpg')
    logo_tag = f'<img src="data:image/jpeg;base64,{logo_base64}" class="circular-logo">' if logo_base64 else '🎓'
    
    st.markdown(f'<div class="logo-text-container">{logo_tag}<h1 class="main-title">무엇을 도와드릴까요?</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="example-text">💡 <b>질문 예시:</b> "빅인 2학년 1학기 전필 과목" | "졸업 학점" | "장학금 신청"</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# 이전 대화 기록 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message:
            with st.expander("📚 참고 출처 보기"):
                for src in message["sources"]:
                    st.write(f"- {src}")

# 6. 사용자 입력 및 백엔드 통신 로직 (Streamlit 공식 패턴)
if prompt := st.chat_input("메시지를 입력하세요..."):
    
    # 사용자 질문 화면에 표시 및 저장
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 히스토리 업데이트
    if prompt not in st.session_state.chat_history:
        st.session_state.chat_history.insert(0, prompt)

    # 줄임말 변환
    processed_prompt = prompt
    for k, v in slang_dict.items():
        if k in processed_prompt:
            processed_prompt = processed_prompt.replace(k, v)

    # 챗봇 답변 생성 및 화면 표시
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🔍 **EU-Bot이 분석 중입니다...**")
        
        try:
            # FastAPI 서버로 요청
            response = requests.post(
                "http://127.0.0.1:8000/chat",
                json={
                    "question": processed_prompt,
                    "dept": dept,
                    "model_type": st.session_state.get('model_type', "Naive Bayes (NB)")
                },
                timeout=15
            )
            response.raise_for_status()
            result = response.json()
            
            # 답변 파싱
            ans = result.get("answer", "답변을 생성하지 못했습니다.")
            srcs = result.get("sources", [])
            
            # 실시간 타이핑 효과
            full_ans = ""
            for chunk in ans.split(" "):
                full_ans += chunk + " "
                message_placeholder.markdown(full_ans + "▌")
                time.sleep(0.04)
            message_placeholder.markdown(ans)
            
            # 출처 표시
            if srcs:
                with st.expander("📚 참고 출처 보기"):
                    for src in srcs:
                        st.write(f"- {src}")
            
            # 답변 세션에 저장
            st.session_state.messages.append({"role": "assistant", "content": ans, "sources": srcs})
            
        except requests.exceptions.ConnectionError:
            err_msg = "⚠️ 백엔드 서버(FastAPI)가 실행 중인지 확인해주세요. (uvicorn api_server:app --reload)"
            message_placeholder.markdown(err_msg)
            st.session_state.messages.append({"role": "assistant", "content": err_msg})
        except Exception as e:
            err_msg = f"⚠️ 에러가 발생했습니다: {str(e)}"
            message_placeholder.markdown(err_msg)
            st.session_state.messages.append({"role": "assistant", "content": err_msg})