import argparse
import csv
import json
import os

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from PIL import Image

LADO = 64  # entrenamos a 64x64 para que sea manejable


class IlustracionesDataset(Dataset):
    def __init__(self, indice_csv, carpeta_imagenes, edad_a_idx):
        self.carpeta = carpeta_imagenes
        self.edad_a_idx = edad_a_idx
        with open(indice_csv, encoding="utf-8") as f:
            self.filas = [fila for fila in csv.DictReader(f)
                          if fila["edad"] in edad_a_idx]

    def __len__(self):
        return len(self.filas)

    def __getitem__(self, i):
        fila = self.filas[i]
        ruta = os.path.join(self.carpeta, fila["archivo"])
        img = Image.open(ruta).convert("RGB").resize((LADO, LADO))
        tensor = torch.tensor(list(img.getdata()), dtype=torch.float32) / 255.0
        tensor = tensor.view(LADO, LADO, 3).permute(2, 0, 1)
        return tensor, self.edad_a_idx[fila["edad"]]


class VAECondicional(nn.Module):
    def __init__(self, n_edades, dim_z=128, dim_edad=16):
        super().__init__()
        self.embed_edad = nn.Embedding(n_edades, dim_edad)

        self.encoder = nn.Sequential(
            nn.Conv2d(3, 32, 4, 2, 1), nn.ReLU(),   # 32x32
            nn.Conv2d(32, 64, 4, 2, 1), nn.ReLU(),  # 16x16
            nn.Conv2d(64, 128, 4, 2, 1), nn.ReLU(), # 8x8
        )
        self.fc_mu = nn.Linear(128 * 8 * 8, dim_z)
        self.fc_logvar = nn.Linear(128 * 8 * 8, dim_z)

        self.fc_dec = nn.Linear(dim_z + dim_edad, 128 * 8 * 8)
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(128, 64, 4, 2, 1), nn.ReLU(),  # 16x16
            nn.ConvTranspose2d(64, 32, 4, 2, 1), nn.ReLU(),   # 32x32
            nn.ConvTranspose2d(32, 3, 4, 2, 1), nn.Sigmoid(), # 64x64
        )

    def encode(self, x):
        h = self.encoder(x).flatten(1)
        return self.fc_mu(h), self.fc_logvar(h)

    def decode(self, z, edad):
        e = self.embed_edad(edad)
        h = self.fc_dec(torch.cat([z, e], dim=1)).view(-1, 128, 8, 8)
        return self.decoder(h)

    def forward(self, x, edad):
        mu, logvar = self.encode(x)
        std = torch.exp(0.5 * logvar)
        z = mu + std * torch.randn_like(std)
        return self.decode(z, edad), mu, logvar


def perdida_vae(recon, x, mu, logvar):
    recon_err = F.binary_cross_entropy(recon, x, reduction="sum")
    kl = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
    return recon_err + kl


def main():
    parser = argparse.ArgumentParser(description="Entrena nuestro VAE condicional de ilustraciones por edad.")
    parser.add_argument("--indice", default="datos/ilustraciones/dataset_ilustraciones.csv")
    parser.add_argument("--imagenes", default="imagenes", help="Carpeta compartida con todas las imagenes")
    parser.add_argument("--salida", default="modelos")
    parser.add_argument("--lote", type=int, default=64)
    parser.add_argument("--epocas", type=int, default=30)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--dim_z", type=int, default=128)
    args = parser.parse_args()

    dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
    print("Dispositivo:", dispositivo)

    edades = set()
    with open(args.indice, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            edades.add(fila["edad"])
    edad_a_idx = {e: i for i, e in enumerate(sorted(edades))}
    print(f"Rangos de edad: {len(edad_a_idx)}")

    datos = IlustracionesDataset(args.indice, args.imagenes, edad_a_idx)
    print(f"Ilustraciones: {len(datos)}")
    cargador = DataLoader(datos, batch_size=args.lote, shuffle=True)

    modelo = VAECondicional(len(edad_a_idx), dim_z=args.dim_z).to(dispositivo)
    optimizador = torch.optim.Adam(modelo.parameters(), lr=args.lr)

    for epoca in range(1, args.epocas + 1):
        modelo.train()
        perdida_total = 0.0
        for imgs, eds in cargador:
            imgs = imgs.to(dispositivo)
            eds = eds.to(dispositivo)
            recon, mu, logvar = modelo(imgs, eds)
            perdida = perdida_vae(recon, imgs, mu, logvar)
            optimizador.zero_grad()
            perdida.backward()
            optimizador.step()
            perdida_total += perdida.item()
        print(f"Epoca {epoca}/{args.epocas}  perdida={perdida_total / len(datos):.2f}")

    os.makedirs(args.salida, exist_ok=True)
    torch.save({"estado": modelo.state_dict(), "dim_z": args.dim_z}, os.path.join(args.salida, "vae_ilustracion.pt"))
    with open(os.path.join(args.salida, "edades_ilustracion.json"), "w", encoding="utf-8") as f:
        json.dump({"edad_a_idx": edad_a_idx}, f, ensure_ascii=False)
    print("Modelo guardado en", args.salida)


if __name__ == "__main__":
    main()
