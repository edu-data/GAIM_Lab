"""
GAIM Lab - RAG 연동 배치 분석 스크립트
18개 영상을 순차적으로 분석하고 요약 리포트 생성
"""

import sys
import io
import os
import json
import csv
import subprocess
import importlib.util
from pathlib import Path
from datetime import datetime
import time

# Windows 콘솔 UTF-8 출력 설정
if hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# 프로젝트 루트 경로
GAIM_ROOT = Path(r"D:\AI\GAIM_Lab")

# .env 로드
from dotenv import load_dotenv
load_dotenv(GAIM_ROOT / ".env")
print(f"✅ 환경 변수 로드: GOOGLE_API_KEY={'있음' if os.getenv('GOOGLE_API_KEY') else '없음'}")


def load_module_from_path(module_name: str, file_path: Path):
    """특정 경로에서 모듈 로드"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# backend/app 경로 추가
sys.path.insert(0, str(GAIM_ROOT / "backend" / "app"))

# 필요한 모듈 직접 로드
timelapse_module = load_module_from_path(
    "timelapse_analyzer", 
    GAIM_ROOT / "core" / "analyzers" / "timelapse_analyzer.py"
)
TimeLapseAnalyzer = timelapse_module.TimeLapseAnalyzer

from core.enhanced_gemini_evaluator import EnhancedGeminiEvaluator
from services.report_generator_v2 import GAIMReportGeneratorV2


def run_single_analysis(video_path: Path, output_dir: Path):
    """
    단일 영상 분석 실행 (RAG 포함)
    
    Returns:
        (evaluation_result, report_path) 튜플
    """
    video_name = video_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n🔍 [Phase 1/3] 영상 분석 중...")
    
    # Phase 1: TimeLapse 분석
    analyzer = TimeLapseAnalyzer(temp_dir=str(output_dir / "cache"))
    vision_results, content_results = analyzer.analyze_video(video_path)
    
    audio_metrics = analyzer.get_audio_metrics()
    audio_timeline = analyzer.get_audio_timeline()
    elapsed_time = analyzer.get_elapsed_time()
    
    print(f"   - 처리 시간: {elapsed_time:.1f}초")
    print(f"   - 비전 프레임: {len(vision_results)}개")
    print(f"   - 오디오 세그먼트: {len(audio_timeline)}개")
    
    # Phase 1.5: 음성 → 텍스트 변환 (Whisper STT)
    transcript = ""
    segments = []
    audio_path = output_dir / "audio.wav"
    
    print(f"\n🎤 [Phase 1.5/3] 음성 인식 (Whisper STT) 중...")
    try:
        cmd = [
            'ffmpeg', '-i', str(video_path),
            '-ar', '16000', '-ac', '1',
            str(audio_path),
            '-y', '-loglevel', 'quiet'
        ]
        subprocess.run(cmd, check=True)
        print(f"   ✅ 오디오 추출 완료: {audio_path.name}")
        
        # Whisper로 음성 인식
        import whisper
        print(f"📝 [STT] Whisper 모델 로딩... (small)")
        model = whisper.load_model("small")
        print(f"   언어: ko")
        print(f"   🎙️ 음성 인식 중...")
        result = model.transcribe(str(audio_path), language="ko")
        
        segments = result.get("segments", [])
        transcript = result.get("text", "")
        
        print(f"   ✅ STT 완료: {len(segments)}개 세그먼트, {len(transcript)}자")
        
    except Exception as e:
        print(f"   ⚠️ STT 오류: {e}")
    
    # Phase 2: Enhanced Gemini 평가 (RAG 포함)
    print("\n📊 [Phase 2/3] RAG 연동 7차원 평가 수행 중...")
    
    evaluator = EnhancedGeminiEvaluator()
    
    if evaluator.knowledge_base and evaluator.knowledge_base.is_initialized:
        print(f"   ✅ RAG 활성화됨: {evaluator.knowledge_base.chunk_count}개 청크")
    else:
        print("   ⚠️ RAG 비활성화 (지식 기반 없음)")
    
    frames_dir = output_dir / "cache" / "frames"
    
    raw_result = evaluator.evaluate_with_frames(
        transcript=transcript,
        frames_dir=frames_dir if frames_dir.exists() else None
    )
    
    evaluation_result = evaluator.get_dimension_scores(raw_result) if raw_result else {
        "total_score": 0, "grade": "F", "dimensions": {}
    }
    
    print(f"   - 총점: {evaluation_result.get('total_score', 0):.1f} / 100")
    print(f"   - 등급: {evaluation_result.get('grade', 'N/A')}")
    
    # 결과 저장
    result_path = output_dir / "evaluation_result.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(evaluation_result, f, ensure_ascii=False, indent=2)
    
    # Phase 3: Report 생성
    print("\n📋 [Phase 3/3] HTML 리포트 생성 중 (V2)...")
    
    generator = GAIMReportGeneratorV2()
    html_path = output_dir / f"gaim_report_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    generator.generate_html_report(evaluation_result, str(html_path))
    print(f"   - HTML 리포트: {html_path.name}")
    
    return evaluation_result, str(html_path)


def run_batch_analysis():
    """
    video 폴더의 18개 영상을 배치 분석
    """
    video_dir = GAIM_ROOT / "video"
    
    # 18개 영상 파일 (youtube_demo.mp4 제외)
    video_files = sorted([
        f for f in video_dir.glob("20251209_*.mp4")
    ])
    
    print("=" * 70)
    print(f"🚀 GAIM Lab 배치 분석 (Gemini + RAG)")
    print(f"📁 영상 폴더: {video_dir}")
    print(f"🎬 분석 대상: {len(video_files)}개 영상")
    print("=" * 70)
    
    # 배치 출력 디렉토리
    batch_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    batch_dir = GAIM_ROOT / "output" / f"batch_v2_{batch_time}"
    batch_dir.mkdir(parents=True, exist_ok=True)
    
    # 결과 저장용
    results = []
    total_start = time.time()
    
    for idx, video_path in enumerate(video_files, 1):
        print(f"\n{'='*70}")
        print(f"📹 [{idx}/{len(video_files)}] {video_path.name}")
        print("=" * 70)
        
        video_name = video_path.stem
        output_dir = batch_dir / video_name
        
        start_time = time.time()
        
        try:
            # 분석 실행
            evaluation_result, report_path = run_single_analysis(video_path, output_dir)
            
            elapsed = time.time() - start_time
            
            if evaluation_result:
                dims = evaluation_result.get("dimensions", [])
                
                # dimensions가 list인 경우 처리 (각 차원의 name으로 점수 추출)
                def get_dim_score(dims_list, dim_name):
                    for d in dims_list:
                        if d.get("name") == dim_name:
                            return d.get("score", 0)
                    return 0
                
                results.append({
                    "video": video_path.name,
                    "total_score": evaluation_result.get("total_score", 0),
                    "grade": evaluation_result.get("grade", "N/A"),
                    "teaching_expertise": get_dim_score(dims, "수업 전문성"),
                    "teaching_method": get_dim_score(dims, "교수학습 방법"),
                    "communication": get_dim_score(dims, "판서 및 언어"),
                    "teaching_attitude": get_dim_score(dims, "수업 태도"),
                    "student_engagement": get_dim_score(dims, "학생 참여"),
                    "time_management": get_dim_score(dims, "시간 배분"),
                    "creativity": get_dim_score(dims, "창의성"),
                    "analysis_time": round(elapsed, 1),
                    "report_path": report_path,
                    "status": "success"
                })
                print(f"✅ 완료: {evaluation_result.get('total_score', 0):.1f}점 ({elapsed:.1f}초)")
            else:
                results.append({
                    "video": video_path.name,
                    "total_score": 0,
                    "grade": "ERROR",
                    "teaching_expertise": 0,
                    "teaching_method": 0,
                    "communication": 0,
                    "teaching_attitude": 0,
                    "student_engagement": 0,
                    "time_management": 0,
                    "creativity": 0,
                    "analysis_time": round(elapsed, 1),
                    "report_path": "",
                    "status": "failed"
                })
                print(f"❌ 실패 ({elapsed:.1f}초)")
                
        except Exception as e:
            elapsed = time.time() - start_time
            results.append({
                "video": video_path.name,
                "total_score": 0,
                "grade": "ERROR",
                "teaching_expertise": 0,
                "teaching_method": 0,
                "communication": 0,
                "teaching_attitude": 0,
                "student_engagement": 0,
                "time_management": 0,
                "creativity": 0,
                "analysis_time": round(elapsed, 1),
                "report_path": "",
                "status": f"error: {str(e)[:50]}"
            })
            print(f"❌ 오류: {e}")
    
    total_elapsed = time.time() - total_start
    
    # CSV 요약 저장
    csv_path = batch_dir / "batch_summary.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        fieldnames = [
            "video", "total_score", "grade",
            "teaching_expertise", "teaching_method", "communication",
            "teaching_attitude", "student_engagement", "time_management",
            "creativity", "analysis_time", "status"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            row = {k: r.get(k, "") for k in fieldnames}
            writer.writerow(row)
    
    # JSON 요약 저장
    json_path = batch_dir / "batch_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "batch_time": batch_time,
            "total_videos": len(video_files),
            "total_time_seconds": round(total_elapsed, 1),
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    # 결과 출력
    print("\n" + "=" * 70)
    print("📊 배치 분석 완료!")
    print("=" * 70)
    
    successful = sum(1 for r in results if r["status"] == "success")
    avg_score = sum(r["total_score"] for r in results if r["status"] == "success") / max(successful, 1)
    
    print(f"\n📈 통계:")
    print(f"   - 성공: {successful}/{len(video_files)}개")
    print(f"   - 평균 점수: {avg_score:.1f}점")
    print(f"   - 총 소요 시간: {total_elapsed/60:.1f}분")
    
    print(f"\n📂 출력 디렉토리: {batch_dir}")
    print(f"   - CSV 요약: {csv_path.name}")
    print(f"   - JSON 결과: {json_path.name}")
    
    # 점수 분포 출력
    print(f"\n📋 개별 결과:")
    for r in results:
        status_icon = "✅" if r["status"] == "success" else "❌"
        print(f"   {status_icon} {r['video']}: {r['total_score']:.1f}점 ({r['grade']})")
    
    return results, str(batch_dir)


if __name__ == "__main__":
    run_batch_analysis()
