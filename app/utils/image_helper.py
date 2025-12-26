import io
import os
import base64

from PIL import Image


def optimize_image_stream(file_storage, max_dimension=1500, quality=80) -> bytes:
    """
    Smart Optimization:
    1. If file is already small (<1MB) and WebP -> Return bytes immediately.
    2. Otherwise -> Resize and compress (Fallback for API clients/errors).
    """
    try:
        # 1. Get file size without reading into memory yet
        file_storage.seek(0, os.SEEK_END)
        file_size = file_storage.tell()
        file_storage.seek(0)  # Reset cursor to start

        # SMART CHECK: If frontend did its job, don't re-compress (Avoids generation loss)
        # Check if size is < 1MB and MIME type is webp
        if file_size < 1 * 1024 * 1024 and file_storage.mimetype == 'image/webp':
            return file_storage.read()

        # --- Fallback (Heavy Processing) ---
        # Only runs if user bypasses frontend or sends a massive raw PNG
        img = Image.open(file_storage)

        # Handle Transparency
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Resize (Longest Edge)
        width, height = img.size
        max_side = max(width, height)
        if max_side > max_dimension:
            scale_factor = max_dimension / max_side
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Compress
        buffer = io.BytesIO()
        img.save(buffer, format="WEBP", quality=quality, method=4)
        return buffer.getvalue()

    except Exception as e:
        print(f"Optimization Error: {e}")
        return None
