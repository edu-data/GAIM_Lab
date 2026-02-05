# 🎓 GAIM Lab

**GINUE AI Microteaching Lab** - 예비교원 수업역량 AI 분석 플랫폼

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![React](https://img.shields.io/badge/react-18+-61DAFB)
![FastAPI](https://img.shields.io/badge/fastapi-0.100+-009688)

---

## 📊 분석 결과

| 보고서 | 설명 |
|--------|------|
| [📋 종합 평가 보고서](https://edu-data.github.io/GAIM_Lab/comprehensive_report.html) | 2025-12-09 수업 시연 18개 영상 분석 |
| [🌐 GAIM Lab 웹사이트](https://edu-data.github.io/GAIM_Lab/) | 시스템 소개 및 데모 |

---

## 📋 개요

GAIM Lab은 **AI 기반 수업 분석 시스템**으로, 예비교원의 수업 영상을 분석하여 7차원 평가 프레임워크에 따라 100점 만점으로 평가합니다. 초등학교 교사 임용 2차 수업실연 기준을 기반으로 구체적인 피드백과 개선점을 제공합니다.

### ✨ 핵심 기능

| 기능 | 설명 |
|------|------|
| 🎬 **영상 분석** | GPU 가속 FFmpeg를 활용한 고속 비디오 처리 |
| 👁️ **비전 분석** | 시선, 제스처, 자세 등 비언어적 요소 분석 |
| 🎤 **오디오 분석** | 음성 인식, 발화 속도, 억양 패턴 분석 |
| 📊 **7차원 평가** | 초등 임용 2차 수업실연 기준 기반 자동 평가 |
| 📦 **일괄 분석** | 다수 영상 배치 처리 및 CSV 리포트 생성 |
| 📈 **포트폴리오** | 학습자별 성장 추적 및 시각화 |
| 🏅 **디지털 배지** | 성취 기반 배지 발급 시스템 |
| 📋 **리포트** | HTML/PDF 상세 보고서 자동 생성 |

---

## 🎯 7차원 평가 프레임워크

초등학교 임용 2차 수업실연 평가 기준을 기반으로 한 100점 만점 평가 체계:

| 차원 | 배점 | 평가 영역 |
|------|:----:|-----------|
| 수업 전문성 | 20점 | 학습목표 명료성, 학습내용 충실성 |
| 교수학습 방법 | 20점 | 교수법 다양성, 학습활동 효과성 |
| 판서 및 언어 | 15점 | 판서 가독성, 언어 명료성, 발화속도 |
| 수업 태도 | 15점 | 교사 열정, 학생 소통, 자신감 |
| 학생 참여 | 15점 | 질문 기법, 피드백 제공 |
| 시간 배분 | 10점 | 수업 단계별 시간 균형 |
| 창의성 | 5점 | 수업 기법의 창의성 |

---

## 🏗️ 시스템 구조

```
GAIM_Lab/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── api/            # REST API 엔드포인트
│   │   ├── core/           # 핵심 비즈니스 로직
│   │   └── services/       # 서비스 레이어 (평가, 리포트)
│   └── requirements.txt
├── frontend/                # React 프론트엔드
│   ├── src/
│   │   ├── components/     # 재사용 컴포넌트
│   │   └── pages/          # 페이지 (Dashboard, BatchAnalysis 등)
│   └── package.json
├── core/                    # 분석 엔진
│   ├── agents/             # AI 에이전트
│   └── analyzers/          # TimeLapse, Audio, Vision 분석 모듈
├── docs/                    # GitHub Pages 문서
├── output/                  # 분석 결과 출력
├── batch_analysis.py        # 일괄 분석 스크립트
└── run_sample_analysis.py   # 단일 영상 분석 스크립트
```

---

## 🚀 시작하기

### 필수 요구사항

- Python 3.9+
- Node.js 18+
- FFmpeg (GPU 가속 권장)
- Google Gemini API Key

### Backend 설치

```bash
cd backend
pip install -r requirements.txt

# 환경변수 설정
export GOOGLE_API_KEY="your-gemini-api-key"

# 서버 실행
uvicorn app.main:app --reload --port 8000
```

### Frontend 설치

```bash
cd frontend
npm install
npm run dev
```

### 단일 영상 분석

```bash
python run_sample_analysis.py video/sample.mp4
```

### 일괄 분석

```bash
# 전체 영상 분석
python batch_analysis.py

# 개수 제한
python batch_analysis.py --limit 5
```

---

## 🔗 API 엔드포인트

| Method | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/api/v1/analysis/upload` | 영상 업로드 |
| POST | `/api/v1/analysis/analyze` | 분석 시작 |
| GET | `/api/v1/analysis/{id}` | 분석 결과 조회 |
| GET | `/api/v1/analysis/batch/videos` | 배치 영상 목록 |
| POST | `/api/v1/analysis/batch/start` | 배치 분석 시작 |
| GET | `/api/v1/analysis/batch/{id}` | 배치 상태 조회 |
| GET | `/api/v1/portfolio` | 포트폴리오 조회 |
| GET | `/api/v1/badges` | 디지털 배지 목록 |

---

## 🧪 테스트

```bash
# Frontend 단위 테스트
cd frontend && npm test

# E2E 테스트
npm run test:e2e
```

---

## 📈 최근 분석 결과

**2025-12-09 수업 시연 데이터** (18개 영상)

- 📊 평균 점수: **15.0점** / 100점
- 🏆 최고 점수: **18.8점** (20251209_154506.mp4)
- ⏱️ 평균 처리 시간: **78.5초** / 영상
- ✅ 성공률: **100%**

[👉 전체 결과 보기](https://edu-data.github.io/GAIM_Lab/comprehensive_report.html)

---

## 📄 라이선스

Private - 경인교육대학교 연구용

---

**경인교육대학교 GAIM Lab** | <educpa@ginue.ac.kr>
