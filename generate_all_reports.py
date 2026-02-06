"""
GAIM Lab - HTML 리포트 일괄 생성 및 시각화 스크립트
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 경로
GAIM_ROOT = Path(r"D:\AI\GAIM_Lab")
sys.path.insert(0, str(GAIM_ROOT / "backend" / "app"))

from services.report_generator_v2 import GAIMReportGeneratorV2

def generate_all_reports():
    """모든 영상에 대한 HTML 리포트 생성"""
    batch_dir = Path(r"D:\AI\GAIM_Lab\output\batch_v2_20260206_181255")
    
    success_count = 0
    error_count = 0
    
    print("=" * 70)
    print("🚀 GAIM Lab HTML 리포트 일괄 생성")
    print("=" * 70)
    
    for video_dir in sorted(batch_dir.iterdir()):
        if not video_dir.is_dir():
            continue
            
        eval_file = video_dir / "evaluation_result.json"
        if not eval_file.exists():
            continue
            
        video_name = video_dir.name
        print(f"\n📹 {video_name} 처리 중...")
        
        try:
            with open(eval_file, "r", encoding="utf-8") as f:
                evaluation = json.load(f)
            
            # HTML 리포트 생성
            generator = GAIMReportGeneratorV2(output_dir=video_dir)
            report_path = generator.generate_html_report(
                evaluation=evaluation,
                video_name=video_name
            )
            
            print(f"   ✅ 생성 완료: {Path(report_path).name}")
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ 오류: {e}")
            error_count += 1
    
    print(f"\n{'=' * 70}")
    print(f"📊 결과: 성공 {success_count}개 / 오류 {error_count}개")
    print("=" * 70)
    
    return success_count, error_count

if __name__ == "__main__":
    generate_all_reports()
