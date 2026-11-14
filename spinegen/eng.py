from lib import *

import os
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
B = REPO + 'books/'


class T:
    """one line of lettering"""
    def __init__(s, text, font, size, color, track=0.0, squeeze=1.0, sc=None, bold=0, outline=None, shadow=None,
                 soft=None, grad=None, organic=0, rough=0, skew=0, box=None, scs=0.8):
        s.__dict__.update(locals()); del s.__dict__['s']

    def render(s, k=1.0, seed=0):
        m = text_mask(s.text, s.font, s.size * k, s.track, s.squeeze, s.sc, s.scs)
        pad = int((10 + s.size * 0.12) * S * k) + (int(s.box[1] * S) if s.box else 0)
        mm = Image.new('L', (m.width + 2 * pad, m.height + 2 * pad), 0)
        mm.paste(m, (pad, pad))
        if s.bold:
            a = np.asarray(mm).astype(np.float32) / 255
            a = cv2.GaussianBlur(a, (0, 0), max(0.6, s.bold * S * 0.6))
            mm = Image.fromarray((np.clip((a - (0.5 - min(0.42, 0.16 * s.bold * S))) * 6 + 0.5, 0, 1) * 255).astype(np.uint8))
        if s.organic:
            a = np.asarray(dilate(mm, max(1, int(s.organic * 0.5 * S)))).astype(np.float32) / 255
            a = cv2.GaussianBlur(a, (0, 0), s.organic * S * k)
            mm = Image.fromarray((np.clip((a - 0.46) * 9 + 0.5, 0, 1) * 255).astype(np.uint8))
        if s.skew:
            mm = mm.transform(mm.size, Image.AFFINE, (1, s.skew, -s.skew * mm.height / 2, 0, 1, 0), Image.BICUBIC)
        if s.rough:
            rng = np.random.default_rng(seed + len(s.text))
            a = np.asarray(mm).astype(np.float32) / 255
            n = fbm(a.shape[0], a.shape[1], 2.2 * S, rng, 2)
            n2 = fbm(a.shape[0], a.shape[1], 14 * S, rng, 2)
            a = cv2.GaussianBlur(a, (0, 0), 1.0 * S)
            a = np.clip((a + n * 0.5 * s.rough + n2 * 0.2 * s.rough - 0.5) * 7 + 0.5, 0, 1)
            mm = Image.fromarray((a * 255).astype(np.uint8))
        cnv = Image.new('RGBA', mm.size, (0, 0, 0, 0))
        if s.box:
            col, px_, py_ = s.box[0], s.box[1], s.box[2] if len(s.box) > 2 else s.box[1]
            d = ImageDraw.Draw(cnv)
            d.rectangle([pad - px_ * S, pad - py_ * S, pad + m.width + px_ * S, pad + m.height + py_ * S], fill=tuple(col) + (255,),
                        outline=(tuple(s.box[3]) + (255,)) if len(s.box) > 3 else None, width=S)
        if s.soft:
            col, r, al = s.soft
            cnv.alpha_composite(colorize(mm.filter(ImageFilter.GaussianBlur(r * S)).point(lambda v: int(v * al)), col))
        o = dilate(mm, max(1, int(s.outline[1] * S * k))) if s.outline else mm
        if s.shadow:
            col, dx, dy = s.shadow
            n = max(1, int(max(abs(dx), abs(dy)) * S * k))
            for i in range(n, 0, -1):
                cnv.alpha_composite(colorize(ImageChops.offset(o, int(dx * S * k * i / n), int(dy * S * k * i / n)), col))
        if s.outline:
            cnv.alpha_composite(colorize(o, s.outline[0]))
        cnv.alpha_composite(vgrad(mm, s.grad) if s.grad else colorize(mm, s.color))
        s._pad = pad
        return cnv


class V:
    def __init__(s, lines, align='start', gap=13):
        s.lines = lines if isinstance(lines, list) else [lines]; s.align = align; s.gap = gap


class Hh:
    def __init__(s, lines, gap=4, margin=8):
        s.lines = lines if isinstance(lines, list) else [lines]; s.gap = gap; s.margin = margin


class Gap:
    def __init__(s, px): s.px = px


class Flex:
    def __init__(s, w=1.0): s.w = w


class Rule:
    def __init__(s, color, th=1.5, inset=20, double=False): s.color = color; s.th = th; s.inset = inset; s.double = double


class Crop:
    """picture from the cover. box rel (x0,y0,x1,y1) or centred column (cx,y0,y1) fitted to h"""
    def __init__(s, box, h=None, inset=0, border=None, smooth=False, full=False):
        s.box = box; s.h = h; s.inset = inset; s.border = border; s.smooth = smooth


class Block:
    """solid band behind following items until EndBlock"""
    def __init__(s, color, to=None): s.color = color


class Fn:
    def __init__(s, fn, h): s.fn = fn; s.h = h


def sr_for(pages):
    return max(0.115, min(0.25, 0.105 + 0.00021 * (pages or 240)))


def make_bg(W, bg, cover, rng):
    h, w = H * S, W * S
    kind = bg[0]
    yy = (np.mgrid[0:h, 0:w][0].astype(np.float32)) / h
    if kind == 'solid':
        a = np.ones((h, w, 3), np.float32) * np.array(bg[1], np.float32)
    elif kind == 'grad':
        a = np.zeros((h, w, 3), np.float32)
        for c in range(3):
            a[..., c] = np.interp(yy, [s[0] for s in bg[1]], [s[1][c] for s in bg[1]])
    elif kind == 'bands':
        a = np.zeros((h, w, 3), np.float32)
        for y0, y1, col in bg[1]:
            a[int(y0 * h):int(y1 * h)] = col
    elif kind == 'strip':
        o = bg[1]
        cov = cv2.cvtColor(cv2.imread(cover), cv2.COLOR_BGR2RGB)
        ch, cw = cov.shape[:2]
        sw = int(round(W * ch / H))
        x0 = int(o.get('x0', 0) * cw)
        st = cov[:, x0:x0 + sw][:, ::-1]
        big = cv2.resize(st, (w, h), interpolation=cv2.INTER_CUBIC)
        if o.get('blur'):
            big = cv2.GaussianBlur(big, (0, 0), o['blur'] * S)
        a = big.astype(np.float32)
        a += (fbm(h, w, 3 * S, rng, 2) * 6)[..., None]
        if o.get('dark'):
            a *= (1 - o['dark'])
        if o.get('wash'):
            col, al = o['wash']
            a = a * (1 - al) + np.array(col, np.float32) * al
    return a


def cloth(a, rng, amt=7):
    h, w, _ = a.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    weave = np.sin(xx * 2 * np.pi / (2.2 * S)) * np.sin(yy * 2 * np.pi / (2.2 * S))
    weave += 0.6 * fbm(h, w, 2 * S, rng, 1)
    return a + (weave * amt)[..., None]


def build(spec, out=None):
    cover = B + spec.get('cover', f"{spec['id']}-cover.jpg")
    W = spec.get('W') or int(round(H * sr_for(spec.get('pages'))))
    seed = spec.get('seed', sum(map(ord, str(spec['id']))))
    rng = np.random.default_rng(seed)
    a = make_bg(W, spec['bg'], cover, rng)
    if spec.get('cloth'):
        a = cloth(a, rng, spec['cloth'])
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert('RGBA')
    for fn in spec.get('under', []):
        r = fn(im, W, rng)
        if r is not None: im = r
    items = spec['items']
    top, bot = spec.get('top', 34), spec.get('bot', 30)
    covim = None

    def crop_img(it, k=1.0):
        nonlocal covim
        if covim is None: covim = Image.open(cover).convert('RGB')
        cw, ch = covim.size
        tw = W - 2 * it.inset
        if len(it.box) == 3:
            cx, y0, y1 = it.box
            hh = it.h or 300
            ph = (y1 - y0) * ch
            pw = ph * tw / hh
            x0 = min(max(0, cx * cw - pw / 2), cw - pw)
            box = (x0, y0 * ch, x0 + pw, y1 * ch)
        else:
            box = (it.box[0] * cw, it.box[1] * ch, it.box[2] * cw, it.box[3] * ch)
            hh = it.h or tw * (box[3] - box[1]) / (box[2] - box[0])
        c = covim.crop(tuple(int(v) for v in box)).resize((int(tw * S), int(hh * S)), Image.BICUBIC)
        if it.smooth:
            c = c.filter(ImageFilter.MedianFilter(7)).filter(ImageFilter.GaussianBlur(1.2)).filter(ImageFilter.UnsharpMask(4, 120, 2))
        else:
            c = c.filter(ImageFilter.UnsharpMask(3, 70, 2))
        return c, hh

    # measure
    def measure(k):
        res = []
        for it in items:
            if isinstance(it, V):
                ims = [t.render(k, seed) for t in it.lines]
                thick = sum(i.height - 2 * t._pad for i, t in zip(ims, it.lines)) / S + it.gap * (len(ims) - 1)
                ln = max(i.width - 2 * t._pad for i, t in zip(ims, it.lines)) / S
                res.append((it, ims, ln, thick))
            elif isinstance(it, Hh):
                ims = []
                for t in it.lines:
                    i_ = t.render(1.0, seed)
                    mw = (W - 2 * it.margin) * S + 2 * t._pad
                    if i_.width > mw:
                        i_ = t.render(mw / i_.width * 0.98, seed)
                    ims.append(i_)
                ln = sum(i.height - 2 * t._pad for i, t in zip(ims, it.lines)) / S + it.gap * (len(ims) - 1)
                res.append((it, ims, ln, 0))
            elif isinstance(it, Gap): res.append((it, None, it.px, 0))
            elif isinstance(it, Rule): res.append((it, None, 6 if it.double else 2, 0))
            elif isinstance(it, Crop):
                c, hh = crop_img(it); res.append((it, c, hh, 0))
            elif isinstance(it, Fn): res.append((it, None, it.h, 0))
            else: res.append((it, None, 0, 0))
        return res
    k = 1.0
    for _ in range(6):
        res = measure(k)
        tot = sum(r[2] for r in res)
        vt = sum(r[2] for r in res if isinstance(r[0], V))
        over = tot - (H - top - bot)
        wide = max([r[3] / (W - spec.get('side', 14)) for r in res if isinstance(r[0], V)] + [0])
        if over <= 0 and wide <= 1: break
        f = 1.0
        if over > 0: f = min(f, (vt - over) / vt)
        if wide > 1: f = min(f, 1 / wide)
        k *= f * 0.985
    spare = max(0, H - top - bot - sum(r[2] for r in res))
    fw = sum(r[0].w for r in res if isinstance(r[0], Flex))
    y = top + (spare / 2 if fw == 0 and spec.get('center') else 0)
    d = ImageDraw.Draw(im)
    blocks = []
    pos = []
    for it, ims, ln, thick in res:
        pos.append(y)
        if isinstance(it, Flex): y += spare * it.w / fw
        else: y += ln
    # blocks first
    for (it, ims, ln, thick), y0 in zip(res, pos):
        if isinstance(it, Block):
            nxt = [p for (i2, _, _, _), p in zip(res, pos) if isinstance(i2, Block) and p > y0 + 0.5]
            y1 = nxt[0] if nxt else H
            if it.color is not None:
                d.rectangle([0, int(y0 * S), W * S, int(y1 * S)], fill=tuple(it.color) + (255,))
    for (it, ims, ln, thick), y0 in zip(res, pos):
        if isinstance(it, V):
            hs = [(i.height - 2 * t._pad) / S for i, t in zip(ims, it.lines)]
            x = W / 2 + thick / 2
            for i_, t, hh in zip(ims, it.lines, hs):
                l = (i_.width - 2 * t._pad) / S
                off = 0 if it.align == 'start' else ((ln - l) / 2 if it.align == 'center' else ln - l)
                put(im, rot(i_), x - hh / 2, y0 + off + l / 2)
                x -= hh + it.gap
        elif isinstance(it, Hh):
            yy_ = y0
            for i_, t in zip(ims, it.lines):
                hh = (i_.height - 2 * t._pad) / S
                put(im, i_, W / 2, yy_ + hh / 2)
                yy_ += hh + it.gap
        elif isinstance(it, Rule):
            col = tuple(it.color) + (255,)
            d.line([(it.inset * S, y0 * S), ((W - it.inset) * S, y0 * S)], fill=col, width=max(1, int(it.th * S)))
            if it.double:
                d.line([(it.inset * S, (y0 + 4) * S), ((W - it.inset) * S, (y0 + 4) * S)], fill=col, width=max(1, int(it.th * S * 0.5)))
        elif isinstance(it, Crop):
            im.paste(ims, (int(it.inset * S), int(y0 * S)))
            if it.border:
                d.rectangle([int(it.inset * S), int(y0 * S), int(it.inset * S) + ims.width - 1, int(y0 * S) + ims.height - 1],
                            outline=tuple(it.border) + (255,), width=int(1.5 * S))
        elif isinstance(it, Fn):
            it.fn(im, W, y0, rng)
            d = ImageDraw.Draw(im)
    for fn in spec.get('over', []):
        r = fn(im, W, rng)
        if r is not None: im = r
    fin = dict(spec.get('fin', {}))
    return finish(im, seed, out=out or (B + f"{spec['id']}-spine-b.jpg"), **fin)
