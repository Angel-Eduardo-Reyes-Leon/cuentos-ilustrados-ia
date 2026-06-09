import argparse
import csv
import json
import os

import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

csv.field_size_limit(10 * 1024 * 1024)


def construir_entrada(tematica):
    """Prompt que recibe el encoder. Debe ser identico al entrenar y al generar."""
    return f"escribe un cuento sobre {tematica.replace('_', ' ')}"


def cargar_dataset(ruta):
    pares = []
    tematicas = set()
    with open(ruta, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            texto = fila["texto"].strip()
            tematica = fila["tematica"].strip()
            if texto and tematica:
                pares.append((construir_entrada(tematica), texto))
                tematicas.add(tematica)
    return pares, sorted(tematicas)


class CuentosDataset(Dataset):
    def __init__(self, pares):
        self.pares = pares

    def __len__(self):
        return len(self.pares)

    def __getitem__(self, i):
        return self.pares[i]


def hacer_colar(tokenizer, max_entrada, max_salida):
    def colar(lote):
        entradas = [e for e, _ in lote]
        objetivos = [o for _, o in lote]
        enc = tokenizer(entradas, max_length=max_entrada, truncation=True,
                        padding=True, return_tensors="pt")
        obj = tokenizer(objetivos, max_length=max_salida, truncation=True,
                        padding=True, return_tensors="pt")
        etiquetas = obj["input_ids"]
        # El padding en las etiquetas se ignora en la perdida con -100.
        etiquetas[etiquetas == tokenizer.pad_token_id] = -100
        enc["labels"] = etiquetas
        return enc
    return colar


def main():
    parser = argparse.ArgumentParser(description="Afina un T5 preentrenado para generar cuentos condicionados por tematica.")
    parser.add_argument("--dataset", default="datos/cuentos/dataset_cuentos.csv")
    parser.add_argument("--salida", default="modelos/texto")
    parser.add_argument("--modelo_base", default="google/mt5-small",
                        help="Modelo preentrenado de Hugging Face. Alternativa mas ligera: mrm8488/spanish-t5-small")
    parser.add_argument("--max_entrada", type=int, default=16)
    parser.add_argument("--max_salida", type=int, default=400)
    parser.add_argument("--lote", type=int, default=8)
    parser.add_argument("--epocas", type=int, default=3)
    parser.add_argument("--lr", type=float, default=0.0003)
    args = parser.parse_args()

    dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
    print("Dispositivo:", dispositivo)
    print("Modelo base:", args.modelo_base)

    tokenizer = AutoTokenizer.from_pretrained(args.modelo_base)
    modelo = AutoModelForSeq2SeqLM.from_pretrained(args.modelo_base).to(dispositivo)

    pares, tematicas = cargar_dataset(args.dataset)
    print(f"Cuentos cargados: {len(pares)}  Tematicas: {len(tematicas)}")

    cargador = DataLoader(
        CuentosDataset(pares), batch_size=args.lote, shuffle=True,
        collate_fn=hacer_colar(tokenizer, args.max_entrada, args.max_salida),
    )

    optimizador = torch.optim.AdamW(modelo.parameters(), lr=args.lr)

    for epoca in range(1, args.epocas + 1):
        modelo.train()
        perdida_total = 0.0
        for lote in cargador:
            lote = {k: v.to(dispositivo) for k, v in lote.items()}
            salida = modelo(**lote)
            perdida = salida.loss

            optimizador.zero_grad()
            perdida.backward()
            torch.nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
            optimizador.step()
            perdida_total += perdida.item()

        print(f"Epoca {epoca}/{args.epocas}  perdida={perdida_total / len(cargador):.4f}")

    os.makedirs(args.salida, exist_ok=True)
    modelo.save_pretrained(args.salida)
    tokenizer.save_pretrained(args.salida)
    with open(os.path.join(args.salida, "tematicas.json"), "w", encoding="utf-8") as f:
        json.dump({"tematicas": tematicas}, f, ensure_ascii=False)

    print("Modelo afinado guardado en", args.salida)


if __name__ == "__main__":
    main()
