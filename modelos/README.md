# Modelos

Aquí viven los **modelos entrenados** del proyecto (pesados y regenerables, por eso están en `.gitignore` y se comparten por Drive) y los **notebooks** (sí se versionan):

- `entrenar_llama_lora_colab.ipynb` — entrena el generador de **cuentos** (Llama-3.1 + LoRA).
- `indexar_ilustraciones_drive.ipynb` — arma el **dataset maestro de ilustraciones** desde tu Drive (paso previo a entrenar imágenes).
- `entrenar_ilustraciones_lora.ipynb` — entrena el generador de **ilustraciones** (Stable Diffusion 1.5 + LoRA).
- `pipeline_cuento_ilustrado.ipynb` — **pipeline final**: junta los dos modelos y genera un cuento con su ilustración.

> Flujo de imágenes: `indexar_ilustraciones_drive.ipynb` → `entrenar_ilustraciones_lora.ipynb` → (con el de cuentos) `pipeline_cuento_ilustrado.ipynb`.

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

## Indexar ilustraciones — `indexar_ilustraciones_drive.ipynb`

Paso **previo** a entrenar imágenes. Recorre desde Colab todas las subcarpetas de ilustraciones de tu Drive y arma el **dataset maestro** `dataset_ilustraciones.csv` (mismo esquema que `scripts/procesar_ilustraciones.py`). El **Drive es la fuente de verdad**: cada fila apunta a un archivo real (`recolector` = carpeta, `archivo` = nombre real), así el entrenamiento siempre encuentra la imagen.

- Itera sobre los **archivos reales** de cada carpeta, valida (que abra, ≥ 64×64), calcula hash y deduplica.
- La **temática** sale del nombre de la carpeta (prefijo de temática + `MAPEO_CARPETAS`); si la carpeta trae `metadata_ilustraciones.csv`, se usa su descripción.
- Los `parcial_*.csv` de **GitHub** (que clona en el Paso 1) solo **enriquecen descripciones** por hash; no cambian rutas.
- Salida en Drive: `ilustraciones_dataset/dataset_ilustraciones.csv` + `parciales_nuevos/` + `descartados.csv`.

En la corrida del equipo dio **19,753 ilustraciones** únicas repartidas en las **12 temáticas**.

## Generador de ilustraciones — `entrenar_ilustraciones_lora.ipynb`

Notebook que **afina Stable Diffusion 1.5 con LoRA** sobre las ilustraciones del equipo, para que aprenda el estilo visual plano del proyecto, condicionado por temática. Reemplaza al viejo VAE condicional entrenado desde cero (daba imágenes borrosas de 64×64). Lee el `dataset_ilustraciones.csv` del indexador.

- **Modelo base:** `stable-diffusion-v1-5/stable-diffusion-v1-5` (público, no requiere token).
- **LoRA** sobre el UNet (`to_q`, `to_k`, `to_v`, `to_out.0`); VAE y text-encoder congelados. Imágenes a 512×512.
- **Entorno:** Colab con GPU; el equipo lo corrió en **A100 (Pro+)** con **bf16** y lote 4.
- **Diseño clave:** se entrena condicionando **solo por temática** (el LoRA aprende el *estilo* y la temática es el puente con el modelo de cuentos). La *relevancia* a cada cuento se agrega **al generar**, sumando una escena corta al prompt (ver `pipeline_cuento_ilustrado.ipynb`). Así se entrena igual que como se infiere.
- **Checkpoints a Drive con reanudación** automática y **ruta de salida propia** (`ilustraciones_modelo/sd15_estilo_lora`).

### Cómo correrlo

1. Corre primero `indexar_ilustraciones_drive.ipynb` para tener `dataset_ilustraciones.csv` en tu Drive.
2. Abre el notebook en Colab (GPU) y corre el **Paso 0** (instala dependencias y monta Drive).
3. En el **Paso 1 (Configuración)** ajusta `RUTA_DATASET_CSV` y `CARPETA_RAIZ` (deben coincidir **exactamente** con lo que usó el indexador); ahí también están los hiperparámetros.
4. Corre en orden: carga el CSV y verifica que las imágenes existen (Pasos 2-4), prepara el dataset y el prompt `"ilustracion plana a color sobre <tematica>"` (Paso 5), carga SD + LoRA (Paso 6) y entrena (Paso 7). Guarda un **checkpoint a Drive** cada `GUARDAR_CADA_PASOS`; si la sesión se cae, vuelve a correr desde el Paso 0 y **retoma el último checkpoint**.
5. El Paso 9 guarda el **adapter LoRA final** en `RUTA_FINAL` y el Paso 10 compara *solo temática* vs *temática + escena*.

### Configuración (celda Paso 1) — valores con los que se entrenó

| Parámetro | Valor | Notas |
|---|---|---|
| `MODELO_BASE` | `stable-diffusion-v1-5/stable-diffusion-v1-5` | Público, sin token |
| `RANGO_LORA` / `LORA_ALPHA` | `8` / `16` | Más capacidad (≈20k imágenes) |
| `LOTE` / `USAR_BF16` | `4` / `True` | Afinado para A100 |
| `PASOS` | `3000` | Con lote 4 ve ~12k imágenes |
| `LR` / `WARMUP` | `1e-4` / `100` | LR con warmup + decaimiento coseno |
| `GUARDAR_CADA_PASOS` | `250` | Checkpoint a Drive |
| `RUTA_SALIDA` | `…/ilustraciones_modelo/sd15_estilo_lora` | Ruta propia (no pisa el de cuentos) |

## Pipeline final — `pipeline_cuento_ilustrado.ipynb`

Junta los **dos modelos** y genera un **cuento ilustrado** de punta a punta a partir de una temática:

1. **Llama-3.1 + LoRA** escribe el cuento (condicionado por temática).
2. El **mismo Llama** extrae una **escena visual** corta del cuento (una frase).
3. **SD 1.5 + LoRA** genera la ilustración con: **temática** (estilo + puente) **+ escena** (relevancia a esa historia).
4. Muestra cuento + ilustración juntos y, opcional, los guarda a Drive.

- Carga el adapter de cuentos desde `RUTA_LORA_TEXTO` (`cuentos_modelo/llama_lora/mejor`) y el de imágenes desde `RUTA_LORA_IMG` (`ilustraciones_modelo/sd15_estilo_lora/final`).
- **Token:** Llama-3.1 es *gated*; define `HF_TOKEN` en los *Secrets* de Colab (**nunca lo pegues en el código**).
- Pensado para Colab Pro+ (A100): Llama en 4-bit + SD en fp16 caben juntos en memoria.

> Los dos modelos se condicionan con la **misma temática**, así que el cuento y la ilustración del mismo tema se generan emparejados: ese es el cuento ilustrado final.

Detalles del flujo en [`../docs/05_entrenamiento.md`](../docs/05_entrenamiento.md).
