# GAIM Lab

**GINUE AI Microteaching Lab** - 예비교원 수업역량 강화 시스템

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![React](https://img.shields.io/badge/react-18+-61DAFB)
![License](https://img.shields.io/badge/license-Private-red)

## 📋 개요

GAIM Lab은 예비교원의 수업 역량을 분석하고 평가하는 AI 기반 시스템입니다. 수업 영상을 분석하여 7차원 평가 프레임워크에 따라 100점 만점으로 평가하고, 구체적인 피드백과 개선점을 제공합니다.

### 주요 기능

- 🎬 **영상 분석**: GPU 가속 FFmpeg를 활용한 고속 비디오 처리
- 👁️ **비전 분석**: 시선, 제스처, 자세 등 비언어적 요소 분석
- 🎤 **오디오 분석**: 음성, 발화 패턴, 억양 분석
- 📊 **7차원 평가**: 초등 임용 2차 수업실연 기준 기반 평가
- 📈 **포트폴리오**: 학습자별 성장 추적 및 시각화
- 🏅 **디지털 배지**: 성취 기반 배지 시스템
- 📋 **리포트 생성**: HTML/PDF 상세 보고서

## 🏗️ 프로젝트 구조

```
GAIM_Lab/
├── backend/              # FastAPI 백엔드
│   ├── app/
│   │   ├── api/          # REST API 엔드포인트
│   │   ├── core/         # 핵심 비즈니스 로직
│   │   └── services/     # 서비스 레이어
│   └── requirements.txt
├── frontend/             # React 프론트엔드
│   ├── src/
│   │   ├── components/   # 재사용 컴포넌트
│   │   └── pages/        # 페이지 컴포넌트
│   ├── e2e/              # E2E 테스트
│   └── package.json
├── core/                 # 분석 엔진
│   ├── agents/           # AI 에이전트
│   └── analyzers/        # 분석 모듈
├── docker/               # Docker 설정
└── run_sample_analysis.py
```

## 🚀 시작하기

### 필수 요구사항

- Python 3.9+
- Node.js 18+
- FFmpeg (GPU 가속 권장)

### 백엔드 설치

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 프론트엔드 설치

```bash
cd frontend
npm install
npm run dev
```

### 샘플 분석 실행

```bash
python run_sample_analysis.py [영상파일경로]
```

## 📊 7차원 평가 프레임워크

| 차원 | 배점 | 평가 영역 |
|------|------|-----------|
| 교수·학습 방법 | 20점 | 수업 전략, 교수법 |
| 학습 내용 | 15점 | 내용 정확성, 구조화 |
| 교수·학습 자료 | 10점 | 자료 활용도 |
| 학습자 상호작용 | 15점 | 참여 유도, 피드백 |
| 교사 언어 | 15점 | 발문, 설명력 |
| 비언어적 요소 | 10점 | 시선, 제스처, 자세 |
| 수업 분위기 | 15점 | 학습 환경 조성 |

## 🔗 API 엔드포인트

| 엔드포인트 | 설명 |
|------------|------|
| `POST /api/v1/analysis/upload` | 영상 업로드 |
| `POST /api/v1/analysis/analyze` | 분석 시작 |
| `GET /api/v1/analysis/{id}` | 분석 결과 조회 |
| `GET /api/v1/portfolio` | 포트폴리오 조회 |
| `GET /api/v1/badges` | 배지 목록 조회 |

## 🧪 테스트

```bash
# 프론트엔드 단위 테스트
cd frontend
npm test

# E2E 테스트
npm run test:e2e
```

## 📄 라이선스

Private - 무단 배포 금지

---

**경인교육대학교 GAIM Lab** | <educpa@ginue.ac.kr>
