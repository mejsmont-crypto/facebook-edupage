import io
import json
import re
import unicodedata
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
CARD_H = 330
GAP = 20
FONT_REG = ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf']
FONT_BOLD = ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf']

def font(size, bold=False):
    for path in FONT_BOLD if bold else FONT_REG:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def posts_from(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ('posts', 'data', 'items'):
            val = data.get(key)
            if isinstance(val, list):
                return val
            if isinstance(val, dict) and isinstance(val.get('data'), list):
                return val['data']
    raise ValueError('Nie rozpoznano struktury posts.json')

def image_urls(post):
    urls = []
    images = post.get('images')
    if isinstance(images, list):
        for item in images:
            if isinstance(item, str):
                urls.append(item)
            elif isinstance(item, dict):
                for key in ('url', 'src', 'source', 'full_picture'):
                    if isinstance(item.get(key), str):
                        urls.append(item[key]); break
    elif isinstance(images, str):
        urls.append(images)
    for key in ('full_picture', 'picture', 'image', 'image_url'):
        if isinstance(post.get(key), str):
            urls.append(post[key])
    return list(dict.fromkeys(urls))

def fetch_photo(url):
    if not isinstance(url, str) or not url.startswith('https://'):
        return None
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'image/avif,image/webp,image/png,image/jpeg,image/*'})
        with urlopen(req, timeout=12) as resp:
            data = resp.read(10 * 1024 * 1024 + 1)
            if len(data) > 10 * 1024 * 1024:
                return None
        photo = Image.open(io.BytesIO(data))
        photo.load()
        return ImageOps.exif_transpose(photo).convert('RGB')
    except Exception as exc:
        print(f'Nie udało się pobrać zdjęcia: {type(exc).__name__}: {exc}')
        return None

def date_label(value):
    if not value:
        return 'Aktualności szkolne'
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00')).strftime('%d.%m.%Y')
    except ValueError:
        return str(value)[:10]

def clean_text(value):
    text = str(value or '').replace('\\n', ' ').replace('\n', ' ')
    text = ''.join(c for c in text if c == '\t' or unicodedata.category(c)[0] != 'C')
    return re.sub(r'\s+', ' ', text).strip()

def wrap_lines(draw, text, f, width, max_lines):
    words = clean_text(text).split()
    lines, current = [], ''
    for word in words:
        trial = f'{current} {word}'.strip()
        if draw.textbbox((0, 0), trial, font=f)[2] <= width:
            current = trial
        else:
            if current:
                lines.append(current)
                current = ''
            if len(lines) >= max_lines:
                break
            while word and draw.textbbox((0, 0), word, font=f)[2] > width:
                part = word
                while part and draw.textbbox((0, 0), part, font=f)[2] > width:
                    part = part[:-1]
                if not part:
                    break
                lines.append(part)
                word = word[len(part):]
                if len(lines) >= max_lines:
                    break
            current = word
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
    used = ' '.join(lines)
    if len(used) < len(clean_text(text)) and lines:
        last = lines[-1]
        while last and draw.textbbox((0, 0), last + '…', font=f)[2] > width:
            last = last[:-1]
        lines[-1] = last.rstrip() + '…'
    return lines

def main():
    data = json.loads(DATA.read_text(encoding='utf-8'))
    posts = [p for p in posts_from(data) if isinstance(p, dict)]
    posts.sort(key=lambda p: p.get('created_time') or p.get('date') or '', reverse=True)
    posts = posts[:3]
    if not posts:
        raise ValueError('Brak postów w posts.json')
    height = 115 + len(posts) * (CARD_H + GAP) + 25
    img = Image.new('RGB', (WIDTH, height), '#f4f7fc')
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((0, 0, WIDTH, 105), radius=18, fill='#163e74')
    draw.text((PAD, 20), 'Najnowsze aktualności', font=font(35, True), fill='white')
    draw.text((PAD, 70), 'Szkoła Podstawowa w Dygowie  •  Facebook', font=font(18), fill='#e6eefb')
    for i, post in enumerate(posts):
        top = 115 + i * (CARD_H + GAP)
        draw.rounded_rectangle((PAD, top, WIDTH-PAD, top+CARD_H), radius=16, fill='white', outline='#dce4ef', width=2)
        px, py, pw, ph = PAD+14, top+14, 350, CARD_H-28
        photo = None
        for url in image_urls(post):
            photo = fetch_photo(url)
            if photo:
                break
        if photo:
            img.paste(ImageOps.fit(photo, (pw, ph), method=Image.Resampling.LANCZOS), (px, py))
        else:
            draw.rounded_rectangle((px, py, px+pw, py+ph), radius=12, fill='#e6eef9')
            draw.text((px+40, py+ph//2-12), 'AKTUALNOŚCI', font=font(24, True), fill='#163e74')
        tx = px + pw + 24
        max_w = WIDTH-PAD-20-tx
        draw.text((tx, top+26), date_label(post.get('created_time') or post.get('date')), font=font(21, True), fill='#315b8d')
        message = post.get('message') or post.get('text') or post.get('description') or post.get('title') or 'Zobacz wpis na Facebooku.'
        body_font = font(21)
        lines = wrap_lines(draw, message, body_font, max_w, 7)
        for j, line in enumerate(lines):
            draw.text((tx, top+72+j*30), line, font=body_font, fill='#263447')
        draw.text((tx, top+CARD_H-37), 'Pełny wpis: kliknij grafikę', font=font(16), fill='#315b8d')
        print(f'Post {i+1}: {len(image_urls(post))} adresów zdjęć, zdjęcie: {bool(photo)}')
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUTPUT, optimize=True)
    print(f'Zapisano {OUTPUT}, liczba postów: {len(posts)}')

if __name__ == '__main__':
    main()
