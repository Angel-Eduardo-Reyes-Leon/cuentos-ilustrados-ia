"""
sincronizar_v3.py  –  Fernanda García
Método robusto: deja que procesar_cuentos.py (el oficial del proyecto)
decida qué .txt son válidos. Lee su salida real, identifica EXACTAMENTE
cuáles archivos quedaron en datos/cuentos/parciales/parcial_fernanda_garcia.csv
comparando el campo "id" (que es fernanda_garcia_0001, 0002, ... en el MISMO
orden en que procesar_cuentos.py recorrió metadata_fernanda.csv), y borra/renumera
solo después de confirmar.

Uso:
    python3 sincronizar_v3.py --solo-verificar
    python3 sincronizar_v3.py --aplicar
"""

import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path

USUARIO       = "fernanda_garcia"
METADATA_PATH = Path("metadata_fernanda.csv")
CARPETA_TXT   = Path("mis_cuentos")
CSV_PARCIAL   = Path("datos/cuentos/parciales/parcial_fernanda_garcia.csv")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solo-verificar", action="store_true")
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()

    if not args.solo_verificar and not args.aplicar:
        print("Usa --solo-verificar primero, o --aplicar para hacer los cambios.")
        return

    # 1) leer metadata actual (en el MISMO orden que procesar_cuentos.py la lee)
    with open(METADATA_PATH, encoding="utf-8") as f:
        filas_meta = list(csv.DictReader(f))

    # 2) leer el CSV parcial: el campo "id" tiene el índice (1-based) que
    #    procesar_cuentos.py asignó según el orden de metadata_fernanda.csv
    with open(CSV_PARCIAL, encoding="utf-8") as f:
        filas_parcial = list(csv.DictReader(f))

    indices_validos = set()
    for row in filas_parcial:
        m = re.search(r"_(\d+)$", row["id"])
        if m:
            indices_validos.add(int(m.group(1)))

    print(f"📋  {len(filas_meta)} filas en metadata_fernanda.csv")
    print(f"📋  {len(filas_parcial)} filas válidas en el CSV parcial")
    print(f"📋  {len(indices_validos)} índices únicos extraídos de los IDs")

    # 3) emparejar: la fila i (1-based) de metadata corresponde al índice i
    archivos_validos = []
    for i, row in enumerate(filas_meta, start=1):
        if i in indices_validos:
            archivos_validos.append(row["archivo"])

    print(f"✅  Archivos .txt identificados como válidos: {len(archivos_validos)}")

    # Verificación cruzada: ¿existen físicamente?
    existen = [a for a in archivos_validos if (CARPETA_TXT / a).exists()]
    print(f"📂  De esos, existen físicamente en la carpeta: {len(existen)}")

    if len(existen) != len(filas_parcial):
        print(f"\n⚠️   Hay un desfase de {len(filas_parcial) - len(existen)} cuentos.")
        print("     Puede deberse a ejecuciones previas que modificaron el orden.")
        print("     NO es seguro continuar automáticamente.")
        if args.aplicar:
            print("     Abortando --aplicar por seguridad.")
            return
    else:
        print("✅  Verificación cruzada exitosa: todo cuadra perfecto.")

    if args.solo_verificar:
        print("\n🛑  Modo verificación: NO se borró ni renombró nada.")
        return

    if len(existen) != len(filas_parcial):
        return

    # ── aplicar ──────────────────────────────────────────────────────────────────
    archivos_validos_set = set(existen)
    borrados = 0
    for ruta in CARPETA_TXT.glob("cuento_*.txt"):
        if ruta.name not in archivos_validos_set:
            ruta.unlink()
            borrados += 1
    print(f"\n🗑️   Borrados: {borrados}")

    meta_dict = {row["archivo"]: row for row in filas_meta}
    archivos_restantes = sorted(CARPETA_TXT.glob("cuento_*.txt"))

    temporales = []
    for i, ruta in enumerate(archivos_restantes):
        temp = CARPETA_TXT / f"_tmp_{i:05d}.txt"
        nombre_original = ruta.name
        ruta.rename(temp)
        temporales.append((temp, nombre_original))

    finales = []
    for i, (temp, nombre_original) in enumerate(temporales, start=1):
        nuevo_nombre = f"cuento_{i:04d}.txt"
        temp.rename(CARPETA_TXT / nuevo_nombre)
        finales.append((nombre_original, nuevo_nombre))

    print(f"🔢  Renumerados: {len(finales)}")

    nuevas_filas_meta = []
    for nombre_original, nuevo_nombre in finales:
        if nombre_original in meta_dict:
            fila = meta_dict[nombre_original].copy()
            fila["archivo"] = nuevo_nombre
            nuevas_filas_meta.append(fila)

    with open(METADATA_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["archivo", "titulo", "autor", "tematica", "fuente"])
        w.writeheader()
        w.writerows(nuevas_filas_meta)

    print(f"💾  metadata_fernanda.csv reescrito con {len(nuevas_filas_meta)} filas")

    print("\n🔄  Corriendo procesar_cuentos.py …")
    res = subprocess.run(
        [sys.executable, "scripts/procesar_cuentos.py",
         "--usuario", USUARIO,
         "--carpeta", str(CARPETA_TXT),
         "--metadata", str(METADATA_PATH)],
    )
    if res.returncode == 0:
        print("✅  CSV parcial final actualizado.")
    else:
        print("⚠️  procesar_cuentos.py terminó con errores.")


if __name__ == "__main__":
    main()
