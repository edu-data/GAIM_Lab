# -*- coding: utf-8 -*-
"""
GAIM Lab - 일괄 영상 분석 스크립트
video 디렉토리의 모든 영상을 순차적으로 분석하고 결과를 CSV로 저장
"""

import sys
import io
import csv
import json
import argparse
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# Windows 콘솔 UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 프로젝트 루트 경로
GAIM_ROOT = Path(r"D:\AI\GAIM_Lab")
VIDEO_DIR = GAIM_ROOT / "video"
OUTPUT_DIR = GAIM_ROOT / "output" / "batch"


def load_module_from_path(module_name: str, file_path: Path):
    """특정 경로에서 모듈 로드"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# 모듈 직접 로드
timelapse_module = load_module_from_path(
    "timelapse_analyzer", 
    GAIM_ROOT / "core" / "analyzers" / "timelapse_analyzer.py"
)
TimeLapseAnalyzer = timelapse_module.TimeLapseAnalyzer

# backend/app 경로를 sys.path에 추가
sys.path.insert(0, str(GAIM_ROOT / "backend" / "app"))
from core.evaluator import GAIMLectureEvaluator
from services.report_generator import GAIMReportGenerator


def list_videos(limit: int = None) -> List[Path]:
    """영상 파일 목록 수집"""
    videos = sorted(VIDEO_DIR.glob("*.mp4"))
    if limit:
        videos = videos[:limit]
    return videos


def analyze_single(video_path: Path, output_dir: Path) -> Tuple[Dict, Path]:
    """
    개별 영상 분석 수행
    
    Args:
        video_path: 분석할 영상 파일 경로
        output_dir: 결과 출력 디렉토리
        
    Returns:
        (evaluation_dict, html_path) 튜플
    """
    video_name = video_path.stem
    video_output = output_dir / video_name
    video_output.mkdir(parents=True, exist_ok=True)
    
    # Phase 1: TimeLapse 분석
    analyzer = TimeLapseAnalyzer(temp_dir=str(video_output / "cache"))
    vision_results, content_results = analyzer.analyze_video(video_path)
    
    audio_metrics = analyzer.get_audio_metrics()
    elapsed_time = analyzer.get_elapsed_time()
    
    # Phase 2: 7차원 평가
    analysis_data = {
        "vision_metrics": _extract_vision_metrics(vision_results),
        "vibe_metrics": audio_metrics,
        "content_metrics": _extract_content_metrics(content_results),
        "text_metrics": {}
    }
    
    evaluator = GAIMLectureEvaluator()
    evaluation_result = evaluator.evaluate(analysis_data)
    evaluation_dict = evaluator.to_dict(evaluation_result)
    
    # 결과 저장
    result_path = video_output / "evaluation_result.json"
    with result_path.open("w", encoding="utf-8") as f:
        json.dump(evaluation_dict, f, ensure_ascii=False, indent=2)
    
    # Phase 3: 리포트 생성
    report_generator = GAIMReportGenerator(output_dir=video_output)
    html_path = report_generator.generate_html_report(evaluation_dict, video_name)
    
    # PDF 생성 시도
    try:
        report_generator.generate_pdf_report(evaluation_dict, video_name)
    except Exception:
        pass  # PDF 생성 실패 무시
    
    return evaluation_dict, html_path, elapsed_time


def _extract_vision_metrics(vision_results):
    """비전 분석 결과에서 메트릭 추출"""
    if not vision_results:
        return {}
    total = len(vision_results)
    eye_contact_count = sum(1 for r in vision_results if r.get("face_visible", False))
    gesture_count = sum(1 for r in vision_results if r.get("gesture_active", False))
    return {
        "eye_contact_ratio": eye_contact_count / total if total > 0 else 0,
        "gesture_ratio": gesture_count / total if total > 0 else 0,
        "frame_count": total
    }


def _extract_content_metrics(content_results):
    """콘텐츠 분석 결과에서 메트릭 추출"""
    if not content_results:
        return {}
    text_densities = [r.get("text_density", 0) for r in content_results if r.get("text_density")]
    return {
        "slide_changes": len(content_results),
        "avg_text_density": sum(text_densities) / len(text_densities) if text_densities else 0
    }


def export_summary_csv(results: List[Dict], output_path: Path):
    """결과 요약 CSV 출력"""
    if not results:
        print("No results to export")
        return
    
    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        
        # 헤더
        headers = [
            "영상파일", "총점", "등급", 
            "수업전문성", "교수학습방법", "판서및언어", 
            "수업태도", "학생참여", "시간배분", "창의성",
            "분석시간(초)", "HTML리포트"
        ]
        writer.writerow(headers)
        
        # 데이터
        for r in results:
            dims = {d["name"]: d["score"] for d in r.get("dimensions", [])}
            row = [
                r.get("video_name", ""),
                r.get("total_score", 0),
                r.get("grade", ""),
                dims.get("수업 전문성", 0),
                dims.get("교수학습 방법", 0),
                dims.get("판서 및 언어", 0),
                dims.get("수업 태도", 0),
                dims.get("학생 참여", 0),
                dims.get("시간 배분", 0),
                dims.get("창의성", 0),
                r.get("elapsed_time", 0),
                r.get("html_path", "")
            ]
            writer.writerow(row)
    
    print(f"\n[CSV] 결과 저장: {output_path}")


def run_batch(limit: int = None, skip_existing: bool = True):
    """
    전체 배치 분석 실행
    
    Args:
        limit: 분석할 영상 수 제한 (None이면 전체)
        skip_existing: 이미 분석된 영상 건너뛰기
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_output = OUTPUT_DIR / f"batch_{timestamp}"
    batch_output.mkdir(parents=True, exist_ok=True)
    
    videos = list_videos(limit)
    total = len(videos)
    
    print("=" * 60)
    print(f"🎬 GAIM Lab 일괄 분석 시작")
    print(f"📁 영상 디렉토리: {VIDEO_DIR}")
    print(f"📂 출력 디렉토리: {batch_output}")
    print(f"📊 분석 대상: {total}개 영상")
    print("=" * 60)
    
    results = []
    success_count = 0
    fail_count = 0
    
    for idx, video in enumerate(videos, 1):
        print(f"\n[{idx}/{total}] 분석 중: {video.name}")
        print("-" * 40)
        
        try:
            eval_dict, html_path_str, elapsed = analyze_single(video, batch_output)
            
            # 결과 저장
            eval_dict["video_name"] = video.name
            eval_dict["elapsed_time"] = round(elapsed, 1)
            eval_dict["html_path"] = str(Path(html_path_str).relative_to(batch_output))
            results.append(eval_dict)
            
            print(f"   ✅ 완료 | 총점: {eval_dict['total_score']:.1f} | 등급: {eval_dict['grade']} | {elapsed:.1f}초")
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ 실패: {e}")
            fail_count += 1
            results.append({
                "video_name": video.name,
                "error": str(e)
            })
    
    # CSV 출력
    csv_path = batch_output / "batch_results.csv"
    export_summary_csv([r for r in results if "error" not in r], csv_path)
    
    # 최종 요약
    print("\n" + "=" * 60)
    print("✅ 일괄 분석 완료!")
    print("=" * 60)
    print(f"   성공: {success_count}개")
    print(f"   실패: {fail_count}개")
    print(f"   결과: {csv_path}")
    print(f"   디렉토리: {batch_output}")
    
    return results, batch_output


def main():
    parser = argparse.ArgumentParser(description="GAIM Lab 일괄 영상 분석")
    parser.add_argument("--limit", type=int, default=None, help="분석할 영상 수 제한")
    parser.add_argument("--list", action="store_true", help="영상 목록만 출력")
    args = parser.parse_args()
    
    if args.list:
        videos = list_videos()
        print(f"\n📁 영상 목록 ({len(videos)}개):")
        for i, v in enumerate(videos, 1):
            size_mb = v.stat().st_size / (1024 * 1024)
            print(f"   {i:2d}. {v.name} ({size_mb:.0f}MB)")
        return
    
    run_batch(limit=args.limit)


if __name__ == "__main__":
    main()
