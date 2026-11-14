import sys, json
from eng import *

PB = dict(creases=3, wear=.5, gloss=.08, crease_strength=.4)
PBO = dict(creases=5, wear=.8, crease_strength=.55, fade=.05, warm=.012, paper=(232, 224, 205))
HC = dict(hinge=True, gloss=.08, wear=.3)
MATTE = dict(wear=.35, creases=2, crease_strength=.3, gloss=.02)
CLOTH = dict(wear=.4, gloss=0, matte=.045)
WHT, BLK, CRM = (250, 248, 242), (22, 21, 20), (244, 238, 220)
import re
_d = json.loads(re.search(r'const DATA = (\{.*?\});\s*$', open(REPO + 'index.html', encoding='utf8').read(), re.M).group(1))
PAGES = {b['id']: b.get('pages') for y in _d for b in _d[y]}
SPECS = {}


def add(id, bg, items, fin=PB, **kw):
    SPECS[str(id)] = dict(id=str(id), pages=PAGES[str(id)], bg=bg, items=items, fin=fin, **kw)


def tiny(text, color, font='intsb', size=14, track=0.2):
    return Hh([T(text, font, size, color, track=track)])


# ---------- motifs (drawn in flow: fn(im, W, y0, rng))
def lay(im, mask, color, alpha=1.0):
    m = Image.fromarray((np.clip(mask, 0, 1) * 255 * alpha).astype(np.uint8))
    im.alpha_composite(colorize(m, color))


def roughen(m, rng, amt=0.5, sc=4):
    h, w = m.shape
    a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.5 * S)
    return np.clip((a + fbm(h, w, sc * S, rng, 3) * amt - 0.5) * 7 + 0.5, 0, 1)


def tiger(color):
    def fn(im, W, rng):
        h, w = im.height, im.width
        m = np.zeros((h, w), np.float32)
        for i in range(10):
            y = (40 + i * 110 + rng.uniform(-20, 20)) * S
            side = i % 2
            x0 = -10 * S if side else w + 10 * S
            x1 = rng.uniform(0.45, 0.8) * w if side else rng.uniform(0.2, 0.55) * w
            pts = []
            for t in np.linspace(0, 1, 20):
                th = (1 - t) ** 0.8 * rng.uniform(13, 22) * S
                xx = x0 + (x1 - x0) * t
                yy = y + math.sin(t * 2.2) * 30 * S * (1 if side else -1)
                pts.append((xx, yy, th))
            for xx, yy, th in pts:
                cv2.circle(m, (int(xx), int(yy)), int(th / 2) + 1, 1.0, -1)
        lay(im, roughen(m, rng, 0.3, 6), color)
    return fn


def figures(im, W, y0, rng, rows=3):
    rows = 3 if y0 < 400 else 2
    d = ImageDraw.Draw(im)
    cw = W / 3
    for r in range(rows):
        for c in range(4):
            x = (c * cw + (cw / 2 if r % 2 else 0) - 4) * S; y = (y0 + r * 58 + 6) * S
            d.ellipse([x + 9 * S, y, x + 19 * S, y + 10 * S], fill=(96, 60, 48, 255))
            d.rectangle([x + 6 * S, y + 11 * S, x + 22 * S, y + 28 * S], fill=(214, 40, 110, 255))
            d.line([x + 10 * S, y + 28 * S, x + 9 * S, y + 46 * S], fill=(120, 120, 120, 255), width=int(2.4 * S))
            d.line([x + 18 * S, y + 28 * S, x + 19 * S, y + 46 * S], fill=(120, 120, 120, 255), width=int(2.4 * S))
            d.ellipse([x + 22 * S, y + 30 * S, x + 30 * S, y + 40 * S], fill=(236, 190, 60, 255))


def papers(n, ys):
    def fn(im, W, rng):
        d = ImageDraw.Draw(im)
        for i in range(n):
            cx, cy = rng.uniform(15, W - 15) * S, rng.uniform(*ys) * S
            a = rng.uniform(0, 3.14); w_, h_ = rng.uniform(16, 26) * S, rng.uniform(22, 34) * S
            pts = [(cx + math.cos(a) * dx * w_ / 2 - math.sin(a) * dy * h_ / 2, cy + math.sin(a) * dx * w_ / 2 + math.cos(a) * dy * h_ / 2) for dx, dy in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]
            d.polygon([(x + 3 * S, y + 3 * S) for x, y in pts], fill=(120, 150, 150, 120))
            d.polygon(pts, fill=(252, 252, 250, 255), outline=(150, 160, 165, 255))
            for j in range(3):
                t = 0.3 + j * 0.2
                p0 = (pts[0][0] + (pts[3][0] - pts[0][0]) * t, pts[0][1] + (pts[3][1] - pts[0][1]) * t)
                p1 = (pts[1][0] + (pts[2][0] - pts[1][0]) * t, pts[1][1] + (pts[2][1] - pts[1][1]) * t)
                d.line([(p0[0] * .8 + p1[0] * .2, p0[1] * .8 + p1[1] * .2), (p0[0] * .2 + p1[0] * .8, p0[1] * .2 + p1[1] * .8)], fill=(170, 175, 180, 255), width=S)
    return fn


def burst(color, r=44, n=14, h=None, inner=0.55, squash=1.0, dot=None):
    def fn(im, W, y0, rng):
        cx, cy = W / 2 * S, (y0 + (h or 2 * r) / 2) * S
        pts = []
        for i in range(2 * n):
            rr = (r if i % 2 == 0 else r * inner) * S * rng.uniform(0.9, 1.1)
            a = i * math.pi / n
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr * squash))
        d = ImageDraw.Draw(im); d.polygon(pts, fill=tuple(color) + (255,))
        if dot: d.ellipse([cx - 8 * S, cy - 8 * S, cx + 8 * S, cy + 8 * S], fill=tuple(dot) + (255,))
    return fn


def spray(color, r=60):
    def fn(im, W, y0, rng):
        h, w = im.height, im.width
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        cx, cy = W / 2 * S, (y0 + r) * S
        dd = np.sqrt((xx - cx) ** 2 + ((yy - cy) * 0.8) ** 2) / (r * S)
        n = fbm(h, w, 18 * S, rng, 4)
        m = np.clip((0.78 - dd + n * 0.55) * 5, 0, 1)
        sp = (rng.random((h // 3, w // 3)) > 0.975).astype(np.float32)
        sp = cv2.resize(sp, (w, h), interpolation=cv2.INTER_LINEAR) * np.clip(1.6 - dd, 0, 1)
        lay(im, np.maximum(m * 0.92, np.clip(sp * 2, 0, 1)), color)
        d = ImageDraw.Draw(im)
        for i in range(3):
            x = cx + rng.uniform(-0.5, 0.5) * r * S
            d.line([x, cy, x, cy + rng.uniform(1.1, 1.9) * r * S], fill=tuple(color) + (230,), width=int(rng.uniform(2, 4) * S))
    return fn


def drip(color, x, y1, w=5):
    def fn(im, W, rng):
        d = ImageDraw.Draw(im)
        d.line([x * S, 0, x * S, y1 * S], fill=tuple(color) + (255,), width=int(w * S))
        d.ellipse([(x - w) * S, (y1 - w) * S, (x + w) * S, (y1 + w * 1.6) * S], fill=tuple(color) + (255,))
    return fn


def tentacle(color, lite, h=200):
    def fn(im, W, y0, rng):
        d = ImageDraw.Draw(im)
        pts = [((W / 2 + (W * 0.3) * math.sin(t * 5.2 + 1)) * S, (y0 + t * h) * S, (26 - 20 * t) * S) for t in np.linspace(0, 1, 90)]
        for x, y, r in pts:
            d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(color) + (255,))
        for x, y, r in pts[4::7]:
            d.ellipse([x - r * .3, y - r * .3, x + r * .3, y + r * .3], fill=tuple(lite) + (255,))
    return fn


def guitar(im, W, y0, rng, h=250):
    d = ImageDraw.Draw(im)
    cx = W / 2
    d.polygon([((cx - 22) * S, (y0 + h) * S), ((cx - 26) * S, (y0 + 70) * S), ((cx - 34) * S, (y0 + 20) * S), ((cx + 4) * S, y0 * S), ((cx + 30) * S, (y0 + 30) * S), ((cx + 22) * S, (y0 + 90) * S), ((cx + 22) * S, (y0 + h) * S)], fill=(18, 18, 18, 255))
    for i in range(4):
        y = (y0 + 28 + i * 20) * S
        d.ellipse([(cx - 4 + i * 2) * S, y - 6 * S, (cx + 8 + i * 2) * S, y + 6 * S], fill=(235, 235, 232, 255))
        d.rectangle([(cx - 50) * S, y - 3 * S, (cx - 28) * S, y + 3 * S], fill=(18, 18, 18, 255))
        d.ellipse([(cx - 60) * S, y - 7 * S, (cx - 46) * S, y + 7 * S], fill=(18, 18, 18, 255))
    for i in range(5):
        x = (cx - 16 + i * 8) * S
        d.line([x, (y0 + 110) * S, x, (y0 + h) * S], fill=(235, 235, 232, 255), width=max(1, int(0.8 * S)))
    for j in range(3):
        y = (y0 + 130 + j * 44) * S
        d.line([(cx - 22) * S, y, (cx + 22) * S, y], fill=(170, 170, 170, 255), width=S)


def fire(y0, y1, cols):
    def fn(im, W, rng):
        h, w = im.height, im.width
        a = np.asarray(im).astype(np.float32)
        yy = np.mgrid[0:h, 0:w][0].astype(np.float32) / S
        t = (yy - y0) / (y1 - y0)
        n = fbm(h, w, 70 * S, rng, 4) * 0.2 + cv2.resize(rng.standard_normal((h // (90 * S) + 2, w // (10 * S) + 2)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC) * 0.07
        tt = np.clip(t + n * 1.4, 0, 1)
        col = np.zeros((h, w, 3), np.float32)
        for c in range(3):
            col[..., c] = np.interp(tt, [s[0] for s in cols], [s[1][c] for s in cols])
        k = np.clip((t + n) * 7, 0, 1)[..., None]
        a[..., :3] = a[..., :3] * (1 - k) + col * k
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
    return fn


def scan(color, y0, y1, step=7, alpha=90):
    def fn(im, W, rng):
        d = ImageDraw.Draw(im, 'RGBA')
        for y in range(int(y0), int(y1), step):
            d.line([0, y * S, W * S, y * S], fill=tuple(color) + (alpha,), width=S)
    return fn


def stripes(c1, c2, y0, y1, n):
    def fn(im, W, rng):
        d = ImageDraw.Draw(im)
        hh = (y1 - y0) / n
        for i in range(n):
            d.rectangle([0, (y0 + i * hh) * S, W * S, (y0 + (i + 1) * hh) * S], fill=tuple(c1 if i % 2 == 0 else c2) + (255,))
    return fn


def stars(color, n, ys):
    def fn(im, W, rng):
        d = ImageDraw.Draw(im)
        for i in range(n):
            cx, cy, r = rng.uniform(8, W - 8) * S, rng.uniform(*ys) * S, rng.uniform(4, 9) * S
            pts = [(cx + math.cos(k * math.pi / 5 - 1.57) * (r if k % 2 == 0 else r * .42), cy + math.sin(k * math.pi / 5 - 1.57) * (r if k % 2 == 0 else r * .42)) for k in range(10)]
            d.polygon(pts, fill=tuple(color) + (255,))
    return fn


def feathers(color, n, ys):
    def fn(im, W, rng):
        for i in range(n):
            L = rng.uniform(16, 26) * S
            leaf = Image.new('RGBA', (int(L * 2), int(L * 2)), (0, 0, 0, 0))
            dd = ImageDraw.Draw(leaf)
            dd.ellipse([L * 0.1, L * 0.72, L * 1.9, L * 1.28], fill=tuple(color) + (255,))
            dd.line([L * 0.1, L, L * 1.9, L], fill=(240, 240, 220, 255), width=S)
            leaf = leaf.rotate(rng.uniform(0, 360), resample=Image.BICUBIC)
            im.alpha_composite(leaf, (int(rng.uniform(0, W) * S - L), int(rng.uniform(*ys) * S - L)))
    return fn


def patches(blocks):
    def fn(im, W, rng):
        d = ImageDraw.Draw(im)
        for (x0, y0, x1, y1, col, pat) in blocks:
            d.rectangle([x0 * W * S, y0 * S, x1 * W * S, y1 * S], fill=tuple(col) + (255,))
            if pat:
                bw, bh = int((x1 - x0) * W * S), int((y1 - y0) * S)
                lay_ = Image.new('RGBA', (bw, bh), tuple(col) + (255,))
                dl = ImageDraw.Draw(lay_)
                for k in range(-40, 80):
                    xx = k * 9 * S
                    dl.line([xx, 0, xx + bh, bh], fill=tuple(pat) + (255,), width=int(1.5 * S))
                    dl.line([xx + bh, 0, xx, bh], fill=tuple(pat) + (255,), width=int(1.5 * S))
                im.paste(lay_, (int(x0 * W * S), int(y0 * S)))
    return fn


# ---------- Everyman Wodehouse series
EG = (54, 56, 55)


def ev(id, l1, l2, col, smooth=False, h=330):
    add(id, ('solid', (243, 239, 221)), [
        Gap(8), Hh([T('P.G.', 'intsb', 20, EG, track=0.08), T('WODEHOUSE', 'intsb', 20, EG, track=0.08)], gap=9), Gap(14), Rule(EG, 1, 50), Gap(22),
        V([T(l1, 'intm', 50, EG, track=0.06, sc='intsb', scs=0.78), T(l2, 'intm', 50, EG, track=0.06, sc='intsb', scs=0.78)] if l2 else [T(l1, 'intm', 54, EG, track=0.06, sc='intsb', scs=0.78)], gap=16),
        Flex(), Crop(col, h=h, border=(30, 28, 30), smooth=smooth), Gap(40), tiny('EVERYMAN', EG, 'intsb', 14, 0.2), Gap(22)],
        fin=dict(HC, gloss=0.05, warm=0.012), top=30)


ev(18053, 'Meet', 'Mr Mulliner', (.47, .40, .97))
ev(16376, 'Full Moon', None, (.42, .36, .97))
ev(18041, 'Mr Mulliner', 'Speaking', (.52, .40, .98))
ev(9850375, 'Right Ho,', 'Jeeves', (.5, .38, .98))
ev(9928818, 'Joy in the', 'Morning', (.42, .30, .97))
ev(16390, 'The Mating', 'Season', (.42, .36, .97))
ev(18029, 'Ring for', 'Jeeves', (.5, .42, .98), smooth=True)
ev(16375, 'Jeeves and the', 'Feudal Spirit', (.62, .37, .86))
ev(16404, 'Jeeves in', 'the Offing', (.47, .30, .98))
ev(18025, 'Something', 'Fresh', (.45, .42, .98), smooth=True)
ev(12550, 'Stiff Upper Lip,', 'Jeeves', (.5, .27, .98))

# ---------- the rest
OR = (240, 128, 34)
add(54983, ('solid', (142, 140, 136)), [
    Gap(20), V(T('John McPhee', 'herb', 44, WHT)), Gap(26), V(T('Oranges', 'herb', 62, OR)),
    Flex(), Crop((.5, .52, 1.0, .86), border=None), Gap(26), tiny('PENGUIN', WHT), Gap(8)])

add(11529868, ('solid', (250, 249, 245)), [
    Gap(14), V([T("THE ORPHAN", 'hcnb', 78, (58, 72, 72), track=0.03), T("MASTER'S SON", 'hcnb', 78, (58, 72, 72), track=0.03)], gap=14),
    Flex(), V(T('ADAM JOHNSON', 'herb', 30, (40, 44, 44), track=0.3)), Gap(34), tiny('RANDOM HOUSE', (40, 44, 44), size=12), Gap(8)],
    under=[tiger((238, 98, 38))], fin=HC)

add(11376, ('bands', [(0, .19, (232, 74, 30)), (.19, .87, (250, 248, 240)), (.87, 1, (16, 14, 14))]), [
    Gap(196), V(T('SINCLAIR LEWIS', 'pagb', 48, (126, 98, 34), track=0.12, bold=0.5)), Gap(34),
    V(T('Main Street', 'cho', 62, (26, 22, 22), bold=1.1)), Gap(40), Flex(),
    Hh([T('MODERN', 'pagb', 14, (200, 176, 104), track=0.2), T('LIBRARY', 'pagb', 14, (200, 176, 104), track=0.2)], gap=7), Gap(40)],
    under=[scan((120, 30, 10), 16, 200, 9, 120)])

add(22237161, ('solid', (247, 242, 240)), [
    Fn(figures, 180), Gap(26), V(T('THE SELLOUT', 'terb', 58, (36, 34, 36), track=0.22)), Gap(40),
    V(T('PAUL BEATTY', 'terb', 44, (36, 34, 36), track=0.22)), Flex(), Fn(figures, 124), Gap(20), tiny('PICADOR', (60, 58, 60)), Gap(6)])

add(55817233, ('solid', (22, 48, 118)), [
    Gap(14), V([T('JOSHUA COHEN', 'herb', 44, WHT, track=0.03)]), Gap(30),
    V(T('THE NETANYAHUS', 'herb', 50, (238, 72, 56), track=0.03)), Flex(),
    Crop((.36, .33, .62), h=230), Gap(36), Hh([T('NEW YORK', 'herb', 12.5, WHT, track=0.1), T('REVIEW', 'herb', 12.5, WHT, track=0.1), T('BOOKS', 'herb', 12.5, WHT, track=0.1)], gap=5), Gap(8)])

add(39927096, ('solid', (188, 222, 216)), [
    Gap(110), V(T('LESS', 'popb', 132, (128, 128, 134), track=0.05, rough=0.25, organic=1.5)), Gap(60),
    V(T('ANDREW SEAN GREER', 'herb', 38, (58, 92, 160), track=0.2)), Flex()],
    under=[papers(5, (20, 120)), papers(4, (860, 1060))], fin=HC)

add(13055592, ('bands', [(0, .07, (238, 180, 50)), (.07, 1, (196, 28, 34))]), [
    Gap(74), V(T('JOHN SCALZI', 'hcnb', 76, BLK, track=0.03)), Gap(30),
    Fn(burst((240, 186, 60), r=54, n=4, inner=0.18, squash=0.5, dot=(196, 28, 34)), 70), Gap(30),
    V(T('REDSHIRTS', 'herbi', 76, WHT, outline=((30, 20, 20), 2.2), shadow=((30, 20, 20), 3, 3))), Flex(), tiny('TOR', WHT, 'herb', 20, 0.1), Gap(10)])

add(30929, ('solid', (250, 200, 28)), [
    Gap(40), V(T('Decline and Fall', 'ter', 64, BLK, box=((252, 252, 248), 26, 30, (120, 120, 110)), bold=0.5)), Gap(60),
    V(T('Evelyn Waugh', 'her', 38, BLK, bold=0.3)), Flex()])

add(34381330, ('strip', dict(x0=.06, blur=12, wash=((250, 250, 250), 0.4))), [
    Gap(20), V(T('IN THE DISTANCE', 'herb', 46, (140, 28, 36), track=0.2)), Gap(46),
    V(T('HERNAN DIAZ', 'herb', 34, (140, 28, 36), track=0.2)), Flex(), Hh([T('COFFEE', 'herb', 12, (90, 60, 60), track=0.14), T('HOUSE', 'herb', 12, (90, 60, 60), track=0.14)], gap=5), Gap(8)])

add(16241167, ('solid', (122, 152, 112)), [
    Gap(10), V(T('P.G. WODEHOUSE', 'bonb', 60, (246, 236, 200), squeeze=0.8, outline=((34, 52, 40), 2.2), shadow=((34, 52, 40), 3, 3))), Gap(34),
    V(T('YOUNG MEN IN SPATS', 'herb', 36, (252, 250, 240), track=0.06, outline=((34, 52, 40), 1.6))), Flex(), tiny('ARROW', (246, 236, 200), 'herb', 15), Gap(8)],
    under=[feathers((52, 122, 150), 9, (20, 1080))])

add(40605285, ('solid', (240, 232, 206)), [
    Gap(12), Rule((70, 50, 36), 1.5, 22, True), Gap(30),
    V([T('The Sweetness at the', 'pagb', 48, (48, 32, 24), sc='pagb', scs=0.8, track=0.03), T('Bottom of the Pie', 'pagb', 48, (48, 32, 24), sc='pagb', scs=0.8, track=0.03)], gap=18),
    Gap(46), V(T('Alan Bradley', 'pagb', 42, (48, 32, 24), sc='pagb', scs=0.8, track=0.05)), Flex(),
    Rule((70, 50, 36), 1.5, 22, True), Gap(18), tiny('THORNDIKE', (58, 40, 30), 'pagb', 13, 0.16), Gap(10)], fin=dict(HC, gloss=0.03))

add(10814, ('grad', [(0, (226, 216, 200)), (1, (206, 196, 180))]), [
    Gap(30), V(T('Here is New York', 'terb', 54, (128, 34, 30))), Gap(50), V(T('E. B. White', 'terb', 42, (34, 30, 28))), Flex()], fin=dict(HC, gloss=.04, warm=.01))

add(60521, ('bands', [(0, .5, (128, 202, 236)), (.5, 1, (20, 20, 22))]), [
    Gap(24), V(T('Pigs Have Wings', 'cho', 72, (20, 20, 22), bold=1.1)), Flex(0.25),
    V([T('P. G. Wodehouse', 'cho', 62, (250, 240, 190), bold=1.0), T('A Blandings Story', 'cho', 44, (246, 130, 150), bold=1.0)], gap=18), Flex(),
    Block((240, 112, 24)), Gap(46)], bot=0)

YEL = (252, 188, 44)
add(211721806, ('solid', (14, 13, 14)), [
    Gap(10), V([T('DUNGEON', 'popb', 62, YEL, organic=1.6), T('CRAWLER', 'popb', 62, YEL, organic=1.6)], gap=12), Gap(22),
    V(T('CARL', 'popb', 120, YEL, organic=2.2)), Gap(30), Fn(burst((240, 30, 120), r=62, n=11, inner=0.5, squash=0.9, dot=(14, 13, 14)), 110), Gap(30),
    V([T('MATT', 'popb', 50, YEL, organic=1.4), T('DINNIMAN', 'popb', 50, YEL, organic=1.4)], gap=12), Flex()])

add(18016, ('bands', [(0, .30, (226, 84, 40)), (.30, 1, (248, 240, 214))]), [
    Gap(14), V(T('P. G. WODEHOUSE', 'advb', 33, (255, 250, 240), track=0.12)), Gap(70),
    V(T('Mulliner Nights', 'cho', 78, (196, 36, 34), bold=1.3)), Flex(), Crop((.28, .36, .76), h=250), Gap(34), tiny('OVERLOOK', (90, 60, 50), size=12.5), Gap(8)])

add(203200544, ('solid', (6, 50, 166)), [
    Gap(26), V(T('PERFECTION', 'terb', 62, WHT, track=0.14)), Gap(70),
    V(T('VINCENZO LATRONICO', 'terb', 36, WHT, track=0.12)), Flex(),
    Hh([T('Fitzcarraldo', 'ter', 15, WHT, bold=0.4), T('Editions', 'ter', 15, WHT, bold=0.4)], gap=6), Gap(12)], fin=MATTE)

add(16241184, ('solid', (246, 242, 232)), [
    Gap(12), V(T('P.G.WODEHOUSE', 'dsc', 62, BLK, squeeze=0.8)), Gap(40),
    V(T('UNCLE DYNAMITE', 'herb', 38, WHT, track=0.05, box=((222, 40, 46), 18, 16))), Flex(),
    Block((240, 112, 24)), Gap(150)], bot=0, fin=PBO)

add(16241186, ('solid', (250, 248, 242)), [
    Gap(12), V(T('P. G. WODEHOUSE', 'terb', 54, BLK, track=0.06)), Gap(34),
    V(T('Cocktail Time', 'terb', 54, BLK, sc='terb', scs=0.8, track=0.06)), Flex(),
    Crop((.5, .30, .70), h=250, inset=14, border=(40, 30, 30)), Gap(30), Block((240, 112, 24)), Gap(90)], bot=0, fin=PBO)

add(297673, ('solid', (226, 226, 222)), [
    Gap(16), V([T('The Brief Wondrous Life', 'popm', 44, (26, 26, 28)), T('of Oscar Wao', 'popm', 44, (26, 26, 28))], gap=20), Gap(50),
    Fn(spray((226, 60, 62), 52), 160), Gap(10), V(T('Junot Díaz', 'popm', 48, (26, 26, 28))), Flex(), tiny('RIVERHEAD', (26, 26, 28), size=12), Gap(8)], fin=HC)

add(898737, ('grad', [(0, (56, 138, 62)), (.6, (70, 150, 70)), (1, (96, 160, 84))]), [
    Gap(12), V(T('P. G. WODEHOUSE', 'pagb', 46, (250, 240, 200), track=0.08)), Gap(40),
    V(T('The Clicking of Cuthbert', 'cho', 64, (252, 248, 224), bold=1.3)), Flex(), Crop((.3, .38, .8), h=280), Gap(40)], bot=0, fin=PBO)

CRD = (240, 232, 212)
add(199698485, ('strip', dict(blur=16, dark=0.42)), [
    Gap(70), V(T('THE GOD OF THE WOODS', 'adv', 58, CRD, track=0.08, bold=1.5)), Gap(60),
    V(T('LIZ MOORE', 'adv', 52, CRD, track=0.1, bold=1.5)), Flex(), tiny('RIVERHEAD', CRD, size=12.5), Gap(8)],
    under=[drip((244, 150, 186), 0, 0)], over=[], fin=HC)
SPECS['199698485']['under'] = [lambda im, W, rng: drip((244, 150, 186), W * 0.72, 300, 4)(im, W, rng)]

add(194802722, ('solid', (42, 104, 248)), [
    Gap(16), V(T('FUNNY STORY', 'hcnb', 104, WHT, track=0.02, skew=-0.12, shadow=((20, 50, 170), 3, 3))), Gap(50),
    V(T('EMILY HENRY', 'hcnb', 58, WHT, track=0.08)), Flex(),
    Fn(burst((250, 190, 50), r=20, n=8, inner=0.6), 40), Gap(24), tiny('BERKLEY', WHT, 'herb', 13), Gap(8)])

GOLD = (212, 196, 70)
add(5, ('grad', [(0, (88, 96, 132)), (.5, (112, 104, 150)), (1, (74, 84, 112))]), [
    Gap(16), V([T('HARRY POTTER', 'pagb', 66, GOLD, track=0.04, outline=((40, 36, 60), 2), shadow=((40, 36, 60), 2.5, 2.5)),
                T('and the Prisoner of Azkaban', 'pagbi', 42, (246, 238, 206), bold=0.6)], gap=18, align='center'), Gap(40),
    Hh([T('YEAR', 'pagb', 15, GOLD, track=0.2), T('3', 'pagb', 54, GOLD)], gap=8), Gap(40),
    V(T('ROWLING', 'pagb', 46, (236, 226, 190), track=0.16)), Flex(), tiny('SCHOLASTIC', WHT, 'herb', 12.5, 0.1), Gap(10)],
    under=[stars((230, 214, 90), 16, (20, 1080))], fin=HC)

add(58613424, ('solid', (200, 34, 30)), [
    Gap(14), V([T('HARRY POTTER', 'terb', 72, (250, 206, 70), track=0.05, outline=((40, 30, 80), 2)),
                T('and the Goblet of Fire', 'terbi', 44, (255, 244, 214), bold=0.7)], gap=18, align='center'), Gap(330),
    V(T('J.K. ROWLING', 'terb', 40, (250, 240, 210), track=0.1, box=((36, 60, 140), 16, 14))), Flex(), tiny('BLOOMSBURY', (250, 240, 210), 'terb', 13, 0.16), Gap(10)],
    under=[fire(430, 1100, [(0, (200, 34, 30)), (.25, (236, 110, 30)), (.6, (250, 170, 40)), (1, (150, 50, 20))])], fin=dict(HC, gloss=0.14))

add(38787, ('solid', (14, 14, 16)), [
    Gap(14), V([T('Pedro', 'dsc', 76, WHT, squeeze=0.78), ]), Gap(16), V(T('Páramo', 'dsc', 76, (116, 146, 236), squeeze=0.78)), Gap(40),
    V(T('JUAN RULFO', 'terb', 34, WHT, track=0.06)), Flex(), Crop((.5, .40, .82), h=250), Gap(36), tiny('GROVE', WHT, 'terb', 14), Gap(8)])

SIL = (222, 232, 236)
add(40526, ('grad', [(0, (44, 86, 106)), (.62, (58, 108, 128)), (1, (60, 110, 130))]), [
    Gap(18), V(T('JACK FINNEY', 'advb', 54, SIL, track=0.06)), Gap(36),
    V(T('Time and Again', 'pagb', 48, SIL, sc='pagb', scs=0.8, track=0.08)), Flex(), Crop((.5, .58, .97), h=270), Gap(34),
    Hh([T('FANTASY', 'pagb', 11.5, SIL, track=0.1), T('MASTERWORKS', 'pagb', 11.5, SIL, track=0.06)], gap=5), Gap(8)],
    under=[scan((200, 220, 230), 20, 700, 8, 40)])

MAR = (92, 30, 46)
add(374233, ('solid', (251, 250, 247)), [
    Gap(12), Crop((.03, .135, .77, .385), inset=0), Gap(40),
    V(T("If on a winter's night a traveler", 'terb', 37, (30, 28, 28))), Gap(46),
    V([T('italo', 'teri', 38, MAR, bold=0.4), T('calvino', 'her', 96, MAR)], gap=4), Flex()], fin=MATTE)

add(56692, ('bands', [(0, .25, (132, 36, 44)), (.25, .93, (236, 248, 206)), (.93, 1, (132, 36, 44))]), [
    Gap(6), V(T('GOTTMAN', 'pagb', 36, (250, 240, 214), track=0.1)), Gap(56),
    V([T('Why Marriages', 'pagb', 50, (24, 72, 82), sc='pagb', scs=0.8, track=0.05), T('Succeed or Fail', 'pagb', 50, (24, 72, 82), sc='pagb', scs=0.8, track=0.05)], gap=18), Flex(),
    tiny('FIRESIDE', (132, 36, 44), 'pagb', 13, 0.14), Gap(96)])

GILT = (214, 180, 96)
add(16241200, ('solid', (24, 72, 54)), [
    Gap(20), Rule(GILT, 2.5, 14, True), Gap(34), V(T('THANK YOU, JEEVES', 'pagb', 52, GILT, track=0.08, soft=((8, 30, 22), 2, 0.8))), Gap(30),
    Rule(GILT, 1.5, 40), Gap(34), V(T('WODEHOUSE', 'pagb', 42, GILT, track=0.14, soft=((8, 30, 22), 2, 0.8))), Flex(),
    Hh([T('HERBERT', 'pagb', 14, GILT, track=0.1), T('JENKINS', 'pagb', 14, GILT, track=0.1)], gap=6), Gap(20), Rule(GILT, 2.5, 14, True), Gap(18)],
    cloth=9, fin=dict(CLOTH, fade=0.04))

add(166997, ('solid', (190, 187, 178)), [
    Gap(60), V(T('STONER', 'herb', 46, (24, 24, 24), track=0.22)), Gap(60), V(T('JOHN WILLIAMS', 'herb', 32, (24, 24, 24), track=0.16)), Flex(),
    tiny('NYRB', (24, 24, 24), 'herb', 14), Gap(10)], cloth=3, fin=dict(MATTE, creases=0))

add(192893, ('solid', (240, 232, 214)), [
    Gap(8), Rule((200, 40, 40), 3, 0), Gap(6), Rule((30, 92, 172), 3, 0), Gap(20), tiny('MYSTERY', (30, 30, 30), 'herb', 14, 0.3), Gap(22),
    V(T('DOROTHY L. SAYERS', 'hcn', 96, (30, 92, 172), squeeze=0.62, track=0.06, bold=0.8, shadow=((206, 50, 44), 2, 2))), Gap(40),
    V(T('WHOSE BODY?', 'hcn', 80, (206, 44, 40), squeeze=0.66, track=0.07, bold=0.8)), Flex(), Rule((30, 92, 172), 3, 0), Gap(6), Rule((200, 40, 40), 3, 0), Gap(14)], fin=PBO)

PINK = (212, 26, 118)
add(41081373, ('solid', (250, 226, 32)), [
    Gap(150), V(T('Girl, Woman, Other', 'schb', 66, BLK)), Gap(60),
    V(T('BERNARDINE EVARISTO', 'herb', 36, PINK, track=0.08)), Flex(), Gap(120)],
    under=[patches([(0, 0, 1, 130, (40, 182, 222), (250, 250, 250)), (0, 1010, 1, 1100, PINK, None), (0, 965, 1, 1010, (150, 204, 60), None), (0.62, 130, 1, 170, (20, 20, 20), None)])])

add(34066798, ('grad', [(0, (58, 58, 60)), (.5, (34, 34, 36)), (1, (22, 22, 24))]), [
    Gap(20), V(T('A GENTLEMAN IN MOSCOW', 'advb', 52, (238, 60, 48), track=0.08)), Gap(50),
    V(T('AMOR TOWLES', 'advb', 44, WHT, track=0.12)), Flex(), tiny('VIKING', WHT, size=13), Gap(8)], fin=dict(HC, gloss=0.14))

BRN = (168, 128, 80)
add(292408, ('solid', BRN), [
    Gap(14), V(T('WALLACE STEGNER', 'pagb', 52, (24, 18, 14), track=0.1)), Gap(30), Crop((.28, .33, .92, .63), h=170), Gap(30),
    V(T('ANGLE OF REPOSE', 'pagb', 52, (24, 18, 14), track=0.1)), Flex(), Block((240, 112, 24)), Gap(70)], bot=0)

add(58733693, ('solid', (22, 138, 220)), [
    Gap(14), V([T('REMARKABLY', 'popb', 46, WHT, track=0.1), T('BRIGHT CREATURES', 'popb', 46, WHT, track=0.1)], gap=18), Gap(30),
    Fn(tentacle((246, 150, 44), (255, 204, 130), 190), 200), Gap(24), V(T('SHELBY VAN PELT', 'popb', 40, WHT, track=0.1)), Flex(), tiny('ECCO', WHT, 'popb', 14), Gap(8)], fin=HC)

add(10975, ('solid', (234, 224, 198)), [
    Gap(16), V([T('THE SOUND', 'pagb', 58, (30, 52, 170), track=0.03), T('AND THE FURY', 'pagb', 58, (30, 52, 170), track=0.03)], gap=16), Gap(46),
    V(T('WILLIAM FAULKNER', 'pagb', 44, (26, 24, 24), track=0.04)), Flex(),
    Hh([T('V-5', 'pagb', 22, (26, 24, 24)), T('VINTAGE', 'pagb', 12.5, (26, 24, 24), track=0.14)], gap=10), Gap(12)], fin=dict(PBO, warm=0.02))

FLAME = [(0, (236, 60, 40)), (.6, (244, 120, 40)), (1, (250, 170, 60))]
TEAL = [(0, (28, 120, 140)), (1, (60, 190, 190))]
add(52845775, ('solid', (252, 240, 226)), [
    Gap(18), V(T('MINOR FEELINGS', 'hcnb', 92, None, track=0.04, grad=FLAME, shadow=((60, 30, 40), 3, 3))), Gap(46),
    V(T('CATHY PARK HONG', 'hcnb', 58, None, track=0.05, grad=TEAL, shadow=((30, 50, 60), 2, 2))), Flex(), tiny('ONE WORLD', (60, 40, 40), 'herb', 12), Gap(8)])

add(608287, ('solid', (12, 11, 12)), [
    Gap(24), V(T("JESUS' SON", 'herb', 80, (222, 226, 96), track=0.12, rough=0.55)), Gap(50),
    V(T('DENIS JOHNSON', 'hcnb', 56, (226, 88, 120), track=0.08, rough=0.25)), Flex(), tiny('PICADOR', (214, 78, 110), size=12.5), Gap(8)])

add(40656712, ('solid', (216, 202, 164)), [
    Gap(6), Hh([T('FAWCETT', 'herb', 12.5, BLK, track=0.06), T('CREST', 'herb', 12.5, BLK, track=0.06), T('95¢', 'herb', 22, BLK)], gap=6), Gap(26),
    V(T('Rabbit, Run', 'bonbi', 76, BLK)), Gap(44), V(T('JOHN UPDIKE', 'bonbi', 50, (28, 108, 128))), Flex()], fin=dict(PBO, creases=6, warm=0.02))

add(1736739, ('strip', dict(blur=14, wash=((236, 244, 224), 0.42))), [
    Gap(24), V(T('ELIZABETH STROUT', 'pagb', 44, MAR, track=0.14)), Gap(46),
    V(T('Olive Kitteridge', 'cho', 78, (24, 26, 22), bold=1.4)), Flex(), Hh([T('RANDOM', 'pagb', 12, MAR, track=0.1), T('HOUSE', 'pagb', 12, MAR, track=0.1)], gap=5), Gap(8)])

add(320, ('bands', [(0, .70, (238, 206, 176)), (.70, 1, (16, 22, 16))]), [
    Gap(10), V([T('ONE HUNDRED YEARS', 'herb', 46, BLK), T('OF SOLITUDE', 'herb', 46, BLK)], gap=14), Gap(30),
    V([T('GABRIEL GARCIA', 'herb', 33, (140, 36, 24), track=0.03), T('MARQUEZ', 'herb', 33, (140, 36, 24), track=0.03)], gap=10), Flex(),
    Crop((.45, .34, .80), h=290), Gap(24), tiny('AVON', WHT, 'herb', 17), Gap(8)], fin=PBO)

MAG = (232, 22, 130)
add(49552, ('solid', (252, 222, 40)), [
    Gap(60), V([T('THE STRANGER,', 'hcnb', 50, WHT, track=0.03), T('THE PLAGUE', 'hcnb', 50, WHT, track=0.03)], gap=14), Gap(30),
    V(T('Notes', 'hcnb', 40, (255, 240, 120))), Gap(26), V(T('CAMUS', 'hcnb', 30, WHT, track=0.1)), Flex(),
    Hh([T('COLES', 'dsc', 30, BLK, box=((252, 222, 40), 8, 8, (20, 20, 20)))]), Gap(24)],
    under=[stripes((252, 222, 40), (18, 18, 18), 0, 1100, 44),
           lambda im, W, rng: ImageDraw.Draw(im).rounded_rectangle([10 * S, 40 * S, (W - 10) * S, 820 * S], radius=40 * S, fill=MAG + (255,), outline=(252, 250, 250, 255), width=5 * S)], fin=PBO)

add(28921, ('solid', (48, 34, 26)), [
    Gap(14), V([T('THE REMAINS', 'terb', 62, (204, 228, 228), squeeze=0.82, track=0.04), T('OF THE DAY', 'terb', 62, (204, 228, 228), squeeze=0.82, track=0.04)], gap=16), Gap(30),
    Crop((.66, .47, .84), h=190), Gap(30), V(T('KAZUO ISHIGURO', 'terb', 38, (214, 76, 172), track=0.05)), Flex(), tiny('FABER', (196, 222, 222), 'terb', 14), Gap(8)])

add(5439, ('strip', dict(x0=.02, blur=14, dark=0.06)), [
    Gap(60), V(T('interpreter of maladies', 'herb', 50, WHT, soft=((120, 60, 10), 4, 0.6))), Gap(50),
    V(T('Jhumpa Lahiri', 'her', 34, (50, 40, 30), bold=0.5, box=((226, 208, 170), 16, 13))), Flex(), tiny('MARINER', WHT, 'herb', 12.5), Gap(8)])

add(46917, ('grad', [(0, (222, 176, 112)), (.5, (206, 150, 84)), (1, (188, 130, 70))]), [
    Gap(40), V([T('John Updike', 'curbi', 62, (22, 20, 30), track=0.04), T('rabbit redux', 'curbi', 50, (22, 20, 30), track=0.06)], gap=22, align='start'), Flex(), tiny('FAWCETT', (40, 26, 16), 'herb', 13), Gap(10)],
    under=[lambda im, W, rng: ImageDraw.Draw(im).polygon([(W * .12 * S, 22 * S), (W * .9 * S, 14 * S), (W * .93 * S, 600 * S), (W * .1 * S, 612 * S)], fill=(250, 248, 244, 255))])

add(58613451, ('bands', [(0, .46, (204, 172, 44)), (.46, 1, (40, 92, 180))]), [
    Gap(14), V([T('HARRY POTTER', 'terb', 80, (132, 30, 40), track=0.05),
                T('and the Order of the Phoenix', 'terbi', 44, (50, 22, 22), bold=0.7)], gap=20, align='center'), Gap(360),
    V(T('J.K. ROWLING', 'terb', 44, (250, 240, 210), track=0.1, box=((132, 30, 40), 16, 14))), Flex(), tiny('BLOOMSBURY', (250, 240, 210), 'terb', 14, 0.16), Gap(10)],
    under=[fire(560, 1100, [(0, (40, 92, 180)), (.3, (236, 120, 40)), (.65, (250, 190, 60)), (1, (190, 60, 30))])], fin=dict(HC, gloss=0.14))

add(13707720, ('solid', (166, 176, 70)), [
    Gap(10), V(T('P.G. WODEHOUSE', 'bonb', 62, (250, 244, 200), squeeze=0.8, outline=((40, 56, 30), 2.2), shadow=((40, 56, 30), 3, 3))), Gap(34),
    V(T('LEAVE IT TO PSMITH', 'herb', 38, (252, 250, 240), track=0.06, outline=((40, 56, 30), 1.6))), Flex(), tiny('ARROW', (40, 56, 30), 'herb', 15), Gap(8)])

add(7331435, ('solid', (72, 200, 216)), [
    Gap(14), V(T('JENNIFER EGAN', 'hcnb', 70, WHT, track=0.04)), Gap(36),
    V([T('A VISIT FROM', 'hcnb', 46, WHT, track=0.04), T('THE GOON SQUAD', 'hcnb', 46, WHT, track=0.04)], gap=14), Flex(), Fn(guitar, 270)], bot=0)

add(58817174, ('solid', (12, 12, 12)), [
    Gap(16), V([T('SHOOTING', 'popb', 36, (250, 226, 30), squeeze=1.2), T('COLUMBO', 'popb', 62, (250, 226, 30), squeeze=1.25)], gap=14), Gap(50),
    V(T('DAVID KOENIG', 'popb', 36, (250, 226, 30), squeeze=1.1)), Flex(), Hh([T('BONAVENTURE', 'herb', 11, WHT, track=0.06), T('PRESS', 'herb', 11, WHT, track=0.06)], gap=5), Gap(8)])

add(187020, ('bands', [(0, .46, (236, 230, 214)), (.46, 1, (18, 16, 16))]), [
    Gap(20), V(T('Empire Falls', 'cho', 100, (150, 26, 34), bold=1.8)), Gap(50), Crop((.34, .50, .73), h=200), Gap(40),
    V(T('RICHARD RUSSO', 'schb', 40, (240, 234, 218), track=0.24)), Flex(), tiny('VINTAGE', (240, 234, 218), 'pagb', 13, 0.16), Gap(8)])

# ---------- added later: new covers supplied by Ian, and Football
def frame(color, inset=9, th=2.0, double=True):
    def fn(im, W, rng):
        d = ImageDraw.Draw(im)
        c = tuple(color) + (255,)
        d.rectangle([inset * S, inset * S, (W - inset) * S, (H - inset) * S], outline=c, width=int(th * S))
        if double:
            d.rectangle([(inset + 5) * S, (inset + 5) * S, (W - inset - 5) * S, (H - inset - 5) * S], outline=c, width=max(1, int(th * S * 0.4)))
    return fn


def speckle(amt=14):
    def fn(im, W, rng):
        a = np.asarray(im).astype(np.float32)
        h, w = a.shape[:2]
        n = cv2.resize(rng.standard_normal((h // 3, w // 3)).astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
        a[..., :3] += (n * amt)[..., None] + (fbm(h, w, 160 * S, rng, 3) * 10)[..., None]
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
    return fn


def stamp(cover, box, color, h, inset=20):
    """lift light line-art (gilt stamping) off a dark cloth cover and re-ink it on the spine"""
    def fn(im, W, y0, rng):
        c = Image.open(B + cover).convert('L')
        cw, ch = c.size
        c = c.crop((int(box[0] * cw), int(box[1] * ch), int(box[2] * cw), int(box[3] * ch)))
        tw = (W - 2 * inset) * S
        th = int(tw * c.height / c.width)
        if th > h * S:
            th = int(h * S); tw = int(th * c.width / c.height)
        a = np.asarray(c.resize((int(tw), th), Image.BICUBIC)).astype(np.float32)
        a = cv2.GaussianBlur(a, (0, 0), 0.8 * S)
        lo, hi = np.percentile(a, 30), np.percentile(a, 99.5)
        m = np.clip((a - (lo + 0.38 * (hi - lo))) / (0.22 * (hi - lo)), 0, 1)
        layer = colorize(Image.fromarray((m * 255).astype(np.uint8)), color)
        im.alpha_composite(layer, (int(W * S / 2 - tw / 2), int((y0 + h / 2) * S - th / 2)))
    return fn


def bars(top, bottom, w=44, hh=9):
    def fn(im, W, y0, rng):
        d = ImageDraw.Draw(im)
        x0 = (W - w) / 2
        d.rectangle([x0 * S, y0 * S, (x0 + w) * S, (y0 + hh) * S], fill=tuple(top) + (255,))
        d.rectangle([x0 * S, (y0 + hh) * S, (x0 + w) * S, (y0 + 2 * hh) * S], fill=tuple(bottom) + (255,))
    return fn


def disc(im, W, y0, rng, r=66):
    h, w = im.height, im.width
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = W / 2 * S, (y0 + r) * S
    ang = np.arctan2(yy - cy, xx - cx)
    wob = 1 + 0.05 * np.sin(ang * 3 + 1) + 0.03 * np.sin(ang * 7)
    dd = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (r * S * wob)
    a = np.asarray(im).astype(np.float32)
    streak = fbm(h, w, 5 * S, rng, 2) * 26 + np.sin(ang * 22 + dd * 30) * 9
    rim = np.clip((1 - dd) * 30, 0, 1)
    inner = np.clip((0.66 - np.sqrt((xx - cx - 5 * S) ** 2 + (yy - cy + 3 * S) ** 2) / (r * S)) * 14, 0, 1)
    col = (236 + streak)[..., None] * np.array([1, 0.99, 0.95], np.float32)
    col = col * (1 - inner[..., None]) + np.array([178, 174, 164], np.float32) * (0.92 + 0.1 * np.clip(dd, 0, 1))[..., None] * inner[..., None]
    sh = np.clip((1 - np.sqrt((xx - cx - 4 * S) ** 2 + (yy - cy - 5 * S) ** 2) / (r * S * 1.06)) * 8, 0, 1) * 0.25
    a[..., :3] *= (1 - sh * (1 - rim))[..., None]
    a[..., :3] = a[..., :3] * (1 - rim[..., None]) + col * rim[..., None]
    im.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA'))


PAGES.update({'138758152': 228, '200700624': PAGES.get('200700624') or 256})

CMINT, CMAR, CPINK = (176, 226, 200), (124, 36, 58), (246, 112, 174)
add(138758152, ('solid', (74, 84, 78)), [
    Gap(8), Fn(bars(CPINK, BLK), 18), Gap(26),
    V(T('RAYMOND CARVER', 'advb', 46, CMAR, track=0.04, box=(CMINT, 16, 13), shadow=((40, 34, 44), 2.5, 2.5))), Gap(40),
    V(T('CATHEDRAL', 'advb', 46, CPINK, track=0.3)), Gap(22), Fn(bars(BLK, BLK, 44, 6), 12), Flex(),
    Crop((.31, .275, .465), h=190), Gap(34),
    Hh([T('VINTAGE', 'herb', 12.5, WHT, track=0.3), T('CONTEMPORARIES', 'herb', 11, WHT, track=0.08)], gap=6), Gap(10)],
    under=[speckle()], fin=dict(PBO, creases=3, crease_strength=.35))

add(60194162, ('solid', (240, 233, 212)), [
    Gap(34), V([T('DEMON COPPERHEAD', 'hcnb', 80, (204, 60, 44), track=0.05),
               T('BARBARA KINGSOLVER', 'hcnb', 72, (32, 80, 160), track=0.05)], gap=26), Flex(),
    Crop((.27, .795, .935), h=170, inset=22, border=(30, 30, 30)), Gap(34), tiny('HARPER', (30, 30, 30), 'herb', 14), Gap(26)],
    cover='demon-cover.jpg', over=[frame((30, 30, 30), 9, 2.2)], fin=HC, side=60)

add(242445364, ('solid', (252, 190, 17)), [
    Gap(20), V([T('SISTERS OF A', 'advb', 50, BLK, track=0.1), T('HALVED HEART', 'advb', 50, BLK, track=0.1)], gap=16), Gap(30),
    Crop((.5, .50, .84), h=270), Gap(30), V(T('NAYANTARA ROY', 'advb', 38, BLK, track=0.1)), Flex()], fin=HC)

add(200700624, ('solid', (242, 195, 205)), [
    Gap(36), V(T('The Stalker', 'terb', 78, BLK)), Gap(40), Fn(disc, 132), Gap(40),
    V(T('Paula Bomer', 'terb', 54, BLK)), Flex(), tiny('SOHO', BLK, 'terb', 15, 0.24), Gap(10)], fin=dict(PB, gloss=.05))

SLN = (22, 44, 68)
add(13707659, ('solid', (208, 84, 94)), [
    Gap(6), Rule(SLN, 2, 0), Gap(30),
    V([T('SUMMER LIGHTNING', 'herb', 52, SLN, track=0.12), T('P. G. WODEHOUSE', 'herb', 52, SLN, track=0.17)], gap=22), Gap(30), Rule(SLN, 2, 0), Flex(),
    Crop((.60, .47, .70), h=230, border=SLN), Gap(30), tiny('NORTON', SLN, 'herb', 14), Gap(8)],
    cover='sl-cover.jpg', fin=PB)

CG = (226, 194, 108)
add(898737, ('solid', (44, 124, 106)), [
    Gap(18), Rule(CG, 2.5, 14, True), Gap(34),
    V([T('THE CLICKING', 'pagb', 58, CG, track=0.06, soft=((14, 60, 48), 2, 0.8)), T('OF CUTHBERT', 'pagb', 58, CG, track=0.06, soft=((14, 60, 48), 2, 0.8))], gap=18), Gap(30), Rule(CG, 1.5, 40), Gap(30),
    V(T('P. G. WODEHOUSE', 'pagb', 42, CG, track=0.1, soft=((14, 60, 48), 2, 0.8))), Flex(),
    Fn(stamp('898737-cover.jpg', (.20, .56, .56, .89), CG, 190, inset=14), 190), Gap(26), Rule(CG, 2.5, 14, True), Gap(18)],
    cloth=9, fin=CLOTH)

add(7354, ('solid', (208, 213, 217)), [
    Gap(14), Hh([T('4th', 'herb', 22, WHT, box=((96, 160, 210), 9, 9))]), Gap(30),
    V([T('Annie Proulx', 'popm', 52, (40, 58, 150)), T('The Shipping News', 'popm', 52, (34, 122, 200))], gap=18), Flex(),
    Crop((.36, .55, 1.0), h=360)], cover='ship-cover.jpg', bot=0, fin=PB)

FG = (224, 182, 98)
add(239522729, ('solid', (140, 33, 22)), [
    Gap(44), V(T('FOOTBALL', 'advb', 60, FG, track=0.22, soft=((60, 10, 6), 2, 0.8))), Gap(46),
    Fn(stamp('football-cover.jpg', (.27, .33, .73, .56), FG, 150, inset=14), 150), Gap(46),
    V(T('CHUCK KLOSTERMAN', 'advb', 39, FG, track=0.14, soft=((60, 10, 6), 2, 0.8))), Flex(),
    Hh([T('PENGUIN', 'advb', 12, FG, track=0.16), T('PRESS', 'advb', 12, FG, track=0.16)], gap=6), Gap(30)],
    cover='football-cover.jpg', cloth=8, over=[frame(FG, 9, 2.0)], fin=dict(CLOTH, hinge=True))


if __name__ == '__main__':
    only = sys.argv[1:]
    for k, sp in SPECS.items():
        if only and k not in only: continue
        try:
            im = build(sp); print(k, im.size)
        except Exception as e:
            import traceback; traceback.print_exc(); print('FAIL', k)
