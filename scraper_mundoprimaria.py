"""
scraper_mundoprimaria.py  –  Fernanda García
Descarga cuentos y leyendas de monstruos/criaturas de mundoprimaria.com
Solo guarda los pocos que faltan para llegar a 1000 (limite bajo por defecto).

Uso:
    python3 scraper_mundoprimaria.py
    python3 scraper_mundoprimaria.py --limite 60

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

URLS_LISTADO = [
    "https://www.mundoprimaria.com/cuentos-infantiles-cortos/cuentos-terror",
    "https://www.mundoprimaria.com/mitos-y-leyendas-para-ninos",
]

# Filtro temático: el texto debe mencionar criaturas/monstruos varias veces
PALABRAS_CLAVE_TEMA = [
    "monstruo", "monstruos", "criatura", "criaturas", "bestia", "bestias",
    "demonio", "demonios", "vampiro", "vampiros", "dragón", "dragon",
    "dragones", "licántropo", "licantropo", "hombre lobo", "zombi", "zombie",
    "fantasma", "fantasmas", "espectro", "espectros", "engendro", "gigante",
    "gigantes", "ogro", "ogros", "troll", "trolls", "duende", "sapo gigante",
    "serpiente gigante", "bruja", "brujas", "hechicera", "diablo", "duendes",
]
MIN_MENCIONES = 2
REGEX_TEMA = re.compile("|".join(re.escape(p) for p in PALABRAS_CLAVE_TEMA), re.IGNORECASE)


def get(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
    return None


def limpiar_texto(texto):
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def enlaces_mundoprimaria(soup):
    links = []
    for a in soup.select("a[href*='mundoprimaria.com']"):
        href = a.get("href", "")
        titulo = a.get_text(strip=True)
        if (href and titulo and len(titulo) > 3 and
                ("/cuentos-infantiles-cortos/" in href or "/mitos-y-leyendas-para-ninos/" in href) and
                href.rstrip("/") not in [u.rstrip("/") for u in URLS_LISTADO]):
            if href not in [l["url"] for l in links]:
                links.append({"url": href, "titulo": titulo})
    return links


def cuento_mundoprimaria(url):
    soup = get(url)
    if not soup:
        return None
    contenido = soup.select_one("div.entry-content, article .content, div.post-content")
    if not contenido:
        return None
    for tag in contenido(["script", "style", "figure", "aside", "nav", "form", "iframe"]):
        tag.decompose()
    texto = limpiar_texto(contenido.get_text(separator="\n"))
    return {"texto": texto, "autor": "Anónimo"}


def cumple_tematica(texto):
    return len(REGEX_TEMA.findall(texto)) >= MIN_MENCIONES


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limite", type=int, default=60)
    parser.add_argument("--no-procesar", action="store_true")
    args = parser.parse_args()

    CARPETA_TXT.mkdir(parents=True, exist_ok=True)
    meta_filas = cargar_metadata()
    archivos_existentes = {f["archivo"] for f in meta_filas}
    urls_vistas = set()

    total_nuevos = 0
    descartados_tema = 0
    descartados_longitud = 0

    for url_listado in URLS_LISTADO:
        if total_nuevos >= args.limite:
            break
        print(f"\n📂  {url_listado}")
        soup = get(url_listado)
        if not soup:
            continue
        time.sleep(ESPERA)

        enlaces = enlaces_mundoprimaria(soup)
        print(f"   {len(enlaces)} enlaces encontrados")

        for item in enlaces:
            if total_nuevos >= args.limite:
                break
            if item["url"] in urls_vistas:
                continue
            urls_vistas.add(item["url"])

            datos = cuento_mundoprimaria(item["url"])
            time.sleep(ESPERA)

            if not datos or not datos.get("texto"):
                continue

            texto = datos["texto"]

            if not cumple_tematica(texto):
                descartados_tema += 1
                continue

            n = len(texto.split())
            if n < MIN_PALABRAS or n > MAX_PALABRAS:
                descartados_longitud += 1
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
                "autor":    "Anónimo",
                "tematica": TEMATICA,
                "fuente":   "Mundo Primaria",
            })
            guardar_metadata(meta_filas)

            total_nuevos += 1
            print(f"  ✅  [{total_nuevos}] {archivo} — '{item['titulo'][:50]}' ({n} palabras)")

    print(f"\n{'='*55}")
    print(f"  Cuentos nuevos                : {total_nuevos}")
    print(f"  Descartados por NO ser tema   : {descartados_tema}")
    print(f"  Descartados por longitud      : {descartados_longitud}")
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


if __name__ == "__main__":
    main()
