#!/usr/bin/env bash
# OPCIONAL (solo si "CUDA disponible: False"):
# Reinstala PyTorch con una build de CUDA 12.6, compatible con drivers NVIDIA
# desde ~R525. Util cuando pip instalo una build de CUDA mas nueva (p.ej. cu130)
# que tu driver no soporta. Ejecutar DENTRO de WSL:  bash entrenamiento/fix_torch.sh
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
source .venv/bin/activate

export TMPDIR="$DIR/.pip-tmp"
mkdir -p "$TMPDIR"

echo "==> Desinstalando torch previo"
pip uninstall -y torch torchvision -q || true

echo "==> Instalando torch para CUDA 12.6"
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126 -q

echo "==> Verificando CUDA"
python - <<'PY'
import torch
print("torch:", torch.__version__)
print("CUDA disponible:", torch.cuda.is_available())
print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A")
PY
