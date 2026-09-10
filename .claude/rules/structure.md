# 파일 구조 규칙

## 디렉토리 역할
- `directives/` — 목표 및 도구 정의 SOP
- `.tmp/` — 중간 처리 파일 (임시)
- 최종 산출물 — Google Sheets 등 클라우드 서비스에 저장

## FILE_MANIFEST.md 관리
새 파일 생성 즉시 추가:
```
| 파일명 | 역할 |
|--------|------|
| main.py | 진입점, 전체 흐름 조율 |
```

## .env.sample 형식
```
# API 키 예시 (실제 값은 .env에 입력)
OPENAI_API_KEY=your_key_here
DATABASE_URL=your_db_url_here
```

## .gitignore 필수 항목
```
.env
.tmp/
__pycache__/
*.pyc
.DS_Store
```
