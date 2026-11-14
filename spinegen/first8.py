import sys
from eng import *

ONLY = sys.argv[1:]


def outp(i): return B + f'{i}-spine-b.jpg'


def poly(d, pts, **kw):
    d.polygon([(x * S, y * S) for x, y in pts], **kw)


# ---------------------------------------------------------------- Uncle Fred
def uncle_fred():
    W = 165
    im = canvas(W, (243, 239, 221))
    d = ImageDraw.Draw(im)
    grey = (54, 56, 55)
    # author, horizontal, head of spine
    for i, (t, sz) in enumerate([('P.G.', 19), ('WODEHOUSE', 19)]):
        m = text_mask(t, 'intsb', sz + 1, track=0.08)
        put(im, colorize(m, grey), W / 2, 52 + i * 30)
    d.line([(52 * S, 100 * S), (113 * S, 100 * S)], fill=grey + (255,), width=S)
    # title, two lines reading down
    l1 = text_mask('Uncle Fred in', 'intm', 48, track=0.06, sc='intsb', sc_scale=0.78)
    l2 = text_mask('the Springtime', 'intm', 48, track=0.06, sc='intsb', sc_scale=0.78)
    put(im, rot(colorize(l1, grey)), W / 2 + 27, 128 + l1.width / S / 2)
    put(im, rot(colorize(l2, grey)), W / 2 - 27, 128 + l2.width / S / 2)
    # deco panel in the cover's flat colours
    y0, y1 = 640, 985
    pan = Image.new('RGBA', (W * S, (y1 - y0) * S), (0, 0, 0, 0))
    p = ImageDraw.Draw(pan)
    PH = y1 - y0
    orange, yellow, tan, green, black = (238, 150, 48), (250, 206, 96), (203, 178, 128), (139, 160, 112), (28, 26, 30)
    p.rectangle([0, 0, W * S, PH * S], fill=tan)
    p.rectangle([0, 0, 50 * S, PH * S], fill=yellow)
    p.rectangle([0, 0, 22 * S, PH * S], fill=orange)
    p.rectangle([120 * S, 0, W * S, PH * S], fill=green)
    p.line([(50 * S, 0), (50 * S, PH * S)], fill=black, width=3 * S)
    # leaf shape bottom-left
    poly(p, [(0, 230), (40, 190), (62, 250), (48, PH), (0, PH)], fill=(246, 232, 170))
    for k in range(5):
        p.line([(0 * S, (250 + k * 22) * S), (55 * S, (215 + k * 22) * S)], fill=black, width=2 * S)
    poly(p, [(0, 230), (40, 190), (62, 250), (48, PH)], outline=black)
    # spear
    p.line([(140 * S, 40 * S), (134 * S, PH * S)], fill=black, width=3 * S)
    poly(p, [(141, 12), (150, 44), (141, 78), (133, 44)], fill=black)
    # figure: body, neck, head
    poly(p, [(58, PH), (62, 250), (78, 205), (98, 196), (118, 214), (128, 270), (124, PH)], fill=black)
    poly(p, [(84, 170), (100, 170), (102, 205), (82, 205)], fill=black)
    p.ellipse([70 * S, 118 * S, 112 * S, 176 * S], fill=black)
    poly(p, [(104, 140), (120, 152), (106, 158)], fill=black)  # nose
    p.arc([74 * S, 198 * S, 110 * S, 222 * S], 10, 170, fill=(245, 240, 225), width=2 * S)  # collar
    p.ellipse([97 * S, 138 * S, 109 * S, 150 * S], outline=(245, 240, 225), width=S)  # spectacle
    # striped headdress
    dome = Image.new('L', pan.size, 0)
    dd = ImageDraw.Draw(dome)
    dd.ellipse([56 * S, 30 * S, 124 * S, 150 * S], fill=255)
    dd.rectangle([0, 128 * S, W * S, PH * S], fill=0)
    stripes = Image.new('RGBA', pan.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(stripes)
    cols = [(200, 60, 70), (60, 150, 160), (70, 80, 150), (226, 120, 150), (40, 40, 60), (200, 60, 70), (60, 150, 160), (70, 80, 150), (226, 120, 150)]
    for k, c in enumerate(cols):
        x = 50 + k * 9
        sd.polygon([((x) * S, 150 * S), ((x + 9) * S, 150 * S), ((x + 9 + (k - 4) * 3) * S, 20 * S), ((x + (k - 4) * 3) * S, 20 * S)], fill=c)
    pan.paste(stripes, (0, 0), ImageChops.multiply(dome, stripes.getchannel('A')))
    p.rectangle([64 * S, 124 * S, 118 * S, 131 * S], fill=(245, 240, 225))
    p.rectangle([0, 0, W * S - 1, PH * S - 1], outline=black, width=2 * S)
    im.alpha_composite(pan, (0, y0 * S))
    m = text_mask('EVERYMAN', 'intsb', 14, track=0.2)
    put(im, colorize(m, grey), W / 2, 1040)
    return finish(im, 11, gloss=0.05, wear=0.35, hinge=True, matte=0.02, warm=0.012, out=outp('13707721'))


# ---------------------------------------------------------------- Middlesex
def middlesex():
    W = 242
    rng = np.random.default_rng(5)
    im = canvas(W, (17, 17, 16))
    # smoke
    sm = np.zeros((H * S, W * S), np.float32)
    for k in range(9):
        x = rng.uniform(0.1, 0.9) * W * S
        pts = []
        amp = rng.uniform(20, 70) * S
        ph = rng.uniform(0, 6.28)
        fr = rng.uniform(1.2, 3.0)
        y0 = rng.uniform(-0.1, 0.5) * H * S
        ln = rng.uniform(0.4, 0.9) * H * S
        for t in np.linspace(0, 1, 120):
            pts.append([x + amp * math.sin(ph + fr * 6.28 * t) * (0.3 + t) + 40 * S * t, y0 + ln * t])
        tmp = np.zeros_like(sm)
        cv2.polylines(tmp, [np.array(pts, np.int32).reshape(-1, 1, 2)], False, 1.0, int(rng.uniform(3, 14) * S), cv2.LINE_AA)
        tmp = cv2.GaussianBlur(tmp, (0, 0), rng.uniform(6, 22) * S)
        sm += tmp * rng.uniform(0.25, 0.6)
    sm *= np.clip(fbm(H * S, W * S, 200 * S, rng, 3) * 1.2 + 0.8, 0.2, 1.6)
    a = np.asarray(im).astype(np.float32)
    a[..., :3] += (np.clip(sm, 0, 1)[..., None] * np.array([205, 203, 190], np.float32)) * 0.62
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
    d = ImageDraw.Draw(im)
    ivory = (236, 232, 218)
    # title: tall condensed deco caps with an engraved inline
    m0 = text_mask('MIDDLESEX', 'hcn', 150, track=0.075)
    m0 = dilate(m0, 1)
    inl0 = erode(m0, 3 * S)
    sz = (int(m0.width * 0.62), m0.height)
    m = m0.resize(sz, Image.LANCZOS)
    inl = inl0.resize(sz, Image.LANCZOS).point(lambda v: min(255, int(v * 1.6)))
    t = colorize(m, ivory)
    hole = Image.new('RGBA', m.size, (17, 17, 16, 0)); hole.putalpha(inl)
    put(im, rot(t), W / 2, 70 + m.width / S / 2)
    yb = 70 + m.width / S
    d.line([(W / 2 * S, (yb + 26) * S), (W / 2 * S, (yb + 76) * S)], fill=ivory + (255,), width=S)
    a1 = text_mask('JEFFREY', 'hcnb', 50, track=0.18, squeeze=0.8)
    a2 = text_mask('EUGENIDES', 'hcnb', 50, track=0.18, squeeze=0.8)
    ya = yb + 100
    put(im, rot(colorize(a1, ivory)), W / 2 + 30, ya + a1.width / S / 2)
    put(im, rot(colorize(a2, ivory)), W / 2 - 30, ya + a2.width / S / 2)
    m = text_mask('PICADOR', 'hcnb', 17, track=0.3)
    put(im, colorize(m, ivory), W / 2, 1046)
    return finish(im, 21, gloss=0.16, creases=3, wear=0.45, paper=(225, 222, 212), crease_strength=0.5, matte=0.03, out=outp('2187'))


# ---------------------------------------------------------------- Goldfinch
GL = {
    'T': (0.80, [[(0.0, 0.06), (0.4, 0.02), (0.8, 0.0)], [(0.42, 0.02), (0.40, 0.5), (0.37, 1.0)]]),
    'H': (0.78, [[(0.06, 0.0), (0.09, 0.5), (0.07, 1.0)], [(0.70, 0.0), (0.69, 0.5), (0.72, 1.0)], [(0.07, 0.52), (0.4, 0.47), (0.71, 0.46)]]),
    'E': (0.70, [[(0.10, 0.0), (0.08, 0.5), (0.09, 1.0)], [(0.08, 0.03), (0.4, 0.0), (0.66, 0.01)], [(0.09, 0.5), (0.3, 0.47), (0.55, 0.48)], [(0.08, 0.99), (0.4, 0.98), (0.70, 0.95)]]),
    'G': (0.86, [[(0.76, 0.16), (0.48, -0.02), (0.14, 0.22), (0.07, 0.62), (0.32, 1.0), (0.66, 0.93), (0.78, 0.56), (0.46, 0.56)]]),
    'O': (0.84, [[(0.42, 0.0), (0.10, 0.25), (0.10, 0.78), (0.42, 1.0), (0.74, 0.76), (0.72, 0.22), (0.38, -0.01)]]),
    'L': (0.66, [[(0.10, 0.0), (0.09, 0.5), (0.10, 1.0)], [(0.09, 0.99), (0.35, 0.98), (0.64, 0.96)]]),
    'D': (0.82, [[(0.11, 0.0), (0.10, 0.5), (0.11, 1.0)], [(0.03, 0.03), (0.45, 0.03), (0.74, 0.34), (0.66, 0.78), (0.36, 0.98), (0.05, 1.0)]]),
    'F': (0.68, [[(0.10, 0.0), (0.09, 0.5), (0.11, 1.0)], [(0.08, 0.03), (0.4, 0.01), (0.68, 0.0)], [(0.10, 0.49), (0.3, 0.46), (0.52, 0.46)]]),
    'I': (0.30, [[(0.14, 0.0), (0.15, 0.5), (0.13, 1.0)]]),
    'N': (0.84, [[(0.08, 1.0), (0.09, 0.5), (0.10, 0.0)], [(0.10, 0.0), (0.40, 0.5), (0.70, 1.0)], [(0.70, 1.0), (0.71, 0.5), (0.73, 0.0)]]),
    'C': (0.80, [[(0.74, 0.17), (0.46, -0.01), (0.12, 0.26), (0.09, 0.70), (0.38, 1.0), (0.74, 0.86)]]),
    'A': (0.82, [[(0.04, 1.0), (0.22, 0.48), (0.39, 0.0)], [(0.39, 0.0), (0.56, 0.5), (0.74, 1.0)], [(0.18, 0.64), (0.4, 0.61), (0.62, 0.62)]]),
    'R': (0.80, [[(0.10, 0.0), (0.09, 0.5), (0.10, 1.0)], [(0.04, 0.04), (0.50, 0.01), (0.68, 0.24), (0.50, 0.47), (0.12, 0.53)], [(0.34, 0.52), (0.52, 0.76), (0.74, 1.0)]]),
}


def catmull(pts, n=24):
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = [np.array(q, float) for q in p[i - 1:i + 3]]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(np.array(pts[-1], float))
    return np.array(out)


def handwrite(text, hgt, rng, weight=1.0, gap=0.2, slant=0.08, xs=1.0):
    """hand-inked caps, returns L mask (horizontal)"""
    px = hgt * S
    wid = int(sum((GL[c][0] + gap) if c != ' ' else 0.55 for c in text) * px + px)
    m = np.zeros((int(px * 1.7), wid), np.uint8)
    x = px * 0.4
    for c in text:
        if c == ' ':
            x += 0.5 * xs * px; continue
        w, strokes = GL[c]
        sc = rng.uniform(0.9, 1.08)
        by = px * 0.35 + rng.uniform(-0.05, 0.05) * px
        sl = slant + rng.uniform(-0.05, 0.05)
        for st in strokes:
            pts = [(px_ + rng.uniform(-0.035, 0.035), py_ + rng.uniform(-0.035, 0.035)) for px_, py_ in st]
            c_ = catmull(pts, 30)
            xs_ = x + (c_[:, 0] * xs + (1 - c_[:, 1]) * sl) * px * sc
            ys = by + c_[:, 1] * px * sc
            n = len(xs_)
            base = rng.uniform(0.050, 0.068) * px * weight
            for i in range(n):
                t = i / max(1, n - 1)
                press = 0.72 + 0.35 * math.sin(math.pi * min(1, t * 1.25 + 0.12)) ** 0.6 + rng.uniform(-0.05, 0.05)
                r = max(1.0, base * press)
                cv2.circle(m, (int(xs_[i]), int(ys[i])), int(round(r)), 255, -1, cv2.LINE_AA)
        x += (w * xs * sc + gap * xs) * px
    # ragged ink edge
    mf = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 1.2 * S)
    n = fbm(m.shape[0], m.shape[1], 3 * S, rng, 2)
    mf = np.clip((mf + n * 0.13 - 0.5) * 6 + 0.5, 0, 1)
    out = Image.fromarray((mf * 255).astype(np.uint8))
    return out.crop(out.getbbox())


def goldfinch():
    W = 264
    rng = np.random.default_rng(8)
    h, w = H * S, W * S
    # wrapped-paper white with soft washes
    base = np.ones((h, w, 3), np.float32) * np.array([234, 231, 224], np.float32)
    wash = fbm(h, w, 260 * S, rng, 3)
    base += wash[..., None] * np.array([9, 9, 10], np.float32)
    fib = fbm(h, w, 4 * S, rng, 2)
    base += fib[..., None] * 2.5
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert('RGBA')
    ink = (26, 24, 24)
    t2 = handwrite('THE GOLDFINCH', 82, rng, weight=0.78, xs=0.8)
    t3 = handwrite('DONNA TARTT', 58, rng, weight=0.85, xs=0.82)
    put(im, rot(colorize(t2, ink)), W / 2 + 44, 56 + t2.width / S / 2)
    yb = 56 + t2.width / S
    put(im, rot(colorize(t3, ink)), W / 2 - 62, yb - t3.width / S / 2)
    # torn slit showing warm dark paint underneath
    ty0, ty1 = yb + 34, yb + 170
    cx = W / 2 - 16
    slit = [(cx - 4, ty0), (cx + 30, ty0 + 18), (cx + 22, ty0 + 60), (cx + 6, ty1), (cx - 12, ty0 + 84), (cx - 20, ty0 + 36)]
    msk = Image.new('L', (w, h), 0)
    ImageDraw.Draw(msk).polygon([(x * S, y * S) for x, y in slit], fill=255)
    mn = np.asarray(msk).astype(np.float32) / 255
    mn = np.clip((cv2.GaussianBlur(mn, (0, 0), 1.5 * S) + fbm(h, w, 5 * S, rng, 2) * 0.16 - 0.5) * 8 + 0.5, 0, 1)
    paint = np.zeros((h, w, 3), np.float32)
    g = fbm(h, w, 40 * S, rng, 4)
    paint[:] = np.array([150, 118, 62], np.float32)
    paint += g[..., None] * np.array([70, 60, 30], np.float32)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dark = np.exp(-(((xx - (cx + 8) * S) / (15 * S)) ** 2 + ((yy - (ty0 + 66) * S) / (34 * S)) ** 2))
    paint = paint * (1 - 0.8 * dark[..., None]) + np.array([40, 30, 26], np.float32) * 0.8 * dark[..., None]
    crack = fbm(h, w, 2.5 * S, rng, 1)
    paint += crack[..., None] * 10
    a = np.asarray(im).astype(np.float32)
    # inner shadow at the torn edge
    inner = cv2.GaussianBlur(mn, (0, 0), 5 * S)
    shade = (1 - np.clip(1 - inner, 0, 1) * 0.75)
    a[..., :3] = a[..., :3] * (1 - mn[..., None]) + (paint * shade[..., None]) * mn[..., None]
    # torn white fibre rim
    rim = np.clip(cv2.GaussianBlur(mn, (0, 0), 1.8 * S) * 4 * (1 - mn), 0, 1) * 0.55
    a[..., :3] = a[..., :3] * (1 - rim[..., None]) + 250 * rim[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
    # curled flap with drop shadow
    flap = [(cx + 30, ty0 + 18), (cx + 56, ty0 + 52), (cx + 26, ty1 + 5), (cx + 6, ty1), (cx + 22, ty0 + 60)]
    sh = Image.new('L', (w, h), 0)
    ImageDraw.Draw(sh).polygon([((x + 7) * S, (y + 6) * S) for x, y in flap], fill=120)
    sh = sh.filter(ImageFilter.GaussianBlur(7 * S))
    im.alpha_composite(colorize(sh, (60, 55, 50)))
    fl = Image.new('L', (w, h), 0)
    ImageDraw.Draw(fl).polygon([(x * S, y * S) for x, y in flap], fill=255)
    fa = np.asarray(im).astype(np.float32)
    fm = np.asarray(fl).astype(np.float32)[..., None] / 255
    gradv = 246 - 26 * np.clip((xx - (cx + 6) * S) / (56 * S), 0, 1)
    fa[..., :3] = fa[..., :3] * (1 - fm) + gradv[..., None] * np.array([1, 0.99, 0.97], np.float32) * fm
    im = Image.fromarray(np.clip(fa, 0, 255).astype(np.uint8), 'RGBA')
    m = text_mask('LITTLE, BROWN', 'ter', 15, track=0.16)
    put(im, colorize(m, (70, 68, 66)), W / 2, 1062)
    return finish(im, 31, gloss=0.03, wear=0.3, hinge=True, matte=0.025, warm=0.008, out=outp('17333223'))


# ---------------------------------------------------------------- Hitchhiker
def planet(d_, stripes, rng, ring=None):
    n = d_ * S
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    cx = cy = n / 2
    r = n / 2 - 2
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    msk = np.clip(r - dist, 0, 1)
    band = ((yy - cy) / r + 0.25 * np.sin((xx - cx) / r * 1.5) + 1) / 2 + 0.12 * (xx - cx) / r
    idx = np.clip((band * len(stripes)).astype(int), 0, len(stripes) - 1)
    col = np.array(stripes, np.float32)[idx]
    lx, ly = -0.45, -0.5
    nz = np.sqrt(np.clip(1 - ((xx - cx) / r) ** 2 - ((yy - cy) / r) ** 2, 0, 1))
    light = np.clip(((xx - cx) / r) * lx + ((yy - cy) / r) * ly + nz * 0.75, 0, 1)
    col = col * (0.35 + 0.85 * light[..., None]) + 60 * (light[..., None] ** 6)
    out = np.dstack([np.clip(col, 0, 255), msk * 255]).astype(np.uint8)
    return Image.fromarray(out, 'RGBA')


def hitchhiker():
    W = 154
    rng = np.random.default_rng(42)
    h, w = H * S, W * S
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    t = yy / h
    stops = [(0, (24, 38, 62)), (0.25, (16, 70, 104)), (0.5, (14, 118, 140)), (0.72, (18, 84, 116)), (1, (26, 42, 60))]
    bg = np.zeros((h, w, 3), np.float32)
    for c in range(3):
        bg[..., c] = np.interp(t, [s[0] for s in stops], [s[1][c] for s in stops])
    neb = fbm(h, w, 120 * S, rng, 4)
    bg += neb[..., None] * np.array([6, 22, 26], np.float32)
    # stars
    st = np.zeros((h, w), np.float32)
    for k in range(520):
        x, y = rng.integers(0, w), rng.integers(0, h)
        b = rng.uniform(0.25, 1.0) ** 2
        cv2.circle(st, (int(x), int(y)), int(rng.choice([1, 1, 1, 2, 2, 3])), float(b), -1, cv2.LINE_AA)
    for k in range(9):
        x, y = rng.integers(8, w - 8), rng.integers(8, h - 8)
        L = int(rng.uniform(5, 10) * S)
        cv2.line(st, (int(x - L), int(y)), (int(x + L), int(y)), 0.8, 1, cv2.LINE_AA)
        cv2.line(st, (int(x), int(y - L)), (int(x), int(y + L)), 0.8, 1, cv2.LINE_AA)
        cv2.circle(st, (int(x), int(y)), 3, 1.0, -1, cv2.LINE_AA)
    st = np.clip(st + cv2.GaussianBlur(st, (0, 0), 2 * S) * 0.8, 0, 1)
    bg = bg * (1 - st[..., None]) + np.array([235, 245, 250], np.float32) * st[..., None]
    im = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).convert('RGBA')

    cream, orange, dk = (252, 224, 190), (236, 118, 44), (120, 44, 16)

    def block(text, size, track=0.0):
        m = text_mask(text, 'popbi', size, track=track)
        pad = 14 * S
        cnv = Image.new('RGBA', (m.width + 2 * pad, m.height + 2 * pad), (0, 0, 0, 0))
        for k in range(int(4.5 * S), 0, -1):
            cnv.alpha_composite(colorize(m, dk if k == int(4.5 * S) else orange), (pad + k, pad + k))
        cnv.alpha_composite(colorize(dilate(m, 1), (150, 60, 20)), (pad, pad))
        cnv.alpha_composite(colorize(m, cream), (pad, pad))
        return cnv
    b1 = block("The Hitchhiker's", 47)
    b2 = block("Guide to the Galaxy", 47)
    put(im, rot(b1), W / 2 + 30, 44 + b1.width / S / 2)
    put(im, rot(b2), W / 2 - 28, 44 + b2.width / S / 2)
    yb = 44 + b2.width / S
    p1 = planet(74, [(190, 50, 60), (60, 160, 90), (50, 90, 180), (200, 60, 110), (70, 170, 120), (60, 80, 170), (190, 50, 60)], rng)
    put(im, p1, W / 2 + 6, yb + 62)
    m = text_mask('DOUGLAS ADAMS', 'popbi', 34, track=0.14)
    au = Image.new('RGBA', (m.width + 20, m.height + 20), (0, 0, 0, 0))
    au.alpha_composite(colorize(m, (90, 30, 10)), (12, 12))
    au.alpha_composite(colorize(m, (240, 128, 50)), (10, 10))
    ya = yb + 128
    put(im, rot(au), W / 2, ya + m.width / S / 2)
    # small ringed planet at the tail
    yr = min(1052, ya + m.width / S + 52)
    p2 = planet(40, [(150, 90, 190), (120, 70, 170), (170, 110, 200), (110, 60, 150)], rng)
    ringl = Image.new('RGBA', (90 * S, 60 * S), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ringl)
    rd.ellipse([4 * S, 20 * S, 86 * S, 40 * S], outline=(240, 170, 90, 255), width=int(2.5 * S))
    ringl = ringl.rotate(18, resample=Image.BICUBIC)
    back = ringl.copy()
    put(im, back, W / 2, yr)
    top = p2.crop((0, 0, p2.width, p2.height // 2 + 2))
    im.alpha_composite(top, (int(W / 2 * S - p2.width / 2), int(yr * S - p2.height / 2)))
    return finish(im, 41, gloss=0.14, creases=4, wear=0.75, paper=(232, 226, 210), crease_strength=0.6, fade=0.06, matte=0.03, warm=0.01, out=outp('11'))


# ---------------------------------------------------------------- Overstory
def overstory():
    W = 231
    rng = np.random.default_rng(3)
    cov = cv2.imread(B + '40180098-cover.jpg')
    ch, cw = cov.shape[:2]
    sw = int(round(W * ch / H))
    strip = cov[:, :sw].copy()
    hsv = cv2.cvtColor(strip, cv2.COLOR_BGR2HSV)
    txt = ((hsv[..., 2] > 150) & (hsv[..., 1] < 95)).astype(np.uint8) * 255
    band = np.zeros_like(txt)
    band[int(ch * .085):int(ch * .165)] = 255
    band[int(ch * .85):int(ch * .91)] = 255
    band[int(ch * .36):int(ch * .47), int(cw * .22):] = 255
    txt = cv2.dilate(txt & band, np.ones((3, 3), np.uint8), iterations=2)
    strip = cv2.inpaint(strip, txt, 4, cv2.INPAINT_TELEA)
    strip = strip[:, ::-1]  # mirror so the art runs on round the fold
    big = cv2.resize(strip, (W * S, H * S), interpolation=cv2.INTER_LANCZOS4)
    big = cv2.bilateralFilter(big, 9, 40, 9)
    a = cv2.cvtColor(big, cv2.COLOR_BGR2RGB).astype(np.float32)
    # painterly canvas grain so the enlargement doesn't read as blur
    h, w = H * S, W * S
    brush = fbm(h, w, 3 * S, rng, 2) * 7 + cv2.resize(rng.standard_normal((h // 6, w // 2)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC) * 4
    a += brush[..., None]
    a = (a - 128) * 1.06 + 124
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert('RGBA')
    white = (250, 248, 240)

    def tx(text, size):
        m = text_mask(text, 'popm', size, track=0.085)
        cnv = Image.new('RGBA', (m.width + 40 * S, m.height + 40 * S), (0, 0, 0, 0))
        shm = Image.new('L', cnv.size, 0); shm.paste(m, (20 * S, 20 * S))
        cnv.alpha_composite(colorize(shm.filter(ImageFilter.GaussianBlur(5 * S)).point(lambda v: int(v * 0.55)), (20, 14, 8)))
        cnv.alpha_composite(colorize(m, white), (20 * S, 20 * S))
        return cnv
    t1 = tx('The Overstory', 60)
    t2 = tx('Richard Powers', 47)
    put(im, rot(t1), W / 2, 30 + t1.width / S / 2)
    y2 = 30 + t1.width / S + 4
    put(im, rot(t2), W / 2, y2 + t2.width / S / 2)
    m = text_mask('NORTON', 'popm', 15, track=0.3)
    put(im, colorize(m, white), W / 2, 1056)
    return finish(im, 51, gloss=0.07, creases=3, wear=0.5, paper=(236, 230, 215), crease_strength=0.45, matte=0.02, out=outp('40180098'))


# ---------------------------------------------------------------- White Noise
def blob(w, h, circles, r_smooth=0):
    m = np.zeros((h, w), np.uint8)
    for (x, y, r) in circles:
        cv2.circle(m, (int(x * S), int(y * S)), int(r * S), 255, -1, cv2.LINE_AA)
    return m


def white_noise():
    W = 187
    rng = np.random.default_rng(77)
    h, w = H * S, W * S
    orange, cream, lite, line = (241, 84, 22), (236, 229, 216), (252, 150, 56), (122, 36, 4)
    im = canvas(W, orange)
    d = ImageDraw.Draw(im)
    yA, yB = 345, 790
    d.rectangle([0, yA * S, w, yB * S], fill=cream)

    def art(mask, fill=lite, lw=2.2):
        m = Image.fromarray(mask)
        out = dilate(m, lw * S / 2 + 1)
        im.alpha_composite(colorize(out, line))
        im.alpha_composite(colorize(erode(m, 1), fill))
    # top band: a slick that drips down over the cream
    m = np.zeros((h, w), np.uint8)
    xs = np.arange(0, w)
    edge = (250 + 22 * np.sin(xs / (26 * S)) + 12 * np.sin(xs / (9 * S) + 1)) * S
    for x in xs:
        m[int(96 * S + 16 * S * math.sin(x / (30 * S) + 2) + 8 * S * math.sin(x / (11 * S))):int(edge[x]), x] = 255
    for (x, L, r) in [(34, 372, 8), (66, 318, 7), (104, 392, 9), (142, 352, 7), (166, 300, 6)]:
        cv2.line(m, (x * S, 230 * S), (x * S, L * S), 255, int(r * 2 * S), cv2.LINE_AA)
        cv2.circle(m, (x * S, L * S), int((r + 2.5) * S), 255, -1, cv2.LINE_AA)
    cv2.circle(m, (104 * S, 424 * S), 6 * S, 255, -1, cv2.LINE_AA)
    m = cv2.GaussianBlur(m, (0, 0), 2 * S); m = ((m > 127) * 255).astype(np.uint8)
    m = cv2.GaussianBlur(m, (0, 0), 0.8 * S)
    art(m, fill=lite)
    # scribbled highlights in the slick
    for k in range(7):
        x0 = rng.uniform(20, W - 20); y0 = rng.uniform(140, 235)
        d.arc([(x0 - 16) * S, (y0 - 10) * S, (x0 + 16) * S, (y0 + 10) * S], rng.uniform(180, 220), rng.uniform(300, 350), fill=line + (255,), width=int(1.6 * S))
    # billowing cloud rising out of the bottom band
    circ = [(30, 905, 34), (70, 880, 40), (115, 872, 44), (155, 900, 36), (95, 930, 50), (40, 960, 40), (150, 960, 44), (95, 835, 30), (130, 820, 22), (60, 830, 24)]
    m = blob(w, h, circ)
    m = cv2.GaussianBlur(m, (0, 0), 0.8 * S)
    art(m, fill=lite)
    for (x, y, r) in circ[:8]:
        d.arc([(x - r * .6) * S, (y - r * .6) * S, (x + r * .6) * S, (y + r * .6) * S], 200, 330, fill=line + (255,), width=int(1.6 * S))
        d.arc([(x - r * .3) * S, (y - r * .3) * S, (x + r * .3) * S, (y + r * .3) * S], 20, 200, fill=line + (255,), width=int(1.4 * S))
    for (x, y, r) in [(22, 810, 7), (168, 822, 6), (150, 790, 4)]:
        mm = blob(w, h, [(x, y, r)]); art(cv2.GaussianBlur(mm, (0, 0), 0.8 * S), fill=lite)
    # type in the cream band
    ink = (30, 28, 28)
    t1 = dilate(text_mask('White Noise', 'adv', 52, track=0.03), 1)
    t2 = dilate(text_mask('Don DeLillo', 'adv', 36, track=0.04), 1)
    ymid = 612
    put(im, rot(colorize(t1, ink)), W / 2 + 24, ymid)
    put(im, rot(colorize(t2, ink)), W / 2 - 42, ymid)
    # the cover's little crossed strokes
    xc, yc = W / 2 - 12, ymid
    d.line([((xc - 5) * S, (yc - 26) * S), ((xc + 5) * S, (yc + 26) * S)], fill=orange + (255,), width=int(1.4 * S))
    d.line([((xc + 5) * S, (yc - 26) * S), ((xc - 5) * S, (yc + 26) * S)], fill=ink + (255,), width=int(1.2 * S))
    for i, t in enumerate(['PENGUIN', 'CLASSICS']):
        m_ = text_mask(t, 'pagb', 14.5, track=0.2)
        put(im, colorize(m_, (255, 246, 236)), W / 2, 1040 + i * 21)
    return finish(im, 61, gloss=0.02, creases=2, wear=0.4, paper=(240, 235, 225), crease_strength=0.35, matte=0.02, out=outp('28251250'))


# ---------------------------------------------------------------- Lonesome Dove
def lonesome_dove():
    W = 275
    rng = np.random.default_rng(9)
    h, w = H * S, W * S
    yy = np.mgrid[0:h, 0:w][0].astype(np.float32) / h
    top, bot = np.array([250, 214, 96], np.float32), np.array([244, 196, 74], np.float32)
    bg = top[None, None] * (1 - yy[..., None]) + bot[None, None] * yy[..., None]
    im = Image.fromarray(bg.astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(im)
    dk = (44, 30, 52)
    grad = [(0, (62, 52, 132)), (0.45, (120, 108, 190)), (0.8, (188, 176, 226)), (1, (150, 112, 120))]

    def western(text, size, squeeze, track=0.02, vertical=False):
        m = text_mask(text, 'bonb', size, track=track, squeeze=squeeze)
        pad = 12 * S
        mm = Image.new('L', (m.width + 2 * pad, m.height + 2 * pad), 0); mm.paste(m, (pad, pad))
        cnv = Image.new('RGBA', mm.size, (0, 0, 0, 0))
        o = dilate(mm, 1.6 * S)
        shd = ImageChops.offset(o, int(3.5 * S), int(3.5 * S))
        cnv.alpha_composite(colorize(shd, (150, 96, 40)))
        cnv.alpha_composite(colorize(o, dk))
        cnv.alpha_composite(vgrad(mm, grad))
        # highlight keyline
        hl = ImageChops.subtract(mm, ImageChops.offset(mm, int(1.2 * S), int(1.2 * S)))
        cnv.alpha_composite(colorize(hl.point(lambda v: int(v * 0.45)), (235, 230, 250)))
        return cnv
    # author across the head
    a1 = western('LARRY', 56, 0.78)
    a2 = western('McMURTRY', 56, 0.74)
    for a_ in (a1, a2):
        if a_.width > (W - 6) * S:
            pass
    a2 = a2.resize((int((W - 14) * S), a2.height), Image.LANCZOS) if a2.width > (W - 14) * S else a2
    put(im, a1, W / 2, 62)
    put(im, a2, W / 2, 122)
    d.line([(26 * S, 165 * S), ((W - 26) * S, 165 * S)], fill=dk + (255,), width=int(1.5 * S))
    d.line([(26 * S, 170 * S), ((W - 26) * S, 170 * S)], fill=dk + (255,), width=S // 2 + 1)
    # title down the spine
    t = western('LONESOME DOVE', 110, 0.64, track=0.012)
    put(im, rot(t), W / 2, 190 + t.width / S / 2)
    yb = 190 + t.width / S
    # the cover's prairie scene, as a framed vignette
    cov = Image.open(B + '256008-cover.jpg').convert('RGB')
    crop = cov.crop((104, 203, 292, 292))
    vw = (W - 30) * S
    vh = int(vw * crop.height / crop.width)
    crop = crop.resize((vw, vh), Image.LANCZOS).filter(ImageFilter.UnsharpMask(3, 60, 2))
    yv = min(yb + 14, 1100 - 60 - vh / S)
    im.paste(crop, (15 * S, int(yv * S)))
    d.rectangle([15 * S, int(yv * S), 15 * S + vw, int(yv * S) + vh], outline=dk + (255,), width=int(1.5 * S))
    m = text_mask('POCKET BOOKS', 'bonb', 13, track=0.18)
    put(im, colorize(m, dk), W / 2, 1066)
    return finish(im, 71, gloss=0.16, creases=7, wear=0.8, paper=(238, 232, 214), crease_strength=0.6, fade=0.05, matte=0.03, warm=0.006, out=outp('256008'))


# ---------------------------------------------------------------- Mrs Dalloway
def organic(mask, r):
    a = np.asarray(mask).astype(np.float32) / 255
    a = cv2.GaussianBlur(a, (0, 0), r * S)
    return Image.fromarray((np.clip((a - 0.46) * 9 + 0.5, 0, 1) * 255).astype(np.uint8))


def dalloway():
    W = 143
    rng = np.random.default_rng(14)
    h, w = H * S, W * S
    yellow, black, red = (246, 184, 18), (20, 19, 17), (196, 34, 40)
    im = canvas(W, yellow)
    d = ImageDraw.Draw(im)
    # author: heavy rounded art-nouveau-ish caps
    m = text_mask('VIRGINIA WOOLF', 'advb', 62, track=0.03, squeeze=0.9)
    pad = 10 * S
    mm = Image.new('L', (m.width + 2 * pad, m.height + 2 * pad), 0); mm.paste(m, (pad, pad))
    mm = organic(dilate(mm, 1.2 * S), 2.4)
    put(im, rot(colorize(mm, black)), W / 2, 40 + mm.width / S / 2)
    ya = 40 + mm.width / S
    # black lower field with a soft shoulder, like the figure on the cover
    yk = ya + 150
    fld = Image.new('L', (w, h), 0)
    fd = ImageDraw.Draw(fld)
    fd.rectangle([0, (yk + 40) * S, w, h], fill=255)
    fd.ellipse([-70 * S, (yk - 10) * S, 150 * S, (yk + 150) * S], fill=255)
    fld = organic(fld, 3)
    im.alpha_composite(colorize(fld, black))
    # sprig of leaves
    lf = Image.new('L', (w, h), 0)
    ld = ImageDraw.Draw(lf)
    stem = [(104 + 12 * math.sin(t * 2.2), yk + 60 - t * 190) for t in np.linspace(0, 1, 40)]
    ld.line([(x * S, y * S) for x, y in stem], fill=255, width=int(3 * S))
    for i in range(4, 40, 5):
        x, y = stem[i]
        for side in (-1, 1):
            L = 26 - i * 0.3
            ang = math.radians(-90 + side * 58 + 8 * math.sin(i))
            leaf = Image.new('L', (int(L * 2 * S), int(L * 2 * S)), 0)
            ImageDraw.Draw(leaf).ellipse([L * S, (L - L * 0.21) * S, 2 * L * S - 2, (L + L * 0.21) * S], fill=255)
            leaf = leaf.rotate(-math.degrees(ang), resample=Image.BICUBIC)
            lf.paste(255, (int(x * S - L * S), int(y * S - L * S)), leaf)
    lf = organic(lf, 1.0)
    im.alpha_composite(colorize(lf, black))
    # the rose
    rx, ry = 58, yk - 58
    d.line([(rx * S, ry * S), ((rx + 10) * S, (ry + 70) * S)], fill=black + (255,), width=int(2.5 * S))
    rm = blob(w, h, [(rx, ry, 13), (rx - 8, ry - 5, 8), (rx + 8, ry - 6, 8), (rx, ry - 11, 8)])
    rm = organic(Image.fromarray(rm), 1.2)
    im.alpha_composite(colorize(rm, red))
    d.arc([(rx - 7) * S, (ry - 8) * S, (rx + 7) * S, (ry + 6) * S], 30, 300, fill=(110, 12, 22, 255), width=int(1.6 * S))
    d.arc([(rx - 3) * S, (ry - 5) * S, (rx + 4) * S, (ry + 2) * S], 200, 90, fill=(110, 12, 22, 255), width=int(1.4 * S))
    # title, white serif on the black
    t = text_mask('Mrs. Dalloway', 'lora', 54, track=0.01)
    put(im, rot(colorize(t, (248, 244, 234))), W / 2, min(yk + 60 + t.width / S / 2 + 20, 1100 - 40 - t.width / S / 2))
    return finish(im, 81, gloss=0.03, creases=2, wear=0.45, paper=(240, 234, 220), crease_strength=0.4, matte=0.025, out=outp('14942'))


ALL = dict(fred=uncle_fred, mid=middlesex, gold=goldfinch, hh=hitchhiker, over=overstory, wn=white_noise, ld=lonesome_dove, dal=dalloway)
ims = []
for k, fn in ALL.items():
    if ONLY and k not in ONLY: continue
    ims.append(fn())
    print(k, ims[-1].size)
