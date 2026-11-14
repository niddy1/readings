import os, numpy as np, cv2, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

S = 2
H = 1100
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
F = {k: os.path.join(FONTS, v) for k, v in dict(
    adv='texgyreadventor-regular.otf',
    advb='texgyreadventor-bold.otf',
    bonb='texgyrebonum-bold.otf',
    bonbi='texgyrebonum-bolditalic.otf',
    cho='texgyrechorus-mediumitalic.otf',
    curbi='texgyrecursor-bolditalic.otf',
    dsc='DejaVuSerifCondensed-Bold.ttf',
    hcn='texgyreheroscn-regular.otf',
    hcnb='texgyreheroscn-bold.otf',
    her='texgyreheros-regular.otf',
    herb='texgyreheros-bold.otf',
    herbi='texgyreheros-bolditalic.otf',
    intm='Inter-Medium.otf',
    intsb='Inter-SemiBold.otf',
    lora='Lora-Variable.ttf',
    pagb='texgyrepagella-bold.otf',
    pagbi='texgyrepagella-bolditalic.otf',
    popb='Poppins-Bold.ttf',
    popbi='Poppins-BoldItalic.ttf',
    popm='Poppins-Medium.ttf',
    schb='texgyreschola-bold.otf',
    ter='texgyretermes-regular.otf',
    terb='texgyretermes-bold.otf',
    terbi='texgyretermes-bolditalic.otf',
    teri='texgyretermes-italic.otf',
).items()}


def fnt(key, size):
    return ImageFont.truetype(F[key], max(4, int(round(size * S))))


def text_mask(text, key, size, track=0.0, squeeze=1.0, sc=None, sc_scale=0.8):
    """Horizontal text as an L mask, tight-cropped. track in em. sc = font key for small caps."""
    f = fnt(key, size)
    fs = fnt(sc, size * sc_scale) if sc else None
    asc, desc = f.getmetrics()
    pad = int(size * S)
    widths = []
    for ch in text:
        if sc and ch.islower():
            widths.append((ch.upper(), fs, fs.getlength(ch.upper())))
        else:
            widths.append((ch, f, f.getlength(ch)))
    tr = track * size * S
    W = int(sum(w for _, _, w in widths) + tr * len(text) + 2 * pad)
    im = Image.new('L', (W, asc + desc + 2 * pad), 0)
    d = ImageDraw.Draw(im)
    x = pad
    for ch, ff, w in widths:
        d.text((x, pad + asc), ch, font=ff, fill=255, anchor='ls')
        x += w + tr
    bb = im.getbbox()
    im = im.crop(bb)
    if squeeze != 1.0:
        im = im.resize((max(1, int(im.width * squeeze)), im.height), Image.LANCZOS)
    return im


def colorize(mask, fill):
    im = Image.new('RGBA', mask.size, tuple(fill) + (0,))
    im.putalpha(mask)
    return im


def vgrad(mask, stops):
    """fill mask with vertical gradient; stops [(t,(r,g,b)),...]"""
    h = mask.height
    ts = np.linspace(0, 1, h)
    arr = np.zeros((h, mask.width, 4), np.uint8)
    for c in range(3):
        arr[:, :, c] = np.interp(ts, [s[0] for s in stops], [s[1][c] for s in stops])[:, None]
    arr[:, :, 3] = np.asarray(mask)
    return Image.fromarray(arr, 'RGBA')


def rot(im):
    return im.rotate(-90, expand=True, resample=Image.BICUBIC)


def put(base, im, cx, cy):
    """paste RGBA centered at (cx,cy) in final px units"""
    x = int(cx * S - im.width / 2)
    y = int(cy * S - im.height / 2)
    base.alpha_composite(im, (x, y))


def dilate(mask, r):
    return mask.filter(ImageFilter.MaxFilter(2 * int(r) + 1))


def erode(mask, r):
    return mask.filter(ImageFilter.MinFilter(2 * int(r) + 1))


def fbm(h, w, scale, rng, octaves=3):
    out = np.zeros((h, w), np.float32)
    amp = 1.0
    tot = 0
    for o in range(octaves):
        sc = max(1, scale / (2 ** o))
        sh, sw = max(2, int(h / sc) + 2), max(2, int(w / sc) + 2)
        n = rng.standard_normal((sh, sw)).astype(np.float32)
        out += amp * cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC)
        tot += amp
        amp *= 0.5
    return out / tot


def finish(img, seed, gloss=0.0, creases=0, wear=0.5, paper=(238, 232, 220), matte=0.02,
           warm=0.0, fade=0.0, crease_strength=0.6, hinge=False, blur=0.55, jpegq=90, out=None):
    """img: RGBA/RGB at S scale. returns final RGB PIL image."""
    rng = np.random.default_rng(seed)
    a = np.asarray(img.convert('RGB')).astype(np.float32) / 255.0
    h, w, _ = a.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    xn = xx / (w - 1)
    yn = yy / (h - 1)
    pap = np.array(paper, np.float32) / 255.0

    # fading / ink unevenness
    if fade:
        a = a * (1 - fade) + fade * (0.5 * pap + 0.5 * a.mean(axis=2, keepdims=True))
    mott = fbm(h, w, 90 * S, rng, 4)
    a *= (1 + matte * mott)[..., None]

    # creases along the spine (paperbacks)
    if creases:
        cm = np.zeros((h, w), np.float32)
        sh = np.zeros((h, w), np.float32)
        for i in range(creases):
            x0 = rng.uniform(0.12, 0.88) * w
            ys = np.arange(0, h, 8)
            wob = np.cumsum(rng.standard_normal(len(ys))) * 0.9
            wob -= np.linspace(wob[0], wob[-1], len(ys))
            pts = np.stack([x0 + wob, ys], 1).astype(np.int32)
            y0, y1 = sorted(rng.uniform(0, 1, 2))
            if y1 - y0 < 0.35:
                y0, y1 = max(0, y0 - 0.25), min(1, y1 + 0.25)
            sel = pts[(pts[:, 1] >= y0 * h) & (pts[:, 1] <= y1 * h)]
            if len(sel) < 2: continue
            tmp = np.zeros((h, w), np.uint8)
            cv2.polylines(tmp, [sel.reshape(-1, 1, 2)], False, 255, int(rng.integers(1, 3)) * S // 2 + 1, cv2.LINE_AA)
            strength = rng.uniform(0.35, 1.0)
            cm = np.maximum(cm, tmp.astype(np.float32) / 255 * strength)
        # break up along length
        brk = np.clip(fbm(h, w, 30 * S, rng, 3) * 1.6 + 0.55, 0, 1)
        cm = cv2.GaussianBlur(cm * brk, (0, 0), 0.7 * S)
        sh = cv2.GaussianBlur(np.roll(cm, 2 * S, axis=1), (0, 0), 1.6 * S)
        a = a * (1 - 0.22 * crease_strength * sh[..., None])
        k = np.clip(cm * crease_strength, 0, 1)[..., None]
        a = a * (1 - k) + pap * k

    # edge / corner wear
    if wear:
        dy = np.minimum(yy, h - 1 - yy) / S
        dx = np.minimum(xx, w - 1 - xx) / S
        n = fbm(h, w, 5 * S, rng, 3) * 0.6 + fbm(h, w, 28 * S, rng, 2) * 0.6
        # each book wears differently: head and tail get their own amount, often none
        wt, wb = [0.0 if rng.random() < 0.45 else rng.uniform(0.35, 1.0) for _ in range(2)]
        reach = rng.uniform(3, 6 + 7 * wear, 2)
        ey = np.maximum(wt * np.clip(1 - (yy / S) / reach[0], 0, 1) ** 2, wb * np.clip(1 - ((h - 1 - yy) / S) / reach[1], 0, 1) ** 2)
        ex = np.clip(1 - dx / (2.5 + 2.5 * wear), 0, 1) ** 2 * rng.uniform(0.2, 1.0)
        k = np.clip((ey * (0.75 + 0.6 * wear) + ex * 0.55 * wear + n * 0.5 - 0.80) * 3.0, 0, 1) * (0.35 + 0.45 * wear)
        sc = np.clip((fbm(h, w, 10 * S, rng, 4) * fbm(h, w, 150 * S, rng, 2) * 4 - 1.7) * 2.0, 0, 1) * 0.04 * wear
        k = np.clip(k + sc, 0, 1)[..., None]
        a = a * (1 - k) + pap * k

    # light: curvature of the spine + overhead falloff
    curve = 1 - 0.16 * (2 * xn - 1) ** 2 - 0.05 * np.clip(2 * xn - 1, 0, 1) ** 2
    vert = 1.0 - rng.uniform(-0.03, 0.05) * (yn - 0.5) + 0.03 * fbm(h, w, 400 * S, rng, 1)
    a *= (curve * vert)[..., None]
    if hinge:
        for xc in (0.035, 0.965):
            g = np.exp(-((xn - xc) / 0.012) ** 2)
            a *= (1 - 0.10 * g)[..., None]
            g2 = np.exp(-((xn - xc - 0.02) / 0.012) ** 2)
            a += (0.03 * g2)[..., None]
    if gloss:
        band = np.exp(-((xn - 0.33 - 0.03 * fbm(h, w, 300 * S, rng, 2)) / 0.075) ** 2)
        band *= np.clip(0.75 + 0.5 * fbm(h, w, 160 * S, rng, 2), 0.2, 1.2)
        a = 1 - (1 - a) * (1 - gloss * band[..., None])
    # head/tail shadow
    if warm:
        a *= np.array([1 + warm, 1 + warm * 0.35, 1 - warm], np.float32)
    a = np.clip(a, 0, 1)
    im = Image.fromarray((a * 255).astype(np.uint8)).resize((w // S, h // S), Image.LANCZOS)
    im = im.filter(ImageFilter.GaussianBlur(blur))
    b = np.asarray(im).astype(np.float32)
    hh, ww, _ = b.shape
    lum = rng.standard_normal((hh, ww, 1)) * 3.2
    chro = rng.standard_normal((hh, ww, 3)) * 1.4
    fine = cv2.GaussianBlur(rng.standard_normal((hh, ww)).astype(np.float32), (0, 0), 1.1)[..., None] * 5.0
    b = np.clip(b + lum + chro + fine, 0, 255).astype(np.uint8)
    im = Image.fromarray(b)
    if out:
        im.save(out, quality=jpegq, subsampling=0)
    return im


def canvas(w, color):
    return Image.new('RGBA', (w * S, H * S), tuple(color) + (255,))
