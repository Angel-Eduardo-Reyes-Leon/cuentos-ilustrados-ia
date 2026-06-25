# Entrenamiento del modelo de texto — T5 local (pipeline heredado)

> **El generador de cuentos vigente del proyecto es el notebook Llama-3.1 + LoRA: [`../modelos/entrenar_llama_lora_colab.ipynb`](../modelos/entrenar_llama_lora_colab.ipynb)** (Colab + GPU, decoder-only, da cuentos más coherentes). Esta carpeta documenta el **pipeline anterior basado en T5/mT5 seq2seq**, que se conserva como referencia y para entrenar en local sin Colab. Si solo quieres el modelo actual, ve directo al notebook de Llama.

Esta carpeta es autocontenida: tiene todo lo necesario para **afinar (fine-tuning) el modelo T5 de cuentos** en tu propia máquina con GPU NVIDIA, usando WSL (Windows Subsystem for Linux). No modifica nada del resto del repo.

El modelo de esta carpeta es un **T5 en español ya preentrenado** (de Hugging Face) que se especializa con nuestro dataset. Es seq2seq: entra `"escribe un cuento sobre <tematica>"` y sale el cuento.

## Contenido

| Archivo | Para qué |
|---|---|
| `entrenar_texto_local.ipynb` | Notebook con todo el flujo: dataset → entrenamiento → generación |
| `requirements.txt` | Dependencias de Python |
| `setup_wsl.sh` | Crea el entorno virtual e instala todo |
| `fix_torch.sh` | (Opcional) arregla PyTorch si tu driver es viejo para CUDA |

## Requisitos previos

- **WSL2 con Ubuntu** y **driver NVIDIA actualizado en Windows** (no instales drivers dentro de WSL).
- Verifica que la GPU se ve desde WSL:
  ```bash
  nvidia-smi
  ```

## Pasos

Desde una terminal de **WSL**, en la raíz del repo clonado:

```bash
# 1. Crear entorno e instalar dependencias
bash entrenamiento/setup_wsl.sh

# 2. Activar el entorno
source entrenamiento/.venv/bin/activate

# 3. Abrir el notebook
jupyter notebook entrenamiento/entrenar_texto_local.ipynb
```

O ábrelo en **VS Code** (extensión WSL + Jupyter) y selecciona el kernel `entrenamiento/.venv`.

Corre las celdas en orden. La celda **Paso 3** construye el dataset maestro a partir de los CSV parciales del repo (`datos/cuentos/parciales/`); si ya existe, no lo regenera. El modelo afinado se guarda en `modelos/texto/` (esa carpeta está en `.gitignore`, no se sube).

## Configuración (celda Paso 2 del notebook)

| Parámetro | Default | Notas |
|---|---|---|
| `MODELO_BASE` | `google/mt5-base` | Alt: `google/mt5-small` (más rápido), `google/mt5-large` (mejor, más pesado) |
| `LOTE` | 16 | Batch. Bájalo si te falta VRAM; súbelo si te sobra |
| `EPOCAS` | 3 | Pocas bastan al partir de un modelo preentrenado |
| `USAR_BF16` | True | Usa bf16 si la GPU lo soporta; si no, cae a fp32 solo |
| `LIMITE_EJEMPLOS` | None | Pon `2000` para una prueba rápida primero |

### Guía rápida por GPU

- **RTX 4090 / 30xx-40xx (≥16 GB, soportan bf16):** valores por defecto (`mt5-base`, bf16, `LOTE=16`). Para máxima calidad: `mt5-large` + `GRADIENT_CHECKPOINTING=True`.
- **RTX 2070 / GPUs Turing (8 GB, sin bf16):** usa `MODELO_BASE="google/mt5-small"` y `LOTE=8`. El notebook detecta que no hay bf16 y entrena en fp32 automáticamente.

## Generar cuentos ya entrenado

El **Paso 8** del notebook genera un cuento de prueba. También puedes usar el script del repo:

```bash
python scripts/generar_texto.py --tematica espacio --temperatura 0.9 --cantidad 3
```

## Solución de problemas

- **`CUDA disponible: False`** aunque `nvidia-smi` funciona → tu driver es más viejo que la build de CUDA que instaló pip. Corre:
  ```bash
  bash entrenamiento/fix_torch.sh
  ```
- **`No space left on device`** al instalar torch → `/tmp` en WSL es un tmpfs chico; `setup_wsl.sh` ya redirige `TMPDIR` al disco para evitarlo.
- **`PicklingError` / `forkserver`** al iniciar el entrenamiento → es de Python 3.14 con `DataLoader`. El notebook ya usa `num_workers=0` para evitarlo.
- **`NaN` en la pérdida** → no uses fp16 con T5/mT5 (son inestables). Usa bf16 (GPU moderna) o fp32. El notebook ya lo maneja.
