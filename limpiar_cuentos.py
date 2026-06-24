"""
limpiar_cuentos.py  –  Fernanda García
Limpia los .txt de mis_cuentos/:
  1. Quita emojis
  2. Quita el título si aparece al inicio del texto
  3. Quita texto basura al final (recomendaciones, redes sociales, etc.)
  4. Vuelve a correr procesar_cuentos.py para actualizar el CSV

Uso:
    python3 limpiar_cuentos.py
    python3 limpiar_cuentos.py --no-procesar
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

# ── patrones de basura al final ────────────────────────────────────────────────
PATRONES_BASURA = [
    r"síguenos.*",
    r"sigue?nos.*",
    r"follow us.*",
    r"comparte.*",
    r"compartir.*",
    r"si te gustó.*",
    r"si te gusto.*",
    r"si disfrutaste.*",
    r"más cuentos.*",
    r"mas cuentos.*",
    r"visita.*nuestra.*",
    r"visita.*página.*",
    r"visita.*pagina.*",
    r"encuéntranos.*",
    r"encuéntranos.*",
    r"encuentranos.*",
    r"lee más.*",
    r"lee mas.*",
    r"otros cuentos.*",
    r"también te puede.*",
    r"también te puede.*",
    r"también podría.*",
    r"recomendamos.*",
    r"te recomendamos.*",
    r"newsletter.*",
    r"suscríbete.*",
    r"suscribete.*",
    r"facebook.*",
    r"instagram.*",
    r"twitter.*",
    r"tiktok.*",
    r"youtube.*",
    r"@\w+",
    r"www\.\S+",
    r"https?://\S+",
    r"copyright.*",
    r"todos los derechos.*",
    r"fin\s*$",
    r"– fin –.*",
    r"--- fin ---.*",
    r"\* \* \*\s*$",
]

REGEX_BASURA = re.compile(
    r"(" + "|".join(PATRONES_BASURA) + r")",
    re.IGNORECASE
)

# ── regex de emojis ────────────────────────────────────────────────────────────
EMOJI_RE = re.compile(
    "[\U00010000-\U0010ffff"
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002500-\U00002BEF"
    "\U00002702-\U000027B0"
    "\u2640-\u2642"
    "\u2600-\u2B55"
    "\u200d"
    "\u23cf"
    "\u23e9"
    "\u231a"
    "\ufe0f"
    "\u3030"
    "]+",
    re.UNICODE
)


def quitar_emojis(texto):
    return EMOJI_RE.sub("", texto)


def quitar_titulo_inicial(texto, titulo):
    """Quita la primera línea si es igual o muy similar al título."""
    if not titulo:
        return texto
    lineas = texto.split("\n")
    if not lineas:
        return texto
    primera = lineas[0].strip().lower()
    titulo_norm = titulo.strip().lower()
    # Quitar si es idéntico, o si la primera línea está contenida en el título
    if primera == titulo_norm or primera in titulo_norm or titulo_norm in primera:
        resto = "\n".join(lineas[1:]).lstrip("\n")
        return resto
    return texto


def quitar_basura_final(texto):
    """Elimina líneas con patrones de basura desde que aparece el primero."""
    lineas = texto.split("\n")
    resultado = []
    for linea in lineas:
        if REGEX_BASURA.search(linea.strip()):
            break  # corta todo lo que viene después
        resultado.append(linea)
    return "\n".join(resultado).rstrip()


def limpiar_texto(texto, titulo=""):
    texto = quitar_emojis(texto)
    texto = quitar_titulo_inicial(texto, titulo)
    texto = quitar_basura_final(texto)
    # limpiar espacios extra
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def cargar_metadata():
    if not METADATA_PATH.exists():
        return []
    with open(METADATA_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-procesar", action="store_true")
    args = parser.parse_args()

    meta = {row["archivo"]: row for row in cargar_metadata()}
    archivos = sorted(CARPETA_TXT.glob("cuento_*.txt"))
    print(f"📋  Procesando {len(archivos)} archivos…\n")

    limpios = 0
    sin_cambios = 0

    for i, ruta in enumerate(archivos, start=1):
        titulo = meta.get(ruta.name, {}).get("titulo", "")
        original = ruta.read_text(encoding="utf-8", errors="ignore")
        limpio = limpiar_texto(original, titulo)

        if limpio != original:
            ruta.write_text(limpio, encoding="utf-8")
            limpios += 1
        else:
            sin_cambios += 1

        if i % 100 == 0:
            print(f"  … {i}/{len(archivos)} procesados")

    print(f"✅  {limpios} archivos limpiados, {sin_cambios} sin cambios")

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
