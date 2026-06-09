import argparse
import csv
import glob
import os
from collections import defaultdict

csv.field_size_limit(10 * 1024 * 1024)


def normalizar_titulo(titulo):
    return " ".join(titulo.lower().split())


def main():
    parser = argparse.ArgumentParser(description="Une todos los CSV parciales de cuentos, deduplica y arma el dataset maestro.")
    parser.add_argument("--entrada", default="datos/cuentos/parciales")
    parser.add_argument("--salida", default="datos/cuentos/dataset_cuentos.csv")
    parser.add_argument("--reporte", default="datos/cuentos/reporte_duplicados.csv")
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
        por_hash[fila["hash_texto"]].append(fila)

    unicos = []
    duplicados = []
    for grupo in por_hash.values():
        unicos.append(grupo[0])
        for repetido in grupo[1:]:
            duplicados.append({
                "tipo": "exacto",
                "titulo": repetido["titulo"],
                "recolector": repetido["recolector"],
                "nota": f"identico a uno de {grupo[0]['recolector']}",
            })

    por_titulo = defaultdict(list)
    for fila in unicos:
        por_titulo[normalizar_titulo(fila["titulo"])].append(fila)
    for grupo in por_titulo.values():
        if len(grupo) > 1:
            for fila in grupo:
                duplicados.append({
                    "tipo": "titulo_similar",
                    "titulo": fila["titulo"],
                    "recolector": fila["recolector"],
                    "nota": "mismo titulo, revisar si es la misma version",
                })

    os.makedirs(os.path.dirname(args.salida), exist_ok=True)
    campos = list(unicos[0].keys())
    with open(args.salida, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(unicos)

    if duplicados:
        with open(args.reporte, "w", encoding="utf-8", newline="") as f:
            escritor = csv.DictWriter(f, fieldnames=["tipo", "titulo", "recolector", "nota"])
            escritor.writeheader()
            escritor.writerows(duplicados)

    exactos = sum(1 for d in duplicados if d["tipo"] == "exacto")
    similares = sum(1 for d in duplicados if d["tipo"] == "titulo_similar")
    print(f"Dataset final: {len(unicos)} cuentos unicos en {args.salida}")
    print(f"Duplicados exactos eliminados: {exactos}")
    print(f"Titulos a revisar manualmente: {similares}  (ver {args.reporte})")


if __name__ == "__main__":
    main()
