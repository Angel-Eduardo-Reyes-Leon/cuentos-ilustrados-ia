"""
scraper_pixabay_espanol.py  –  Fernanda García
Más ilustraciones de Pixabay con términos en ESPAÑOL (no probados antes).

Uso:
    python3 scraper_pixabay_espanol.py
    python3 scraper_pixabay_espanol.py --limite 400

Requiere:  pip install requests Pillow
"""

import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path

import requests

USUARIO         = "fernanda_garcia"
TEMATICA        = "monstruos_y_criaturas"
CARPETA_IMG     = Path("mis_ilustraciones")
METADATA_PATH   = Path("metadata_ilustraciones.csv")
CAMPOS_META     = ["archivo", "tematica", "descripcion", "fuente"]
PIXABAY_API_KEY = "56351894-efa556fe88147d78d16248309"
ESPERA          = 0.5
MIN_DIM         = 64

TERMINOS = [
    "monstruo caricatura", "monstruo infantil", "monstruo lindo",
    "criatura caricatura", "criatura fantasia", "dragon caricatura",
    "dragon infantil", "dragon bebe", "vampiro caricatura",
    "vampiro infantil", "bruja caricatura", "bruja infantil",
    "fantasma caricatura", "fantasma infantil", "zombi caricatura",
    "hombre lobo caricatura", "ogro caricatura", "duende caricatura",
    "gigante caricatura", "demonio caricatura", "esqueleto caricatura",
    "esqueleto infantil", "monstruo halloween", "criatura halloween",
    "monstruo verde", "monstruo morado", "monstruo azul",
    "monstruo de peluche", "monstruo amigable", "monstruo divertido",
    "criatura marina caricatura", "sirena caricatura", "trol caricatura",
    "gnomo caricatura", "hada caricatura", "unicornio caricatura",
    "kraken caricatura", "yeti caricatura", "minotauro caricatura",
    "monster", "creature", "dragon", "vampire", "witch", "ghost",
    "zombie", "werewolf", "goblin", "demon", "skeleton", "ogre",
    "troll", "gnome", "fairy", "unicorn", "yeti", "minotaur",
]
TIPOS_IMAGEN = ["illustration", "vector"]


def siguiente_numero():
    import re
    existentes = []
    for pat in ["img_*.png", "img_*.jpg"]:
        for f in CARPETA_IMG.glob(pat):
            m = re.match(r"img_(\d+)\.", f.name)
            if m:
                existentes.append(int(m.group(1)))
    return max(existentes, default=0) + 1


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


def descargar_imagen(url, ruta):
    try:
        r = requests.get(url, timeout=20, stream=True)
        if r.status_code == 200:
            with open(ruta, "wb") as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            return True
    except Exception:
        pass
    return False


def imagen_valida(ruta):
    try:
        from PIL import Image
        with Image.open(ruta) as img:
            w, h = img.size
            return w >= MIN_DIM and h >= MIN_DIM
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limite", type=int, default=10_000)
    parser.add_argument("--no-procesar", action="store_true")
    args = parser.parse_args()

    CARPETA_IMG.mkdir(parents=True, exist_ok=True)
    meta_filas = cargar_metadata()
    archivos_existentes = {f["archivo"] for f in meta_filas}
    urls_vistas = set()
    total = 0

    print("📂  Pixabay (términos español + inglés, illustration + vector)")
    for termino in TERMINOS:
        if total >= args.limite:
            break
        for tipo_img in TIPOS_IMAGEN:
            if total >= args.limite:
                break
            for page in range(1, 4):
                if total >= args.limite:
                    break
                try:
                    r = requests.get(
                        "https://pixabay.com/api/",
                        params={
                            "key": PIXABAY_API_KEY, "q": termino,
                            "image_type": tipo_img, "orientation": "all",
                            "min_width": 64, "min_height": 64,
                            "safesearch": "true", "per_page": 50, "page": page,
                        },
                        timeout=15
                    )
                    if r.status_code != 200:
                        break
                    hits = r.json().get("hits", [])
                    if not hits:
                        break
                    print(f"  🔍  '{termino}' [{tipo_img}] p{page}: {len(hits)} resultados")
                    for hit in hits:
                        if total >= args.limite:
                            break
                        url = hit.get("webformatURL", "")
                        if not url or url in urls_vistas:
                            continue
                        tags = hit.get("tags", "").lower()
                        if any(x in tags for x in ["photo", "realistic", "3d", "render", "portrait", "real"]):
                            continue
                        urls_vistas.add(url)
                        ext = ".jpg" if ".jpg" in url else ".png"
                        num = siguiente_numero()
                        archivo = f"img_{num:04d}{ext}"
                        while archivo in archivos_existentes:
                            num += 1
                            archivo = f"img_{num:04d}{ext}"
                        ruta = CARPETA_IMG / archivo
                        if descargar_imagen(url, ruta) and imagen_valida(ruta):
                            archivos_existentes.add(archivo)
                            meta_filas.append({
                                "archivo": archivo, "tematica": TEMATICA,
                                "descripcion": f"{tags[:80]} caricatura plana",
                                "fuente": "Pixabay",
                            })
                            guardar_metadata(meta_filas)
                            total += 1
                            print(f"      ✅  [{total}] {archivo} — {tags[:50]}")
                        elif ruta.exists():
                            ruta.unlink()
                    time.sleep(ESPERA)
                except Exception as e:
                    print(f"  ⚠️  Error '{termino}': {e}")
                    break

    print(f"\n{'='*55}")
    print(f"  Imágenes nuevas      : {total}")
    print(f"  Total en metadata    : {len(meta_filas)}")
    print(f"{'='*55}")

    if not args.no_procesar:
        print("\n🔄  Corriendo procesar_ilustraciones.py …")
        res = subprocess.run(
            [sys.executable, "scripts/procesar_ilustraciones.py", "--usuario", USUARIO],
        )
        if res.returncode == 0:
            print("✅  CSV parcial actualizado.")
        else:
            print("⚠️  procesar_ilustraciones.py terminó con errores.")


if __name__ == "__main__":
    main()
