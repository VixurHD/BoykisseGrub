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
    out = Image.new("RGBA", (img.width+40, img.height+40), (0,0,0,0))
    paded_img = Image.new("RGBA", out.size)
    paded_img.paste(img, (20, 20))
    comp_canvas: Image.Image = Image.new("RGBA", out.size)
    for radius in [20, 10, 5, 4, 2, 1]:
        layer = paded_img.filter(ImageFilter.GaussianBlur(radius))
        comp_canvas.paste(layer, (0, 0))
        out = Image.alpha_composite(out, comp_canvas)
    return out

def drawText(img: Image.Image, text: str, x: int, y: int, size: int = 32, color: T_RGB = (0,0,0)) -> Image.Image:
    font: ImageFont.FreeTypeFont = ImageFont.truetype("assets/Comfortaa/static/Comfortaa-Regular.ttf", size)
    draw: ImageDraw.ImageDraw = ImageDraw.Draw(img)
    draw.text((x, y), text, font=font, fill=color)
    return img

# Give expected size of text
def textSize(text, size=32) -> tuple[float, float, float, float]:
    font: ImageFont.FreeTypeFont = ImageFont.truetype("assets/Comfortaa/static/Comfortaa-Regular.ttf", size)
    dummy: ImageDraw.ImageDraw = ImageDraw.Draw(Image.new("RGBA", (1,1)))
    return dummy.textbbox((0,0), text, font=font)

def accentFromSvg(svg_path: T_PATH_STR, sample_size: int = 64) -> T_RGB:
    img = svgToPil(svg_path, sample_size, sample_size)
    arr = np.array(img)

    mask = arr[:, :, 3] > 128
    pixels = arr[mask][:, :3]

    if len(pixels) == 0:
        return (255, 255, 255)

    r, g, b = pixels[:, 0].astype(float), pixels[:, 1].astype(float), pixels[:, 2].astype(float)
    max_rgb = np.maximum(np.maximum(r, g), b)
    min_rgb = np.minimum(np.minimum(r, g), b)
    saturation = np.where(max_rgb > 0, (max_rgb - min_rgb) / max_rgb, 0)

    top_n = min(50, len(saturation))
    top_indices = np.argpartition(saturation, -top_n)[-top_n:]
    top_pixels = pixels[top_indices]
    mean = top_pixels.mean(axis=0)
    return (int(mean[0]), int(mean[1]), int(mean[2]))

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

def renderBackground(name_distr: str, screen_size: tuple[int, int] = (1920, 1080)) -> Image.Image:
    img_logo: Image.Image = svgToPil(f"assets/images/distrs/{name_distr}/logo.svg", 862, 862)
    img_text: Image.Image = svgToPil(f"assets/images/distrs/{name_distr}/text.svg", 650, 180)
    img_canvas: Image.Image = Image.new("RGBA", screen_size, (0, 7, 17, 255));

    img_logo_glow = glow(img_logo);
    img_text_glow = glow(img_text);

    img_boykisser: Image.Image = load("assets/images/boykisser.png")

    img_compositor = Image.new("RGBA", screen_size, (0, 0, 0, 0));

    img_compositor.paste(img_logo_glow, (1042+(882-img_logo_glow.width), 932-img_logo_glow.height));
    img_canvas = Image.alpha_composite(img_canvas, img_compositor);

    img_compositor.paste((0, 0, 0, 0), (0, 0, *screen_size))

    img_compositor.paste(img_text_glow, (1067-img_text_glow.width, 870-img_text_glow.height));
    img_canvas = Image.alpha_composite(img_canvas, img_compositor);

    img_canvas = Image.alpha_composite(img_canvas,  img_boykisser)

    return img_canvas;

def joinButton(*parts: Image.Image) -> Image.Image:
    total_w = sum(p.width for p in parts)
    h = parts[0].height
    out = Image.new("RGBA", (total_w, h), (0, 0, 0, 0))
    x = 0
    for p in parts:
        out.paste(p, (x, 0))
        x += p.width
    return out

def renderButtons(img_canvas: Image.Image, distrs_list: list[str], select_index: int, accent_color: T_RGB) -> Image.Image:
    max_size: float = 0
    for text in distrs_list:
        size: float = textSize(text, 32)[2] - textSize(text, 32)[0]
        if size > max_size: max_size = size

    img_button_unselect_base:      Image.Image = load("assets/images/buttons/standart.png").resize((60, 60))
    img_button_unselect_base_mask: Image.Image = load("assets/images/buttons/standart_mask.png").resize((60, 60))
    img_button_select_base:        Image.Image = load("assets/images/buttons/select.png").resize((60, 60))
    img_button_select_base_mask:   Image.Image = load("assets/images/buttons/select_mask.png").resize((60, 60))

    part_lr_size: int = img_button_unselect_base.width // 3;
    w: int = img_button_unselect_base.width
    h: int = img_button_unselect_base.height;

    img_left_unselect:        Image.Image = sliceImg(img_button_unselect_base,      0,       part_lr_size)
    img_center_unselect:      Image.Image = sliceImg(img_button_unselect_base,      part_lr_size,       w - part_lr_size*2)
    img_right_unselect:       Image.Image = sliceImg(img_button_unselect_base,      w - part_lr_size,   part_lr_size)

    img_left_unselect_mask:   Image.Image = sliceImg(img_button_unselect_base_mask, 0,       part_lr_size)
    img_center_unselect_mask: Image.Image = sliceImg(img_button_unselect_base_mask, part_lr_size,       w - part_lr_size*2)
    img_right_unselect_mask:  Image.Image = sliceImg(img_button_unselect_base_mask, w - part_lr_size,   part_lr_size)

    img_left_select:          Image.Image = sliceImg(img_button_select_base,        0,       part_lr_size)
    img_center_select:        Image.Image = sliceImg(img_button_select_base,        part_lr_size,       w - part_lr_size*2)
    img_right_select:         Image.Image = sliceImg(img_button_select_base,        w - part_lr_size,   part_lr_size)

    img_left_select_mask:     Image.Image = sliceImg(img_button_select_base_mask,   0,       part_lr_size);
    img_center_select_mask:   Image.Image = sliceImg(img_button_select_base_mask,   part_lr_size,       w - part_lr_size*2)
    img_right_select_mask:    Image.Image = sliceImg(img_button_select_base_mask,   w - part_lr_size,   part_lr_size)

    tile_w: int = int(max_size) + 50

    tiled_unselect: Image.Image = tileInLenImg(img_center_unselect, tile_w)
    tiled_unselect_mask: Image.Image = tileInLenImg(img_center_unselect_mask, tile_w)
    tiled_select: Image.Image = tileInLenImg(img_center_select, tile_w)
    tiled_select_mask: Image.Image = tileInLenImg(img_center_select_mask, tile_w)

    img_unselect:      Image.Image = joinButton(img_left_unselect,      tiled_unselect,      img_right_unselect)
    img_unselect_mask: Image.Image = joinButton(img_left_unselect_mask, tiled_unselect_mask, img_right_unselect_mask)
    img_select:        Image.Image = joinButton(img_left_select,        tiled_select,        img_right_select)
    img_select_mask:   Image.Image = joinButton(img_left_select_mask,   tiled_select_mask,   img_right_select_mask)

    compositor: Image.Image = Image.new("RGBA", img_canvas.size, (0, 0, 0, 0))

    for i, name in enumerate(distrs_list):
        y: int = i * h
        is_selected: bool = (i == select_index)

        base: Image.Image = img_select.copy() if is_selected else img_unselect.copy()
        mask: Image.Image  = img_select_mask.copy() if is_selected else img_unselect_mask.copy()

        fill_color: T_RGB = accent_color if is_selected else (75, 75, 75)
        color_layer: Image.Image = Image.new("RGBA", base.size, (*fill_color, 255))

        compositor.paste(base, (0, y));
        compositor.paste(color_layer, (0, y), mask);

        text_x = 10
        bbox: tuple[float, float, float, float] = textSize(name, 32)
        text_y: float = y + (h - (bbox[3] - bbox[1])) // 2
        compositor: Image.Image = drawText(compositor, name, int(text_x), int(text_y), size=32, color=(255, 255, 255))

        if is_selected:
            heart_text = "<3"
            heart_bbox = textSize(heart_text, 32)
            heart_w = heart_bbox[2]
            heart_x = tile_w - heart_w + 20
            compositor: Image.Image = drawText(compositor, heart_text, int(heart_x), int(text_y), size=32, color=accent_color)

    return Image.alpha_composite(img_canvas, compositor)



    return img_canvas;
if __name__ == "__main__":
    import sys
    args = sys.argv;
    print(args);
    img_canvas = renderBackground(args[2]);
    img_canvas = renderButtons(img_canvas, args[3:], int(args[1]), accentFromSvg(f"assets/images/distrs/{args[2]}/logo.svg"));
    save(img_canvas, f"Boykisser/icons/{args[2]}.png");
    save(img_canvas, f"Boykisser/os_{args[2]}.png");
    save(img_canvas, f"Boykisser/icons/submenu-{args[2]}.png");
    save(img_canvas, f"Boykisser/os_submenu-{args[2]}.png");

