import argparse
import json
import os

import torch
import torch.nn.functional as F

from entrenar_texto import GeneradorCuentos, INICIO, FIN


def cargar(carpeta):
    with open(os.path.join(carpeta, "vocabularios.json"), encoding="utf-8") as f:
        vocab = json.load(f)
    char_a_idx = vocab["char_a_idx"]
    edad_a_idx = vocab["edad_a_idx"]
    idx_a_char = {i: c for c, i in char_a_idx.items()}

    estado = torch.load(os.path.join(carpeta, "generador_texto.pt"), map_location="cpu")
    modelo = GeneradorCuentos(len(char_a_idx), len(edad_a_idx),
                              dim_oculto=estado["dim_oculto"], capas=estado["capas"])
    modelo.load_state_dict(estado["estado"])
    modelo.eval()
    return modelo, char_a_idx, edad_a_idx, idx_a_char


def generar(modelo, char_a_idx, edad_a_idx, idx_a_char, edad,
            temperatura=0.8, max_chars=1200):
    if edad not in edad_a_idx:
        raise ValueError(f"Edad '{edad}' no existe. Disponibles: {sorted(edad_a_idx)}")

    t_edad = torch.tensor([edad_a_idx[edad]])
    actual = torch.tensor([[char_a_idx[INICIO]]])
    estado = None
    salida = []

    with torch.no_grad():
        for _ in range(max_chars):
            logits, estado = modelo(actual, t_edad, estado)
            logits = logits[0, -1] / temperatura
            probs = F.softmax(logits, dim=-1)
            siguiente = torch.multinomial(probs, 1).item()
            if siguiente == char_a_idx[FIN]:
                break
            salida.append(idx_a_char[siguiente])
            actual = torch.tensor([[siguiente]])

    return "".join(salida)


def main():
    parser = argparse.ArgumentParser(description="Genera un cuento para un rango de edad.")
    parser.add_argument("--modelo", default="modelos")
    parser.add_argument("--edad", required=True, help="Rango de edad, ej. 6-8")
    parser.add_argument("--temperatura", type=float, default=0.8)
    parser.add_argument("--max_chars", type=int, default=1200)
    parser.add_argument("--cantidad", type=int, default=1)
    parser.add_argument("--guardar", default=None, help="Archivo .txt opcional para guardar la salida")
    args = parser.parse_args()

    modelo, char_a_idx, edad_a_idx, idx_a_char = cargar(args.modelo)

    textos = []
    for i in range(args.cantidad):
        texto = generar(modelo, char_a_idx, edad_a_idx, idx_a_char,
                        args.edad, args.temperatura, args.max_chars)
        textos.append(texto)
        print(f"\n--- Cuento {i + 1} (edad: {args.edad}) ---\n")
        print(texto)

    if args.guardar:
        with open(args.guardar, "w", encoding="utf-8") as f:
            f.write("\n\n=====\n\n".join(textos))
        print("\nGuardado en", args.guardar)


if __name__ == "__main__":
    main()
