import argparse
import csv

csv.field_size_limit(10 * 1024 * 1024)


def ngramas(texto, n):
    tokens = texto.lower().split()
    return set(tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1))


def cargar_ngramas_entrenamiento(ruta, n):
    conjunto = set()
    with open(ruta, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            conjunto |= ngramas(fila["texto"], n)
    return conjunto


def solapamiento(texto, ngramas_train, n):
    g = ngramas(texto, n)
    if not g:
        return 0.0
    copiados = len(g & ngramas_train)
    return copiados / len(g)


def main():
    parser = argparse.ArgumentParser(
        description="Mide cuanto del texto generado fue copiado del dataset (control de memorizacion).")
    parser.add_argument("--dataset", default="datos/cuentos/dataset_cuentos.csv")
    parser.add_argument("--generado", required=True, help="Archivo .txt con cuentos separados por '====='")
    parser.add_argument("--n", type=int, default=4, help="Tamano de los n-gramas")
    args = parser.parse_args()

    print(f"Construyendo {args.n}-gramas del dataset...")
    ngramas_train = cargar_ngramas_entrenamiento(args.dataset, args.n)

    with open(args.generado, encoding="utf-8") as f:
        textos = [t.strip() for t in f.read().split("=====") if t.strip()]

    print(f"\nSolapamiento de {args.n}-gramas con el entrenamiento (mas alto = mas copiado):\n")
    for i, texto in enumerate(textos, start=1):
        s = solapamiento(texto, ngramas_train, args.n)
        marca = "  <- revisar, posible memorizacion" if s > 0.5 else ""
        print(f"  Cuento {i}: {s:.1%}{marca}")

    if textos:
        promedio = sum(solapamiento(t, ngramas_train, args.n) for t in textos) / len(textos)
        print(f"\nPromedio: {promedio:.1%}")
        print("Un modelo que generaliza bien deberia tener solapamiento bajo.")


if __name__ == "__main__":
    main()
