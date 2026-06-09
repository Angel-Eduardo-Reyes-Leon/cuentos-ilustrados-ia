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

## Modelo de cuentos (LSTM por edad)

Es una red recurrente que aprende a escribir carácter por carácter. En cada paso recibe el carácter actual más un vector que representa la edad, y así aprende a escribir distinto según el rango. Entrenar:

```bash
python scripts/entrenar_texto.py --epocas 30
```

Parámetros útiles: `--lote` (bájalo si te falta memoria), `--dim_oculto` (más grande = más capacidad), `--capas`, `--lr`. Al terminar guarda `modelos/generador_texto.pt` y `modelos/vocabularios.json`. Generar un cuento:

```bash
python scripts/generar_texto.py --edad 6-8 --temperatura 0.8 --cantidad 3 --guardar cuentos_generados.txt
```

La `--temperatura` controla qué tan arriesgado escribe: baja (0.5) es repetitivo y seguro, alta (1.0) es caótico; entre 0.7 y 0.9 suele ser el mejor balance.

## Modelo de ilustraciones (VAE por edad)

Es un autoencoder variacional condicional: aprende a comprimir las imágenes en un espacio pequeño y a reconstruirlas, condicionado por la edad, de modo que después podemos pedirle imágenes nuevas para un rango. Entrenar (las imágenes a 64x64 para que sea manejable):

```bash
python scripts/entrenar_ilustraciones.py --epocas 30 --imagenes imagenes
```

Guarda `modelos/vae_ilustracion.pt` y `modelos/edades_ilustracion.json`. Generar una ilustración:

```bash
python scripts/generar_ilustracion.py --edad 6-8 --salida ilustracion.png --cantidad 4
```

## El resultado final: cuento + ilustración juntos

Como los dos modelos se condicionan con la misma etiqueta de edad, basta con pedirles a ambos el mismo rango: el de texto escribe el cuento y el de imagen dibuja la ilustración, las dos para la misma audiencia. Eso es el cuento ilustrado que entregamos.

## Qué esperar de la calidad

Entrenando desde cero con nuestro dataset, los cuentos saldrán cortos y con errores y las imágenes borrosas y abstractas. Es lo esperado para este alcance. Lo que demostramos es el sistema completo funcionando: datos bien recolectados, dos modelos generativos condicionados por edad, generación y análisis.
