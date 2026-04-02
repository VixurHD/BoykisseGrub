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

def blurGaussian(img: Image.Image, radius: float = 2) -> Image.Image:
    return img.filter(ImageFilter.GaussianBlur(radius))

# Trangle Blur (camera object)
def blurLens(img: Image.Image, radius: float = 5) -> Image.Image:
    def triangleKernel(r: float) -> NDArray[np.float64]:
        size: int = int(2*r + 1)
        k: NDArray[np.float64] = np.array([r + 1 - abs(i - r) for i in range(size)], dtype=float)
        return k / k.sum()

    def convolve(arr: NDArray[np.float64], kernel: NDArray[np.float64], axis: int) -> NDArray[np.float64]:
        pad: int = len(kernel) // 2
        arr = np.pad(arr, pad_width=[(pad, pad) if i == axis else (0, 0) for i in range(arr.ndim)], mode="reflect")
        out: NDArray[np.float64] = np.zeros_like(arr)
        for i, w in enumerate(kernel):
            if axis == 0:
                out += w * arr[i:i + arr.shape[0]]
            else:
                out += w * arr[:, i:i + arr.shape[1]]
        return out

    k: NDArray[np.float64] = triangleKernel(radius)
    arr: NDArray[np.float64] = np.array(img, dtype=float)
    arr: NDArray[np.float64] = convolve(arr, kernel=k, axis=0)
    arr: NDArray[np.float64] = convolve(arr, kernel=k, axis=1)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode=img.mode)


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

if __name__ == "__main__":
    # TODO
    pass


# # test
# img: Image.Image = load("image.png")

# img = blurGaussian(img, 3)

# left, top, right, bottom = textSize("TestTestTTTTTTestestestestestest", 40)
# text_w = right - left

# width_right_image:  int = img.width // 3;
# width_left_image:   int = img.width // 3;
# width_middle_image: int = img.width - 2*(img.width // 3);

# left_img: Image.Image = img.crop( (
#     0                , 0,         # of
#     width_left_image, img.height  # to
# ) )
# middle_img: Image.Image = img.crop( (
#     width_left_image  , 0,
#     width_left_image + width_middle_image, img.height
# ) )
# right_img: Image.Image = img.crop( (
#     width_left_image + width_middle_image, 0,
#     img.width, img.height
# ) )

# left_part: Image.Image = left_img;
# right_part: Image.Image = right_img
# middle_part: Image.Image = tileInLenImg(
#     middle_img,
#     round(text_w) - width_right_image*2
# )
# canvas = Image.new(
#     "RGBA",
#     (left_part.width + right_part.width + middle_part.width, img.height),
#     (0, 0, 0, 0)
# )

# canvas.paste(left_part, (0, 0))
# canvas.paste(middle_part, (left_part.width, 0))
# canvas.paste(right_part, (left_part.width + middle_part.width, 0))

# img = drawText(canvas, "TestTestTTTTTTestestestestestest", 50, 50, size=40)

# save(img, "out.png")
