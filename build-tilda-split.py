#!/usr/bin/env python3
"""
Сборка 3 блоков T123 для walk-walk.ru/intervals.

Tilda T123 имеет лимит ~30 000 символов на блок. Кроме того, через T123
кириллица часто рендерится как mojibake (Тильда хранит / отдаёт байты
с разной кодировкой) → ВСЯ не-ASCII кодируется как HTML-сущности
&#NNNN;. Это раздувает файл в ~1.85×, поэтому требуется 3 блока.

Структура:
- Блок 1: <head>-хинты + header + mobile-nav + hero + offer + method +
  ПОПАПЫ + sticky-cta + back-to-top  (попапы вынесены сюда, потому что
  они position:fixed — место в DOM роли не играет, а так выигрываем
  ~4.5 KB в блоке 3)
- Блок 2: bonus + rates + license
- Блок 3: cases + help + footer + <script src>

CSS и JS — внешние ссылки на GitHub Pages.
Все assets/ — абсолютные URL на CDN.
"""
import re
from pathlib import Path

BASE = Path(__file__).parent
CDN = "https://npopko55-cmd.github.io/intervals"
VER = "intv-I"

html = (BASE / "index.html").read_text(encoding="utf-8")
body = re.search(r"<body[^>]*>(.*?)</body>", html, re.DOTALL).group(1)

# --- 1. Чистим комментарии и абсолютизируем assets ---
body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
# href="assets/..." и src="assets/..."
body = re.sub(
    r'(href|src)="(assets/[^"]+)"',
    lambda m: f'{m.group(1)}="{CDN}/{m.group(2)}"',
    body,
)
# url('assets/...') и url("assets/...") (в инлайн style= и где угодно)
body = re.sub(
    r"url\((['\"])(assets/[^'\")]+)\1\)",
    lambda m: f"url({m.group(1)}{CDN}/{m.group(2)}{m.group(1)})",
    body,
)
# url(assets/...) без кавычек — на всякий
body = re.sub(
    r"url\((assets/[^'\")]+)\)",
    lambda m: f"url({CDN}/{m.group(1)})",
    body,
)

# --- 2. Находим границы секций (в RAW виде, до encoding) ---
def pos(patt):
    m = re.search(patt, body)
    if not m:
        raise SystemExit(f"Не нашёл секцию: {patt}")
    return m.start()

p_bonus    = pos(r'<section class="section bonus"')
p_cases    = pos(r'<section class="section cases"')
p_popups   = pos(r'<div class="popup"[^>]*id="popup-installment"')
# Конец body — без хвоста (popups+sticky+back уже отдельно)

# --- 3. Режем body на три части ---
# part_a = от начала до BONUS (header + nav + hero + offer + method)
# part_b = от BONUS до CASES (bonus + rates + license)
# part_c = от CASES до popup-installment (cases + help + footer)
# tail   = от popup-installment до конца (popups + sticky + back-to-top)
part_a = body[:p_bonus]
part_b = body[p_bonus:p_cases]
part_c = body[p_cases:p_popups]
tail   = body[p_popups:]

# --- 4. Кодируем всю не-ASCII (анти-mojibake) ---
def to_entities(text: str) -> str:
    return "".join(c if ord(c) < 128 else f"&#{ord(c)};" for c in text)

part_a = to_entities(part_a)
part_b = to_entities(part_b)
part_c = to_entities(part_c)
tail   = to_entities(tail)

# --- 5. Head-хинты для блока 1 ---
HEAD_HINTS = f"""<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link rel="preconnect" href="https://npopko55-cmd.github.io" crossorigin />
<link rel="preload" as="font" type="font/woff2" crossorigin href="https://fonts.gstatic.com/s/unbounded/v12/Yq6W-LOTXCb04q32xlpwv8ZfvRIkSYZH.woff2" />
<link href="https://fonts.googleapis.com/css2?family=Unbounded:wght@500;600&family=Inter:wght@400;500;600&family=Caveat:wght@600;700&display=swap&subset=latin,cyrillic" rel="stylesheet" />
<link rel="preload" as="image" href="{CDN}/assets/hero/hero-2girls.webp" fetchpriority="high" />
<link rel="stylesheet" href="{CDN}/styles.css?v={VER}" />
"""

TAIL_SCRIPT = f'\n<script src="{CDN}/script.js?v={VER}"></script>\n'

# --- 6. Сборка блоков ---
# Блок 1: head + part_a + tail (popups+sticky+back)
# Блок 2: part_b
# Блок 3: part_c + script
block1 = HEAD_HINTS + "\n" + part_a + "\n" + tail + "\n"
block2 = part_b
block3 = part_c + TAIL_SCRIPT

(BASE / "tilda-block-1.html").write_text(block1, encoding="utf-8")
(BASE / "tilda-block-2.html").write_text(block2, encoding="utf-8")
(BASE / "tilda-block-3.html").write_text(block3, encoding="utf-8")

# --- 7. Отчёт ---
def sz(s):
    n = len(s)
    ok = "✓ помещается" if n < 30000 else "✗ ПРЕВЫШЕН лимит 30000"
    return f"{n:,} chars ({n/1024:.1f} KB)  {ok}"

print("✅ Готово")
print(f"   tilda-block-1.html: {sz(block1)}")
print(f"   tilda-block-2.html: {sz(block2)}")
print(f"   tilda-block-3.html: {sz(block3)}")
print(f"   Лимит Tilda T123:   30,000 chars / блок")
print()
print("   Содержимое:")
print("   Блок 1: head-хинты + header + nav + hero + offer + method + ПОПАПЫ + sticky + back-to-top")
print("   Блок 2: bonus + rates + license")
print("   Блок 3: cases + help + footer + script")
print()
print("   Особенности:")
print("   • Вся кириллица → HTML-сущности (&#NNNN;). Это лечит mojibake в Tilda.")
print("   • Попапы вынесены в блок 1 (они position:fixed, место в DOM не критично).")
print("   • CSS и JS грузятся с GitHub Pages — в блоки не инлайнятся.")
