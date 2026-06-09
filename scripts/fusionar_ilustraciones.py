import argparse
import csv
import glob
import os
from collections import defaultdict


def main():
    parser = argparse.ArgumentParser(description="Une los indices parciales de ilustraciones, deduplica y arma el indice maestro.")
    parser.add_argument("--entrada", default="datos/ilustraciones/parciales")
    parser.add_argument("--salida", default="datos/ilustraciones/dataset_ilustraciones.csv")
    args = parser.parse_args()

    archivos = sorted(glob.glob(os.path.join(args.entrada, "*.csv")))
    if not archivos:
        print("No hay CSVs parciales en", args.entrada)
        return

    filas = []
    for ruta in archivos:
        with open(ruta, encoding="utf-8") as f:
            filas.extend(csv.DictReader(f))

    print(f"Leidas {len(filas)} filas de {len(archivos)} archivos")

    por_hash = defaultdict(list)
    for fila in filas:
        por_hash[fila["hash_imagen"]].append(fila)

    unicos = []
    repetidos = 0
    for grupo in por_hash.values():
        unicos.append(grupo[0])
        repetidos += len(grupo) - 1

    os.makedirs(os.path.dirname(args.salida), exist_ok=True)
    campos = list(unicos[0].keys())
    with open(args.salida, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(unicos)

    print(f"Indice final: {len(unicos)} ilustraciones unicas en {args.salida}")
    print(f"Duplicadas eliminadas: {repetidos}")


if __name__ == "__main__":
    main()
