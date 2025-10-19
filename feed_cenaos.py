# feed_cenaos.py
import re
import sys
from urllib.request import urlopen, Request
from urllib.parse import urljoin
from email.utils import formatdate
from datetime import datetime, timezone
import mimetypes

BASE_URL = "https://cenaos.copeco.gob.hn/"
PAGE_URL = urljoin(BASE_URL, "modelosnum.html")
FEED_TITLE = "CENAOS-COPECO | Modelos Numéricos (WRF)"
FEED_LINK = PAGE_URL
FEED_DESC = "Últimos mapas de precipitación, temperatura máxima y mínima del modelo WRF (CENAOS-COPECO)."
OUTPUT_FILE = "feed.xml"

def fetch_html(url: str) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=25) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")

def extract_img_urls(html: str) -> list[str]:
    # Extrae src de <img ...> de forma simple (sin BeautifulSoup)
    # Captura valores entre comillas simples o dobles
    pattern = r'<img[^>]+src\s*=\s*["\']([^"\']+)["\']'
    urls = re.findall(pattern, html, flags=re.IGNORECASE)
    # Normaliza a absolutas
    abs_urls = [urljoin(PAGE_URL, u) for u in urls]
    # Filtra a formatos comunes de imagen
    keep_ext = (".png", ".jpg", ".jpeg", ".webp")
    return [u for u in abs_urls if u.lower().endswith(keep_ext)]

def pick_main_images(urls: list[str]) -> dict:
    """
    Devuelve un dict con hasta 3 claves: precip, tmax, tmin
    escogiendo el primer match que aparezca en la página (más reciente visualmente).
    """
    out = {"precip": None, "tmax": None, "tmin": None}
    for u in urls:
        l = u.lower()
        if out["precip"] is None and ("precip" in l or "lluv" in l or "rain" in l):
            out["precip"] = u
        elif out["tmax"] is None and ("tmax" in l or " max" in l or l.endswith("max.png") or l.endswith("max.jpg")):
            out["tmax"] = u
        elif out["tmin"] is None and ("tmin" in l or " min" in l or "mín" in l or l.endswith("min.png") or l.endswith("min.jpg")):
            out["tmin"] = u
        # Si ya tenemos las tres, paramos
        if all(out.values()):
            break
    # Elimina claves None
    return {k: v for k, v in out.items() if v}

def guess_mime(url: str) -> str:
    mt, _ = mimetypes.guess_type(url)
    return mt or "image/jpeg"

def build_item_xml(title: str, img_url: str, pub_dt: datetime) -> str:
    pub_rfc2822 = formatdate(pub_dt.timestamp(), usegmt=True)
    mime = guess_mime(img_url)
    # En description incluimos la imagen embebida para visores que no usan media:content
    description = f"<![CDATA[<p>{title}</p><p><img src=\"{img_url}\" alt=\"{title}\"/></p>]]>"
    # Usamos media namespace y enclosure para mayor compatibilidad
    item = f"""
    <item>
      <title>{title}</title>
      <link>{FEED_LINK}</link>
      <guid isPermaLink="false">{img_url}</guid>
      <pubDate>{pub_rfc2822}</pubDate>
      <description>{description}</description>
      <enclosure url="{img_url}" type="{mime}" />
      <media:content url="{img_url}" type="{mime}" medium="image" />
    </item>""".strip()
    return item

def build_rss(items_xml: list[str]) -> str:
    now = datetime.now(timezone.utc)
    now_rfc2822 = formatdate(now.timestamp(), usegmt=True)
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <title>{FEED_TITLE}</title>
    <link>{FEED_LINK}</link>
    <description>{FEED_DESC}</description>
    <language>es</language>
    <lastBuildDate>{now_rfc2822}</lastBuildDate>
    {''.join(items_xml)}
  </channel>
</rss>"""
    return rss

def main():
    try:
        html = fetch_html(PAGE_URL)
        urls = extract_img_urls(html)
        picked = pick_main_images(urls)

        if not picked:
            print("No se detectaron imágenes relevantes (precip/tmax/tmin).", file=sys.stderr)

        # Orden sugerido de publicación
        order = [("Precipitación (WRF)", picked.get("precip")),
                 ("Temperatura Máxima (WRF)", picked.get("tmax")),
                 ("Temperatura Mínima (WRF)", picked.get("tmin"))]

        pub_dt = datetime.now(timezone.utc)
        items = []
        for title, url in order:
            if url:
                items.append(build_item_xml(title, url, pub_dt))

        rss = build_rss(items)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(rss)

        print(f"✅ RSS generado: {OUTPUT_FILE}")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
