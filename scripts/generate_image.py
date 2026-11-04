import io
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
DATA = SITE / 'posts.json'
OUTPUT = SITE / 'aktualnosci.png'
WIDTH = 1080
PAD = 34
CARD_GAP = 20
CARD_H = 350
FONT_CANDIDATES = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
]
BOLD_CANDIDATES = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf',
]

def font(size, bold=False):
    for path in (BOLD_CANDIDATES if bold else FONT_CANDIDATES):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def get_posts(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ('posts', 'data', 'items'):
            val = payload.get(key)
            if isinstance(val, list):
                return val
            if isinstance(val, dict) and isinstance(val.get('data'), list):
                return val['data']
    raise ValueError('Nieznana struktura site/posts.json')

def text_lines(draw, text, f, max_width, max_lines):
    words = str(text or '').replace('\r', '').replace('\n', ' ').split()
    lines, line = [], ''
    for word in words:
        candidate = (line + ' ' + word).strip()
        if draw.textbbox((0, 0), candidate, font=f)[2] <= max_width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
            if len(lines) >= max_lines:
                break
    if line and len(lines) < max_lines:
        lines.append(line)
    if len(lines) == max_lines and len(words) > sum(len(x.split()) for x in lines):
        last = lines[-1]
        while last and draw.textbbox((0, 0), last + '…', font=f)[2] > max_width:
            last = last[:-1]
        lines[-1] = last.rstrip() + '…'
    return lines

def fetch_photo(url):
    if not url or not str(url).startswith('https://'):
        return None
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; SchoolNews/1.0)'})
        with urlopen(req, timeout=15) as response:
            if 'image/' not in response.headers.get('Content-Type', ''):
                return None
            data = response.read(8 * 1024 * 1024 + 1)
            if len(data) > 8 * 1024 * 1024:
                return None
        return Image.open(io.BytesIO(data)).convert('RGB')
    except Exception as exc:
        print(f'Nie pobrano zdjęcia: {exc}')
        return None

def date_label(value):
    if not value:
        return 'Aktualność szkolna'
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00')).strftime('%d.%m.%Y')
    except ValueError:
        return str(value)[:10]

def main():
    if not DATA.exists():
        raise FileNotFoundError(f'Brak pliku {DATA}. Sprawdź, czy fetch.py tworzy site/posts.json.')
    posts = get_posts(json.loads(DATA.read_text(encoding='utf-8')))
    posts = [p for p in posts if isinstance(p, dict)]
    posts.sort(key=lambda p: p.get('created_time') or p.get('date') or '', reverse=True)
    posts = posts[:3]
    if not posts:
        raise ValueError('Brak postów w posts.json')
    height = 115 + len(posts) * (CARD_H + CARD_GAP) + 30
    img = Image.new('RGB', (WIDTH, height), '#f4f7fc')
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, WIDTH, 105), radius=18, fill='#163e74')
    d.text((PAD, 20), 'Najnowsze aktualności', font=font(36, True), fill='white')
    d.text((PAD, 68), 'Szkoła Podstawowa w Dygowie  •  Facebook', font=font(19), fill='#e6eefb')
    for i, post in enumerate(posts):
        top = 115 + i * (CARD_H + CARD_GAP)
        d.rounded_rectangle((PAD, top, WIDTH-PAD, top+CARD_H), radius=16, fill='white', outline='#dce4ef', width=2)
        image_url = post.get('full_picture') or post.get('picture') or post.get('image') or post.get('image_url')
        photo = fetch_photo(image_url)
        x, y, photo_w, photo_h = PAD+16, top+16, 360, CARD_H-32
        if photo:
            crop = ImageOps.fit(photo, (photo_w, photo_h), method=Image.Resampling.LANCZOS)
            img.paste(crop, (x, y))
        else:
            d.rounded_rectangle((x, y, x+photo_w, y+photo_h), radius=10, fill='#e8f0fb')
            d.text((x+42, y+130), 'AKTUALNOŚCI', font=font(25, True), fill='#163e74')
        tx = x + photo_w + 26
        d.text((tx, top+30), date_label(post.get('created_time') or post.get('date')), font=font(21, True), fill='#315b8d')
        content = post.get('message') or post.get('text') or post.get('description') or post.get('title') or 'Zobacz najnowszy wpis na Facebooku.'
        for j, line in enumerate(text_lines(d, content, font(23), WIDTH-PAD-24-tx, 8)):
            d.text((tx, top+80+j*33), line, font=font(23), fill='#202b3a')
        d.text((tx, top+CARD_H-44), 'Pełny wpis: kliknij grafikę', font=font(18), fill='#315b8d')
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUTPUT, optimize=True)
    print(f'Zapisano {OUTPUT}, liczba postów: {len(posts)}')

if __name__ == '__main__':
    main()
