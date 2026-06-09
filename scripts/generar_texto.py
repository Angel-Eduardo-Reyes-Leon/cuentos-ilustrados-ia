import argparse
import json
import os

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

from entrenar_texto import construir_entrada


def cargar(carpeta):
    tokenizer = AutoTokenizer.from_pretrained(carpeta)
    modelo = AutoModelForSeq2SeqLM.from_pretrained(carpeta)
    modelo.eval()
    tematicas = []
    ruta_tem = os.path.join(carpeta, "tematicas.json")
    if os.path.exists(ruta_tem):
        with open(ruta_tem, encoding="utf-8") as f:
            tematicas = json.load(f)["tematicas"]
    return tokenizer, modelo, tematicas


def generar(tokenizer, modelo, tematica, temperatura=0.9, max_tokens=400):
    entrada = tokenizer(construir_entrada(tematica), return_tensors="pt")
    with torch.no_grad():
        salida = modelo.generate(
            **entrada,
            do_sample=True,
            temperature=temperatura,
            top_p=0.95,
            max_length=max_tokens,
            repetition_penalty=1.3,
            no_repeat_ngram_size=3,
        )
    return tokenizer.decode(salida[0], skip_special_tokens=True)


def main():
    parser = argparse.ArgumentParser(description="Genera un cuento de una tematica dada con el T5 afinado.")
    parser.add_argument("--modelo", default="modelos/texto")
    parser.add_argument("--tematica", required=True, help="Tematica, ej. espacio")
    parser.add_argument("--temperatura", type=float, default=0.9)
    parser.add_argument("--max_tokens", type=int, default=400)
    parser.add_argument("--cantidad", type=int, default=1)
    parser.add_argument("--guardar", default=None, help="Archivo .txt opcional para guardar la salida")
    args = parser.parse_args()

    tokenizer, modelo, tematicas = cargar(args.modelo)
    if tematicas and args.tematica not in tematicas:
        print(f"Aviso: '{args.tematica}' no estaba en el entrenamiento. Disponibles: {tematicas}")

    textos = []
    for i in range(args.cantidad):
        texto = generar(tokenizer, modelo, args.tematica, args.temperatura, args.max_tokens)
        textos.append(texto)
        print(f"\n--- Cuento {i + 1} (tematica: {args.tematica}) ---\n")
        print(texto)

    if args.guardar:
        with open(args.guardar, "w", encoding="utf-8") as f:
            f.write("\n\n=====\n\n".join(textos))
        print("\nGuardado en", args.guardar)


if __name__ == "__main__":
    main()
