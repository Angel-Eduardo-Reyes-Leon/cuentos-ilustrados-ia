"""
scraper_wikisource.py  –  Fernanda García
Descarga cuentos de monstruos/criaturas desde es.wikisource.org usando su
API oficial de MediaWiki (estable, permite scraping, dominio público).
Filtra por contenido real (igual que Algernon/mitología).

Uso:
    python3 scraper_wikisource.py
    python3 scraper_wikisource.py --limite 200

Requiere:  pip install requests
"""

import argparse
import csv
import re
import subprocess
import sys
import time
from pathlib import Path

import requests

USUARIO        = "fernanda_garcia"
METADATA_PATH  = Path("metadata_fernanda.csv")
CARPETA_TXT    = Path("mis_cuentos")
TEMATICA       = "monstruos_y_criaturas"
CAMPOS_META    = ["archivo", "titulo", "autor", "tematica", "fuente"]
MIN_PALABRAS   = 100
MAX_PALABRAS   = 20_000
ESPERA         = 1.0
HEADERS        = {"User-Agent": "Mozilla/5.0 (educational scraper, proyecto universitario; fernanda@example.com)"}

API_URL = "https://es.wikisource.org/w/api.php"

# Categorías de Wikisource que sabemos tienen autores de terror/fantasía
CATEGORIAS = [
    "Cuentos_de_Edgar_Allan_Poe",
    "Cuentos_de_Horacio_Quiroga",
    "Cuentos_de_Leopoldo_Lugones",
    "Cuentos_de_los_hermanos_Grimm",
    "Cuentos",  # categoría general, se filtra por contenido
]

PALABRAS_CLAVE_TEMA = [
    "monstruo", "monstruos", "criatura", "criaturas", "bestia", "bestias",
    "demonio", "demonios", "vampiro", "vampiros", "dragón", "dragon", "dragones",
    "licántropo", "licantropo", "hombre lobo", "zombi", "zombie",
    "fantasma", "fantasmas", "espectro", "espectros", "engendro", "gigante",
    "gigantes", "ogro", "ogros", "troll", "trolls", "kraken", "hidra",
    "quimera", "minotauro", "cíclope", "ciclope", "leviatán", "leviatan",
    "sirena", "sirenas", "esfinge", "cancerbero", "medusa", "centauro",
    "duende", "duendes", "bruja", "brujas", "hechicera", "diablo",
]
MIN_MENCIONES = 3
REGEX_TEMA = re.compile("|".join(re.escape(p) for p in PALABRAS_CLAVE_TEMA), re.IGNORECASE)


def obtener_paginas_categoria(categoria, limite=300):
    """Usa la API de MediaWiki para listar páginas de una categoría."""
    paginas = []
    cont = None
    while len(paginas) < limite:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Categoría:{categoria}",
            "cmlimit": "100",
            "format": "json",
        }
        if cont:
            params["cmcontinue"] = cont
        try:
            r = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
            data = r.json()
        except Exception as e:
            print(f"  ⚠️  Error API: {e}")
            break

        miembros = data.get("query", {}).get("categorymembers", [])
        for m in miembros:
            if m.get("ns") == 0:  # solo páginas de contenido, no subcategorías
                paginas.append(m["title"])

        cont = data.get("continue", {}).get("cmcontinue")
        if not cont:
            break
        time.sleep(0.3)

    return paginas[:limite]


def obtener_texto_pagina(titulo):
    """Obtiene el texto plano (wikitext renderizado) de una página."""
    params = {
        "action": "query",
        "prop": "extracts",
        "explaintext": "1",
        "titles": titulo,
        "format": "json",
    }
    try:
        r = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
        data = r.json()
        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            extract = page_data.get("extract", "")
            if extract:
                return extract
    except Exception as e:
        print(f"  ⚠️  Error obteniendo '{titulo}': {e}")
    return None


def limpiar_texto(texto):
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


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
    parser.add_argument("--limite", type=int, default=10_000)
    parser.add_argument("--no-procesar", action="store_true")
    args = parser.parse_args()

    CARPETA_TXT.mkdir(parents=True, exist_ok=True)
    meta_filas = cargar_metadata()
    archivos_existentes = {f["archivo"] for f in meta_filas}
    titulos_vistos = set()

    total_nuevos = 0
    descartados_tema = 0
    descartados_longitud = 0

    for categoria in CATEGORIAS:
        if total_nuevos >= args.limite:
            break
        print(f"\n📂  Categoría: {categoria}")
        paginas = obtener_paginas_categoria(categoria, limite=300)
        print(f"   {len(paginas)} páginas encontradas")

        for titulo in paginas:
            if total_nuevos >= args.limite:
                break
            if titulo in titulos_vistos:
                continue
            titulos_vistos.add(titulo)

            texto = obtener_texto_pagina(titulo)
            time.sleep(ESPERA)

            if not texto:
                continue

            texto = limpiar_texto(texto)

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

            # limpiar título (quitar guiones bajos)
            titulo_limpio = titulo.replace("_", " ")

            meta_filas.append({
                "archivo":  archivo,
                "titulo":   titulo_limpio,
                "autor":    "Varios autores",
                "tematica": TEMATICA,
                "fuente":   "Wikisource ES",
            })
            guardar_metadata(meta_filas)

            total_nuevos += 1
            print(f"  ✅  [{total_nuevos}] {archivo} — '{titulo_limpio[:50]}' ({n} palabras)")

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
