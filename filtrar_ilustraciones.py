"""
filtrar_ilustraciones.py  –  Fernanda García
Usa la API de Claude para revisar cada imagen y decidir si es
ilustración plana/caricatura (válida) o foto/3D/realista (inválida).
Borra las inválidas y vuelve a correr procesar_ilustraciones.py.

Uso:
    python3 filtrar_ilustraciones.py
    python3 filtrar_ilustraciones.py --no-procesar
    python3 filtrar_ilustraciones.py --limite 100   # probar con 100 primero

Requiere:  pip install anthropic
"""

import argparse
import base64
import json
import subprocess
import sys
import time
from pathlib import Path

import anthropic

USUARIO     = "fernanda_garcia"
CARPETA_IMG = Path("mis_ilustraciones")
ESPERA      = 0.3   # segundos entre llamadas a la API

PROMPT = """Mira esta imagen y responde SOLO con un JSON así:
{"valida": true, "razon": "descripción breve"}

Es VÁLIDA si es:
- Ilustración digital plana, a color
- Estilo caricatura o animación (tipo clipart)
- Fondo simple o de un color
- Un personaje o escena clara con formas simples

Es INVÁLIDA si es:
- Fotografía realista
- Render 3D fotorrealista
- Pintura al óleo o acuarela
- Grabado antiguo o blanco y negro
- Muy recargada o con muchos detalles (se vería mal a 64x64)
- No tiene nada que ver con monstruos, criaturas, fantasía o terror

Solo responde el JSON, sin explicación extra."""


def imagen_a_base64(ruta):
    with open(ruta, "rb") as f:
        datos = f.read()
    ext = ruta.suffix.lower()
    media_type = "image/png" if ext == ".png" else "image/jpeg"
    return base64.standard_b64encode(datos).decode("utf-8"), media_type


def es_valida(cliente, ruta):
    try:
        b64, media_type = imagen_a_base64(ruta)
        respuesta = cliente.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64,
                        }
                    },
                    {"type": "text", "text": PROMPT}
                ]
            }]
        )
        texto = respuesta.content[0].text.strip()
        # limpiar posibles backticks
        texto = texto.replace("```json", "").replace("```", "").strip()
        resultado = json.loads(texto)
        return resultado.get("valida", False), resultado.get("razon", "")
    except Exception as e:
        print(f"      ⚠️  Error al revisar {ruta.name}: {e}")
        return True, "error al revisar, se conserva"  # conservar si hay error


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limite", type=int, default=999_999)
    parser.add_argument("--no-procesar", action="store_true")
    args = parser.parse_args()

    cliente = anthropic.Anthropic()  # toma ANTHROPIC_API_KEY del entorno

    imagenes = sorted(
        list(CARPETA_IMG.glob("*.png")) +
        list(CARPETA_IMG.glob("*.jpg")) +
        list(CARPETA_IMG.glob("*.jpeg"))
    )[:args.limite]

    print(f"📋  {len(imagenes)} imágenes a revisar\n")

    validas = 0
    borradas = 0

    for i, ruta in enumerate(imagenes, 1):
        valida, razon = es_valida(cliente, ruta)
        if valida:
            validas += 1
            if i % 50 == 0:
                print(f"  [{i}/{len(imagenes)}] ✅  {validas} válidas hasta ahora…")
        else:
            ruta.unlink()
            borradas += 1
            print(f"  [{i}/{len(imagenes)}] 🗑️  {ruta.name} borrada — {razon}")
        time.sleep(ESPERA)

    print(f"\n{'='*55}")
    print(f"  Válidas conservadas : {validas}")
    print(f"  Borradas            : {borradas}")
    print(f"{'='*55}")

    if not args.no_procesar:
        print("\n🔄  Corriendo procesar_ilustraciones.py …")
        res = subprocess.run(
            [sys.executable, "scripts/procesar_ilustraciones.py",
             "--usuario", USUARIO],
        )
        if res.returncode == 0:
            print("✅  CSV parcial de ilustraciones actualizado.")
        else:
            print("⚠️  procesar_ilustraciones.py terminó con errores.")


if __name__ == "__main__":
    main()
