"""
GAIM Lab - 18개 영상 배치 분석 스크립트
Gemini LLM + Whisper STT 통합 버전
"""

import os
import sys
import json
import csv
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 설정
GAIM_ROOT = Path(__file__).parent
sys.path.insert(0, str(GAIM_ROOT))

# 환경변수 설정 (.env 파일에서 로드)
env_file = GAIM_ROOT / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

from run_sample_analysis import run_sample_analysis

def batch_analyze():
    """18개 영상 배치 분석"""
    video_dir = GAIM_ROOT / "video"
    output_base = GAIM_ROOT / "output" / f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_base.mkdir(parents=True, exist_ok=True)
    
    # 분석할 영상 목록 (youtube_demo 제외)
    videos = sorted([
        f for f in video_dir.glob("*.mp4") 
        if "youtube" not in f.name.lower()
    ])
    
    print("=" * 70)
    print(f"🎬 GAIM Lab 배치 분석 시작")
    print(f"📁 영상 수: {len(videos)}개")
    print(f"📂 출력: {output_base}")
    print("=" * 70)
    
    results = []
    
    for i, video in enumerate(videos, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(videos)}] 분석 중: {video.name}")
        print("=" * 70)
        
        try:
            video_output = output_base / video.stem
            video_output.mkdir(exist_ok=True)
            
            result, report_path = run_sample_analysis(
                str(video), 
                str(video_output)
            )
            
            if result:
                results.append({
                    "video": video.name,
                    "total_score": result.total_score,
                    "grade": result.grade,
                    "professionalism": next((d.score for d in result.dimensions if d.dimension == "수업 전문성"), 0),
                    "teaching_method": next((d.score for d in result.dimensions if d.dimension == "교수학습 방법"), 0),
                    "language": next((d.score for d in result.dimensions if d.dimension == "판서 및 언어"), 0),
                    "attitude": next((d.score for d in result.dimensions if d.dimension == "수업 태도"), 0),
                    "participation": next((d.score for d in result.dimensions if d.dimension == "학생 참여"), 0),
                    "time_management": next((d.score for d in result.dimensions if d.dimension == "시간 배분"), 0),
                    "creativity": next((d.score for d in result.dimensions if d.dimension == "창의성"), 0),
                    "status": "success"
                })
                print(f"   ✅ 완료: {result.total_score}점 ({result.grade})")
            else:
                results.append({
                    "video": video.name,
                    "total_score": 0,
                    "grade": "N/A",
                    "status": "no_result"
                })
                print(f"   ⚠️ 결과 없음")
                
        except Exception as e:
            results.append({
                "video": video.name,
                "total_score": 0,
                "grade": "ERROR",
                "status": f"error: {str(e)}"
            })
            print(f"   ❌ 오류: {e}")
    
    # CSV 요약 저장
    csv_path = output_base / "batch_summary.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    
    # JSON 요약 저장
    json_path = output_base / "batch_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 최종 요약 출력
    print("\n" + "=" * 70)
    print("📊 배치 분석 완료!")
    print("=" * 70)
    
    successful = [r for r in results if r.get("status") == "success"]
    if successful:
        avg_score = sum(r["total_score"] for r in successful) / len(successful)
        print(f"\n✅ 성공: {len(successful)}/{len(results)}개")
        print(f"📈 평균 점수: {avg_score:.1f}점")
        
        # 등급 분포
        grades = {}
        for r in successful:
            g = r["grade"]
            grades[g] = grades.get(g, 0) + 1
        
        print("\n📊 등급 분포:")
        for grade in ["A+", "A", "B+", "B", "C+", "C", "D", "F"]:
            if grade in grades:
                print(f"   {grade}: {grades[grade]}개")
    
    print(f"\n📂 결과 저장:")
    print(f"   - CSV: {csv_path}")
    print(f"   - JSON: {json_path}")
    
    return results


if __name__ == "__main__":
    batch_analyze()
