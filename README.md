# 🤖 MAS — Multi-Agent System for Class Analysis

**멀티 에이전트 수업 분석 시스템** · 8개 AI 에이전트가 협업하여 수업 영상을 7차원 평가하는 플랫폼

[![Version](https://img.shields.io/badge/version-8.2.0-7c3aed)](https://github.com/edu-data/GAIM_Lab/releases)
[![Python](https://img.shields.io/badge/python-3.9+-3776AB)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React_18-61DAFB)](https://react.dev)
[![Gemini](https://img.shields.io/badge/Gemini_AI-4285F4)](https://ai.google.dev)
[![pyannote](https://img.shields.io/badge/pyannote.audio-FF6F00)](https://github.com/pyannote/pyannote-audio)
[![PWA](https://img.shields.io/badge/PWA-ready-5A0FC8)](https://web.dev/progressive-web-apps/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

<p align="center">
  <a href="https://edu-data.github.io/GAIM_Lab/app/"><strong>🌐 홈페이지</strong></a> ·
  <a href="https://edu-data.github.io/GAIM_Lab/app/#/dashboard"><strong>📊 대시보드</strong></a> ·
  <a href="https://edu-data.github.io/GAIM_Lab/app/#/live"><strong>🔴 실시간 코칭</strong></a> ·
  <a href="https://github.com/edu-data/GAIM_Lab/releases"><strong>📦 릴리스</strong></a>
</p>

> **🆕 v8.2** — GitHub Pages 풀스택 · Gemini 실시간 코칭 · 클라이언트 인증
>
> - 🔴 **실시간 코칭 7차원 Gemini 평가**: 세션 종료 시 Gemini AI가 교원임용 7차원 분석
> - 🔐 **클라이언트 인증**: GitHub Pages에서 로그인·회원가입·관리자 기능 (SHA-256)
> - 📊 **클라이언트 배치/코호트 분석**: 백엔드 없이 Gemini API로 연구 도구 완전 작동
> - 📈 **통계 모듈**: Welch's t-test, Cohen's d, Satterthwaite df 직접 구현
> - 📄 **포트폴리오 PDF**: A4 인쇄용 성장 보고서 생성

---

## 🎯 프로젝트 소개

MAS(Multi-Agent System)는 **예비교원의 수업 영상**을 8개 전문화된 AI 에이전트가 **병렬·순차 파이프라인**으로 분석하여, 초등학교 임용 2차 수업실연 기준에 따라 **7차원 100점 만점**으로 자동 평가하는 시스템입니다.

### 주요 성과

| 지표 | 결과 |
| ---- | ---- |
| ✅ 분석 성공률 | **18/18 (100%)** |
| 📊 평균 점수 | **76.1점 (C+등급)** |
| 🏆 최고 점수 | **84점 (B등급, 20251209_110545)** |
| 📉 최저 점수 | **67점 (D+등급, 20251209_153522)** |
| 📊 등급 분포 | **B×5 · C+×4 · C×7 · D+×1** |
| ⏱️ 영상당 처리 | **~1.5분 (TURBO MODE v3)** |
| 🤖 에이전트 수 | **8개** |
| 📐 평가 차원 | **7개 (전체 Gemini LLM v8.0)** |
| 🗣️ 화자 분리 | **pyannote 3.3 (v5.0+)** |
| 🔬 신뢰도 분석 | **Test-Retest r=0.68, ±5pt 일치 82.6%** |
| 🗄️ 데이터 영속성 | **SQLite DB auto-save (v7.0)** |
| 🎬 클라이언트 분석 | **브라우저 직접 분석 가능 (v8.0 NEW)** |
| 🔴 실시간 코칭 | **Gemini 7차원 평가 + 라이브 피드백 (v8.2)** |
| 🧪 A/B 실험 | **루브릭 비교 실험 (v7.1)** |
| 📱 PWA | **오프라인 접근, 설치 가능 (v7.1)** |

---

## 🔗 에이전트 파이프라인

```
┌─────────────┐
│  Extractor   │  GPU 가속 FFmpeg 프레임/오디오 추출
└──────┬──────┘
       │
  ┌────┴────────────────────────┐
  │         병렬 실행             │
  ├──────────┬─────────┬────────┤
  │ Vision   │ Content │  STT   │  시각/콘텐츠/음성 분석
  │ Agent    │ Agent   │ Agent  │
  └────┬─────┴────┬────┴───┬───┘
       └──────────┼────────┘
                  │
          ┌───────┴───────┐
          │  Vibe Agent   │  프로소디(억양·속도·에너지) 분석
          └───────┬───────┘
          ┌───────┴───────┐
          │ Pedagogy Agent│  교육학 7차원 체계적 평가
          └───────┬───────┘
          ┌───────┴───────┐
          │ Feedback Agent│  LLM + 규칙 기반 맞춤형 피드백
          └───────┬───────┘
          ┌───────┴───────┐
          │ Master Agent  │  종합 보고서 생성
          └───────────────┘
```

---

## 🤖 8개 AI 에이전트

| # | 에이전트 | 역할 | 핵심 기술 |
| - | ------- | ---- | -------- |
| 1 | **Extractor** | 영상에서 프레임·오디오 초고속 추출 | FFmpeg CUDA, GPU 가속 |
| 2 | **Vision** | 교사 시선, 제스처, 자세 비언어적 분석 | OpenCV, Gemini Vision |
| 3 | **Content** | 판서, 교수자료, 멀티미디어 콘텐츠 분석 | Gemini AI |
| 4 | **STT** | 음성→텍스트 변환, 화자 분리, 한국어 필러 감지 | OpenAI Whisper, pyannote.audio |
| 5 | **Vibe** | 음성 프로소디(억양·속도·에너지) 분석 | Librosa |
| 6 | **Pedagogy** | 교육학 이론 기반 7차원 체계적 평가 | RAG + Gemini |
| 7 | **Feedback** | 개인 맞춤형 피드백·액션 플랜 생성 | LLM + Rule Engine |
| 8 | **Master** | 전체 결과 종합, 최종 보고서 생성 | Gemini AI |

---

## 📐 7차원 평가 프레임워크

초등학교 임용 2차 수업실연 평가 기준 기반 **100점 만점** 체계:

| 차원 | 배점 | 평가 영역 |
| ---- | :--: | -------- |
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
MAS/
├── core/                        # 🧠 분석 엔진
│   ├── agents/                  # 8개 AI 에이전트
│   │   ├── orchestrator.py      # AgentOrchestrator v7 (Pydantic 계약)
│   │   ├── vision_agent.py      # 비전 분석
│   │   ├── content_agent.py     # 콘텐츠 분석
│   │   ├── stt_agent.py         # 음성 인식
│   │   ├── vibe_agent.py        # 프로소디 분석
│   │   ├── pedagogy_agent.py    # 교육학 평가 v7 (구간화 채점)
│   │   ├── feedback_agent.py    # 피드백 생성
│   │   └── master_agent.py      # 종합 보고서
│   ├── database.py              # 🗄️ SQLite CRUD (v7.0)
│   ├── growth_analyzer.py       # 📈 성장 경로 + 로드맵 (v7.1)
│   └── analyzers/               # 기반 분석 모듈
│       ├── timelapse_analyzer.py # FFmpeg 프레임 추출
│       └── audio_analyzer.py    # 오디오 처리
├── backend/                     # ⚡ FastAPI 백엔드
│   └── app/
│       ├── api/                 # REST API
│       │   ├── auth.py          # 👤 Google OAuth + JWT (v7.1 NEW)
│       │   ├── cohort.py        # 📊 코호트 비교 분석 (v7.1 NEW)
│       │   ├── live_coaching.py # 🔴 WebSocket 실시간 코칭 (v7.1 NEW)
│       │   └── rubric_experiment.py # 🧪 A/B 루브릭 실험 (v7.1 NEW)
│       ├── core/                # RAG, Gemini 평가기
│       └── services/            # 리포트 생성
├── frontend/                    # 💻 React 18 + Vite + PWA
│   ├── public/                  # 📱 manifest.json, SW (v7.1 NEW)
│   └── src/
│       ├── App.jsx              # 🧭 사이드바 레이아웃 + 라우팅 (v7.1 NEW)
│       ├── components/          # VideoHighlights 등 (v7.1 NEW)
│       └── pages/               # 11개 페이지 (HomePage 신규 v7.1)
│           ├── HomePage.jsx     # 🏠 랜딩 페이지 (v7.1 NEW)
│           ├── Dashboard.jsx    # 📊 위젯 대시보드 (v7.1 NEW)
│           └── LoginPage.jsx    # 👤 2-column 로그인 (v7.1 NEW)
├── data/                        # 🗄️ SQLite DB
├── config/                      # ⚙️ rubric_config.yaml
├── scripts/                     # 📜 분석/배치/리포트 스크립트
├── tests/                       # 🧪 검증 테스트
├── docs/                        # 📄 GitHub Pages
└── pyproject.toml               # 📦 패키지 설정
```

---

## 🚀 시작하기

### 필수 요구사항

- **Python** 3.9+
- **Node.js** 18+
- **FFmpeg** (CUDA GPU 가속 권장)
- **Google Gemini API Key**

### 설치 및 실행

```bash
# 1. 저장소 클론
git clone https://github.com/edu-data/GAIM_Lab.git
cd GAIM_Lab

# 2. 환경변수 설정
export GOOGLE_API_KEY="your-gemini-api-key"

# 3. Backend 실행
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 4. Frontend 실행 (새 터미널)
cd frontend
npm install
npm run dev
```

### 분석 실행

```bash
# 단일 영상 분석
python run_sample_analysis.py video/sample.mp4

# 배치 분석 (MAS 파이프라인)
python run_batch_agents.py

# 레거시 배치 분석
python batch_analysis.py --limit 5
```

---

## 🔗 API 엔드포인트

### 분석 API

| Method | 엔드포인트 | 설명 |
| ------ | --------- | ---- |
| POST | `/api/v1/analysis/upload` | 영상 업로드 |
| POST | `/api/v1/analysis/analyze` | 분석 시작 |
| GET | `/api/v1/analysis/{id}` | 분석 결과 조회 |

### 에이전트 모니터링 API

| Method | 엔드포인트 | 설명 |
| ------ | --------- | ---- |
| POST | `/api/v1/agents/start` | MAS 파이프라인 시작 |
| GET | `/api/v1/agents/status/{id}` | 에이전트 상태 조회 |
| GET | `/api/v1/agents/events/{id}` | 이벤트 히스토리 조회 |

### 이력·성장·포트폴리오 (v7.0)

| Method | 엔드포인트 | 설명 |
| ------ | --------- | ---- |
| GET | `/api/v1/history` | 분석 이력 조회 |
| GET | `/api/v1/growth/{prefix}` | 성장 추세 분석 |
| DELETE | `/api/v1/history/{id}` | 분석 결과 삭제 |
| POST | `/api/v1/analysis/batch/start` | 배치 분석 시작 |
| GET | `/api/v1/portfolio` | 포트폴리오 조회 |

### 신규 기능 API (v7.1 NEW)

| Method | 엔드포인트 | 설명 |
| ------ | --------- | ---- |
| WS | `/api/v1/ws/live-coaching` | 실시간 코칭 WebSocket |
| POST | `/api/v1/cohort/compare` | 코호트 비교 (t-test, Cohen's d) |
| GET | `/api/v1/experiment/rubrics` | A/B 루브릭 목록 조회 |
| POST | `/api/v1/experiment/ab` | A/B 루브릭 비교 실험 |
| GET | `/api/v1/auth/google/login` | Google OAuth 로그인 |
| POST | `/api/v1/auth/login` | JWT 로그인 |
| POST | `/api/v1/growth/roadmap` | 성장 경로 로드맵 생성 |

---

## 📊 분석 결과

### 🤖 v8.0 — Gemini 7차원 전면 평가 (최신)

| 통계 | 결과 |
| ---- | ---- |
| ✅ 성공률 | **18/18 (100%)** |
| 📊 평균 점수 | **76.1점 (C+등급)** |
| 🏆 최고 점수 | **84점 (20251209_110545, B등급)** |
| 📉 최저 점수 | **67점 (20251209_153522, D+등급)** |
| 📏 점수 범위 | **17pt (67~84)** |
| ⏱️ 영상당 처리 | **~1.5분 (TURBO MODE v3)** |
| 🔧 핵심 수정 | **3개 차원 rule-based → Gemini LLM** |

**등급 분포**: B등급 5개 (28%) / C+등급 4개 (22%) / C등급 7개 (39%) / D+등급 1개 (6%)

**v7.2 대비 개선**: 평균 59.9 → **76.1** (+16.2pt), F등급 8 → **0**, B등급 0 → **5**

### 🔬 v6.0 — 신뢰도·타당도 분석 (최신)

6회 반복 배치 분석 × 18영상 × 7차원 신뢰도 검증:

| 신뢰도 지표 | 결과 | 비고 |
| ---- | :--: | ---- |
| Cronbach's α | 0.33 | 7차원 각각 독립적 구인 측정 |
| Test-Retest r | **0.68** (0.35~0.93) | 실행 간 순위 안정성 |
| MAD (평균 절대차) | **3.09점** | 100점 만점 기준 |
| ±5점 일치율 | **82.6%** | 실용적 일치 수준 |
| ±3점 일치율 | 57.0% | 엄격 일치 수준 |

**차원별 우수 지표**:

| 차원 | ICC(2,1) | Retest r | 판정 |
| ---- | :--: | :--: | :--: |
| 판서 및 언어 | 0.7454 | 0.8647 | ✅ 우수 |
| 시간 배분 | 0.5747 | 0.9531 | ✅ 우수 |
| 수업 전문성 | 0.4894 | 0.5721 | ⚠️ 양호 |

| 대시보드 | 링크 |
| -------- | ---- |
| 🏠 **React 홈페이지 (NEW)** | [edu-data.github.io/GAIM_Lab/app/](https://edu-data.github.io/GAIM_Lab/app/) — 히어로·파이프라인·에이전트·기술스택 |
| 📊 **React 대시보드 (NEW)** | [edu-data.github.io/GAIM_Lab/app/#/dashboard](https://edu-data.github.io/GAIM_Lab/app/#/dashboard) — 통계·차트·이력·데모 |
| 🤖 MAS 홈페이지 | [edu-data.github.io/mas](https://edu-data.github.io/mas/mas-index.html) |
| 📊 v5.0 배치 대시보드 | [18개 영상 시각화 + 화자 분리](https://edu-data.github.io/GAIM_Lab/batch_dashboard.html) |
| 📊 MAS 대시보드 | [v4.2 분석 결과](https://edu-data.github.io/mas/mas-dashboard.html) |

### 📋 이전 보고서

| 보고서 | 설명 |
| ------ | ---- |
| [v5.0 배치 대시보드](https://edu-data.github.io/GAIM_Lab/batch_dashboard.html) | 화자분리·점수분포·산점도 |
| [최고점 리포트](https://edu-data.github.io/GAIM_Lab/best_report_110545.html) | 84점 영상 상세 분석 |
| [FIAS 대시보드](https://edu-data.github.io/GAIM_Lab/fias-dashboard.html) | Flanders 상호작용 분석 |
| [종합 평가 보고서](https://edu-data.github.io/GAIM_Lab/comprehensive_report.html) | 18개 영상 종합 분석 |
| [GAIM Lab 웹사이트](https://edu-data.github.io/GAIM_Lab/) | 시스템 소개 |

---

## 📜 버전 히스토리 (Changelog)

### v8.2 — GitHub Pages 풀스택 · Gemini 실시간 코칭 · 클라이언트 인증 `2026-02-23`

- **🔴 실시간 코칭 Gemini 7차원 평가** (`LiveCoaching.jsx` + `clientAnalyzer.js`)
  - 세션 종료 시 전사 텍스트 + 메트릭을 Gemini API로 전송하여 7차원 수업 평가
  - 기존 heuristic 8차원 스코어링 → Gemini AI 기반 7차원 분석으로 전면 교체
  - `analyzeTranscript()` 함수 추가: 텍스트 기반 Gemini 호출
  - 'analyzing' 로딩 페이즈 (스피너) + 점수별 근거 피드백 + 강점/개선점/종합 피드백 표시
  - API Key 미설정 시 fallback 안내 UI
- **🔐 클라이언트 인증 시스템** (`clientAuth.js` 신규)
  - GitHub Pages에서 백엔드 없이 로그인·회원가입 작동 (SHA-256 + Web Crypto API)
  - localStorage 기반 사용자 CRUD + 관리자 자동 시드 (admin/admin1234)
  - `LoginPage.jsx` dual-mode: localhost → 서버 API, GitHub Pages → 로컬 인증
  - `AdminUsers.jsx`: GitHub Pages에서도 사용자 관리 가능
- **📊 클라이언트 배치 분석** (`BatchAnalysis.jsx` 리팩토링)
  - GitHub Pages에서 파일 선택 → Gemini API로 직접 분석 (서버 불필요)
  - 영상별 실시간 진행률 추적, 점수 차트, 등급 배지
- **📊 클라이언트 코호트 비교** (`CohortCompare.jsx` 리팩토링)
  - A/B 그룹 파일 선택 → Gemini 분석 → 실시간 t-test, Cohen's d 계산
- **📈 통계 모듈** (`statistics.js` 신규)
  - Welch's t-test (Satterthwaite df) + Cohen's d (pooled SD)
  - Regularized incomplete beta (Lentz 연분수) + Lanczos log-gamma
  - 16/16 단위 테스트 통과
- **📄 포트폴리오 PDF 다운로드** (포트폴리오 페이지)
  - A4 인쇄용 HTML 리포트: 프로필, 7차원 성장 비교표, 세션 이력, 배지
  - 브라우저 print-to-PDF 대화상자
- **📹 카메라 안정화** (`useCamera.js` 개선)
  - LGE 전면 카메라 자동 감지 (디바이스 라벨 매칭)
  - 'Device in use' 에러 시 3회 자동 재시도 + 백오프
  - 콜백 체인 안정화: ref 기반 onFrame으로 재시작 루프 방지
- **🔧 성장 경로/포트폴리오**: GitHub Pages 호환 (API 우회, 샘플 데이터 표시)
- **🔖 버전**: `__APP_VERSION__` → `8.2.0`

### v8.1 — PDF 내보내기 · 멘토 매칭 · 테스트 강화 `2026-02-23`

- **📄 PDF 내보내기**: 분석 결과 페이지에 `📄 PDF 내보내기` 버튼 추가
  - `window.print()` 기반, `@media print` CSS로 깨끗한 인쇄 출력
  - 사이드바·액션 버튼 자동 숨김, 2-column 레이아웃 최적화
- **🎓 멘토 매칭 페이지** (`MentorMatch.jsx` 신규)
  - 약점 차원(7개) 기반 멘토 필터링 + 이름/키워드 검색
  - 글라스모피즘 멘토 카드: 아바타, 전문성, 평점, 바이오, 태그
  - 사이드바 `🎓 멘토 매칭` 메뉴 + `/mentor` 라우트 추가
- **📊 대시보드 이력 관리**: `/api/v1/history` 연동 분석 이력 조회 + 결과 네비게이션
- **🧪 테스트 강화** (4개 신규 테스트 파일)
  - `ErrorBoundary.test.jsx`: fallback UI 렌더링, 에러 메시지, 리트라이 동작
  - `AgentMonitor.test.jsx`: 8개 에이전트 카드, 업로드 영역, 초기 상태
  - `api.test.js`: GET/POST, 인증 토큰, 에러 처리, FormData
  - `HomePage.test.jsx`: 히어로, 파이프라인, 7차원, 에이전트, 기술 스택
- **🔖 버전**: `__APP_VERSION__` → `8.1.0`

### v8.0 — Gemini 7차원 전면 평가 · 클라이언트 사이드 분석 · Hook 리팩토링 `2026-02-22`

- **🤖 Gemini 7차원 전면 평가** (`evaluator.py`)
  - 3개 차원(판서/언어, 수업 태도, 시간 배분)에 Gemini LLM 점수 우선 적용
  - 기존: rule-based scoring (vision/vibe/text 메트릭 의존) → 점수 극저
  - 수정 후: 평균 59.9 → **76.1점** (+16.2pt), F등급 8 → **0**, B등급 0 → **5**
- **🎬 클라이언트 사이드 분석 엔진** (`videoAnalyzer.js` 신규)
  - 브라우저에서 직접 영상 분석 (백엔드 불필요, GitHub Pages 동작)
  - Canvas 프레임 추출, Web Audio API 음성 분석, 움직임/제스처 감지
  - 영상 업로드 drag-and-drop, 미리보기 썸네일
  - 에이전트별 실시간 진행 표시
- **🔧 React Hooks 리팩토링**
  - `useCamera` 훅: `LiveCoaching.jsx` 카메라 로직 분리 (`hooks/useCamera.js`)
  - `useAsyncTask` 훅: `AgentMonitor.jsx` 비동기 작업 관리 (`hooks/useAsyncTask.js`)
  - `ErrorBoundary` 컴포넌트 추가 (`ErrorBoundary.jsx`)
- **📊 배치 분석 개선** (`run_batch_18.py`)
  - 차원 키 버그 수정 (`"dimension"` → `"name"`)
  - CSV/JSON 요약에 정확한 차원별 점수 기록
- **🖥️ UI 안정화**: 분석 중 블랙 스크린 방지, 비디오 프레임 추출 타임아웃, UI 스레드 양보
- **📂 신규 파일**: `backend/app/config/`, `backend/app/models/`, `backend/tests/`, `core/paths.py`

### v7.1 — 신규 기능 7종 · PWA · 실시간 코칭 · UI 리디자인 `2026-02-20`

- **✨ UI 글라스모피즘 리디자인**: 사이드바 네비게이션 + 새 홈페이지 + 대시보드 위젯 (`App.jsx`, `HomePage.jsx`, `Dashboard.jsx`)
  - 10개 메뉴 사이드바, 모바일 햄버거, 인디고/바이올렛 다크 테마
  - 히어로 섹션 + 파이프라인 시각화 + 에이전트 그리드 + v7.1 기능 카드
  - 4개 통계 카드 + 점수 추세 차트 + 분석 이력 테이블 + 데모 분석
  - 2-column 로그인 페이지 (Google OAuth + JWT)
- **🎯 성장 경로 (P0)**: 3/6/12주 맞춤 개선 로드맵 생성 (`growth_analyzer.py` + `GrowthPath.jsx`)
- **🔴 실시간 코칭 라이트 (P1)**: WebSocket 기반 실시간 피드백 (`live_coaching.py` + `LiveCoaching.jsx`)
  - 필러워드 감지, WPM 모니터링, 침묵 탐지
- **📊 코호트 비교 분석 (P1)**: 집단 간 t-test, Cohen's d 통계 비교 (`cohort.py` + `CohortCompare.jsx`)
- **👤 Google OAuth (P1)**: JWT + Google 소셜 로그인 (`auth.py` + `LoginPage.jsx`)
- **📱 PWA 지원 (P2)**: Service Worker + Web App Manifest (`manifest.json`, `service-worker.js`)
- **🧪 A/B 루브릭 실험 (P2)**: 2개 루브릭 동시 적용 채점 비교 (`rubric_experiment.py` + `ABExperiment.jsx`)
- **🎬 영상 하이라이트 (P2)**: 비디오 타임라인 마커 컴포넌트 (`VideoHighlights.jsx` → `AnalysisResult.jsx` 통합)
- **프로젝트 구조 정리**: 스크립트 `scripts/` 디렉토리 이동, `data/` 분리

### v7.0 — Pydantic 계약 · SQLite 영속성 · 성장 분석 `2026-02-20`

- **채점 엔진 v7 리팩토링** (`pedagogy_agent.py`)
  - 구간화(Binning) 기반 결정론적 채점 (LLM 판단 의존 제거)
  - 차원별 `confidence_score` 메타데이터 추가
  - `w*0.95` 천장 방지 + `adjust_range` 확대
  - 차원별 독립 프로필 리포팅 (`profile_summary`)
- **Orchestrator v7** (`orchestrator.py`)
  - `SharedContext` → Pydantic `BaseModel` 타입 계약
  - 에이전트별 신뢰도 메타데이터 전파 (confidence propagation)
  - 자동 DB 저장 hook (`_try_save_to_db`)
- **SQLite 데이터 영속성** (`core/database.py` 신규)
  - `analyses` + `dimension_scores` 테이블
  - `AnalysisRepository` CRUD (save/get/history/growth/delete)
  - WAL 모드, 자동 DB 파일 생성
- **성장 경로 분석기** (`core/growth_analyzer.py` 신규)
  - 차원별 선형 회귀 추세 분석
  - 강점/약점 프로필 + 자동 개선 피드백 (규칙 기반)
- **UX 개선**: History API (`/history`, `/growth`, `/delete`), Dashboard DB 이력 연동
- **코드 품질**: 프로젝트 전체 하드코딩 경로 제거 (9개 파일), 레거시 스크립트 정리
- **배치 결과**: 18/18 성공, 평균 76.2점, 점수 범위 18.5pt

### v6.0 — 신뢰도·기준타당도 분석 도구 `2026-02-19`

- **pyannote.audio 3.3 통합**: Python 3.14 + PyTorch 2.10 환경 8-layer 호환성 패치
  - torchaudio 2.10 API 스텁, numpy 2.0 NaN 별칭, torchcodec DLL mock
  - huggingface_hub `use_auth_token→token` 자동 변환
  - `torch.serialization.load` weights_only 패치
- **신뢰도 분석** (`reliability_analysis.py`)
  - Cronbach's α / ICC(2,1) / ICC(2,k) / SEM
  - Test-Retest 상관(Pearson r) / MAD / ±3pt·±5pt 일치율
  - IQR 기반 이상치 실행 자동 필터링
  - HTML 리포트 (Chart.js 시각화)
- **기준타당도 분석** (`criterion_validity.py`)
  - Pearson r / Spearman ρ / R² / MAE / RMSE
  - Bland-Altman 일치도 분석 + 산점도
  - 등급 정확·인접 일치율
  - `expert_scores.csv` 전문가 채점 템플릿
- **교차 분석** (`cross_analysis.py`) / **YouTube 다운로더** (`download_youtube_videos.py`)
- `pedagogy_agent.py` v6.0 채점 리밸런싱

### v5.0 — 화자 분리 & 담화 분석 `2026-02-18`

- **Discourse Analyzer** 신규 추가: STT 결과에서 교사/학생 발화를 분리하여 담화 패턴 분석
- 교사 발화 비율, 학생 발화 횟수, 질문 유형 자동 분류
- v5.0 배치 대시보드: 화자 분리 산점도 차트 (교사비율 vs 총점, 학생발화 vs 총점)
- 점수 범위 확대: v4.2 **9.7pt** → v5.0 **13.5pt** (1.4배)
- 등급분포 개선: A-:4 / B+:11 / B:2 / B-:1
- 평균 점수: **77.4점** (v4.2 대비 +0.4pt)

### v4.2 — 에이전트 버그 수정 `2026-02-18`

- **Vision/Content 프레임 경로 버그 수정**: `flash_extract_resources`가 `{temp_dir}/frame_*.jpg`에 저장하지만, 오케스트레이터가 `{temp_dir}/frames/`에서 검색하던 경로 불일치 해결
- Vision Agent 0.02s → **5.24s** (얼굴감지·제스처·움직임 실분석)
- Content Agent 0.0s → **161.3s** (OCR·슬라이드·텍스트밀도 실분석)
- `_phase_synthesize`에 vision/content/vibe 요약 데이터 추가
- 배치 재분석 결과: 평균 **77.0점**, 등급분포 A-:2 / B+:13 / B:3

### v4.1 — 점수 차별화 강화 `2026-02-18`

- `pedagogy_agent.py` 전면 리팩토링
- `_safe()` 헬퍼로 에이전트 에러/빈 데이터 안전 처리
- STT 데이터 기반 7차원 전체 차별화 강화
- 한국어 발화속도 기준 보정 (3.0~5.0 음절/초)
- 점수 범위 **71.5~82.6** (11pt range, 이전 44.9~53.4에서 대폭 개선)
- 등급분포 A- 11개 / B+ 4개 / B 3개

### v4.0 — MAS 멀티 에이전트 시스템 `2026-02-17`

- **AgentOrchestrator** 파이프라인 아키텍처 도입
- 8개 AI 에이전트 설계 및 구현 (Extractor, Vision, Content, STT, Vibe, Pedagogy, Feedback, Master)
- `SharedContext` 에이전트 간 데이터 공유 프레임워크
- Event-driven Pub/Sub 메시지 버스
- MAS 전용 홈페이지 (`mas-index.html`) 및 대시보드 (`mas-dashboard.html`)
- 18개 영상 배치 분석 자동화 (`run_batch_agents.py`)

### v3.0 — 웹 UI 및 리포트 시스템 `2026-02-05`

- **FastAPI 백엔드** + **React 18 프론트엔드** 풀스택 구현
- 학생 포트폴리오 레이더 차트·성장 추적·디지털 배지 시스템
- 실시간 분석 진행 피드백 UI
- 모의수업 영상 분석 자동화 및 HTML/PDF 리포트 생성
- E2E 테스트 (Vitest + Playwright)

### v2.0 — 배치 분석 및 RAG 통합 `2026-02-05`

- **배치 분석 시스템** (`batch_analysis.py`): 18개 영상 순차 처리, CSV 요약
- **RAG 파이프라인**: Vertex AI Search + 교육학 지식 베이스 통합
- 리포트 v2: QR코드 삽입, 반응형 차트
- FIAS(Flanders 상호작용 분석) 대시보드 추가
- 배치 대시보드 (점수분포·등급·레이더차트 시각화)

### v1.0 — 초기 시스템 `2026-02-04`

- **GAIM Lab 영상 분석 시스템** 초기 아키텍처 설계
- `TimeLapseAnalyzer` 영상 프레임 추출 및 분석
- `GAIMLectureEvaluator` 7차원 100점 만점 평가 프레임워크 구현
- `GAIMReportGenerator` HTML 리포트 생성
- GPU 가속 FFmpeg 프레임 추출 구현
- 병렬 프레임 분석 (`ParallelFrameAnalyzer`) 멀티프로세싱 최적화
- GitHub Pages 프로모션 랜딩 페이지

---

## ⚙️ 기술 스택

| 영역 | 기술 |
| ---- | ---- |
| **AI/ML** | Google Gemini AI, OpenAI Whisper, pyannote.audio, OpenCV, Librosa |
| **분석 도구** | ICC, Cronbach's α, Bland-Altman, Test-Retest, SEM |
| **Backend** | FastAPI, WebSocket, Python 3.9+, RAG Pipeline, Pydantic |
| **Frontend** | React 18, Vite, Chart.js, Recharts, PWA |
| **인증** | Google OAuth 2.0, JWT |
| **데이터** | SQLite (WAL mode), Growth Analyzer |
| **영상 처리** | FFmpeg (CUDA GPU 가속) |
| **아키텍처** | Pydantic Contract AgentOrchestrator, Pub/Sub MessageBus |
| **배포** | GitHub Pages, GitHub Actions, PWA Service Worker |

---

## 🧪 테스트

```bash
# Frontend 단위 테스트
cd frontend && npm test

# E2E 테스트
npm run test:e2e

# RAG 파이프라인 테스트
python test_rag_pipeline.py
```

---

## 📄 라이선스

MIT License · 경인교육대학교 GAIM Lab

---

<p align="center">
  <strong>경인교육대학교 GINUE AI Microteaching Lab</strong><br/>
  <a href="mailto:educpa@ginue.ac.kr">educpa@ginue.ac.kr</a> ·
  <a href="https://github.com/edu-data/GAIM_Lab">GitHub</a> ·
  <a href="https://edu-data.github.io/GAIM_Lab/app/">웹사이트</a>
</p>
