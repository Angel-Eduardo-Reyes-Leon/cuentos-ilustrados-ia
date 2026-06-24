"""
scraper_algernon.py  –  Fernanda García
Descarga SOLO cuentos de monstruos/criaturas desde cuentosparaalgernon.wordpress.com
Filtra por contenido: el cuento debe mencionar términos de monstruos/criaturas
para ser guardado (no basta con que el sitio sea de terror/fantasía en general).

Uso:
    python3 scraper_algernon.py
    python3 scraper_algernon.py --limite 300

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

URL_INDICE = "https://cuentosparaalgernon.wordpress.com/relatos-publicados/"

# Palabras clave que confirman que el cuento ES de monstruos/criaturas.
# Se exige que aparezcan varias veces para evitar falsos positivos
# (un cuento de ciencia ficción que solo menciona "monstruo" una vez de pasada).
PALABRAS_CLAVE_TEMA = [
    "monstruo", "monstruos", "criatura", "criaturas", "bestia", "bestias",
    "demonio", "demonios", "vampiro", "vampiros", "dragón", "dragones",
    "dragon", "dragones", "licántropo", "licantropo", "hombre lobo",
    "zombi", "zombie", "fantasma", "fantasmas", "espectro", "espectros",
    "engendro", "engendros", "gigante", "gigantes", "ogro", "ogros",
    "troll", "trolls", "duende maligno", "ser sobrenatural",
    "criatura marina", "kraken", "abominación", "abominacion",
    "alimaña", "sabueso infernal", "hidra", "quimera", "minotauro",
    "cíclope", "ciclope", "leviatán", "leviatan", "wendigo",
]
MIN_MENCIONES = 3  # mínimo de menciones distintas para considerarlo del tema

REGEX_TEMA = re.compile(
    "|".join(re.escape(p) for p in PALABRAS_CLAVE_TEMA), re.IGNORECASE
)


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


def obtener_enlaces_indice():
    """Recorre el índice completo (puede tener varias páginas de letras)."""
    soup = get(URL_INDICE)
    if not soup:
        return []
    links = []
    contenido = soup.select_one("div.entry-content, div#content")
    if not contenido:
        contenido = soup
    for a in contenido.select("a[href*='cuentosparaalgernon.wordpress.com/20']"):
        href = a.get("href", "")
        titulo = a.get_text(strip=True)
        if href and titulo and len(titulo) > 2:
            if href not in [l["url"] for l in links]:
                links.append({"url": href, "titulo": titulo})
    return links


def cuento_algernon(url):
    soup = get(url)
    if not soup:
        return None
    contenido = soup.select_one("div.entry-content")
    if not contenido:
        return None
    for tag in contenido(["script", "style", "figure", "figcaption", "aside",
                           "nav", "div.sharedaddy", ".wp-block-buttons"]):
        tag.decompose()
    texto = limpiar_texto(contenido.get_text(separator="\n"))

    # Quitar la parte de "Descargar en formatos ebook..." al inicio si aparece
    # (el cuento real empieza después del título y autor)
    lineas = texto.split("\n")
    inicio_real = 0
    for i, linea in enumerate(lineas):
        if "descargar" in linea.lower() and ("epub" in linea.lower() or "pdf" in linea.lower() or "mega" in linea.lower()):
            inicio_real = i + 1
    if inicio_real > 0:
        texto = "\n".join(lineas[inicio_real:]).strip()

    autor = "Anónimo"
    title = soup.title.string if soup.title else ""
    m = re.search(r",\s*de\s+(.+?)\s*[\|\-–]", title)
    if m:
        autor = m.group(1).strip()

    return {"texto": texto, "autor": autor}


def cumple_tematica(texto):
    menciones = set(m.lower() for m in REGEX_TEMA.findall(texto))
    return len(menciones) >= 1 and len(REGEX_TEMA.findall(texto)) >= MIN_MENCIONES


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
    parser.add_argument("--limite", type=int, default=10_000)
    parser.add_argument("--no-procesar", action="store_true")
    args = parser.parse_args()

    CARPETA_TXT.mkdir(parents=True, exist_ok=True)
    meta_filas = cargar_metadata()
    archivos_existentes = {f["archivo"] for f in meta_filas}

    print("📚  Obteniendo índice de relatos publicados…")
    enlaces = obtener_enlaces_indice()
    print(f"   {len(enlaces)} relatos encontrados en el índice\n")

    total_nuevos = 0
    descartados_tema = 0
    descartados_longitud = 0

    for item in enlaces:
        if total_nuevos >= args.limite:
            break
        datos = cuento_algernon(item["url"])
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
            "autor":    datos.get("autor", "Anónimo"),
            "tematica": TEMATICA,
            "fuente":   "Cuentos para Algernon",
        })
        guardar_metadata(meta_filas)

        total_nuevos += 1
        print(f"  ✅  [{total_nuevos}] {archivo} — '{item['titulo'][:50]}' ({n} palabras)")

    print(f"\n{'='*55}")
    print(f"  Cuentos nuevos (sí son de monstruos/criaturas): {total_nuevos}")
    print(f"  Descartados por NO ser del tema                : {descartados_tema}")
    print(f"  Descartados por longitud                       : {descartados_longitud}")
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
