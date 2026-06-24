"""
integrar_json.py  –  Fernanda García
Toma uno o varios JSON de cuentos generados por Claude y los integra
a mis_cuentos_fernanda_garcia/ actualizando metadata_fernanda.csv.

Uso:
    python3 integrar_json.py cuentos_generados_final-2.json
    python3 integrar_json.py *.json   (varios JSONs a la vez)
"""

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

USUARIO        = "fernanda_garcia"
METADATA_PATH  = Path("metadata_fernanda.csv")
CARPETA_TXT    = Path("mis_cuentos_fernanda_garcia")
TEMATICA       = "monstruos_y_criaturas"
CAMPOS_META    = ["archivo", "titulo", "autor", "tematica", "fuente"]


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
    if len(sys.argv) < 2:
        print("Uso: python3 integrar_json.py archivo.json [archivo2.json ...]")
        sys.exit(1)

    CARPETA_TXT.mkdir(parents=True, exist_ok=True)
    meta_filas = cargar_metadata()
    archivos_existentes = {f["archivo"] for f in meta_filas}

    total = 0
    for json_path in sys.argv[1:]:
        print(f"\n📂  Procesando {json_path}")
        with open(json_path, encoding="utf-8") as f:
            cuentos = json.load(f)

        print(f"   {len(cuentos)} cuentos encontrados")

        for c in cuentos:
            contenido = c.get("contenido", "").strip()
            titulo = c.get("titulo", "Sin título").strip()
            autor = c.get("autor", "Anónimo").strip()
            fuente = c.get("fuente", "sintetica").strip()

            if not contenido or len(contenido.split()) < 50:
                print(f"  ⏭️  Saltado (muy corto): {titulo[:50]}")
                continue

            num = siguiente_numero(CARPETA_TXT)
            archivo = f"cuento_{num:04d}.txt"
            while archivo in archivos_existentes:
                num += 1
                archivo = f"cuento_{num:04d}.txt"

            (CARPETA_TXT / archivo).write_text(contenido, encoding="utf-8")
            archivos_existentes.add(archivo)

            meta_filas.append({
                "archivo":  archivo,
                "titulo":   titulo,
                "autor":    autor,
                "tematica": TEMATICA,
                "fuente":   fuente,
            })
            total += 1
            print(f"  ✅  [{total}] {archivo} — {titulo[:50]}")

    guardar_metadata(meta_filas)
    print(f"\n💾  metadata_fernanda.csv actualizado con {len(meta_filas)} filas")

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
