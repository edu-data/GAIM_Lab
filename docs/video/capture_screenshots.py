# -*- coding: utf-8 -*-
"""
GAIM Lab 홈페이지 스크린샷 캡처 스크립트
Playwright를 사용하여 각 섹션을 캡처합니다.
"""

from playwright.sync_api import sync_playwright
import os

def capture_screenshots():
    output_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(os.path.dirname(output_dir), "index.html")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        
        # 로컬 HTML 파일 열기
        page.goto(f"file:///{html_path}")
        page.wait_for_timeout(2000)  # 애니메이션 대기
        
        # 1. Hero 섹션 캡처
        print("Capturing Hero section...")
        page.screenshot(path=os.path.join(output_dir, "capture_hero.png"))
        print("[OK] capture_hero.png saved")
        
        # 2. 7차원 평가 프레임워크 섹션 캡처
        print("Capturing 7-dimension framework section...")
        page.evaluate("document.querySelector('#evaluation').scrollIntoView({behavior: 'instant'})")
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(output_dir, "capture_framework.png"))
        print("[OK] capture_framework.png saved")
        
        # 3. 기술 스택 섹션 캡처
        print("Capturing Tech Stack section...")
        page.evaluate("document.querySelector('#tech').scrollIntoView({behavior: 'instant'})")
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(output_dir, "capture_techstack.png"))
        print("[OK] capture_techstack.png saved")
        
        # 4. Footer 섹션 캡처
        print("Capturing Footer section...")
        page.evaluate("document.querySelector('.footer').scrollIntoView({behavior: 'instant'})")
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(output_dir, "capture_footer.png"))
        print("[OK] capture_footer.png saved")
        
        browser.close()
        print("\nAll screenshots captured successfully!")

if __name__ == "__main__":
    capture_screenshots()
