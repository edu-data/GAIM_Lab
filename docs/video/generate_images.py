# -*- coding: utf-8 -*-
"""
GAIM Lab 프로모션 비디오용 이미지 생성 스크립트
"""

from PIL import Image, ImageDraw, ImageFont
import os

# 기본 설정
WIDTH = 1920
HEIGHT = 1080
BG_COLOR_TOP = (10, 10, 40)  # 진한 네이비
BG_COLOR_BOTTOM = (20, 50, 100)  # 진한 파란색
ACCENT_COLOR = (0, 200, 255)  # 시안
TEXT_COLOR = (255, 255, 255)  # 흰색
SECONDARY_TEXT = (180, 180, 200)  # 연한 회색

def create_gradient_background():
    """그라데이션 배경 생성"""
    img = Image.new('RGB', (WIDTH, HEIGHT))
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(BG_COLOR_TOP[0] * (1 - ratio) + BG_COLOR_BOTTOM[0] * ratio)
        g = int(BG_COLOR_TOP[1] * (1 - ratio) + BG_COLOR_BOTTOM[1] * ratio)
        b = int(BG_COLOR_TOP[2] * (1 - ratio) + BG_COLOR_BOTTOM[2] * ratio)
        for x in range(WIDTH):
            img.putpixel((x, y), (r, g, b))
    return img

def get_font(size, bold=False):
    """시스템 폰트 가져오기"""
    font_paths = [
        "C:/Windows/Fonts/malgun.ttf",      # 맑은 고딕
        "C:/Windows/Fonts/malgunbd.ttf",    # 맑은 고딕 Bold
        "C:/Windows/Fonts/segoeui.ttf",     # Segoe UI
        "C:/Windows/Fonts/arial.ttf",       # Arial
    ]
    if bold:
        font_paths.insert(0, "C:/Windows/Fonts/malgunbd.ttf")
    
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def create_framework_image():
    """7차원 평가 프레임워크 이미지 생성"""
    img = create_gradient_background()
    draw = ImageDraw.Draw(img)
    
    # 제목
    title_font = get_font(60, bold=True)
    title = "7차원 평가 프레임워크"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = bbox[2] - bbox[0]
    draw.text(((WIDTH - title_width) // 2, 60), title, font=title_font, fill=ACCENT_COLOR)
    
    # 부제목
    subtitle_font = get_font(28)
    subtitle = "초등 임용 2차 수업실연 평가 기준 기반 100점 만점 체계적 평가"
    bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    subtitle_width = bbox[2] - bbox[0]
    draw.text(((WIDTH - subtitle_width) // 2, 140), subtitle, font=subtitle_font, fill=SECONDARY_TEXT)
    
    # 평가 항목들
    dimensions = [
        ("교수·학습 방법", 20, 100),
        ("학습 내용", 15, 75),
        ("학습자 상호작용", 15, 75),
        ("교사 언어", 15, 75),
        ("수업 분위기", 15, 75),
        ("교수·학습 자료", 10, 50),
        ("비언어적 요소", 10, 50),
    ]
    
    start_y = 200
    bar_width = 800
    bar_height = 50
    bar_x = (WIDTH - bar_width) // 2
    
    item_font = get_font(32, bold=True)
    score_font = get_font(28)
    
    for i, (name, score, percent) in enumerate(dimensions):
        y = start_y + i * 100
        
        # 항목 이름
        draw.text((bar_x, y), name, font=item_font, fill=TEXT_COLOR)
        
        # 점수 표시
        score_text = f"{score}점"
        draw.text((bar_x + bar_width - 80, y), score_text, font=score_font, fill=ACCENT_COLOR)
        
        # 진행 바 배경
        bar_y = y + 45
        draw.rounded_rectangle(
            [(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)],
            radius=10,
            fill=(40, 40, 60)
        )
        
        # 진행 바 채우기
        fill_width = int(bar_width * percent / 100)
        if fill_width > 0:
            # 그라데이션 효과
            for dx in range(fill_width):
                ratio = dx / fill_width
                color = (
                    int(0 * (1 - ratio) + 100 * ratio),
                    int(150 * (1 - ratio) + 220 * ratio),
                    int(255 * (1 - ratio) + 255 * ratio),
                )
                draw.line([(bar_x + dx, bar_y + 5), (bar_x + dx, bar_y + bar_height - 5)], fill=color)
    
    # 총점
    total_font = get_font(48, bold=True)
    total_text = "총점: 100점"
    bbox = draw.textbbox((0, 0), total_text, font=total_font)
    total_width = bbox[2] - bbox[0]
    draw.text(((WIDTH - total_width) // 2, 940), total_text, font=total_font, fill=ACCENT_COLOR)
    
    return img

def create_techstack_image():
    """기술 스택 이미지 생성"""
    img = create_gradient_background()
    draw = ImageDraw.Draw(img)
    
    # 제목
    title_font = get_font(60, bold=True)
    title = "기술 스택"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = bbox[2] - bbox[0]
    draw.text(((WIDTH - title_width) // 2, 80), title, font=title_font, fill=ACCENT_COLOR)
    
    # 카테고리들
    categories = [
        ("Backend", ["FastAPI", "Python 3.9+", "WebSocket"]),
        ("Frontend", ["React 18", "Vite", "Chart.js"]),
        ("AI & Analysis", ["FFmpeg GPU", "Gemini AI", "Multiprocessing"]),
        ("Testing", ["Vitest", "Playwright", "E2E Tests"]),
    ]
    
    category_width = 400
    start_x = (WIDTH - (len(categories) * category_width)) // 2
    start_y = 200
    
    category_font = get_font(36, bold=True)
    badge_font = get_font(24)
    
    for i, (cat_name, items) in enumerate(categories):
        x = start_x + i * category_width + category_width // 2
        
        # 카테고리 이름
        bbox = draw.textbbox((0, 0), cat_name, font=category_font)
        cat_width = bbox[2] - bbox[0]
        draw.text((x - cat_width // 2, start_y), cat_name, font=category_font, fill=TEXT_COLOR)
        
        # 배지들
        badge_y = start_y + 80
        for j, item in enumerate(items):
            y = badge_y + j * 70
            
            # 배지 배경
            bbox = draw.textbbox((0, 0), item, font=badge_font)
            item_width = bbox[2] - bbox[0]
            padding = 30
            
            badge_x1 = x - item_width // 2 - padding
            badge_x2 = x + item_width // 2 + padding
            
            draw.rounded_rectangle(
                [(badge_x1, y), (badge_x2, y + 50)],
                radius=25,
                fill=(40, 80, 120),
                outline=ACCENT_COLOR,
                width=2
            )
            
            # 배지 텍스트
            draw.text((x - item_width // 2, y + 12), item, font=badge_font, fill=TEXT_COLOR)
    
    # 하단 특징
    feature_y = 700
    features = [
        "🚀 GPU 가속 처리",
        "⚡ 실시간 WebSocket",
        "🤖 Gemini AI 분석",
        "✅ 완전한 테스트 커버리지"
    ]
    
    feature_font = get_font(28)
    feature_start_x = (WIDTH - 1200) // 2
    
    for i, feature in enumerate(features):
        x = feature_start_x + i * 300
        bbox = draw.textbbox((0, 0), feature, font=feature_font)
        fw = bbox[2] - bbox[0]
        draw.text((x + 150 - fw // 2, feature_y), feature, font=feature_font, fill=SECONDARY_TEXT)
    
    return img

def create_outro_image():
    """종료 이미지 생성"""
    img = create_gradient_background()
    draw = ImageDraw.Draw(img)
    
    # 로고 (이모지 대신 텍스트)
    logo_font = get_font(100, bold=True)
    logo = "🎓 GAIM Lab"
    bbox = draw.textbbox((0, 0), logo, font=logo_font)
    logo_width = bbox[2] - bbox[0]
    draw.text(((WIDTH - logo_width) // 2, 280), logo, font=logo_font, fill=ACCENT_COLOR)
    
    # 기관명
    org_font = get_font(48)
    org = "경인교육대학교"
    bbox = draw.textbbox((0, 0), org, font=org_font)
    org_width = bbox[2] - bbox[0]
    draw.text(((WIDTH - org_width) // 2, 450), org, font=org_font, fill=TEXT_COLOR)
    
    # 영문명
    eng_font = get_font(32)
    eng = "GINUE AI Microteaching Lab"
    bbox = draw.textbbox((0, 0), eng, font=eng_font)
    eng_width = bbox[2] - bbox[0]
    draw.text(((WIDTH - eng_width) // 2, 520), eng, font=eng_font, fill=SECONDARY_TEXT)
    
    # 이메일
    email_font = get_font(28)
    email = "📧 educpa@ginue.ac.kr"
    bbox = draw.textbbox((0, 0), email, font=email_font)
    email_width = bbox[2] - bbox[0]
    draw.text(((WIDTH - email_width) // 2, 620), email, font=email_font, fill=SECONDARY_TEXT)
    
    # GitHub
    github = "🔗 github.com/edu-data/GAIM_Lab"
    bbox = draw.textbbox((0, 0), github, font=email_font)
    github_width = bbox[2] - bbox[0]
    draw.text(((WIDTH - github_width) // 2, 670), github, font=email_font, fill=SECONDARY_TEXT)
    
    # 저작권
    copyright_font = get_font(24)
    copyright_text = "© 2026 GAIM Lab. All rights reserved."
    bbox = draw.textbbox((0, 0), copyright_text, font=copyright_font)
    cr_width = bbox[2] - bbox[0]
    draw.text(((WIDTH - cr_width) // 2, 900), copyright_text, font=copyright_font, fill=(120, 120, 140))
    
    return img

if __name__ == "__main__":
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("Generating 7-dimension framework image...")
    framework_img = create_framework_image()
    framework_img.save(os.path.join(output_dir, "slide_framework.png"), "PNG")
    print("[OK] slide_framework.png saved")
    
    print("Generating tech stack image...")
    techstack_img = create_techstack_image()
    techstack_img.save(os.path.join(output_dir, "slide_techstack.png"), "PNG")
    print("[OK] slide_techstack.png saved")
    
    print("Generating outro image...")
    outro_img = create_outro_image()
    outro_img.save(os.path.join(output_dir, "slide_outro.png"), "PNG")
    print("[OK] slide_outro.png saved")
    
    print("\nAll images generated successfully!")
