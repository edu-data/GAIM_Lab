"""
📥 YouTube 외부 영상 다운로드 & 분석
초등임용 2차 수업실연 만점 영상을 다운받아 GAIM Lab으로 분석한다.

사용법:
  python download_youtube_videos.py            # 다운로드만
  python download_youtube_videos.py --analyze  # 다운로드 + 분석
"""

import sys
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime

GAIM_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(GAIM_ROOT))

# 외부 영상 저장 디렉토리
EXT_VIDEO_DIR = GAIM_ROOT / "video" / "external"
EXT_VIDEO_DIR.mkdir(parents=True, exist_ok=True)

# 초등임용 2차 수업실연 만점 영상 후보
# 연구/교육 목적으로만 활용
YOUTUBE_VIDEOS = [
    {
        "url": "https://www.youtube.com/watch?v=A6E4_mmJ1E8",
        "title": "2022_서울_국어_수업실연_만점",
        "desc": "2022 서울 실연 만점자 국어 수업실연 (20:31)",
    },
    {
        "url": "https://www.youtube.com/watch?v=CgfCuoHwgZw",
        "title": "초등임용_일반_수업실연_300만뷰",
        "desc": "초등임용 2번 합격 일반 수업실연 (10:10)",
    },
    {
        "url": "https://www.youtube.com/watch?v=ZXSVBKAvUE4",
        "title": "2024_경기_수업실연_복기",
        "desc": "2024 경기 초등 수업실연 복기 (14:55)",
    },
]


def download_video(video_info: dict) -> Path:
    """yt-dlp로 영상 다운로드"""
    url = video_info["url"]
    title = video_info["title"]
    output_path = EXT_VIDEO_DIR / f"{title}.mp4"

    if output_path.exists():
        print(f"  ⏭️  이미 다운로드됨: {output_path.name}")
        return output_path

    print(f"  ⬇️  다운로드 중: {video_info['desc']}")
    print(f"     URL: {url}")

    try:
        cmd = [
            "yt-dlp",
            "-f", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best",
            "--merge-output-format", "mp4",
            "-o", str(output_path),
            "--no-playlist",
            "--socket-timeout", "30",
            url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode == 0 and output_path.exists():
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"  ✅ 다운로드 완료: {output_path.name} ({size_mb:.1f} MB)")
            return output_path
        else:
            print(f"  ❌ 다운로드 실패: {result.stderr[:200]}")
            return None
    except subprocess.TimeoutExpired:
        print(f"  ❌ 다운로드 시간 초과")
        return None
    except Exception as e:
        print(f"  ❌ 오류: {e}")
        return None


def analyze_video(video_path: Path, output_dir: Path):
    """GAIM Lab 분석 실행"""
    import importlib.util
    from dotenv import load_dotenv
    load_dotenv(GAIM_ROOT / ".env")

    spec = importlib.util.spec_from_file_location(
        "orchestrator", GAIM_ROOT / "core" / "agents" / "orchestrator.py"
    )
    orch_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(orch_mod)

    orch = orch_mod.AgentOrchestrator()
    cache_dir = str(output_dir / "cache")
    result = orch.run_pipeline(str(video_path), temp_dir=cache_dir)

    # 결과 저장
    result_file = output_dir / "agent_result.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)

    return result


def extract_scores(result):
    """결과에서 점수 추출"""
    report = result.get("report", {})
    ped = report.get("pedagogy", {})
    return {
        "total": ped.get("total_score", 0),
        "grade": ped.get("grade", ""),
        "dimensions": {d["name"]: d["score"] for d in ped.get("dimensions", [])},
    }


def main():
    do_analyze = "--analyze" in sys.argv

    print("=" * 60)
    print("📥 YouTube 초등임용 만점 수업실연 영상 다운로드")
    print("=" * 60)

    downloaded = []
    for i, video_info in enumerate(YOUTUBE_VIDEOS, 1):
        print(f"\n[{i}/{len(YOUTUBE_VIDEOS)}] {video_info['title']}")
        path = download_video(video_info)
        if path:
            downloaded.append({"path": path, "info": video_info})

    print(f"\n✅ {len(downloaded)}/{len(YOUTUBE_VIDEOS)}개 다운로드 완료")

    if not do_analyze:
        print("\n💡 분석하려면: python download_youtube_videos.py --analyze")
        return

    if not downloaded:
        print("❌ 분석할 영상이 없습니다.")
        return

    # 분석 실행
    print(f"\n{'='*60}")
    print("🔬 외부 영상 GAIM Lab 분석")
    print(f"{'='*60}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_base = GAIM_ROOT / "output" / f"external_analysis_{timestamp}"
    output_base.mkdir(parents=True, exist_ok=True)

    results = []
    for i, item in enumerate(downloaded, 1):
        video_path = item["path"]
        info = item["info"]

        print(f"\n[{i}/{len(downloaded)}] {info['title']}")
        out_dir = output_base / info["title"]
        out_dir.mkdir(parents=True, exist_ok=True)

        t_start = time.time()
        result = analyze_video(video_path, out_dir)
        elapsed = time.time() - t_start

        scores = extract_scores(result)
        stt = result.get("report", {}).get("stt", {})

        print(f"  총점: {scores['total']}점 ({scores['grade']})")
        print(f"  화자분리: {stt.get('diarization_method', 'N/A')}")
        print(f"  분석시간: {elapsed:.0f}s")

        results.append({
            "title": info["title"],
            "total": scores["total"],
            "grade": scores["grade"],
            "diarization": stt.get("diarization_method", "N/A"),
            "elapsed": round(elapsed, 1),
            **scores.get("dimensions", {}),
        })

    # 비교 출력
    print(f"\n{'='*60}")
    print("📊 외부 영상 분석 결과")
    print(f"{'='*60}")
    for r in results:
        print(f"  {r['title']}: {r['total']}점 ({r['grade']}) [화자분리: {r['diarization']}]")

    # 교내 평균과 비교
    internal_avg = 72.6  # v6.0 배치 평균
    ext_avg = sum(r["total"] for r in results) / len(results)
    print(f"\n  교내 영상 v6.0 평균: {internal_avg:.1f}점")
    print(f"  외부 만점 영상 평균: {ext_avg:.1f}점")
    print(f"  차이: {ext_avg - internal_avg:+.1f}점")

    print(f"\n📂 결과: {output_base}")


if __name__ == "__main__":
    main()
