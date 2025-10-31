import io
import zipfile
from pathlib import Path
import streamlit as st
from PIL import Image, ImageOps

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_ENABLED = True
except Exception:
    HEIC_ENABLED = False

st.set_page_config(page_title="画像をWebPに変換", page_icon="🖼️", layout="centered")
st.title("🖼️ 画像をまとめて WebP に変換")
st.caption("JPG / JPEG / PNG / GIF / BMP / TIFF / HEIC などを一括アップロードして WebP 形式に変換できます。")

col1, col2 = st.columns(2)
with col1:
    quality = st.slider("品質（quality）", 50, 100, 90)
with col2:
    keep_transparency = st.toggle("透過を保持する", value=True)

bg_hex = st.color_picker("透過を埋める背景色（透過を保持しない場合）", "#FFFFFF")
bg_rgb = tuple(int(bg_hex[i:i+2], 16) for i in (1, 3, 5))

accept_exts = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp"]
if HEIC_ENABLED:
    accept_exts += [".heic", ".heif"]

uploaded_files = st.file_uploader("画像ファイルをアップロード（複数可）", type=[e.strip(".") for e in accept_exts], accept_multiple_files=True)

def to_webp(data: bytes, filename: str) -> tuple[bytes, str]:
    im = Image.open(io.BytesIO(data))
    im = ImageOps.exif_transpose(im)
    if im.mode in ("RGBA", "LA") and not keep_transparency:
        bg = Image.new("RGB", im.size, bg_rgb)
        bg.paste(im, mask=im.split()[-1])
        im = bg
    im = im.convert("RGBA" if keep_transparency else "RGB")
    out = io.BytesIO()
    im.save(out, "WEBP", quality=quality, method=6)
    out.seek(0)
    return out.read(), f"{Path(filename).stem}.webp"

if uploaded_files:
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in uploaded_files:
            try:
                webp_bytes, name = to_webp(file.read(), file.name)
                st.download_button(f"⬇️ {name} をダウンロード", webp_bytes, name, mime="image/webp")
                zf.writestr(name, webp_bytes)
            except Exception as e:
                st.error(f"{file.name} の変換に失敗しました: {e}")

    zip_buf.seek(0)
    st.download_button("🗜️ すべてをZIPでダウンロード", zip_buf, "converted_webp.zip", mime="application/zip")

st.caption("対応拡張子: " + ", ".join(accept_exts))
