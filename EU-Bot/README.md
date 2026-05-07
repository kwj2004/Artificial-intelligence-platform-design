# EU-Bot Final Package

## Setup
```
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

## Run
```
python EU-Bot_임베딩_VectorDB.py
python EU-Bot_모델_학습_비교.py
```

## Files

| File | Description |
|------|-------------|
| EU-Bot_청크_데이터.json | RAG Vector DB input (369 chunks) |
| EU-Bot_통합_학습데이터.csv | NB/RF training data (3,602 questions) |
| EU-Bot_통합_RAG데이터.json | Full RAG dataset (369 articles) |
| EU-Bot_정답_데이터.json | Ground truth for RAG evaluation |
| EU-Bot_임베딩_VectorDB.py | Embedding + ChromaDB builder |
| EU-Bot_모델_학습_비교.py | NB vs RF model training + comparison |
| requirements.txt | Python dependencies |

## Data Sources
- Curriculum (4 programs, 279 chunks)
- Abbreviation dictionary (37 chunks)
- Graduation certification rules (22 chunks)
- Academic calendar (21 chunks)
- Professor info (8 chunks)
- Department contacts (2 chunks)
