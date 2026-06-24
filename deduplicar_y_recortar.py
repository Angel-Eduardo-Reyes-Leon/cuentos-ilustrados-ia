"""
deduplicar_y_recortar.py  –  Fernanda García
1. Detecta cuentos con el MISMO TÍTULO (duplicados, posiblemente uno cortado).
   De cada grupo de duplicados, conserva solo el que tiene MÁS PALABRAS.
2. Recorta el resto a un máximo de N cuentos (default 1000).
3. Borra de mis_cuentos/ los .txt que no se conserven.
4. Actualiza metadata_fernanda.csv.
5. Vuelve a correr procesar_cuentos.py.

Uso:
    python3 deduplicar_y_recortar.py
    python3 deduplicar_y_recortar.py --max 1000
"""

import argparse
import csv
import random
import re
import subprocess
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

USUARIO       = "fernanda_garcia"
METADATA_PATH = Path("metadata_fernanda.csv")
CARPETA_TXT   = Path("mis_cuentos")


def normalizar_titulo(titulo):
    """Normaliza para comparar títulos que son 'el mismo' aunque varíe mayúsculas/acentos."""
    t = titulo.lower().strip()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9 ]", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


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
    parser.add_argument("--max", type=int, default=1000)
    parser.add_argument("--no-procesar", action="store_true")
    parser.add_argument("--semilla", type=int, default=42)
    args = parser.parse_args()

    meta = cargar_metadata()
    print(f"📋  {len(meta)} cuentos en metadata\n")

    # ── Paso 1: agrupar por título normalizado ──────────────────────────────────
    grupos = defaultdict(list)
    for row in meta:
        ruta = CARPETA_TXT / row["archivo"]
        if not ruta.exists():
            continue
        texto = ruta.read_text(encoding="utf-8", errors="ignore")
        n_palabras = len(texto.split())
        clave = normalizar_titulo(row.get("titulo", ""))
        grupos[clave].append((row, n_palabras))

    # ── Paso 2: de cada grupo, conservar el de más palabras ─────────────────────
    conservados = []
    descartados_duplicado = []

    for clave, items in grupos.items():
        if len(items) == 1:
            conservados.append(items[0][0])
        else:
            # ordenar por num palabras descendente, conservar el más largo
            items.sort(key=lambda x: x[1], reverse=True)
            ganador, n_ganador = items[0]
            conservados.append(ganador)
            for row, n in items[1:]:
                descartados_duplicado.append((row["archivo"], row.get("titulo", ""), n, n_ganador))

    print(f"🔁  Grupos de duplicados encontrados: {sum(1 for v in grupos.values() if len(v) > 1)}")
    print(f"🗑️   Descartados por ser versión más corta del mismo cuento: {len(descartados_duplicado)}")
    for archivo, titulo, n, n_ganador in descartados_duplicado[:20]:
        print(f"      - {archivo} ({titulo[:40]}) — {n} palabras (se conservó otra versión con {n_ganador})")
    if len(descartados_duplicado) > 20:
        print(f"      … y {len(descartados_duplicado) - 20} más")

    print(f"\n✅  Cuentos únicos tras deduplicar: {len(conservados)}")

    # ── Paso 3: recortar al máximo (estratégico) ─────────────────────────────────
    # Prioridad de conservación:
    #   1) Cuentos de "Cuentos para Algernon" (los más recientes, filtrados por
    #      tema con más cuidado y en mejor estado) — SIEMPRE se conservan todos.
    #   2) El resto, recortado al azar hasta completar el máximo.
    FUENTES_PRIORITARIAS = {
        "Cuentos para Algernon",
        "Cuentos de terror",
        "Manual de zoología fantástica",
        "El libro de los seres imaginarios",
        "CUENTOS POPULARES Y MITOS DE DRAGONES (Cuentos Populares y Mitos Infantiles, #5)",
        "Mares tenebrosos",
        "Noches de pesadilla",
        "Cuentos chilenos de terror, misterio y fantasía",
        "Los mejores relatos de terror llevados al cine [3468]",
        "No grites no podran oirte",
    }

    prioritarios   = [r for r in conservados if r.get("fuente", "").strip() in FUENTES_PRIORITARIAS]
    resto          = [r for r in conservados if r.get("fuente", "").strip() not in FUENTES_PRIORITARIAS]

    print(f"⭐  Cuentos de fuentes prioritarias (Algernon + zip) — se conservan siempre: {len(prioritarios)}")

    espacio_restante = max(args.max - len(prioritarios), 0)

    if len(resto) > espacio_restante:
        random.seed(args.semilla)
        random.shuffle(resto)
        resto_final = resto[:espacio_restante]
    else:
        resto_final = resto

    finales = prioritarios + resto_final

    if len(prioritarios) > args.max:
        print(f"⚠️   Los prioritarios ({len(prioritarios)}) ya superan el máximo ({args.max}).")
        print(f"     Se conservan TODOS los prioritarios y NINGUNO del resto.")

    print(f"✂️   Conservando {len(finales)} (máximo pedido: {args.max})")

    # ── Paso 4: borrar archivos no conservados ──────────────────────────────────
    archivos_conservar = {row["archivo"] for row in finales}
    borrados = 0
    for ruta in CARPETA_TXT.glob("cuento_*.txt"):
        if ruta.name not in archivos_conservar:
            ruta.unlink()
            borrados += 1

    print(f"🗑️   Archivos .txt borrados de la carpeta: {borrados}")

    # ── Paso 5: actualizar metadata ──────────────────────────────────────────────
    guardar_metadata(finales)
    print(f"💾  metadata_fernanda.csv actualizado con {len(finales)} filas")

    # ── Paso 6: volver a procesar ──────────────────────────────────────────────
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
