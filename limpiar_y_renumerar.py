"""
limpiar_y_renumerar.py  –  Fernanda García
Usa datos/cuentos/parciales/parcial_fernanda_garcia.csv (la fuente de verdad,
generada por procesar_cuentos.py) para:
  1. Identificar qué archivos .txt SÍ pasaron la validación.
  2. Borrar de mis_cuentos/ los .txt que NO están en ese CSV.
  3. Renumerar los que quedan de forma limpia (cuento_0001.txt, 0002, ...).
  4. Reescribir metadata_fernanda.csv solo con esos archivos.
  5. Volver a correr procesar_cuentos.py para regenerar el CSV final.

Uso:
    python3 limpiar_y_renumerar.py
"""

import csv
import re
import subprocess
import sys
from pathlib import Path

USUARIO          = "fernanda_garcia"
METADATA_PATH    = Path("metadata_fernanda.csv")
CARPETA_TXT      = Path("mis_cuentos")
CSV_PARCIAL      = Path("datos/cuentos/parciales/parcial_fernanda_garcia.csv")


def main():
    # ── Paso 1: leer el CSV parcial (fuente de verdad) ──────────────────────────
    with open(CSV_PARCIAL, encoding="utf-8") as f:
        filas_parcial = list(csv.DictReader(f))

    print(f"📋  {len(filas_parcial)} cuentos válidos según el CSV parcial")

    # El CSV parcial no guarda el nombre del .txt original, pero sí el hash y
    # el título — usamos el título + autor para emparejar con metadata_fernanda.csv
    with open(METADATA_PATH, encoding="utf-8") as f:
        filas_meta = list(csv.DictReader(f))

    meta_por_titulo_autor = {}
    for row in filas_meta:
        clave = (row["titulo"].strip().lower(), row["autor"].strip().lower())
        # si hay choque de clave, preferimos el primero (no debería pasar tras dedup)
        meta_por_titulo_autor.setdefault(clave, row)

    # Emparejar cada fila del parcial con su archivo .txt real
    archivos_validos = []
    no_encontrados = 0
    for row in filas_parcial:
        clave = (row["titulo"].strip().lower(), row["autor"].strip().lower())
        meta_row = meta_por_titulo_autor.get(clave)
        if meta_row:
            archivos_validos.append(meta_row["archivo"])
        else:
            no_encontrados += 1

    archivos_validos_set = set(archivos_validos)
    print(f"🔗  Emparejados con su .txt: {len(archivos_validos_set)}")
    if no_encontrados:
        print(f"⚠️   No se pudieron emparejar: {no_encontrados} (se ignoran)")

    # ── Paso 2: borrar lo que sobra en la carpeta ───────────────────────────────
    borrados = 0
    for ruta in CARPETA_TXT.glob("cuento_*.txt"):
        if ruta.name not in archivos_validos_set:
            ruta.unlink()
            borrados += 1
    print(f"🗑️   Archivos .txt borrados (no estaban en el CSV válido): {borrados}")

    # ── Paso 3: renumerar limpio ─────────────────────────────────────────────────
    archivos_restantes = sorted(CARPETA_TXT.glob("cuento_*.txt"))
    print(f"📦  Archivos restantes antes de renumerar: {len(archivos_restantes)}")

    # primero renombrar a nombres temporales para evitar colisiones
    temporales = []
    for i, ruta in enumerate(archivos_restantes):
        temp = CARPETA_TXT / f"_tmp_{i:05d}.txt"
        ruta.rename(temp)
        temporales.append((temp, ruta.name))  # guardamos el nombre original

    finales = []
    for i, (temp, nombre_original) in enumerate(temporales, start=1):
        nuevo_nombre = f"cuento_{i:04d}.txt"
        nueva_ruta = CARPETA_TXT / nuevo_nombre
        temp.rename(nueva_ruta)
        finales.append((nombre_original, nuevo_nombre))

    print(f"🔢  Renumerados {len(finales)} archivos de forma limpia")

    # ── Paso 4: reescribir metadata ──────────────────────────────────────────────
    mapa_nombres = dict(finales)  # nombre_original -> nuevo_nombre
    nuevas_filas_meta = []
    for row in filas_meta:
        if row["archivo"] in mapa_nombres:
            nueva_fila = row.copy()
            nueva_fila["archivo"] = mapa_nombres[row["archivo"]]
            nuevas_filas_meta.append(nueva_fila)

    with open(METADATA_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["archivo", "titulo", "autor", "tematica", "fuente"])
        w.writeheader()
        w.writerows(nuevas_filas_meta)

    print(f"💾  metadata_fernanda.csv reescrito con {len(nuevas_filas_meta)} filas")

    # ── Paso 5: volver a procesar ─────────────────────────────────────────────────
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
