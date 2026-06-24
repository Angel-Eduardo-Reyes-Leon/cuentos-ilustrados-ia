"""
sincronizar_cuentos_seguro.py  –  Fernanda García
Sincroniza mis_cuentos/ con el CSV parcial usando HASH DE TEXTO
(comparación exacta del contenido, no por título/autor que puede fallar).

PASO 1 (verificación, no borra nada): muestra cuántos coinciden.
PASO 2 (solo si confirmas): borra lo que sobra y renumera.

Uso:
    python3 sincronizar_cuentos_seguro.py --solo-verificar
    python3 sincronizar_cuentos_seguro.py --aplicar
"""

import argparse
import csv
import hashlib
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

USUARIO       = "fernanda_garcia"
METADATA_PATH = Path("metadata_fernanda.csv")
CARPETA_TXT   = Path("mis_cuentos")
CSV_PARCIAL   = Path("datos/cuentos/parciales/parcial_fernanda_garcia.csv")


def normalizar(texto):
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"[^a-z0-9 ]", "", texto)
    return texto


def hash_texto(texto):
    return hashlib.sha1(normalizar(texto).encode("utf-8")).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solo-verificar", action="store_true")
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()

    if not args.solo_verificar and not args.aplicar:
        print("Usa --solo-verificar primero, o --aplicar para hacer los cambios.")
        return

    # ── leer hashes válidos del CSV parcial ──────────────────────────────────────
    with open(CSV_PARCIAL, encoding="utf-8") as f:
        filas_parcial = list(csv.DictReader(f))
    hashes_validos = {row["hash_texto"] for row in filas_parcial}
    print(f"📋  {len(hashes_validos)} hashes válidos en el CSV parcial")

    # ── calcular hash de cada .txt en la carpeta ─────────────────────────────────
    archivos_validos = []
    archivos_invalidos = []
    for ruta in sorted(CARPETA_TXT.glob("cuento_*.txt")):
        texto = ruta.read_text(encoding="utf-8", errors="ignore")
        h = hash_texto(texto)
        if h in hashes_validos:
            archivos_validos.append(ruta.name)
        else:
            archivos_invalidos.append(ruta.name)

    print(f"✅  Archivos .txt que SÍ coinciden con el CSV: {len(archivos_validos)}")
    print(f"❌  Archivos .txt que NO coinciden (se borrarían): {len(archivos_invalidos)}")

    if len(archivos_validos) != len(hashes_validos):
        print(f"\n⚠️   ADVERTENCIA: hay {len(hashes_validos)} hashes válidos pero solo")
        print(f"     se encontraron {len(archivos_validos)} archivos que coinciden.")
        print(f"     Diferencia: {len(hashes_validos) - len(archivos_validos)} cuentos del CSV")
        print(f"     no tienen un .txt correspondiente en la carpeta (no se pueden recuperar).")

    if args.solo_verificar:
        print("\n🛑  Modo verificación: NO se borró ni renombró nada.")
        print("    Si los números te parecen correctos, corre con --aplicar")
        return

    # ── PASO 2: aplicar cambios ───────────────────────────────────────────────────
    print("\n🔧  Aplicando cambios…")

    # leer metadata actual para preservar título/autor/fuente
    with open(METADATA_PATH, encoding="utf-8") as f:
        filas_meta = list(csv.DictReader(f))
    meta_dict = {row["archivo"]: row for row in filas_meta}

    # borrar inválidos
    borrados = 0
    for nombre in archivos_invalidos:
        (CARPETA_TXT / nombre).unlink()
        borrados += 1
    print(f"🗑️   Borrados: {borrados}")

    # renumerar limpio (con paso intermedio para evitar colisiones)
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

    # reescribir metadata con los nuevos nombres
    mapa = dict(finales)
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

    # volver a procesar
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
