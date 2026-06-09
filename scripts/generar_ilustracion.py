import argparse
import json
import os

import torch
from PIL import Image

from entrenar_ilustraciones import VAECondicional, LADO


def cargar(carpeta):
    with open(os.path.join(carpeta, "edades_ilustracion.json"), encoding="utf-8") as f:
        edad_a_idx = json.load(f)["edad_a_idx"]
    estado = torch.load(os.path.join(carpeta, "vae_ilustracion.pt"), map_location="cpu")
    modelo = VAECondicional(len(edad_a_idx), dim_z=estado["dim_z"])
    modelo.load_state_dict(estado["estado"])
    modelo.eval()
    return modelo, edad_a_idx


def main():
    parser = argparse.ArgumentParser(description="Genera una ilustracion para un rango de edad.")
    parser.add_argument("--modelo", default="modelos")
    parser.add_argument("--edad", required=True, help="Rango de edad, ej. 6-8")
    parser.add_argument("--salida", default="ilustracion.png")
    parser.add_argument("--cantidad", type=int, default=1)
    args = parser.parse_args()

    modelo, edad_a_idx = cargar(args.modelo)
    if args.edad not in edad_a_idx:
        raise ValueError(f"Edad '{args.edad}' no existe. Disponibles: {sorted(edad_a_idx)}")

    dim_z = modelo.fc_mu.out_features
    with torch.no_grad():
        for i in range(args.cantidad):
            z = torch.randn(1, dim_z)
            edad = torch.tensor([edad_a_idx[args.edad]])
            img = modelo.decode(z, edad)[0]
            arr = (img.permute(1, 2, 0).numpy() * 255).astype("uint8")
            ruta = args.salida if args.cantidad == 1 else args.salida.replace(".png", f"_{i + 1}.png")
            Image.fromarray(arr, "RGB").save(ruta)
            print("Guardada", ruta)


if __name__ == "__main__":
    main()
