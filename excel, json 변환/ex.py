import pandas as pd
import json

# 1. 설정: 엑셀 파일 경로 및 시트별 학과 정보 매핑
file_path = "의아, 빅융 교육과정.xlsx"
sheet_mapping = {
    "의아22교육과정": {"dept": "의료IT학과", "year": "22교육과정"},
    "빅융22교육과정": {"dept": "빅데이터의료융합학부", "year": "22교육과정"}
}

# 최종 JSON 구조 틀 잡기
knowledge_base = {
    "project": "EU-Bot 학사정보 비서",
    "version": "1.0",
    "description": "학과별 교육과정 및 과목 상세 정보 정답지 (컬럼 분리형)",
    "knowledge_base": {
        "function_1_curriculum_summaries": [],
        "function_2_subject_details": []
    }
}

try:
    for sheet_name, info in sheet_mapping.items():
        dept = info["dept"]
        year = info["year"]
        
        # 엑셀 파일 읽기
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        df = df.dropna(subset=['과목명']) 

        # ----------------------------------------------------
        # [기능 1] 학년/학기별 커리큘럼 요약 (Text Chunk)
        # ----------------------------------------------------
        grouped = df.groupby(['학년', '학기'])
        for (grade, semester), group in grouped:
            req_subjects = group[group['이수구분'] == '전공필수']['과목명'].tolist()
            sel_subjects = group[group['이수구분'] == '전공선택']['과목명'].tolist()
            
            req_str = f"'{', '.join(req_subjects)}' 총 {len(req_subjects)}과목" if req_subjects else "개설되지 않았습니다."
            sel_str = f"'{', '.join(sel_subjects)}' 총 {len(sel_subjects)}과목" if sel_subjects else "개설되지 않았습니다."
            
            summary_text = (
                f"[커리큘럼 요약] {dept}({sheet_name[:2]}) {year} {int(grade)}학년 {int(semester)}학기입니다. "
                f"전공필수 과목은 {req_str}으며, 전공선택은 {sel_str}입니다."
            )
            
            summary_dict = {
                "id": f"{sheet_name}_{int(grade)}_{int(semester)}",
                "dept": dept,
                "curriculum_year": year,
                "grade": int(grade),
                "semester": int(semester),
                "content": summary_text
            }
            knowledge_base["knowledge_base"]["function_1_curriculum_summaries"].append(summary_dict)

        # ----------------------------------------------------
        # [기능 2] 과목별 상세 정보 (요청하신 9개 컬럼 완벽 분리)
        # ----------------------------------------------------
        for _, row in df.iterrows():
            subject_dict = {
                "dept": dept,
                "year": year,
                "subject_name": row['과목명'],
                "full_data": {
                    "이수구분": row['이수구분'] if pd.notna(row['이수구분']) else "",
                    "학년": int(row['학년']) if pd.notna(row['학년']) else "",
                    "학기": int(row['학기']) if pd.notna(row['학기']) else "",
                    "코드": str(row['코드']).split('.')[0] if pd.notna(row['코드']) else "",
                    "과목명": row['과목명'] if pd.notna(row['과목명']) else "",
                    "학점": int(row['학점']) if pd.notna(row['학점']) else 0,
                    "이론": int(row['이론']) if pd.notna(row['이론']) else 0,
                    "실습": int(row['실습']) if pd.notna(row['실습']) else 0,
                    "성적방식": row['성적방식'] if pd.notna(row['성적방식']) else ""
                },
                "source": sheet_name
            }
            knowledge_base["knowledge_base"]["function_2_subject_details"].append(subject_dict)

    # 3. JSON 파일로 저장
    output_filename = "eu_bot_knowledge_base_separated.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(knowledge_base, f, indent=4, ensure_ascii=False)
        
    print(f"✅ 성공적으로 생성 완료! '{output_filename}' 파일을 확인해 주세요.")

except Exception as e:
    print(f"오류가 발생했습니다: {e}")