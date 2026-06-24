"""
recortar_cuentos.py  –  Fernanda García
1. Filtra cuentos con contenido fuera de tema (satanismo, contenido religioso
   ofensivo, sexual, etc.) por palabras clave.
2. Recorta el resto a un máximo de N cuentos (default 1100).
3. Borra de mis_cuentos/ los .txt que no se conserven.
4. Actualiza metadata_fernanda.csv.
5. Vuelve a correr procesar_cuentos.py.

Uso:
    python3 recortar_cuentos.py
    python3 recortar_cuentos.py --max 1100
"""

import argparse
import csv
import random
import re
import subprocess
import sys
from pathlib import Path

USUARIO       = "fernanda_garcia"
METADATA_PATH = Path("metadata_fernanda.csv")
CARPETA_TXT   = Path("mis_cuentos")

# Palabras/frases que indican contenido fuera de tema para un cuento infantil
# de "monstruos y criaturas" (satanismo, contenido explícito, blasfemia, etc.)
PALABRAS_PROHIBIDAS = [
    "satanico", "satánico", "satanismo", "satanás", "satanas",
    "culto satánico", "culto satanico", "ritual satánico", "ritual satanico",
    "anticristo", "misa negra", "pentagrama invertido",
    "pacto con el diablo", "venerar al diablo", "adorador del diablo",
    "sacrificio humano", "sacrificio satánico",
    "pornograf", "sexual explícit", "violación", "violacion",
    "incesto", "pedofil", "abuso sexual",
    "suicidio", "autolesion", "automutilacion",
    "nazi", "supremacista", "genocidio",
]

REGEX = re.compile("|".join(re.escape(p) for p in PALABRAS_PROHIBIDAS), re.IGNORECASE)


def cargar_metadata():
    if not METADATA_PATH.exists():
        return []
    with open(METADATA_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def guardar_metadata(filas):
    with open(METADATA_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["archivo", "titulo", "autor", "tematica", "fuente"])
        w.writeheader()
        w.writerows(filas)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=1100)
    parser.add_argument("--no-procesar", action="store_true")
    parser.add_argument("--semilla", type=int, default=42, help="Semilla aleatoria para reproducibilidad")
    args = parser.parse_args()

    meta = cargar_metadata()
    print(f"📋  {len(meta)} cuentos en metadata\n")

    # ── Paso 1: filtrar por contenido prohibido ────────────────────────────────
    validos = []
    descartados_contenido = []

    for row in meta:
        ruta = CARPETA_TXT / row["archivo"]
        if not ruta.exists():
            continue
        texto = ruta.read_text(encoding="utf-8", errors="ignore")
        texto_completo = f"{row.get('titulo','')} {texto}"
        match = REGEX.search(texto_completo)
        if match:
            descartados_contenido.append((row["archivo"], row.get("titulo", ""), match.group()))
        else:
            validos.append(row)

    print(f"🚫  Descartados por contenido fuera de tema: {len(descartados_contenido)}")
    for archivo, titulo, palabra in descartados_contenido[:30]:
        print(f"      - {archivo} ({titulo[:40]}) — detectado: '{palabra}'")
    if len(descartados_contenido) > 30:
        print(f"      … y {len(descartados_contenido) - 30} más")

    print(f"\n✅  Cuentos válidos tras filtro de contenido: {len(validos)}")

    # ── Paso 2: recortar al máximo ──────────────────────────────────────────────
    if len(validos) > args.max:
        random.seed(args.semilla)
        random.shuffle(validos)
        conservados = validos[:args.max]
        sobrantes = validos[args.max:]
    else:
        conservados = validos
        sobrantes = []

    print(f"✂️   Conservando {len(conservados)} (máximo pedido: {args.max})")

    # ── Paso 3: borrar archivos no conservados ──────────────────────────────────
    archivos_conservar = {row["archivo"] for row in conservados}
    borrados = 0
    for ruta in CARPETA_TXT.glob("cuento_*.txt"):
        if ruta.name not in archivos_conservar:
            ruta.unlink()
            borrados += 1

    print(f"🗑️   Archivos .txt borrados de la carpeta: {borrados}")

    # ── Paso 4: actualizar metadata ──────────────────────────────────────────────
    guardar_metadata(conservados)
    print(f"💾  metadata_fernanda.csv actualizado con {len(conservados)} filas")

    # ── Paso 5: volver a procesar ──────────────────────────────────────────────
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
