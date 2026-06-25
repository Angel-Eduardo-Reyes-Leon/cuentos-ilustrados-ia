# Modelos

Aquí viven los **modelos entrenados** del proyecto (pesados y regenerables, por eso están en `.gitignore` y se comparten por Drive) y el **notebook del generador de cuentos**, que sí se versiona.

## Generador de cuentos — `entrenar_llama_lora_colab.ipynb`

Notebook que **afina un modelo de lenguaje en español ya preentrenado con LoRA** para escribir cuentos infantiles condicionados por temática (y opcionalmente título). Es la forma vigente de entrenar y generar texto en el proyecto (reemplaza al viejo pipeline T5/mT5 seq2seq).

- **Arquitectura:** decoder-only + **LoRA** (PEFT), formato chat (system + user → assistant). La pérdida se calcula solo sobre el cuento.
- **Modelo base:** `meta-llama/Llama-3.1-8B-Instruct` con **QLoRA** (4-bit). Alternativa sin token: `Qwen/Qwen3-4B-Instruct-2507` (Apache-2).
- **Entorno:** pensado para **Google Colab Pro+ con GPU A100**.

### Cómo correrlo

1. Abre el notebook en Colab (Runtime con GPU A100).
2. **Token de Hugging Face:** Llama-3.1 es *gated*. Pide acceso en su página de HF, crea un token y defínelo como variable de entorno / *Secret* de Colab:
   ```python
   import os; os.environ["HF_TOKEN"] = "hf_..."   # o usa los Secrets de Colab
   ```
   **Nunca pegues el token en el código.** Si usas el modelo Qwen no hace falta token.
3. Sube `dataset_cuentos_ampliado.csv` a tu Drive y ajusta `RUTA_DATASET` en la celda de configuración (Paso 1).
4. Corre las celdas en orden. Guarda checkpoints a Drive con reanudación automática; si la sesión se cae, vuelve a correr desde el Paso 0 y retoma el último checkpoint.

### Configuración (celda Paso 1)

| Parámetro | Default | Notas |
|---|---|---|
| `MODELO_BASE` | `meta-llama/Llama-3.1-8B-Instruct` | Alt. sin token: `Qwen/Qwen3-4B-Instruct-2507` |
| `USAR_QLORA` | `True` | 4-bit para que el 8B entre en memoria |
| `TOPE_POR_TEMA` | `500` | Balanceo por temática (evita el colapso a una plantilla genérica) |
| `MAX_LEN` | `1280` | Tokens totales (prompt + cuento) |
| `LOTE` / `ACUMULAR` | `4` / `4` | Lote efectivo = 16 |
| `EPOCAS` | `3` | Pocas bastan al partir de un modelo preentrenado |
| `LR` | `2e-4` | Típico para LoRA |

### Salida y generación

- El **adapter LoRA** (ligero) se guarda en `RUTA_MEJOR` (en Drive). Para inferir se carga el modelo base + el adapter (`PeftModel.from_pretrained`).
- La última celda (Paso 7) genera cuentos de prueba por temática. Usa el **slug exacto** de la temática (p.ej. `princesas_y_castillos`, no "castillos").

Detalles del flujo en [`../docs/05_entrenamiento.md`](../docs/05_entrenamiento.md).
