import streamlit as st
import base64
import time

# 1. 페이지 설정 및 테마 (조건 5: 챗봇 느낌의 색상 테마)
st.set_page_config(page_title="EU-Bot: 을지대 스마트 비서", layout="wide")

# 로고 파일을 Base64로 인코딩하는 함수 (로고와 텍스트를 한 줄에 배치하기 위함)
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

# 커스텀 CSS (UI 디자인 보완)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    .example-text { color: #6c757d; font-size: 0.85rem; text-align: center; margin-top: -10px; padding-bottom: 20px; }
    .logo-text-container { display: flex; align-items: center; justify-content: center; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 사이드바 구성 (제안서 5.1 및 71번 항목 반영 [cite: 67, 71])
with st.sidebar:
    st.title(" EU-Bot")
    st.info("RAG 기반 을지대학교 학사정보 스마트 비서")
    
    # 학과 선택 드롭다운 [cite: 62, 67]
    dept = st.selectbox("소속 학과를 선택하세요", ["빅데이터인공지능전공", "빅데이터의료융합학과", "의료IT학과", "첨단학부"])
    
    st.divider()
    st.markdown("### 🔗 주요 링크 바로가기")
    st.page_link("https://www.eulji.ac.kr", label="을지대학교 홈페이지", icon="🏫")
    st.page_link("https://potal.eulji.ac.kr", label="을지대 포털 (성적/수강신청)", icon="💻")
    
    # 모델 선택 (제안서 3.2 파이프라인 비교 반영 [cite: 47, 53])
    st.divider()
    st.markdown("### ⚙️ 모델 설정 (테스트)")
    model_type = st.radio("의도 분류 모델 선택", ["Naive Bayes (NB)", "Random Forest (RF)"])

# 3. 메인 영역 구성 (조건 1, 2: 로고 + 타이틀 한 줄 배치)
logo_base64 = get_base64_of_bin_file('을지대 로고.jpg') # 실제 로고 파일명으로 수정하세요.
if logo_base64:
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" width="50" style="margin-right: 15px;">'
else:
    logo_html = '<span style="font-size: 40px; margin-right: 15px;">🎓</span>' # 로고 파일 없을 시 대체 아이콘

st.markdown(
    f"""
    <div class="logo-text-container">
        {logo_html}
        <h1 style="margin: 0; color: #1E3A8A;">학생을 위한 EU챗봇</h1>
    </div>
    """, 
    unsafe_allow_html=True
)
st.markdown("<p style='text-align: center; color: #666;'>학칙, 졸업 요건, 장학금 정보를 인공지능이 알려드립니다.</p>", unsafe_allow_html=True)

# 대화 이력 저장용 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 대화 이력 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message: # 출처 표시 [cite: 69, 73]
            with st.expander("📚 참고 출처 보기"):
                for src in message["sources"]:
                    st.write(f"- {src}")

# 4. 채팅 입력창 및 질문 예시 (조건 3, 6 반영)
if prompt := st.chat_input("질문을 입력하세요..."):
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 챗봇 응답 생성 (추후 백엔드 API /ask 엔드포인트와 연결 )
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # 가상 응답 (API 연결 전 프론트엔드 확인용)
        mock_response = f"[{dept}] 관련 답변입니다. 현재 {model_type} 모델을 통해 의도를 분류하고 관련 규정을 찾고 있습니다. 질문하신 '{prompt}'에 대한 정확한 규정을 확인 중입니다."
        
        for chunk in mock_response.split():
            full_response += chunk + " "
            time.sleep(0.05)
            message_placeholder.markdown(full_response + "▌")
        
        # 가상의 출처 데이터 (RAG Source Tagging [cite: 74, 75])
        sources = ["을지대학교 학사관리규정 제34조 (학사경고)", "2026학년도 빅데이터인공지능전공 교육과정표"]
        message_placeholder.markdown(full_response)
        
        with st.expander("📚 참고 출처 보기"):
            for src in sources:
                st.write(f"- {src}")
        
    st.session_state.messages.append({"role": "assistant", "content": full_response, "sources": sources})

# 채팅창 하단 질문 예시 (조건 3)
st.markdown("""
    <div class="example-text">
        💡 <b>질문 예시:</b> "빅인 2학년 1학기 전공필수 과목 알려주세요" | "대체 과목 알려주세요" | "장학금 지급 기준이 뭐야?"
    </div>
    """, unsafe_allow_html=True)

# 5. 줄임말 번역기 및 추가 시각화 (제안서 5.1, 6.2 반영 [cite: 68, 80])
st.divider()
col1, col2 = st.columns(2)

with col1:
    st.subheader("🔍 캠퍼스 줄임말 사전")
    word = st.text_input("줄임말을 입력하면 정식 명칭을 알려드려요.", placeholder="예: 학고, 교필")
    if word == "학고":
        st.success("**정식 명칭:** 학사 경고")
    elif word == "교필":
        st.success("**정식 명칭:** 교양 필수")

with col2:
    st.subheader("📊 RAG 검색 관련도")
    # 제안서의 시각화 기능 예시 (유사도 바 차트 [cite: 80])
    st.progress(85, text="문서 유사도: 85%")