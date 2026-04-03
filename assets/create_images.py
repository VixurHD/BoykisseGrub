from PIL import Image, ImageDraw, ImageFont, ImageFilter
import cairosvg
import io
import numpy as np
from typing import TypeAlias
from numpy.typing import NDArray
import re

T_PATH_STR: TypeAlias = str
T_RGB: TypeAlias = tuple[int, int, int]

def load(path: T_PATH_STR) -> Image.Image:
    return Image.open(path).convert("RGBA")

def save(img: Image.Image, path: T_PATH_STR) -> Image.Image:
    img.save(path)
    return img

def sliceImg(img: Image.Image, x_start: int , width: int) -> Image.Image:
    return img.crop( (
        x_start, 0, # of
        x_start + width, img.height # to
    ) );

# Position the image horizontally to create a new image with a total width up to len_
def tileInLenImg(img: Image.Image, len_: int) -> Image.Image:
    tiles_count: int = len_ // img.width;
    canvas: Image.Image= Image.new("RGBA", (tiles_count*img.width, img.height), (0, 0, 0, 0));
    for i in range(tiles_count):
        canvas.paste(img, (i*img.width, 0));
    return canvas;

def glow(img: Image.Image) -> Image.Image:
    out = Image.new("RGBA", img.size, (0,0,0,0))
    for radius in [20, 10, 5, 4, 2, 1]:
        layer = img.filter(ImageFilter.GaussianBlur(radius))
        out = Image.alpha_composite(out, layer)
    return out

def drawText(img: Image.Image, text: str, x: int, y: int, size: int = 32, color: T_RGB = (0,0,0)) -> Image.Image:
    font: ImageFont.FreeTypeFont = ImageFont.truetype("DejaVuSans.ttf", size)
    draw: ImageDraw.ImageDraw = ImageDraw.Draw(img)
    draw.text((x, y), text, font=font, fill=color)
    return img

# Give expected size of text
def textSize(text, size=32) -> tuple[float, float, float, float]:
    font: ImageFont.FreeTypeFont = ImageFont.truetype("DejaVuSans.ttf", size)
    dummy: ImageDraw.ImageDraw = ImageDraw.Draw(Image.new("RGBA", (1,1)))
    return dummy.textbbox((0,0), text, font=font)

# Converts svg to pil with magnification to the maximum
def svgToPil(svg_path: T_PATH_STR, max_width: int, max_height: int, dpi: int = 96) -> Image.Image:

    with open(svg_path, "r", encoding="utf-8") as f:
        content = f.read()

    w = re.search(r'<svg[^>]+width=["\']([0-9.]+)', content)
    h = re.search(r'<svg[^>]+height=["\']([0-9.]+)', content)

    if w and h:
        svg_w, svg_h = float(w.group(1)), float(h.group(1))
    else:
        vb = re.search(r'viewBox=["\']([0-9. ]+)["\']', content)
        if not vb:
            raise ValueError("Не удалось определить размер SVG")
        _, _, svg_w, svg_h = map(float, vb.group(1).split())

    scale = min(max_width / svg_w, max_height / svg_h)

    png_bytes = cairosvg.svg2png(
        bytestring=content.encode(),
        output_width=int(svg_w * scale),
        output_height=int(svg_h * scale),
        dpi=dpi,
    )
    assert png_bytes is not None
    return Image.open(io.BytesIO(png_bytes)).convert("RGBA")

def createFoDistr(name_distr: str, screen_size: tuple[int, int] = (1920, 1080)):
    img_logo: Image.Image = svgToPil(f"./images/distrs/{name_distr}/logo.svg", 700, 900)
    img_text: Image.Image = svgToPil(f"./images/distrs/{name_distr}/text.svg", 900, 300)
    img_canvas: Image.Image = Image.new("RGBA", screen_size, (0, 7, 17, 255));

    img_logo_glow = glow(img_logo);
    # img_text_blur = blurLens(img_text, 8);

    img_compositor = Image.new("RGBA", screen_size, (0, 0, 0, 0));

    img_compositor.paste(img_logo_glow, (0, 0)); #TODO set correct positions
    img_canvas = Image.alpha_composite(img_canvas, img_compositor);

    # img_compositor.paste(img_text_blur, (700, 0)); #TODO set correct positions
    # img_canvas = Image.alpha_composite(img_canvas, img_compositor);
    # img_canvas.paste(img_text, (700, 0), img_text);

    save(img_canvas, "./out.png");

if __name__ == "__main__":
    import sys
    args = sys.argv;
    print(args);
    createFoDistr(args[1]);
