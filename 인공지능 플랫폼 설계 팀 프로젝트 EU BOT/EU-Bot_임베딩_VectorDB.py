"""
EU-Bot Embedding + Vector DB 구축 스크립트
===========================================
로컬에서 실행하세요!

필요 패키지:
  pip install sentence-transformers chromadb

실행:
  python embedding_vectordb.py
"""

import json
from sentence_transformers import SentenceTransformer
import chromadb

# ===== 설정 =====
EMBEDDING_MODEL = "jhgan/ko-sroberta-multitask"  # 한국어 특화 모델
COLLECTION_NAME = "eubot_knowledge"
CHROMA_DB_PATH = "./chroma_db"  # Vector DB 저장 경로
CHUNK_DATA_PATH = "./EU-Bot_청크_데이터.json"  # 청크 데이터 경로

print("=" * 60)
print("🚀 EU-Bot Embedding + Vector DB 구축")
print("=" * 60)

# ===== 1. 청크 데이터 로드 =====
with open(CHUNK_DATA_PATH, "r", encoding="utf-8") as f:
    chunk_data = json.load(f)

chunks = chunk_data["chunks"]
print(f"\n📄 청크 데이터 로드: {len(chunks)}개")

# ===== 2. 임베딩 모델 로드 =====
print(f"\n🤖 임베딩 모델 로드 중: {EMBEDDING_MODEL}")
model = SentenceTransformer(EMBEDDING_MODEL)
print(f"  ✅ 모델 로드 완료")

# ===== 3. 텍스트 임베딩 =====
texts = [c["text"] for c in chunks]
print(f"\n🔄 {len(texts)}개 청크 임베딩 중...")
embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
print(f"  ✅ 임베딩 완료: 벡터 차원 = {embeddings.shape[1]}")

# ===== 4. Chroma DB 저장 =====
print(f"\n💾 Vector DB 구축 중: {CHROMA_DB_PATH}")
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

# 기존 컬렉션 삭제 (재실행 시)
try:
    client.delete_collection(COLLECTION_NAME)
except:
    pass

collection = client.create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}  # 코사인 유사도
)

# 배치로 추가
BATCH_SIZE = 100
for i in range(0, len(chunks), BATCH_SIZE):
    batch = chunks[i:i+BATCH_SIZE]
    batch_embeddings = embeddings[i:i+BATCH_SIZE].tolist()
    
    ids = [c["chunk_id"] for c in batch]
    documents = [c["text"] for c in batch]
    metadatas = [{
        "source_id": c["source_id"],
        "document": c["document"],
        "article": c["article"],
        "title": c["title"],
        "category": c["category"],
        "page": c.get("page", 0),
        "start_date": c.get("start_date", ""),
        "end_date": c.get("end_date", ""),
        "place": c.get("place", ""),
    } for c in batch]
    
    collection.add(
        ids=ids,
        embeddings=batch_embeddings,
        documents=documents,
        metadatas=metadatas,
    )

print(f"  ✅ Vector DB 저장 완료: {collection.count()}개 벡터")

# ===== 5. 검색 테스트 =====
print(f"\n{'=' * 60}")
print(f"🔍 검색 테스트")
print(f"{'=' * 60}")

test_queries = [
    "졸업인증제 필수 분야가 뭐야?",
    "MT 언제야?",
    "이사 임기가 어떻게 돼?",
    "토익 몇 점이면 외국어 인증이 돼?",
    "중간고사 언제야?",
]

for query in test_queries:
    query_embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=3,
    )
    
    print(f"\n  Q: {query}")
    for j, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    )):
        similarity = 1 - dist  # 코사인 거리 → 유사도
        print(f"    [{j+1}] 유사도: {similarity:.3f} | {meta['document']} > {meta['article']}")
        print(f"        {doc[:80]}...")

print(f"\n{'=' * 60}")
print(f"✅ Vector DB 구축 완료!")
print(f"   저장 위치: {CHROMA_DB_PATH}")
print(f"   컬렉션명: {COLLECTION_NAME}")
print(f"   총 벡터: {collection.count()}개")
print(f"{'=' * 60}")
