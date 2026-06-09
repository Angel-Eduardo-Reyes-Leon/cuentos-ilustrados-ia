import argparse
import csv
import hashlib
import os
from pathlib import Path

from PIL import Image

EDADES_VALIDAS = {"0-5", "6-8", "9-11", "12-14", "15-17", "18+"}
LADO_MINIMO = 64  # descartamos imagenes demasiado chicas para entrenar


def hash_archivo(ruta):
    h = hashlib.sha1()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(8192), b""):
            h.update(bloque)
    return h.hexdigest()


def cargar_metadata(ruta):
    with open(ruta, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    parser = argparse.ArgumentParser(description="Indexa nuestras ilustraciones crudas y genera el CSV parcial de una persona.")
    parser.add_argument("--usuario", required=True, help="Tu usuario, ej. angel_reyes")
    parser.add_argument("--carpeta", default="mis_ilustraciones", help="Carpeta con las imagenes")
    parser.add_argument("--metadata", default="metadata_ilustraciones.csv", help="CSV con archivo,edad,descripcion,fuente")
    parser.add_argument("--salida", default=None)
    args = parser.parse_args()

    salida = args.salida or f"datos/ilustraciones/parciales/parcial_{args.usuario}.csv"
    os.makedirs(os.path.dirname(salida), exist_ok=True)

    filas = []
    vistos = set()
    descartados = []

    for i, meta in enumerate(cargar_metadata(args.metadata), start=1):
        archivo = meta["archivo"].strip()
        ruta = Path(args.carpeta) / archivo
        if not ruta.exists():
            descartados.append((archivo, "archivo no encontrado"))
            continue

        edad = meta["edad"].strip()
        if edad not in EDADES_VALIDAS:
            descartados.append((archivo, f"edad invalida: {edad}"))
            continue

        try:
            with Image.open(ruta) as img:
                ancho, alto = img.size
                img.verify()
        except Exception:
            descartados.append((archivo, "imagen corrupta o no valida"))
            continue

        if ancho < LADO_MINIMO or alto < LADO_MINIMO:
            descartados.append((archivo, f"muy chica: {ancho}x{alto}"))
            continue

        h = hash_archivo(ruta)
        if h in vistos:
            descartados.append((archivo, "duplicado dentro de tu carpeta"))
            continue
        vistos.add(h)

        filas.append({
            "id": f"{args.usuario}_img_{i:04d}",
            "archivo": archivo,
            "edad": edad,
            "ancho": ancho,
            "alto": alto,
            "descripcion": meta.get("descripcion", "").strip(),
            "fuente": meta.get("fuente", "").strip(),
            "recolector": args.usuario,
            "hash_imagen": h,
        })

    campos = ["id", "archivo", "edad", "ancho", "alto",
              "descripcion", "fuente", "recolector", "hash_imagen"]
    with open(salida, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(filas)

    print(f"Indexadas {len(filas)} ilustraciones en {salida}")
    if descartados:
        print(f"Descartadas {len(descartados)}:")
        for archivo, motivo in descartados:
            print(f"  - {archivo}: {motivo}")


if __name__ == "__main__":
    main()
