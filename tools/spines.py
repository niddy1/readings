"""Render book spines as JPGs from per-book specs.

usage: python3 -I spines.py SPECS.json BOOKS_DIR [id ...]
Each spec: {"id", "sr" (width/height), "bg": "#hex" | {"crop":[x0,y0,x1,y1]} ,
            "top": [els], "mid": el (flex title), "bot": [els], "tex": 0..1}
Elements: {"t":"text","s":..,"f":font,"wt":700,"c":"#hex","o":"v"|"h","sz":frac of W,"tr":tracking em}
          {"t":"crop","box":[fractions],"o":"h"|"v","h":frac of H (h only)}
          {"t":"rule","c":"#hex","h":px-frac} {"t":"gap","h":frac} {"t":"band","c":"#hex","h":frac, "els":[...]}
"""
import json, os, sys, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

G = "/home/claude/gfonts/"
FONTS = {
    "cinzel": "ofl/cinzel/Cinzel[wght].ttf", "garamond": "ofl/ebgaramond/EBGaramond[wght].ttf",
    "cormorant": "ofl/cormorantgaramond/CormorantGaramond[wght].ttf",
    "oswald": "ofl/oswald/Oswald[wght].ttf", "playfair": "ofl/playfairdisplay/PlayfairDisplay[wght].ttf",
    "baskerville": "ofl/librebaskerville/LibreBaskerville[wght].ttf", "bodoni": "ofl/bodonimoda/BodoniModa[opsz,wght].ttf",
    "karla": "ofl/karla/Karla[wght].ttf", "josefin": "ofl/josefinsans/JosefinSans[wght].ttf",
    "bebas": "ofl/bebasneue/BebasNeue-Regular.ttf", "anton": "ofl/anton/Anton-Regular.ttf",
    "rye": "ofl/rye/Rye-Regular.ttf", "abril": "ofl/abrilfatface/AbrilFatface-Regular.ttf",
    "dmserif": "ofl/dmserifdisplay/DMSerifDisplay-Regular.ttf", "caveat": "ofl/caveat/Caveat[wght].ttf",
    "limelight": "ofl/limelight/Limelight-Regular.ttf", "poiret": "ofl/poiretone/PoiretOne-Regular.ttf",
    "sixcaps": "ofl/sixcaps/SixCaps.ttf", "italiana": "ofl/italiana/Italiana-Regular.ttf",
    "fraunces": "ofl/fraunces/Fraunces[SOFT,WONK,opsz,wght].ttf", "spectral": "ofl/spectral/Spectral-SemiBold.ttf",
    "barlowc": "ofl/barlowcondensed/BarlowCondensed-SemiBold.ttf", "barlowcb": "ofl/barlowcondensed/BarlowCondensed-Bold.ttf",
    "barlowcl": "ofl/barlowcondensed/BarlowCondensed-Light.ttf", "fjalla": "ofl/fjallaone/FjallaOne-Regular.ttf",
    "oldstd": "ofl/oldstandardtt/OldStandard-Regular.ttf", "oldstdb": "ofl/oldstandardtt/OldStandard-Bold.ttf",
    "fell": "ofl/imfelldwpica/IMFePIrm28P.ttf", "felli": "ofl/imfelldwpica/IMFePIit28P.ttf",
    "typewriter": "apache/specialelite/SpecialElite-Regular.ttf", "crimson": "ofl/crimsontext/CrimsonText-SemiBold.ttf",
    "poppinsbi": "/usr/share/fonts/truetype/google-fonts/Poppins-BoldItalic.ttf",
    "poppinsb": "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
    "poppins": "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf",
    "inter": "Inter", "slab": "ofl/alfaslabone/AlfaSlabOne-Regular.ttf",
}
H = 900


def font(name, size, wt=None):
    p = FONTS[name]
    if p == "Inter":
        f = ImageFont.truetype("/usr/share/fonts/truetype/inter/Inter.ttc" if os.path.exists("/usr/share/fonts/truetype/inter/Inter.ttc") else "DejaVuSans.ttf", size)
    else:
        f = ImageFont.truetype(p if p.startswith("/") else G + p, size)
    if wt:
        try:
            axes = f.get_variation_axes()
            vals = []
            for a in axes:
                n = a.get("name", b"")
                n = n.decode() if isinstance(n, bytes) else str(n)
                if n.lower().startswith("weight") or n == "wght":
                    vals.append(max(a["minimum"], min(a["maximum"], wt)))
                elif n.lower().startswith("optical") or n == "opsz":
                    vals.append(a["maximum"] if size > 40 else a["default"])
                else:
                    vals.append(a["default"])
            f.set_variation_by_axes(vals)
        except Exception:
            pass
    return f


def text_img(s, fname, size, color, wt=None, tr=0.0, italic=False):
    f = font(fname, size, wt)
    if tr:
        ws = [f.getbbox(ch) for ch in s]
        adv = [f.getlength(ch) + tr * size for ch in s]
        width = int(sum(adv) + size)
    else:
        width = int(f.getlength(s) + size)
    asc, desc = f.getmetrics()
    im = Image.new("RGBA", (width, asc + desc + size // 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if tr:
        x = size // 4
        for ch, a in zip(s, adv):
            d.text((x, size // 4), ch, font=f, fill=color)
            x += a
    else:
        d.text((size // 4, size // 4), s, font=f, fill=color)
    bb = im.getbbox()
    return im.crop(bb) if bb else im


def lines_img(lines, fname, size, color, wt=None, tr=0.0, lead=1.05, align="c"):
    ims = [text_img(l, fname, size, color, wt, tr) for l in lines]
    if len(ims) == 1:
        return ims[0]
    w = max(i.width for i in ims)
    step = int(size * lead)
    h = step * (len(ims) - 1) + ims[-1].height
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for k, i in enumerate(ims):
        x = (w - i.width) // 2 if align == "c" else 0
        out.alpha_composite(i, (x, k * step + (step - i.height if k < len(ims) - 1 and i.height < step else 0) * 0))
    return out


def render_el(e, W, avail=None, cover=None):
    """Return an RGBA image for element e fitted to width W (and height avail for flex)."""
    t = e["t"]
    if t == "gap":
        return Image.new("RGBA", (W, int(H * e["h"])), (0, 0, 0, 0))
    if t == "rule":
        im = Image.new("RGBA", (W, max(2, int(H * e.get("h", 0.004)))), e["c"])
        if e.get("inset"):
            pad = int(W * e["inset"]); m = Image.new("RGBA", im.size, (0, 0, 0, 0)); m.paste(im.crop((pad, 0, W - pad, im.height)), (pad, 0)); im = m
        return im
    if t == "band":
        bh = int(H * e["h"])
        im = Image.new("RGBA", (W, bh), e["c"])
        inner = [render_el(x, W, None, cover) for x in e.get("els", [])]
        y = (bh - sum(i.height for i in inner)) // 2
        for i in inner:
            im.alpha_composite(i, ((W - i.width) // 2, max(0, y))); y += i.height
        return im
    if t == "crop":
        x0, y0, x1, y1 = e["box"]
        c = cover.crop((int(x0 * cover.width), int(y0 * cover.height), int(x1 * cover.width), int(y1 * cover.height))).convert("RGBA")
        if e.get("o") == "v":
            c = c.rotate(-90, expand=True)
        if "h" in e:  # fill W x h, cropping centre
            th = int(H * e["h"])
            s = max(W / c.width, th / c.height)
            c = c.resize((max(W, round(c.width * s)), max(th, round(c.height * s))), Image.LANCZOS)
            ox, oy = (c.width - W) // 2, int((c.height - th) * e.get("ay", 0.5))
            return c.crop((ox, oy, ox + W, oy + th))
        fw = W * e.get("w", 0.8)
        s = fw / c.width
        if avail and c.height * s > avail:
            s = avail / c.height
        return c.resize((max(1, round(c.width * s)), max(1, round(c.height * s))), Image.LANCZOS)
    if t == "text":
        lines = e["s"].split("\n")
        o = e.get("o", "v")
        if o == "h":
            size = int(W * e.get("sz", 0.2))
            im = lines_img(lines, e["f"], size, e["c"], e.get("wt"), e.get("tr", 0), e.get("lead", 1.1))
            maxw = W * e.get("w", 0.82)
            if im.width > maxw:
                im = im.resize((int(maxw), max(1, int(im.height * maxw / im.width))), Image.LANCZOS)
            return im
        # vertical: text reads top to bottom
        maxw = W * e.get("w", 0.62)  # glyph-height budget across the spine
        maxlen = avail if avail else H * e.get("len", 0.3)
        size = int(e.get("sz", 0.5) * W) if not avail else 400
        im = None
        for _ in range(60):
            im = lines_img(lines, e["f"], size, e["c"], e.get("wt"), e.get("tr", 0), e.get("lead", 1.0)).rotate(-90, expand=True)
            if im.width <= maxw and im.height <= maxlen:
                break
            size = int(size * 0.93)
        if e.get("sx"):  # horizontal squash (condensed look)
            im = im.resize((im.width, int(im.height * e["sx"])), Image.LANCZOS)
        return im
    raise ValueError(t)


def wear(im, amt):
    W, Hh = im.size
    rnd = random.Random(W * 7 + Hh)
    noise = Image.effect_noise((W, Hh), 22).convert("L")
    grain = Image.merge("RGB", (noise, noise, noise))
    im = ImageChops.blend(im, ImageChops.overlay(im, grain), 0.18 * amt + 0.06)
    # soft darkening at head and tail, and a faint crease line
    sh = Image.new("L", (W, Hh), 0); d = ImageDraw.Draw(sh)
    for k in range(int(Hh * 0.03)):
        a = int(70 * amt * (1 - k / (Hh * 0.03)))
        d.line((0, k, W, k), fill=a); d.line((0, Hh - 1 - k, W, Hh - 1 - k), fill=a)
    for _ in range(int(3 * amt)):
        x = rnd.randint(int(W * .15), int(W * .85))
        d.line((x, 0, x + rnd.randint(-2, 2), Hh), fill=int(18 * amt))
    sh = sh.filter(ImageFilter.GaussianBlur(1.2))
    im = Image.composite(Image.new("RGB", im.size, (20, 14, 8)), im, sh)
    return im


def render(spec, books):
    cover = Image.open(os.path.join(books, spec["id"] + "-cover.jpg")).convert("RGB")
    W = max(30, round(H * spec["sr"]))
    bg = spec.get("bg", "#ffffff")
    if isinstance(bg, dict):
        x0, y0, x1, y1 = bg["crop"]
        c = cover.crop((int(x0 * cover.width), int(y0 * cover.height), int(x1 * cover.width), int(y1 * cover.height)))
        if bg.get("o") == "v":
            c = c.rotate(-90, expand=True)
        s = max(W / c.width, H / c.height)
        c = c.resize((round(c.width * s) + 1, round(c.height * s) + 1), Image.LANCZOS)
        if bg.get("blur"):
            c = c.filter(ImageFilter.GaussianBlur(bg["blur"]))
        canvas = c.crop(((c.width - W) // 2, (c.height - H) // 2, (c.width - W) // 2 + W, (c.height - H) // 2 + H)).convert("RGBA")
        if bg.get("tint"):
            canvas = Image.blend(canvas, Image.new("RGBA", canvas.size, bg["tint"]), bg.get("ta", 0.3))
    else:
        canvas = Image.new("RGBA", (W, H), bg)
    pad = int(H * spec.get("pad", 0.035))
    tops = [render_el(e, W, None, cover) for e in spec.get("top", [])]
    bots = [render_el(e, W, None, cover) for e in spec.get("bot", [])]
    gap = int(H * spec.get("gap", 0.02))
    used = sum(i.height for i in tops) + sum(i.height for i in bots)
    used += gap * (len(tops) + len(bots))
    avail = H - 2 * pad - used
    y = pad
    for e, i in zip(spec.get("top", []), tops):
        yy = 0 if e.get("bleed") else y
        canvas.alpha_composite(i, ((W - i.width) // 2, yy)); y = yy + i.height + gap
    if spec.get("mid"):
        m = render_el(spec["mid"], W, avail, cover)
        al = spec["mid"].get("al", "c")
        my = y if al == "t" else y + (avail - m.height) // 2
        canvas.alpha_composite(m, ((W - m.width) // 2, my))
    y = H - pad
    for e, i in reversed(list(zip(spec.get("bot", []), bots))):
        yy = H - i.height if e.get("bleed") else y - i.height
        canvas.alpha_composite(i, ((W - i.width) // 2, yy)); y = yy - gap
    out = wear(canvas.convert("RGB"), spec.get("tex", 0.6))
    out.save(os.path.join(books, spec["id"] + "-spine.jpg"), quality=88)
    return W / H


if __name__ == "__main__":
    specs = json.load(open(sys.argv[1]))
    books = sys.argv[2]
    only = set(sys.argv[3:])
    res = {}
    for s in specs:
        if only and s["id"] not in only:
            continue
        res[s["id"]] = round(render(s, books), 3)
    print(json.dumps(res))
