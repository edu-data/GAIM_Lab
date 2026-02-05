"""
🎥 Enhanced Gemini Multimodal Evaluator v2.0
Gemini API를 활용한 멀티모달(비디오 + 오디오 + 텍스트) 수업 분석

특징:
- 비디오 프레임 시각 분석 (표정, 제스처, 시선)
- 오디오 특성 분석 (톤, 속도, 에너지)
- 텍스트 내용 분석 (교수법, 발문)
- 신뢰도 점수 제공
"""

import os
import json
import base64
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import google.generativeai as genai


GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


# 향상된 멀티모달 평가 프롬프트
MULTIMODAL_PROMPT = """
당신은 초등학교 교사 임용 2차 수업실연 평가 전문가입니다.
제공된 수업 영상 프레임과 텍스트를 종합 분석하여 7차원 평가를 수행하세요.

[분석 대상]
1. 영상 프레임 분석:
   - 교사의 표정과 자신감
   - 손 제스처 활용도
   - 시선 처리 (학생과의 눈맞춤)
   - 자세와 움직임
   - 판서 및 시각 자료 활용

2. 수업 텍스트 분석:
{transcript}

[평가 기준 - 100점 만점]
1. 수업 전문성 (20점): 학습목표 명료성, 학습내용 충실성
2. 교수학습 방법 (20점): 교수법 다양성, 학습활동 효과성
3. 판서 및 언어 (15점): 판서 가독성, 언어 명료성, 발화속도
4. 수업 태도 (15점): 교사 열정, 학생 소통, 자신감
5. 학생 참여 (15점): 발문 기법, 피드백 제공
6. 시간 배분 (10점): 도입-전개-정리 균형
7. 창의성 (5점): 독창적 아이디어

[응답 형식 - 순수 JSON만]
{{
  "수업_전문성": {{
    "점수": 0-20,
    "학습목표_명료성": 0-10,
    "학습내용_충실성": 0-10,
    "근거": "분석 근거",
    "신뢰도": 0.0-1.0
  }},
  "교수학습_방법": {{
    "점수": 0-20,
    "교수법_다양성": 0-10,
    "학습활동_효과성": 0-10,
    "근거": "분석 근거",
    "신뢰도": 0.0-1.0
  }},
  "판서_및_언어": {{
    "점수": 0-15,
    "판서_가독성": 0-5,
    "언어_명료성": 0-5,
    "발화속도_적절성": 0-5,
    "근거": "분석 근거",
    "신뢰도": 0.0-1.0
  }},
  "수업_태도": {{
    "점수": 0-15,
    "교사_열정": 0-5,
    "학생_소통": 0-5,
    "자신감": 0-5,
    "시선_분석": "프레임 기반 시선 분석",
    "제스처_분석": "프레임 기반 제스처 분석",
    "근거": "분석 근거",
    "신뢰도": 0.0-1.0
  }},
  "학생_참여": {{
    "점수": 0-15,
    "질문_기법": 0-7,
    "피드백_제공": 0-8,
    "근거": "분석 근거",
    "신뢰도": 0.0-1.0
  }},
  "시간_배분": {{
    "점수": 0-10,
    "시간_균형": 0-10,
    "근거": "분석 근거",
    "신뢰도": 0.0-1.0
  }},
  "창의성": {{
    "점수": 0-5,
    "수업_창의성": 0-5,
    "근거": "분석 근거",
    "신뢰도": 0.0-1.0
  }},
  "총점": 0-100,
  "평균_신뢰도": 0.0-1.0,
  "종합_평가": "전문가 수준의 종합 피드백",
  "강점": ["강점1", "강점2", "강점3"],
  "개선점": ["개선점1", "개선점2", "개선점3"],
  "하이라이트_순간": [
    {{"시간": "예: 3분 20초", "설명": "우수한 발문 사례"}}
  ]
}}
"""


class EnhancedGeminiEvaluator:
    """향상된 멀티모달 Gemini 평가기"""
    
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        self.model_name = model_name
        self.model = None
        self.vision_model = None
        
        if GOOGLE_API_KEY:
            try:
                self.model = genai.GenerativeModel(model_name)
                self.vision_model = genai.GenerativeModel("gemini-2.0-flash")
                print(f"✅ Enhanced Gemini 초기화 완료: {model_name}")
            except Exception as e:
                print(f"❌ Gemini 초기화 실패: {e}")
    
    def load_frame_as_base64(self, frame_path: Path) -> Optional[str]:
        """프레임을 base64로 로드"""
        try:
            with open(frame_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            print(f"⚠️ 프레임 로드 실패: {frame_path}, {e}")
            return None
    
    def select_key_frames(self, frames_dir: Path, count: int = 8) -> List[Path]:
        """주요 프레임 선택 (시간적으로 균등 분포)"""
        frames = sorted(frames_dir.glob("*.jpg")) + sorted(frames_dir.glob("*.png"))
        
        if len(frames) <= count:
            return frames
        
        step = len(frames) // count
        selected = [frames[i * step] for i in range(count)]
        return selected
    
    def evaluate_with_frames(
        self, 
        transcript: str, 
        frames_dir: Optional[Path] = None,
        key_frames: Optional[List[Path]] = None
    ) -> Optional[Dict]:
        """프레임과 텍스트를 함께 분석"""
        if not self.model:
            print("❌ Gemini 모델이 초기화되지 않았습니다.")
            return None
        
        # 프레임 준비
        image_parts = []
        if frames_dir and frames_dir.exists():
            key_frames = self.select_key_frames(frames_dir)
        
        if key_frames:
            print(f"📸 {len(key_frames)}개 프레임 분석 중...")
            for frame in key_frames:
                b64 = self.load_frame_as_base64(frame)
                if b64:
                    image_parts.append({
                        "mime_type": "image/jpeg",
                        "data": b64
                    })
        
        # 프롬프트 구성
        prompt = MULTIMODAL_PROMPT.format(transcript=transcript[:10000])
        
        try:
            print("🤖 Enhanced Gemini 분석 중...")
            
            if image_parts:
                # 멀티모달 분석
                content = [prompt] + image_parts
                response = self.vision_model.generate_content(content)
            else:
                # 텍스트만 분석
                response = self.model.generate_content(prompt)
            
            # JSON 파싱
            result_text = response.text.strip()
            
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            result = json.loads(result_text)
            
            # 신뢰도 계산
            confidences = []
            for dim in ["수업_전문성", "교수학습_방법", "판서_및_언어", 
                       "수업_태도", "학생_참여", "시간_배분", "창의성"]:
                if dim in result and "신뢰도" in result[dim]:
                    confidences.append(result[dim]["신뢰도"])
            
            if confidences:
                result["평균_신뢰도"] = sum(confidences) / len(confidences)
            
            print(f"✅ 분석 완료: {result.get('총점', 0)}점 (신뢰도: {result.get('평균_신뢰도', 0):.1%})")
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 오류: {e}")
            return None
        except Exception as e:
            print(f"❌ API 오류: {e}")
            return None
    
    def analyze_single_frame(self, frame_path: Path) -> Optional[Dict]:
        """단일 프레임 정밀 분석"""
        if not self.vision_model:
            return None
        
        b64 = self.load_frame_as_base64(frame_path)
        if not b64:
            return None
        
        prompt = """
        이 수업 장면을 분석하세요:
        1. 교사의 표정 (자신감, 열정)
        2. 제스처 활용 여부
        3. 시선 방향 (학생을 보고 있는지)
        4. 자세 (열린 자세인지)
        5. 시각 자료 활용 여부
        
        JSON으로 응답: {"표정": "", "제스처": true/false, "시선": "", "자세": "", "시각자료": true/false}
        """
        
        try:
            response = self.vision_model.generate_content([
                prompt,
                {"mime_type": "image/jpeg", "data": b64}
            ])
            return json.loads(response.text.strip())
        except:
            return None
    
    def get_dimension_scores(self, result: Dict) -> Dict:
        """결과를 표준 형식으로 변환"""
        if not result:
            return {}
        
        dimensions = []
        dim_mapping = {
            "수업_전문성": ("수업 전문성", 20),
            "교수학습_방법": ("교수학습 방법", 20),
            "판서_및_언어": ("판서 및 언어", 15),
            "수업_태도": ("수업 태도", 15),
            "학생_참여": ("학생 참여", 15),
            "시간_배분": ("시간 배분", 10),
            "창의성": ("창의성", 5)
        }
        
        for key, (name, max_score) in dim_mapping.items():
            dim_data = result.get(key, {})
            score = dim_data.get("점수", 0)
            
            # criteria 추출
            criteria = {}
            for k, v in dim_data.items():
                if k not in ["점수", "근거", "신뢰도", "시선_분석", "제스처_분석"]:
                    criteria[k] = v
            
            # 피드백 구성
            feedback = [dim_data.get("근거", "")]
            if "시선_분석" in dim_data:
                feedback.append(f"시선: {dim_data['시선_분석']}")
            if "제스처_분석" in dim_data:
                feedback.append(f"제스처: {dim_data['제스처_분석']}")
            
            dimensions.append({
                "name": name,
                "score": score,
                "max_score": max_score,
                "percentage": round((score / max_score) * 100, 1) if max_score > 0 else 0,
                "criteria": criteria,
                "feedback": [f for f in feedback if f],
                "confidence": dim_data.get("신뢰도", 0.8)
            })
        
        # 강점/개선점 포맷
        strengths = [f"✅ {s}" for s in result.get("강점", [])]
        improvements = [f"🔧 {i}" for i in result.get("개선점", [])]
        
        return {
            "total_score": result.get("총점", 0),
            "max_score": 100.0,
            "grade": self._calculate_grade(result.get("총점", 0)),
            "dimensions": dimensions,
            "strengths": strengths,
            "improvements": improvements,
            "overall_feedback": result.get("종합_평가", ""),
            "confidence": result.get("평균_신뢰도", 0.8),
            "highlights": result.get("하이라이트_순간", [])
        }
    
    def _calculate_grade(self, score: float) -> str:
        """점수 기반 등급 산출"""
        if score >= 90:
            return "S"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"


# CLI 테스트
if __name__ == "__main__":
    import sys
    
    evaluator = EnhancedGeminiEvaluator()
    
    test_text = """
    여러분, 오늘 수업 주제는 지구촌 문제입니다.
    먼저 이 사진을 보세요. 어떤 문제가 보이나요?
    네, 맞아요. 기아 문제입니다. 
    그럼 우리가 할 수 있는 일은 무엇일까요?
    모둠별로 토의해보세요.
    """
    
    if evaluator.model:
        result = evaluator.evaluate_with_frames(test_text)
        if result:
            formatted = evaluator.get_dimension_scores(result)
            print(json.dumps(formatted, ensure_ascii=False, indent=2))
    else:
        print("GOOGLE_API_KEY 필요")
