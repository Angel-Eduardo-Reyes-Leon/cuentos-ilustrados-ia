"""
integrar_zip_extra.py  –  Fernanda García
Integra los 18 cuentos adicionales del zip (umbral relajado a 2 menciones).

Uso:
    python3 integrar_zip_extra.py
"""

import csv
import re
import subprocess
import sys
from pathlib import Path

USUARIO        = "fernanda_garcia"
METADATA_PATH  = Path("metadata_fernanda.csv")
CARPETA_TXT    = Path("mis_cuentos")
TEMATICA       = "monstruos_y_criaturas"
CAMPOS_META    = ["archivo", "titulo", "autor", "tematica", "fuente"]
CSV_VALIDOS    = Path("cuentos_validos_zip_extra.csv")


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
    CARPETA_TXT.mkdir(parents=True, exist_ok=True)
    meta_filas = cargar_metadata()
    archivos_existentes = {f["archivo"] for f in meta_filas}

    with open(CSV_VALIDOS, encoding="utf-8") as f:
        cuentos = list(csv.DictReader(f))

    print(f"📋  {len(cuentos)} cuentos adicionales del zip a integrar\n")

    agregados = 0
    for c in cuentos:
        num = siguiente_numero(CARPETA_TXT)
        archivo = f"cuento_{num:04d}.txt"
        while archivo in archivos_existentes:
            num += 1
            archivo = f"cuento_{num:04d}.txt"

        (CARPETA_TXT / archivo).write_text(c["texto"], encoding="utf-8")
        archivos_existentes.add(archivo)

        meta_filas.append({
            "archivo":  archivo,
            "titulo":   c["titulo"],
            "autor":    c["autor"],
            "tematica": TEMATICA,
            "fuente":   c["fuente"],
        })
        agregados += 1
        print(f"  ✅  [{agregados}] {archivo} — '{c['titulo'][:50]}' ({c['n_palabras']} palabras)")

    guardar_metadata(meta_filas)
    print(f"\n💾  metadata_fernanda.csv actualizado con {len(meta_filas)} filas totales")

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
