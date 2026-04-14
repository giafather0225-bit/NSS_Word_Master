"""
이미지 전처리 모듈 — 교과서 뒷면 비침(bleed-through) 제거 및 OCR 정확도 향상
"""
import io
from PIL import Image, ImageEnhance, ImageFilter

def preprocess_for_ocr(image_bytes: bytes) -> bytes:
    """
    교과서 사진을 OCR에 최적화된 이미지로 변환.
    1) HEIC 등 → JPEG 변환
    2) 밝기(brightness) 올려서 희미한 비침 텍스트 제거
    3) 대비(contrast) 높여서 실제 텍스트 선명하게
    4) 선명도(sharpness) 강화
    5) 적정 해상도로 리사이즈 (너무 크면 축소)
    """
    img = Image.open(io.BytesIO(image_bytes))
    
    # RGBA → RGB 변환
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    # 1) 해상도 최적화: 긴 변 기준 2400px (300DPI A4 상당)
    max_side = 2400
    w, h = img.size
    if max(w, h) > max_side:
        ratio = max_side / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
    elif max(w, h) < 1200:
        # 너무 작으면 2배 업스케일
        img = img.resize((w * 2, h * 2), Image.LANCZOS)
    
    # 2) 밝기 올리기 — 희미한 비침 텍스트를 날림
    brightness = ImageEnhance.Brightness(img)
    img = brightness.enhance(1.15)
    
    # 3) 대비 높이기 — 실제 텍스트를 더 선명하게
    contrast = ImageEnhance.Contrast(img)
    img = contrast.enhance(1.5)
    
    # 4) 선명도 강화
    sharpness = ImageEnhance.Sharpness(img)
    img = sharpness.enhance(1.8)
    
    # JPEG로 변환 (품질 92)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()
