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

## Modelo de cuentos (T5 preentrenado, afinado por temática)

Para los cuentos no entrenamos desde cero: partimos de un **Transformer T5 en español ya preentrenado** (de Hugging Face) y lo **afinamos** con nuestro dataset. T5 es seq2seq, así que el condicionamiento es natural: la entrada del encoder es la temática (un texto como "escribe un cuento sobre espacio") y la salida del decoder es el cuento. El profe nos permitió usar transformers; aquí no implementamos un GPT, usamos un transformer ya entrenado y solo lo especializamos.

Por defecto usamos `google/mt5-small` (multilingüe, incluye español). Una alternativa más ligera y específica de español es `mrm8488/spanish-t5-small`; se cambia con `--modelo_base`. Esto descarga el modelo de Hugging Face la primera vez, así que conviene correrlo en Colab con GPU. Entrenar:

```bash
python scripts/entrenar_texto.py --epocas 3
```

Parámetros útiles: `--modelo_base` (qué T5 usar), `--lote` (bájalo si te falta memoria), `--max_salida` (largo máximo del cuento en tokens), `--epocas` y `--lr`. Como partimos de un modelo ya entrenado, bastan pocas épocas. Al terminar guarda el modelo afinado en la carpeta `modelos/texto/`. Generar un cuento:

```bash
python scripts/generar_texto.py --tematica espacio --temperatura 0.9 --cantidad 3 --guardar cuentos_generados.txt
```

La `--temperatura` controla qué tan arriesgado escribe: baja (0.5) es repetitivo y seguro, alta (1.0) es más variado; alrededor de 0.9 suele dar buen balance.

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

Afinando un T5 ya entrenado, los cuentos saldrán más coherentes que si entrenáramos desde cero, aunque seguirán siendo cortos y con algún error por el tamaño del modelo y lo acotado del afinado. Las imágenes del VAE saldrán borrosas. Es lo esperado para este alcance. Lo que demostramos es el sistema completo funcionando: datos bien recolectados, los dos modelos generativos condicionados por temática, generación y análisis.
