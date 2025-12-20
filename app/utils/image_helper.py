import io
import base64

from PIL import Image


def resize_image_for_analysis(base64_str, max_width=1024, quality=80):
    """
    Decodes a base64 image, resizes it if it exceeds max_width,
    and returns the optimized base64 string.
    """
    try:
        # 1. Strip header if present
        if "," in base64_str:
            base64_str = base64_str.split(",")[1]

        # 2. Decode to bytes
        image_data = base64.b64decode(base64_str)
        img = Image.open(io.BytesIO(image_data))

        # 3. Convert to RGB (in case of PNG with transparency)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # 4. Resize if width > max_width
        width, height = img.size
        if width > max_width:
            ratio = max_width / width
            new_height = int(height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

        # 5. Compress to JPEG
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    except Exception as e:
        print(f"Image Resizing Error: {e}")
        return base64_str  # Return original if resizing fails
