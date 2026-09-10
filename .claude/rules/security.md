# 환경 및 보안 규칙

## API 키 관리
- 실제 키: `.env` 파일에 저장, `.gitignore`로 제외
- 형식 예시: `.env.sample` 파일로 제공
- 코드에 자격증명 직접 노출 절대 금지

## 의존성 관리
변경 시 항상 업데이트:
- Python: `requirements.txt`
- Node: `package.json`
- 문서: `README.md`

## 실행 명령어
`README.md`에 "바로 실행 가능한" 명령어 명시:
- Python: `python main.py`
- Flutter: 빌드 아티팩트 경로
- 환경별 실행 방법 포함

## OS 독립성
- 각 OS에서 독립적으로 실행 가능하도록 구성
- 절대 경로 사용 지양, 상대 경로 또는 환경변수 활용
