#!/usr/bin/env bash
# Configura el entorno para entrenar el modelo de texto. Ejecutar DENTRO de WSL:
#   bash entrenamiento/setup_wsl.sh
set -e

# Carpeta entrenamiento/ (donde vive este script)
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "==> Creando entorno virtual en $DIR/.venv"
python3 -m venv .venv
source .venv/bin/activate

echo "==> Actualizando pip"
pip install --upgrade pip -q

# En WSL /tmp suele ser un tmpfs pequeno (en RAM); usamos disco para descomprimir
# wheels grandes (torch pesa varios GB) y evitar 'No space left on device'.
export TMPDIR="$DIR/.pip-tmp"
mkdir -p "$TMPDIR"

echo "==> Instalando dependencias (incluye PyTorch con CUDA)"
pip install -r requirements.txt -q

echo "==> Verificando CUDA"
python - <<'PY'
import torch
print("torch:", torch.__version__)
print("CUDA disponible:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
    print("Soporta bf16:", torch.cuda.is_bf16_supported())
else:
    print("AVISO: CUDA no disponible. Si tu driver es viejo para esta build de torch,")
    print("       corre:  bash entrenamiento/fix_torch.sh")
PY

echo ""
echo "==> LISTO. Para usar el entorno:"
echo "    source $DIR/.venv/bin/activate"
echo "    jupyter notebook entrenamiento/entrenar_texto_local.ipynb"
