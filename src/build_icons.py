"""Иконки виджета «Тихий день» v3: цветные иконки погоды, флаги, логотипы монет, интерфейс (Pillow)."""
import math
import os

from PIL import Image, ImageDraw, ImageFont

from td_common import SKIN_DIR

SS = 4
FONTS = r"C:\Windows\Fonts"


def canvas(size):
    return Image.new("RGBA", (size * SS, size * SS), (0, 0, 0, 0))


def finish(img, size):
    return img.resize((size, size), Image.LANCZOS)


def vgrad(w, h, top, bottom):
    g = Image.new("RGBA", (w, h))
    px = g.load()
    for y in range(h):
        t = y / max(1, h - 1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(4))
        for x in range(w):
            px[x, y] = c
    return g


def paste_grad(img, mask, top, bottom):
    img.paste(vgrad(img.width, img.height, top, bottom), (0, 0), mask)


def circle_mask(size):
    m = Image.new("L", (size * SS, size * SS), 0)
    ImageDraw.Draw(m).ellipse([0, 0, size * SS - 1, size * SS - 1], fill=255)
    return m


# ------------------------------------------------------------------ погода
def cloud_mask(size, ox=0.0, oy=0.0, scale=1.0):
    s = size * SS
    m = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(m)
    k = s / 128.0 * scale

    def P(x, y):
        return ((x + ox) * k, (y + oy) * k)

    d.rounded_rectangle([P(20, 62), P(112, 98)], radius=18 * k, fill=255)
    for cx, cy, r in ((44, 66, 20), (70, 54, 27), (94, 68, 19)):
        d.ellipse([P(cx - r, cy - r), P(cx + r, cy + r)], fill=255)
    return m


def draw_cloud(img, size, dark=False, ox=0.0, oy=0.0, scale=1.0):
    m = cloud_mask(size, ox, oy, scale)
    top, bot = ((168, 182, 204, 255), (112, 128, 156, 255)) if dark else ((250, 252, 255, 255), (196, 211, 232, 255))
    paste_grad(img, m, top, bot)


def draw_sun(img, size, cx, cy, r, rays=True):
    d = ImageDraw.Draw(img)
    k = size * SS / 128.0
    if rays:
        for a in range(0, 360, 45):
            x0 = cx + math.cos(math.radians(a)) * (r + 6)
            y0 = cy + math.sin(math.radians(a)) * (r + 6)
            x1 = cx + math.cos(math.radians(a)) * (r + 15)
            y1 = cy + math.sin(math.radians(a)) * (r + 15)
            d.line([(x0 * k, y0 * k), (x1 * k, y1 * k)], fill=(255, 196, 61, 255), width=int(5 * k))
            for x, y in ((x0, y0), (x1, y1)):
                d.ellipse([x * k - 2.5 * k, y * k - 2.5 * k, x * k + 2.5 * k, y * k + 2.5 * k], fill=(255, 196, 61, 255))
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).ellipse([(cx - r) * k, (cy - r) * k, (cx + r) * k, (cy + r) * k], fill=255)
    paste_grad(img, m, (255, 226, 112, 255), (255, 160, 40, 255))


def weather_icon(kind, size=128):
    img = canvas(size)
    d = ImageDraw.Draw(img)
    k = size * SS / 128.0
    if kind == "clear":
        draw_sun(img, size, 64, 64, 26)
    elif kind == "partly":
        draw_sun(img, size, 46, 46, 20)
        draw_cloud(img, size, ox=6, oy=10)
    elif kind == "cloud":
        draw_cloud(img, size, oy=2)
    elif kind in ("rain", "snow", "storm"):
        draw_cloud(img, size, dark=(kind == "storm"), oy=-14)
        if kind == "rain":
            for x in (40, 62, 84):
                d.line([(x * k, 88 * k), ((x - 7) * k, 108 * k)], fill=(91, 168, 255, 255), width=int(7 * k))
                d.ellipse([(x - 3.5) * k, 84.5 * k, (x + 3.5) * k, 91.5 * k], fill=(91, 168, 255, 255))
                d.ellipse([(x - 10.5) * k, 104.5 * k, (x - 3.5) * k, 111.5 * k], fill=(91, 168, 255, 255))
        elif kind == "snow":
            for x, y in ((42, 100), (64, 108), (86, 100)):
                for a in (0, 60, 120):
                    dx, dy = math.cos(math.radians(a)) * 7, math.sin(math.radians(a)) * 7
                    d.line([((x - dx) * k, (y - dy) * k), ((x + dx) * k, (y + dy) * k)], fill=(190, 225, 255, 255), width=int(3.4 * k))
        else:
            pts = [(70, 82), (52, 104), (64, 104), (56, 124), (84, 96), (70, 96), (80, 82)]
            d.polygon([(x * k, y * k) for x, y in pts], fill=(255, 205, 60, 255))
    elif kind == "fog":
        draw_cloud(img, size, scale=0.8, ox=10, oy=-6)
        for y, x0, x1 in ((88, 24, 104), (102, 36, 116), (116, 24, 96)):
            d.line([(x0 * k, y * k), (x1 * k, y * k)], fill=(178, 192, 214, 255), width=int(7 * k))
            for x in (x0, x1):
                d.ellipse([(x - 3.5) * k, (y - 3.5) * k, (x + 3.5) * k, (y + 3.5) * k], fill=(178, 192, 214, 255))
    return finish(img, size)


# ------------------------------------------------------------------ флаги
def font(name, px):
    return ImageFont.truetype(os.path.join(FONTS, name), px * SS)


def flag(code, size=64):
    s = size * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if code == "usd":
        h = s / 7
        for i in range(7):
            d.rectangle([0, i * h, s, (i + 1) * h], fill=(214, 40, 57, 255) if i % 2 == 0 else (255, 255, 255, 255))
        d.rectangle([0, 0, s * 0.56, h * 4], fill=(30, 58, 138, 255))
        for r in range(3):
            for c in range(3):
                x, y = s * (0.1 + c * 0.17), h * (0.7 + r * 1.1)
                d.ellipse([x - s * 0.025, y - s * 0.025, x + s * 0.025, y + s * 0.025], fill=(255, 255, 255, 255))
    elif code == "eur":
        d.rectangle([0, 0, s, s], fill=(0, 51, 153, 255))
        for i in range(12):
            a = math.radians(i * 30)
            x, y = s / 2 + math.cos(a) * s * 0.30, s / 2 + math.sin(a) * s * 0.30
            d.ellipse([x - s * 0.04, y - s * 0.04, x + s * 0.04, y + s * 0.04], fill=(255, 204, 0, 255))
    elif code == "pln":
        d.rectangle([0, 0, s, s / 2], fill=(255, 255, 255, 255))
        d.rectangle([0, s / 2, s, s], fill=(220, 20, 60, 255))
    elif code == "czk":
        d.rectangle([0, 0, s, s / 2], fill=(255, 255, 255, 255))
        d.rectangle([0, s / 2, s, s], fill=(215, 20, 26, 255))
        d.polygon([(0, 0), (s * 0.55, s / 2), (0, s)], fill=(17, 69, 126, 255))
    elif code == "uah":
        d.rectangle([0, 0, s, s / 2], fill=(0, 87, 183, 255))
        d.rectangle([0, s / 2, s, s], fill=(255, 215, 0, 255))
    elif code == "gbp":
        d.rectangle([0, 0, s, s], fill=(1, 33, 105, 255))
        d.line([(0, 0), (s, s)], fill=(255, 255, 255, 255), width=int(s * 0.16))
        d.line([(0, s), (s, 0)], fill=(255, 255, 255, 255), width=int(s * 0.16))
        d.line([(0, 0), (s, s)], fill=(200, 16, 46, 255), width=int(s * 0.06))
        d.line([(0, s), (s, 0)], fill=(200, 16, 46, 255), width=int(s * 0.06))
        d.rectangle([s * 0.4, 0, s * 0.6, s], fill=(255, 255, 255, 255))
        d.rectangle([0, s * 0.4, s, s * 0.6], fill=(255, 255, 255, 255))
        d.rectangle([s * 0.45, 0, s * 0.55, s], fill=(200, 16, 46, 255))
        d.rectangle([0, s * 0.45, s, s * 0.55], fill=(200, 16, 46, 255))
    else:
        d.rectangle([0, 0, s, s], fill=(70, 84, 108, 255))
        f = font("segoeuib.ttf", int(size * 0.5))
        t = code[:1].upper()
        bb = d.textbbox((0, 0), t, font=f)
        d.text(((s - (bb[2] - bb[0])) / 2 - bb[0], (s - (bb[3] - bb[1])) / 2 - bb[1]), t, font=f, fill=(235, 240, 248, 255))
    out = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    out.paste(img, (0, 0), circle_mask(size))
    ImageDraw.Draw(out).ellipse([1, 1, s - 2, s - 2], outline=(255, 255, 255, 70), width=SS)
    return finish(out, size)


# ------------------------------------------------------------------ монеты
def coin(code, size=64):
    s = size * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if code == "btc":
        paste_grad(img, circle_mask(size), (255, 168, 54, 255), (240, 130, 10, 255))
        f = font("segoeuib.ttf", int(size * 0.62))
        t = "B"
        bb = d.textbbox((0, 0), t, font=f)
        tx, ty = (s - (bb[2] - bb[0])) / 2 - bb[0], (s - (bb[3] - bb[1])) / 2 - bb[1]
        d.text((tx, ty), t, font=f, fill=(255, 255, 255, 255))
        for fx in (0.40, 0.56):
            d.line([(s * fx, s * 0.16), (s * fx, s * 0.27)], fill=(255, 255, 255, 255), width=int(s * 0.055))
            d.line([(s * fx, s * 0.73), (s * fx, s * 0.84)], fill=(255, 255, 255, 255), width=int(s * 0.055))
    elif code == "eth":
        paste_grad(img, circle_mask(size), (58, 62, 72, 255), (22, 24, 30, 255))
        cx, cy = s / 2, s / 2
        u = s * 0.16
        d.polygon([(cx, cy - 2.2 * u), (cx + 1.25 * u, cy + 0.1 * u), (cx, cy - 0.3 * u), (cx - 1.25 * u, cy + 0.1 * u)], fill=(235, 238, 245, 255))
        d.polygon([(cx - 1.25 * u, cy + 0.45 * u), (cx, cy + 0.15 * u), (cx + 1.25 * u, cy + 0.45 * u), (cx, cy + 2.2 * u)], fill=(170, 178, 195, 255))
    elif code == "ton":
        paste_grad(img, circle_mask(size), (40, 170, 240, 255), (0, 120, 210, 255))
        cx, cy = s / 2, s / 2
        u = s * 0.2
        d.polygon([(cx - 1.55 * u, cy - 1.15 * u), (cx + 1.55 * u, cy - 1.15 * u), (cx, cy + 1.7 * u)], outline=(255, 255, 255, 255), width=int(s * 0.07))
        d.line([(cx, cy - 1.15 * u), (cx, cy + 1.7 * u)], fill=(255, 255, 255, 255), width=int(s * 0.06))
    else:
        paste_grad(img, circle_mask(size), (110, 124, 150, 255), (70, 84, 108, 255))
        f = font("segoeuib.ttf", int(size * 0.46))
        t = code[:3].upper()
        bb = d.textbbox((0, 0), t, font=f)
        d.text(((s - (bb[2] - bb[0])) / 2 - bb[0], (s - (bb[3] - bb[1])) / 2 - bb[1]), t, font=f, fill=(240, 244, 250, 255))
    return finish(img, size)


# ------------------------------------------------------------------ интерфейс
def ui(kind, size=48, color=(174, 187, 204, 255)):
    img = canvas(size)
    d = ImageDraw.Draw(img)
    k = size * SS / 24.0
    w = int(1.7 * k)

    def L(pts):
        pts = [(x * k, y * k) for x, y in pts]
        d.line(pts, fill=color, width=w, joint="curve")
        for p in (pts[0], pts[-1]):
            d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=color)
    if kind == "pin":
        d.ellipse([6.5 * k, 3.5 * k, 17.5 * k, 14.5 * k], outline=color, width=w)
        L([(8.2, 13.2), (12, 21), (15.8, 13.2)])
        d.ellipse([10 * k, 7 * k, 14 * k, 11 * k], fill=color)
    elif kind == "wind":
        L([(3, 9), (14, 9)]); d.arc([13 * k, 4 * k, 19 * k, 10 * k], 270, 90 + 180, fill=color, width=w)
        L([(3, 14), (17, 14)]); d.arc([16 * k, 14 * k, 22 * k, 20 * k], 270, 90 + 180, fill=color, width=w)
        L([(3, 19), (10, 19)])
    elif kind == "drop":
        blue = (86, 168, 255, 255)
        d.polygon([(12 * k, 3 * k), (18 * k, 13 * k), (6 * k, 13 * k)], fill=blue)
        d.ellipse([5.5 * k, 8.5 * k, 18.5 * k, 21.5 * k], fill=blue)
    elif kind == "sync":
        c = (139, 212, 232, 255)
        d.arc([4 * k, 4 * k, 20 * k, 20 * k], 200, 340, fill=c, width=w)
        d.arc([4 * k, 4 * k, 20 * k, 20 * k], 20, 160, fill=c, width=w)
        d.polygon([(19 * k, 3.5 * k), (19.5 * k, 9.5 * k), (13.5 * k, 8.5 * k)], fill=c)
        d.polygon([(5 * k, 20.5 * k), (4.5 * k, 14.5 * k), (10.5 * k, 15.5 * k)], fill=c)
    elif kind == "plus":
        c = (255, 255, 255, 255)
        d.line([(12 * k, 5 * k), (12 * k, 19 * k)], fill=c, width=w)
        d.line([(5 * k, 12 * k), (19 * k, 12 * k)], fill=c, width=w)
    elif kind == "plus_blue":
        c = (120, 170, 255, 255)
        d.line([(12 * k, 5 * k), (12 * k, 19 * k)], fill=c, width=w)
        d.line([(5 * k, 12 * k), (19 * k, 12 * k)], fill=c, width=w)
    elif kind == "chev_r":
        L([(9, 5), (16, 12), (9, 19)])
    elif kind == "chev_l":
        L([(15, 5), (8, 12), (15, 19)])
    elif kind == "link":
        c = (255, 255, 255, 255)
        d.rounded_rectangle([3 * k, 8.5 * k, 12 * k, 15.5 * k], radius=3.5 * k, outline=c, width=w)
        d.rounded_rectangle([12 * k, 8.5 * k, 21 * k, 15.5 * k], radius=3.5 * k, outline=c, width=w)
        d.line([(8 * k, 12 * k), (16 * k, 12 * k)], fill=c, width=w)
    elif kind == "check":
        L([(5, 12.5), (10, 17.5), (19, 7)])
    return finish(img, size)


def google_g(size=96):
    s = size * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, s - 1, s - 1], fill=(255, 255, 255, 255))
    f = font("segoeuib.ttf", int(size * 0.70))
    t = "G"
    bb = d.textbbox((0, 0), t, font=f)
    tx, ty = (s - (bb[2] - bb[0])) / 2 - bb[0], (s - (bb[3] - bb[1])) / 2 - bb[1]
    m = Image.new("L", (s, s), 0)
    ImageDraw.Draw(m).text((tx, ty), t, font=f, fill=255)
    bands = [(0, 0.38, (234, 67, 53, 255)), (0.38, 0.62, (251, 188, 5, 255)), (0.62, 0.80, (52, 168, 83, 255)), (0.80, 1.01, (66, 133, 244, 255))]
    col = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    cd = ImageDraw.Draw(col)
    cd.rectangle([0, 0, s, s], fill=(66, 133, 244, 255))
    # верх красный, середина-право синий, низ зелёный/жёлтый (упрощённая «G»)
    cd.rectangle([0, 0, s, s * 0.36], fill=(234, 67, 53, 255))
    cd.rectangle([0, s * 0.36, s * 0.45, s * 0.62], fill=(251, 188, 5, 255))
    cd.rectangle([0, s * 0.62, s * 0.62, s], fill=(52, 168, 83, 255))
    img.paste(col, (0, 0), m)
    return finish(img, size)


def build():
    out = os.path.join(SKIN_DIR, "@Resources", "icons")
    os.makedirs(out, exist_ok=True)
    for kind in ("clear", "partly", "cloud", "rain", "snow", "storm", "fog"):
        weather_icon(kind, 128).save(os.path.join(out, f"w_{kind}.png"))
    Image.new("RGBA", (8, 8), (0, 0, 0, 0)).save(os.path.join(out, "w_none.png"))
    for code in ("usd", "eur", "pln", "czk", "uah", "gbp", "other"):
        flag(code, 64).save(os.path.join(out, f"f_{code}.png"))
    Image.new("RGBA", (8, 8), (0, 0, 0, 0)).save(os.path.join(out, "f_none.png"))
    for code in ("btc", "eth", "ton", "other"):
        coin(code, 64).save(os.path.join(out, f"c_{code}.png"))
    Image.new("RGBA", (8, 8), (0, 0, 0, 0)).save(os.path.join(out, "c_none.png"))
    for kind in ("pin", "wind", "drop", "sync", "plus", "plus_blue", "chev_r", "chev_l", "link", "check"):
        ui(kind, 48).save(os.path.join(out, f"u_{kind}.png"))
    google_g(96).save(os.path.join(out, "u_google.png"))
    return sorted(os.listdir(out))


if __name__ == "__main__":
    print(build())
