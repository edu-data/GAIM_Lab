"""QR 코드 생성 및 HTML 업데이트"""
import qrcode
import base64
from io import BytesIO
from pathlib import Path

# QR 코드 생성
url = "https://edu-data.github.io/GAIM_Lab/best_report_110545.html"
qr = qrcode.QRCode(version=1, box_size=10, border=4)
qr.add_data(url)
qr.make(fit=True)
img = qr.make_image(fill_color='black', back_color='white')

# Base64로 변환
buffer = BytesIO()
img.save(buffer, format='PNG')
b64 = base64.b64encode(buffer.getvalue()).decode()

print(f"QR Code Base64 length: {len(b64)}")
print("=" * 50)

# HTML 파일 업데이트
html_path = Path(r"D:\AI\GAIM_Lab\docs\best_report_110545.html")
content = html_path.read_text(encoding='utf-8')

# 기존 QR 코드 찾아서 교체
import re
old_qr_pattern = r'data:image/png;base64,[A-Za-z0-9+/=]+'
new_qr = f'data:image/png;base64,{b64}'
new_content = re.sub(old_qr_pattern, new_qr, content, count=1)

html_path.write_text(new_content, encoding='utf-8')
print(f"✅ QR 코드가 {url}로 업데이트되었습니다.")
