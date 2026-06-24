"""
scraper_monstruos.py  –  Fernanda García
Descarga cuentos de monstruos y criaturas de múltiples sitios.

Uso:
    python3 scraper_monstruos.py
    python3 scraper_monstruos.py --limite 500
    python3 scraper_monstruos.py --no-procesar

Requiere:  pip install requests beautifulsoup4
"""

import argparse
import csv
import re
import subprocess
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USUARIO        = "fernanda_garcia"
METADATA_PATH  = Path("metadata_fernanda.csv")
CARPETA_TXT    = Path("mis_cuentos")
TEMATICA       = "monstruos_y_criaturas"
CAMPOS_META    = ["archivo", "titulo", "autor", "tematica", "fuente"]
MIN_PALABRAS   = 100
MAX_PALABRAS   = 20_000
ESPERA         = 1.5
HEADERS        = {"User-Agent": "Mozilla/5.0 (educational scraper, proyecto universitario)"}

# relatoscortos.org — terror latinoamericano, criaturas, leyendas
URLS_RELATOSCORTOS = []
categorias_relatos = [
    "cuentos-de-terror", "cuentos-de-miedo", "cuentos-de-fantasmas",
    "cuentos-de-monstruos", "cuentos-de-vampiros", "cuentos-de-brujas",
    "leyendas-de-terror", "creepypastas", "historias-de-terror",
    "cuentos-de-zombies", "cuentos-de-demonios", "cuentos-de-hombres-lobo",
    "cuentos-de-criaturas", "cuentos-de-ogros", "cuentos-de-dragones",
]
for cat in categorias_relatos:
    for p in range(1, 8):
        if p == 1:
            URLS_RELATOSCORTOS.append(f"https://relatoscortos.org/{cat}/")
        else:
            URLS_RELATOSCORTOS.append(f"https://relatoscortos.org/{cat}/page/{p}/")

# narrativabreve — términos adicionales no usados antes
URLS_NARRATIVABREVE_EXTRA = []
terminos_extra = [
    "criatura", "engendro", "abominacion", "espanto", "tinieblas",
    "maldicion", "pesadilla", "espíritu", "maligno", "tenebroso",
    "aparecido", "endemoniado", "bestia", "ogro", "lobo",
    "zombie", "esqueleto", "demonio", "hechizo", "bruja",
    "centauro", "minotauro", "ciclope", "sirena", "kraken",
    "hidra", "quimera", "gorgona", "medusa", "leviatan",
    "esfinge", "cancerbero", "titan", "gigante", "duende",
    "trol", "goblin", "vampiresa", "drácula", "frankenstein",
    "hombre lobo", "criatura nocturna", "ser maligno", "espectro",
    "fantasma", "alma en pena", "anima sola", "duende maligno",
    "trasgo", "diablillo", "íncubo", "súcubo", "necromante",
    "esqueleto andante", "muerto viviente", "no muerto", "criatura abisal",
]
for t in terminos_extra:
    for p in range(1, 4):
        if p == 1:
            URLS_NARRATIVABREVE_EXTRA.append(f"https://narrativabreve.com/?s={t}")
        else:
            URLS_NARRATIVABREVE_EXTRA.append(f"https://narrativabreve.com/?s={t}&paged={p}")

# encuentos — páginas adicionales
URLS_ENCUENTOS = [
    "https://www.encuentos.com/cuentos-de-monstruos/page/4/",
    "https://www.encuentos.com/cuentos-de-monstruos/page/5/",
    "https://www.encuentos.com/cuentos-fantasticos/page/3/",
    "https://www.encuentos.com/cuentos-fantasticos/page/4/",
    "https://www.encuentos.com/cuentos-de-misterio/page/3/",
    "https://www.encuentos.com/cuentos-de-misterio/page/4/",
    "https://www.encuentos.com/leyendas/",
    "https://www.encuentos.com/leyendas/page/2/",
]


def get(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return BeautifulSoup(r.text, "html.parser")
        print(f"  ⚠️  HTTP {r.status_code}: {url}")
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
    return None


def limpiar_texto(texto):
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def enlaces_relatoscortos(soup):
    links = []
    for a in soup.select("h2.entry-title a, h3.entry-title a, .post-title a, article h2 a"):
        href = a.get("href", "")
        titulo = a.get_text(strip=True)
        if href and titulo and "relatoscortos.org" in href:
            if href not in [l["url"] for l in links]:
                links.append({"url": href, "titulo": titulo})
    return links


def cuento_relatoscortos(url):
    soup = get(url)
    if not soup:
        return None
    contenido = soup.select_one("div.entry-content, div.post-content, article .entry-content")
    if not contenido:
        return None
    for tag in contenido(["script", "style", "figure", "figcaption", "aside",
                           "nav", "div.sharedaddy", ".wp-block-buttons", "form"]):
        tag.decompose()
    texto = limpiar_texto(contenido.get_text(separator="\n"))
    autor = "Anónimo"
    a = soup.select_one("span.author a, a[rel='author'], .entry-author a")
    if a:
        autor = a.get_text(strip=True)
    return {"texto": texto, "autor": autor}


def enlaces_narrativabreve(soup):
    links = []
    for a in soup.select("h2.entry-title a, h1.entry-title a, .post-title a"):
        href = a.get("href", "")
        titulo = a.get_text(strip=True)
        if href and titulo and "narrativabreve.com" in href:
            if href not in [l["url"] for l in links]:
                links.append({"url": href, "titulo": titulo})
    return links


def cuento_narrativabreve(url):
    soup = get(url)
    if not soup:
        return None
    contenido = soup.select_one("div.entry-content, div.post-content, article .entry-content")
    if not contenido:
        return None
    for tag in contenido(["script", "style", "figure", "figcaption", "aside",
                           "nav", "div.sharedaddy", ".wp-block-buttons"]):
        tag.decompose()
    texto = limpiar_texto(contenido.get_text(separator="\n"))
    autor = "Anónimo"
    title = soup.title.string if soup.title else ""
    m = re.search(r",\s*de\s+(.+?)[\|\-–]", title)
    if m:
        autor = m.group(1).strip()
    else:
        a = soup.select_one("span.author a, a[rel='author'], .entry-author a")
        if a:
            autor = a.get_text(strip=True)
    return {"texto": texto, "autor": autor}


def enlaces_encuentos(soup):
    links = []
    for a in soup.select("h2.entry-title a, h3.entry-title a"):
        href = a.get("href", "")
        titulo = a.get_text(strip=True)
        if href and titulo:
            links.append({"url": href, "titulo": titulo})
    return links


def cuento_encuentos(url):
    soup = get(url)
    if not soup:
        return None
    contenido = soup.select_one("div.entry-content")
    if not contenido:
        return None
    for tag in contenido(["script", "style", "figure", "figcaption", "aside"]):
        tag.decompose()
    texto = limpiar_texto(contenido.get_text(separator="\n"))
    autor = "Anónimo"
    a = soup.select_one("span.author a, a[rel='author']")
    if a:
        autor = a.get_text(strip=True)
    return {"texto": texto, "autor": autor}


def cargar_metadata():
    if not METADATA_PATH.exists():
        return []
    with open(METADATA_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def guardar_metadata(filas):
    with open(METADATA_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS_META)
        w.writeheader()
        w.writerows(filas)


def siguiente_numero(carpeta):
    existentes = [
        int(m.group(1))
        for f in carpeta.glob("cuento_*.txt")
        if (m := re.match(r"cuento_(\d+)\.txt", f.name))
    ]
    return max(existentes, default=0) + 1


def procesar_fuente(nombre, urls, fn_enlaces, fn_cuento, meta_filas,
                    archivos_existentes, urls_vistas, total_nuevos, limite):
    total_descartados = 0
    print(f"\n📂  {nombre}")

    for url_listado in urls:
        if total_nuevos >= limite:
            break
        print(f"  🔍  {url_listado}")
        soup = get(url_listado)
        if not soup:
            continue
        time.sleep(ESPERA)

        enlaces = fn_enlaces(soup)
        print(f"      {len(enlaces)} enlaces encontrados")

        for item in enlaces:
            if total_nuevos >= limite:
                break
            url_cuento = item["url"]
            if url_cuento in urls_vistas:
                continue
            urls_vistas.add(url_cuento)

            datos = fn_cuento(url_cuento)
            time.sleep(ESPERA)

            if not datos or not datos.get("texto"):
                total_descartados += 1
                continue

            texto = datos["texto"]
            n = len(texto.split())
            if n < MIN_PALABRAS or n > MAX_PALABRAS:
                print(f"      ⏭️  '{item['titulo'][:40]}' — {n} palabras")
                total_descartados += 1
                continue

            num = siguiente_numero(CARPETA_TXT)
            archivo = f"cuento_{num:04d}.txt"
            while archivo in archivos_existentes:
                num += 1
                archivo = f"cuento_{num:04d}.txt"

            (CARPETA_TXT / archivo).write_text(texto, encoding="utf-8")
            archivos_existentes.add(archivo)

            meta_filas.append({
                "archivo":  archivo,
                "titulo":   item["titulo"],
                "autor":    datos.get("autor", "Anónimo"),
                "tematica": TEMATICA,
                "fuente":   nombre,
            })
            guardar_metadata(meta_filas)

            total_nuevos += 1
            print(f"      ✅  [{total_nuevos}] {archivo} — '{item['titulo'][:45]}' ({n} palabras)")

    return total_nuevos, total_descartados


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limite", type=int, default=10_000)
    parser.add_argument("--no-procesar", action="store_true")
    args = parser.parse_args()

    CARPETA_TXT.mkdir(parents=True, exist_ok=True)
    meta_filas = cargar_metadata()
    archivos_existentes = {f["archivo"] for f in meta_filas}
    urls_vistas = set()
    total_nuevos = 0
    total_descartados = 0

    fuentes = [
        ("relatoscortos.org",     URLS_RELATOSCORTOS,       enlaces_relatoscortos, cuento_relatoscortos),
        ("narrativabreve.com",    URLS_NARRATIVABREVE_EXTRA, enlaces_narrativabreve, cuento_narrativabreve),
        ("encuentos.com",         URLS_ENCUENTOS,            enlaces_encuentos,     cuento_encuentos),
    ]

    for nombre, urls, fn_e, fn_c in fuentes:
        if total_nuevos >= args.limite:
            break
        total_nuevos, desc = procesar_fuente(
            nombre, urls, fn_e, fn_c,
            meta_filas, archivos_existentes, urls_vistas,
            total_nuevos, args.limite
        )
        total_descartados += desc

    print(f"\n{'='*55}")
    print(f"  Cuentos nuevos descargados : {total_nuevos}")
    print(f"  Descartados (fuera de rango): {total_descartados}")
    print(f"  Total en metadata          : {len(meta_filas)}")
    print(f"{'='*55}")

    if not args.no_procesar:
        print("\n🔄  Corriendo procesar_cuentos.py …")
        res = subprocess.run(
            [sys.executable, "scripts/procesar_cuentos.py",
             "--usuario", USUARIO,
             "--carpeta", str(CARPETA_TXT),
             "--metadata", str(METADATA_PATH)],
        )
        if res.returncode == 0:
            print("✅  CSV parcial actualizado.")
        else:
            print("⚠️  procesar_cuentos.py terminó con errores.")
    else:
        print("\nℹ️  Recuerda correr procesar_cuentos.py manualmente.")


if __name__ == "__main__":
    main()
