import argparse
import csv

csv.field_size_limit(10 * 1024 * 1024)

CAMPOS = ["id", "titulo", "autor", "edad", "idioma",
          "num_palabras", "fuente", "recolector", "hash_texto", "texto"]

META = 600


def main():
    parser = argparse.ArgumentParser(description="Revisa que tu CSV parcial de cuentos cumpla el esquema antes de subirlo.")
    parser.add_argument("archivo")
    args = parser.parse_args()

    with open(args.archivo, encoding="utf-8") as f:
        lector = csv.DictReader(f)
        if lector.fieldnames != CAMPOS:
            print("ERROR: las columnas no coinciden con el esquema.")
            print("  esperado:  ", CAMPOS)
            print("  encontrado:", lector.fieldnames)
            return
        filas = list(lector)

    errores = 0
    hashes = set()
    for i, fila in enumerate(filas, start=2):
        if not fila["texto"].strip():
            print(f"  fila {i}: texto vacio"); errores += 1
        if not fila["titulo"].strip():
            print(f"  fila {i}: titulo vacio"); errores += 1
        if not fila["hash_texto"].strip():
            print(f"  fila {i}: falta hash"); errores += 1
        elif fila["hash_texto"] in hashes:
            print(f"  fila {i}: duplicado dentro de tu propio archivo"); errores += 1
        else:
            hashes.add(fila["hash_texto"])

    print(f"\n{len(filas)} filas revisadas, {errores} errores")
    if len(filas) < META:
        print(f"AVISO: vas en {len(filas)} de {META} cuentos.")
    else:
        print("Cuota cumplida.")


if __name__ == "__main__":
    main()
