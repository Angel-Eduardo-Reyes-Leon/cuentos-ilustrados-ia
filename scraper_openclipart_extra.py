"""
scraper_openclipart_extra.py  –  Fernanda García
Descarga MÁS ilustraciones de Openclipart con términos nuevos,
sin repetir los ya usados en corridas anteriores.

Uso:
    python3 scraper_openclipart_extra.py
    python3 scraper_openclipart_extra.py --limite 400

Requiere:  pip install requests Pillow
"""

import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path

import requests

USUARIO       = "fernanda_garcia"
TEMATICA      = "monstruos_y_criaturas"
CARPETA_IMG   = Path("mis_ilustraciones")
METADATA_PATH = Path("metadata_ilustraciones.csv")
CAMPOS_META   = ["archivo", "tematica", "descripcion", "fuente"]
ESPERA        = 0.4
MIN_DIM       = 64

# Términos NUEVOS no usados en corridas anteriores
TERMINOS = [
    "spooky", "haunted", "phantom", "spirit creature", "beast cartoon",
    "fang", "claw monster", "horn creature", "scales creature",
    "wing dragon", "fire breathing", "magic creature", "evil eye monster",
    "boogeyman", "boogey", "nightmare creature", "shadow creature",
    "cursed creature", "enchanted creature", "fairy tale monster",
    "wicked witch", "old witch", "scary witch", "cauldron witch",
    "vampire bat", "vampire fangs", "count dracula cartoon",
    "frankenstein cartoon", "mummy wrap", "egyptian mummy cartoon",
    "swamp thing", "bog monster", "forest spirit", "tree monster",
    "rock monster", "stone creature", "ice monster", "snow creature",
    "fire demon", "lava creature", "underwater monster", "deep sea creature",
    "dragon egg", "baby monster", "monster family", "monster friends",
    "halloween character", "halloween creature", "october monster",
    "small monster", "big monster", "tiny monster", "giant creature",
    "blue monster", "red monster", "orange monster", "yellow monster",
    "many eyes monster", "one eye monster", "tooth monster",
]


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

    print("📂  Openclipart (términos extra)")
    for termino in TERMINOS:
        if total >= args.limite:
            break
        for page in range(1, 6):
            if total >= args.limite:
                break
            try:
                r = requests.get(
                    "https://openclipart.org/search/json/",
                    params={"query": termino, "page": page, "amount": 25},
                    timeout=15
                )
                if r.status_code != 200:
                    break
                clips = r.json().get("payload", [])
                if not clips:
                    break

                print(f"  🔍  '{termino}' p{page}: {len(clips)} resultados")

                for clip in clips:
                    if total >= args.limite:
                        break
                    url = (clip.get("svg", {}).get("png_2400px") or
                           clip.get("svg", {}).get("png_240px") or "")
                    if not url or url in urls_vistas:
                        continue
                    urls_vistas.add(url)

                    titulo = clip.get("title", termino)
                    num = siguiente_numero()
                    archivo = f"img_{num:04d}.png"
                    while archivo in archivos_existentes:
                        num += 1
                        archivo = f"img_{num:04d}.png"

                    ruta = CARPETA_IMG / archivo
                    if descargar_imagen(url, ruta) and imagen_valida(ruta):
                        archivos_existentes.add(archivo)
                        meta_filas.append({
                            "archivo": archivo, "tematica": TEMATICA,
                            "descripcion": f"{titulo} clipart ilustración plana",
                            "fuente": "Openclipart",
                        })
                        guardar_metadata(meta_filas)
                        total += 1
                        print(f"      ✅  [{total}] {archivo} — {titulo[:50]}")
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
