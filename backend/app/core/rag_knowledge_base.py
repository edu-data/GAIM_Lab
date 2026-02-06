"""
GAIM Lab - RAG 지식 기반 시스템 (경량 버전)
Gemini Embedding API를 직접 사용하여 교육학 문서 기반 피드백 강화
ChromaDB 없이 인메모리 벡터 검색 구현
"""

import os
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    print("Warning: google-generativeai not installed. Run: pip install google-generativeai")


class EducationKnowledgeBase:
    """교육학 지식 기반 경량 RAG 시스템
    
    7차원 평가 기준 및 교육학 이론을 벡터화하여
    수업 분석 피드백에 이론적 근거를 추가합니다.
    
    ChromaDB 없이 인메모리 벡터 검색을 사용합니다.
    """
    
    # 차원 이름과 파일명 매핑
    DIMENSION_FILES = {
        "수업 전문성": "01_수업전문성.md",
        "교수학습 방법": "02_교수학습방법.md",
        "판서 및 언어": "03_판서_언어.md",
        "수업 태도": "04_수업태도.md",
        "학생 참여": "05_학생참여.md",
        "시간 배분": "06_시간배분.md",
        "창의성": "07_창의성.md"
    }
    
    def __init__(self, knowledge_dir: str = None, cache_file: str = None):
        """RAG 시스템 초기화
        
        Args:
            knowledge_dir: 교육학 문서 폴더 경로
            cache_file: 임베딩 캐시 파일 경로
        """
        self.knowledge_dir = Path(knowledge_dir) if knowledge_dir else Path(__file__).parent / "knowledge"
        self.cache_file = Path(cache_file) if cache_file else Path(__file__).parent / "embeddings_cache.json"
        
        self.documents: List[Dict] = []  # {"content": str, "metadata": dict, "embedding": list}
        self.is_initialized = False
        
        if HAS_GENAI:
            self._initialize()
    
    @property
    def chunk_count(self) -> int:
        """로드된 문서 청크 수 반환"""
        return len(self.documents)
    
    def _initialize(self):
        """임베딩 초기화 및 문서 로드"""
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                print("Warning: GOOGLE_API_KEY not set. RAG features disabled.")
                return
            
            genai.configure(api_key=api_key)
            
            # 캐시된 임베딩 로드 또는 새로 생성
            if self.cache_file.exists():
                self._load_cache()
            else:
                self._build_embeddings()
            
            self.is_initialized = True
            print(f"RAG initialized with {len(self.documents)} document chunks")
            
        except Exception as e:
            print(f"RAG initialization error: {e}")
            self.is_initialized = False
    
    def _load_documents(self) -> List[Dict]:
        """교육학 문서 로드 및 청킹"""
        documents = []
        
        # dimensions 폴더 문서 로드
        dimensions_dir = self.knowledge_dir / "dimensions"
        if dimensions_dir.exists():
            for file_path in dimensions_dir.glob("*.md"):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    
                    # 섹션별로 청킹
                    chunks = self._chunk_document(content)
                    for i, chunk in enumerate(chunks):
                        documents.append({
                            "content": chunk,
                            "metadata": {
                                "source": str(file_path.name),
                                "type": "dimension",
                                "chunk_index": i,
                                "dimension_name": file_path.stem.split("_", 1)[-1] if "_" in file_path.stem else file_path.stem
                            }
                        })
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
        
        print(f"Loaded {len(documents)} document chunks")
        return documents
    
    def _chunk_document(self, content: str, max_chunk_size: int = 1000) -> List[str]:
        """문서를 섹션 기반으로 청킹"""
        chunks = []
        
        # ## 또는 ### 으로 분할
        sections = content.split("\n## ")
        for section in sections:
            if len(section) > max_chunk_size:
                # 추가 분할
                sub_sections = section.split("\n### ")
                for sub in sub_sections:
                    if sub.strip():
                        chunks.append(sub.strip()[:max_chunk_size])
            elif section.strip():
                chunks.append(section.strip())
        
        return chunks if chunks else [content[:max_chunk_size]]
    
    def _get_embedding(self, text: str) -> List[float]:
        """Gemini Embedding API로 텍스트 임베딩 생성"""
        try:
            result = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            print(f"Embedding error: {e}")
            return []
    
    def _get_query_embedding(self, text: str) -> List[float]:
        """쿼리용 임베딩 생성"""
        try:
            result = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            print(f"Query embedding error: {e}")
            return []
    
    def _build_embeddings(self):
        """모든 문서에 대해 임베딩 생성 및 캐시"""
        raw_docs = self._load_documents()
        
        for doc in raw_docs:
            embedding = self._get_embedding(doc["content"])
            if embedding:
                doc["embedding"] = embedding
                self.documents.append(doc)
        
        # 캐시에 저장
        self._save_cache()
        print(f"Built embeddings for {len(self.documents)} chunks")
    
    def _save_cache(self):
        """임베딩 캐시 저장"""
        try:
            cache_data = []
            for doc in self.documents:
                cache_data.append({
                    "content": doc["content"],
                    "metadata": doc["metadata"],
                    "embedding": doc["embedding"]
                })
            
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            print(f"Cache saved to {self.cache_file}")
        except Exception as e:
            print(f"Cache save error: {e}")
    
    def _load_cache(self):
        """임베딩 캐시 로드"""
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                self.documents = json.load(f)
            print(f"Cache loaded: {len(self.documents)} chunks")
        except Exception as e:
            print(f"Cache load error: {e}")
            self._build_embeddings()
    
    def rebuild_index(self):
        """인덱스 재빌드 (문서 변경 시 호출)"""
        self.documents = []
        if self.cache_file.exists():
            self.cache_file.unlink()
        self._build_embeddings()
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """코사인 유사도 계산"""
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    def search(self, query: str, k: int = 3) -> List[Dict]:
        """관련 교육학 내용 검색
        
        Args:
            query: 검색 쿼리
            k: 반환할 결과 수
            
        Returns:
            검색 결과 리스트 [{"content": str, "metadata": dict, "score": float}]
        """
        if not self.is_initialized or not self.documents:
            return []
        
        try:
            query_embedding = self._get_query_embedding(query)
            if not query_embedding:
                return []
            
            # 모든 문서와 유사도 계산
            scores = []
            for doc in self.documents:
                if "embedding" in doc:
                    score = self._cosine_similarity(query_embedding, doc["embedding"])
                    scores.append((doc, score))
            
            # 상위 k개 반환
            scores.sort(key=lambda x: x[1], reverse=True)
            
            return [
                {
                    "content": doc["content"],
                    "metadata": doc["metadata"],
                    "score": score
                }
                for doc, score in scores[:k]
            ]
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def search_for_dimension(self, dimension_name: str, feedback: str, k: int = 2) -> List[Dict]:
        """특정 차원에 대한 이론적 근거 검색"""
        query = f"{dimension_name}: {feedback}"
        return self.search(query, k=k)
    
    def enhance_feedback(self, dimension_name: str, raw_feedback: str, score_percentage: float) -> Dict:
        """피드백에 교육학적 근거 추가
        
        Args:
            dimension_name: 차원 이름
            raw_feedback: 원본 피드백
            score_percentage: 점수 퍼센티지 (0-100)
            
        Returns:
            {
                "original_feedback": str,
                "enhanced_feedback": str,
                "theory_references": List[str],
                "improvement_tips": List[str]
            }
        """
        if not self.is_initialized:
            return {
                "original_feedback": raw_feedback,
                "enhanced_feedback": raw_feedback,
                "theory_references": [],
                "improvement_tips": []
            }
        
        # 관련 이론 검색
        search_results = self.search_for_dimension(dimension_name, raw_feedback)
        
        theory_references = []
        improvement_tips = []
        
        for result in search_results:
            content = result["content"]
            
            # 교육학적 근거 추출
            if "교육학적 근거" in content:
                theory_part = content.split("교육학적 근거")[1].split("##")[0] if "##" in content.split("교육학적 근거")[1] else content.split("교육학적 근거")[1]
                theory_references.append(theory_part.strip()[:300])
            
            # 개선 피드백 추출
            if "개선 피드백" in content:
                tips_part = content.split("개선 피드백")[1].split("###")[0] if "###" in content.split("개선 피드백")[1] else content.split("개선 피드백")[1]
                for line in tips_part.strip().split("\n"):
                    if line.strip().startswith("-"):
                        improvement_tips.append(line.strip().lstrip("- "))
        
        # 강화된 피드백 생성
        enhanced = raw_feedback
        if score_percentage < 70 and improvement_tips:
            enhanced += f"\n\n💡 개선 제안: {improvement_tips[0]}"
        
        return {
            "original_feedback": raw_feedback,
            "enhanced_feedback": enhanced,
            "theory_references": theory_references[:2],
            "improvement_tips": improvement_tips[:3]
        }
    
    def get_dimension_theory(self, dimension_name: str) -> str:
        """특정 차원의 교육학적 근거 반환"""
        results = self.search(dimension_name, k=1)
        if results:
            return results[0]["content"]
        return ""


# 싱글턴 인스턴스
_knowledge_base = None

def get_knowledge_base() -> EducationKnowledgeBase:
    """글로벌 지식 기반 인스턴스 반환"""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = EducationKnowledgeBase()
    return _knowledge_base


if __name__ == "__main__":
    # 테스트
    print("=== RAG Knowledge Base Test ===")
    kb = EducationKnowledgeBase(knowledge_dir="D:/AI/GAIM_Lab/backend/app/knowledge")
    
    if kb.is_initialized:
        # 검색 테스트
        print("\n[Search Test]")
        results = kb.search("학생 참여 유도 발문 기법")
        print(f"Found {len(results)} results")
        for r in results:
            print(f"  - Score: {r['score']:.3f}")
            print(f"    Content: {r['content'][:80]}...")
        
        # 피드백 강화 테스트
        print("\n[Feedback Enhancement Test]")
        enhanced = kb.enhance_feedback(
            dimension_name="학생 참여",
            raw_feedback="질문이 단답형에 그쳐 학생들의 사고를 확장시키지 못함",
            score_percentage=45.0
        )
        print(f"Original: {enhanced['original_feedback']}")
        print(f"Enhanced: {enhanced['enhanced_feedback']}")
        print(f"Theory refs: {len(enhanced['theory_references'])}")
        print(f"Tips: {enhanced['improvement_tips'][:2] if enhanced['improvement_tips'] else 'None'}")
    else:
        print("RAG system not initialized. Check API key.")
