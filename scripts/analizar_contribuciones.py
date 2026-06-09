import argparse
import csv
import math
import os
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

csv.field_size_limit(10 * 1024 * 1024)


def cargar(ruta):
    if not os.path.exists(ruta):
        return []
    with open(ruta, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def entropia(conteos):
    total = sum(conteos.values())
    if total == 0:
        return 0.0
    h = 0.0
    for n in conteos.values():
        p = n / total
        if p > 0:
            h -= p * math.log2(p)
    return h


def resumen_por_persona(cuentos, ilustraciones):
    personas = set(c["recolector"] for c in cuentos) | set(i["recolector"] for i in ilustraciones)
    cuentos_por = defaultdict(list)
    for c in cuentos:
        cuentos_por[c["recolector"]].append(c)
    ilus_por = defaultdict(list)
    for i in ilustraciones:
        ilus_por[i["recolector"]].append(i)

    resumen = []
    for persona in sorted(personas):
        cs = cuentos_por[persona]
        palabras = [int(c["num_palabras"]) for c in cs] or [0]
        edades = Counter(c["edad"] for c in cs)
        resumen.append({
            "recolector": persona,
            "cuentos": len(cs),
            "ilustraciones": len(ilus_por[persona]),
            "palabras_promedio": round(sum(palabras) / len(palabras), 1),
            "edades_distintas": len(edades),
            "entropia_edades": round(entropia(edades), 3),
        })
    return resumen


def riqueza_lexica(cuentos):
    total_tokens = 0
    vocabulario = set()
    for fila in cuentos:
        tokens = fila["texto"].lower().split()
        total_tokens += len(tokens)
        vocabulario.update(tokens)
    if total_tokens == 0:
        return 0.0, 0, 0
    return len(vocabulario) / total_tokens, len(vocabulario), total_tokens


def graficar(resumen, cuentos, ilustraciones, carpeta):
    os.makedirs(carpeta, exist_ok=True)
    personas = [r["recolector"] for r in resumen]

    plt.figure(figsize=(12, 4))
    x = range(len(personas))
    plt.bar([i - 0.2 for i in x], [r["cuentos"] for r in resumen], width=0.4, label="cuentos")
    plt.bar([i + 0.2 for i in x], [r["ilustraciones"] for r in resumen], width=0.4, label="ilustraciones")
    plt.axhline(600, linestyle="--")
    plt.title("Muestras recolectadas por persona")
    plt.xticks(list(x), personas, rotation=75, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(carpeta, "muestras_por_persona.png"))
    plt.close()

    if cuentos:
        palabras = [int(f["num_palabras"]) for f in cuentos]
        plt.figure(figsize=(8, 4))
        plt.hist(palabras, bins=40)
        plt.title("Distribucion de longitud de los cuentos")
        plt.xlabel("Numero de palabras")
        plt.ylabel("Frecuencia")
        plt.tight_layout()
        plt.savefig(os.path.join(carpeta, "longitud_cuentos.png"))
        plt.close()

    todas_edades = Counter(c["edad"] for c in cuentos) + Counter(i["edad"] for i in ilustraciones)
    if todas_edades:
        plt.figure(figsize=(8, 4))
        plt.bar(list(todas_edades.keys()), list(todas_edades.values()))
        plt.title("Muestras por rango de edad (cuentos + ilustraciones)")
        plt.ylabel("Muestras")
        plt.tight_layout()
        plt.savefig(os.path.join(carpeta, "muestras_por_edad.png"))
        plt.close()


def escribir_reporte(resumen, cuentos, ilustraciones, carpeta):
    rtt, vocab, tokens = riqueza_lexica(cuentos)
    edades_c = Counter(c["edad"] for c in cuentos)

    ruta_csv = os.path.join(carpeta, "resumen_por_persona.csv")
    campos = ["recolector", "cuentos", "ilustraciones", "palabras_promedio",
              "edades_distintas", "entropia_edades"]
    with open(ruta_csv, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(resumen)

    ruta_md = os.path.join(carpeta, "reporte.md")
    with open(ruta_md, "w", encoding="utf-8") as f:
        f.write("# Reporte de contribuciones\n\n")
        f.write(f"- Cuentos totales: {len(cuentos)}\n")
        f.write(f"- Ilustraciones totales: {len(ilustraciones)}\n")
        f.write(f"- Personas: {len(resumen)}\n")
        f.write(f"- Entropia de edades en cuentos: {entropia(edades_c):.3f} bits\n")
        f.write(f"- Vocabulario unico: {vocab}  Tokens totales: {tokens}\n")
        f.write(f"- Riqueza lexica (type-token ratio): {rtt:.4f}\n\n")
        f.write("Por debajo de cuota (menos de 600 cuentos o 600 ilustraciones):\n\n")
        rezagados = [r for r in resumen if r["cuentos"] < 600 or r["ilustraciones"] < 600]
        if rezagados:
            for r in rezagados:
                f.write(f"- {r['recolector']}: {r['cuentos']} cuentos, {r['ilustraciones']} ilustraciones\n")
        else:
            f.write("- nadie, vamos completos\n")
    return ruta_csv, ruta_md


def main():
    parser = argparse.ArgumentParser(description="Analiza cuanto y que tan variado aporto cada persona.")
    parser.add_argument("--cuentos", default="datos/cuentos/dataset_cuentos.csv")
    parser.add_argument("--ilustraciones", default="datos/ilustraciones/dataset_ilustraciones.csv")
    parser.add_argument("--salida", default="analisis")
    args = parser.parse_args()

    cuentos = cargar(args.cuentos)
    ilustraciones = cargar(args.ilustraciones)
    if not cuentos and not ilustraciones:
        print("No hay datasets que analizar todavia.")
        return

    resumen = resumen_por_persona(cuentos, ilustraciones)
    graficar(resumen, cuentos, ilustraciones, args.salida)
    ruta_csv, ruta_md = escribir_reporte(resumen, cuentos, ilustraciones, args.salida)

    print(f"Analizados {len(cuentos)} cuentos y {len(ilustraciones)} ilustraciones de {len(resumen)} personas.")
    print("Resumen:", ruta_csv)
    print("Reporte:", ruta_md)
    print("Graficas en:", args.salida)


if __name__ == "__main__":
    main()
