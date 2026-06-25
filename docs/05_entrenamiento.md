# 05 · Entrenamiento

Esta parte la hace el encargado de entrenamiento cuando ya tenemos los datasets maestros. Conviene correrla en Google Colab para usar GPU gratis. Primero instala lo necesario:

```bash
pip install -r requirements.txt
```

## Antes de entrenar: armar los datasets maestros

Una vez que todos subieron sus CSV parciales, el coordinador los une y quita duplicados:

```bash
python scripts/fusionar_cuentos.py
python scripts/fusionar_ilustraciones.py
```

Esto deja `datos/cuentos/dataset_cuentos.csv` y `datos/ilustraciones/dataset_ilustraciones.csv`. Para las imágenes también necesitamos la carpeta compartida `imagenes/` con todas las ilustraciones juntas (la del Drive).

## Modelo de cuentos (Llama-3.1 preentrenado, afinado con LoRA por temática)

Para los cuentos no entrenamos desde cero: partimos de un **modelo de lenguaje en español ya preentrenado** (de Hugging Face) y lo **afinamos con LoRA** sobre nuestro dataset. Es un modelo **decoder-only** (Llama-3.1-8B-Instruct), más natural para texto largo libre que un seq2seq, así que los cuentos salen más coherentes. El condicionamiento se hace con **formato chat**: en el prompt va la temática (y opcionalmente el título) y la respuesta es el cuento; la pérdida se calcula solo sobre el cuento. El profe nos permitió usar transformers; aquí no entrenamos un modelo de lenguaje desde cero, partimos de uno ya entrenado y solo lo especializamos.

El flujo completo está en el notebook **`modelos/entrenar_llama_lora_colab.ipynb`** (pensado para Colab Pro+ con GPU A100). Por defecto usa `meta-llama/Llama-3.1-8B-Instruct` con **QLoRA** (4-bit); Llama-3.1 es *gated*, así que necesitas pedir acceso en su página de Hugging Face y definir tu token en la variable de entorno `HF_TOKEN` (o en los *Secrets* de Colab — **nunca lo pegues en el código**). Si no quieres token, el notebook trae como alternativa `Qwen/Qwen3-4B-Instruct-2507` (Apache-2, no requiere token): cámbialo en la celda de configuración.

Pasos: abre el notebook en Colab, ajusta `RUTA_DATASET` a tu `dataset_cuentos_ampliado.csv` en Drive y corre las celdas en orden. Guarda checkpoints a Drive con reanudación automática, y al terminar guarda el **adapter LoRA** (ligero) en `RUTA_MEJOR`. La última celda (Paso 7) genera cuentos de prueba por temática.

Parámetros útiles en la celda de configuración: `MODELO_BASE` (Llama o Qwen), `USAR_QLORA` (4-bit para que el 8B entre en memoria), `TOPE_POR_TEMA` (balanceo por temática para evitar el colapso a una plantilla genérica), `MAX_LEN`, `LOTE`/`ACUMULAR`, `EPOCAS` y `LR`. Como partimos de un modelo ya entrenado, bastan pocas épocas.

Al generar, la **temperatura** controla qué tan arriesgado escribe: baja (0.5) es repetitiva y segura, alta (1.0) es más variada; alrededor de 0.7-0.9 suele dar buen balance. Recuerda usar el **slug exacto** de la temática (p.ej. `princesas_y_castillos`, no "castillos").

> Nota: el pipeline anterior basado en T5/mT5 seq2seq (`scripts/entrenar_texto.py`, `scripts/generar_texto.py` y `entrenamiento/entrenar_texto_local.ipynb`) sigue en el repo como referencia, pero el generador de cuentos vigente es el notebook Llama + LoRA de arriba.

## Modelo de ilustraciones (VAE por temática)

Es un autoencoder variacional condicional: aprende a comprimir las imágenes en un espacio pequeño y a reconstruirlas, condicionado por la temática, de modo que después podemos pedirle imágenes nuevas de un tema. Entrenar (las imágenes a 64x64 para que sea manejable):

```bash
python scripts/entrenar_ilustraciones.py --epocas 30 --imagenes imagenes
```

Guarda `modelos/vae_ilustracion.pt` y `modelos/tematicas_ilustracion.json`. Generar una ilustración:

```bash
python scripts/generar_ilustracion.py --tematica espacio --salida ilustracion.png --cantidad 4
```

## El resultado final: cuento + ilustración juntos

Como los dos modelos se condicionan con la misma temática, basta con pedirles a ambos el mismo tema: el de texto escribe el cuento y el de imagen dibuja la ilustración, los dos del mismo tema. Eso es el cuento ilustrado que entregamos. Y como todas las imágenes se entrenaron con el mismo estilo plano, las ilustraciones salen consistentes entre sí.

## Qué esperar de la calidad

Afinando con LoRA un Llama-3.1 ya entrenado, los cuentos saldrán bastante más coherentes que con el T5 seq2seq anterior, porque es un modelo más grande y decoder-only (mejor para texto largo). Aun así pueden tener algún error o repetición por lo acotado del afinado. Las imágenes del VAE saldrán borrosas. Es lo esperado para este alcance. Lo que demostramos es el sistema completo funcionando: datos bien recolectados, los dos modelos generativos condicionados por temática, generación y análisis.
