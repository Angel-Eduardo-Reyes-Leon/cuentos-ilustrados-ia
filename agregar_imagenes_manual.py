"""
agregar_imagenes_manual.py  –  Fernanda García
Toma las imágenes que pongas en la carpeta nuevas_manual/ (cualquier nombre),
las copia a mis_ilustraciones/ con el formato img_XXXX correcto,
actualiza metadata_ilustraciones.csv y corre procesar_ilustraciones.py.

Uso:
    1. Crea la carpeta nuevas_manual/ en la raíz del proyecto (si no existe)
    2. Arrastra/descarga ahí las imágenes que quieras agregar (.png, .jpg, .jpeg)
    3. Corre:  python3 agregar_imagenes_manual.py
    4. Te pedirá una descripción corta y la fuente para CADA imagen
       (o usa --fuente y --descripcion-generica para que sea automático)

Uso rápido sin preguntas:
    python3 agregar_imagenes_manual.py --fuente Pixabay --descripcion-generica "monstruo caricatura"
"""

import argparse
import csv
import shutil
import subprocess
import sys
from pathlib import Path

USUARIO         = "fernanda_garcia"
TEMATICA        = "monstruos_y_criaturas"
CARPETA_NUEVAS  = Path("nuevas_manual")
CARPETA_IMG     = Path("mis_ilustraciones")
METADATA_PATH   = Path("metadata_ilustraciones.csv")
CAMPOS_META     = ["archivo", "tematica", "descripcion", "fuente"]
EXTENSIONES_OK  = {".png", ".jpg", ".jpeg"}


def siguiente_numero():
    import re
    existentes = []
    for pat in ["img_*.png", "img_*.jpg", "img_*.jpeg"]:
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fuente", default=None, help="Fuente para todas las imágenes (ej. Pixabay)")
    parser.add_argument("--descripcion-generica", default=None,
                         help="Si se da, se usa para todas en vez de preguntar una por una")
    parser.add_argument("--no-procesar", action="store_true")
    args = parser.parse_args()

    CARPETA_NUEVAS.mkdir(exist_ok=True)
    CARPETA_IMG.mkdir(exist_ok=True)

    imagenes = sorted(
        f for f in CARPETA_NUEVAS.iterdir()
        if f.is_file() and f.suffix.lower() in EXTENSIONES_OK
    )

    if not imagenes:
        print(f"⚠️   No hay imágenes en {CARPETA_NUEVAS}/")
        print(f"     Pon ahí tus .png/.jpg/.jpeg y vuelve a correr este script.")
        return

    print(f"📋  {len(imagenes)} imágenes encontradas en {CARPETA_NUEVAS}/\n")

    meta_filas = cargar_metadata()
    archivos_existentes = {f["archivo"] for f in meta_filas}

    agregadas = 0
    for img in imagenes:
        num = siguiente_numero()
        archivo = f"img_{num:04d}{img.suffix.lower()}"
        while archivo in archivos_existentes:
            num += 1
            archivo = f"img_{num:04d}{img.suffix.lower()}"

        shutil.copy(img, CARPETA_IMG / archivo)
        archivos_existentes.add(archivo)

        if args.descripcion_generica:
            descripcion = args.descripcion_generica
        else:
            descripcion = input(f"  Descripción para '{img.name}' (Enter = 'monstruo ilustración plana'): ").strip()
            if not descripcion:
                descripcion = "monstruo ilustración plana"

        if args.fuente:
            fuente = args.fuente
        else:
            fuente = input(f"  Fuente para '{img.name}' (Enter = 'Pixabay'): ").strip() or "Pixabay"

        meta_filas.append({
            "archivo":     archivo,
            "tematica":    TEMATICA,
            "descripcion": descripcion,
            "fuente":      fuente,
        })
        guardar_metadata(meta_filas)
        agregadas += 1
        print(f"  ✅  [{agregadas}] {img.name} → {archivo}")

    print(f"\n💾  metadata_ilustraciones.csv actualizado con {len(meta_filas)} filas totales")

    # limpiar carpeta temporal
    for img in imagenes:
        img.unlink()
    print(f"🧹  Carpeta {CARPETA_NUEVAS}/ vaciada (las imágenes ya están en {CARPETA_IMG}/)")

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
