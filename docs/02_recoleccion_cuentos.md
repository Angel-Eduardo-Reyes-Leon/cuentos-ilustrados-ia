# 02 · Recolección de cuentos

Aquí dejas tus cuentos listos para el modelo. Al terminar tendrás un archivo CSV limpio que subirás al repo. Tu meta son 600 cuentos del rango de edad que te tocó.

## 1. Confirma tu asignación

Abre `coordinacion/asignaciones.csv`, busca tu nombre y anota dos cosas: tu **rango de edad** y tu **fuente de cuentos**. Solo trabajas esa fuente, para no juntar lo mismo que tus compañeros del mismo rango. De dónde sacar el material de cada fuente está en `docs/04_fuentes.md`.

## 2. Prepara tu carpeta

Crea una carpeta llamada `mis_cuentos/` en la raíz del repo. Esta carpeta no se sube (está en `.gitignore`), es solo tu espacio de trabajo. Guarda **un cuento por archivo `.txt`**, en español y en texto plano:

```
mis_cuentos/
├── cuento_001.txt
├── cuento_002.txt
└── ...
```

Al guardar cada cuento, déjalo limpio: quita índices, prólogos, números de página y notas del editor. Solo el cuento. Si una página trae varios cuentos, sepáralos en archivos distintos.

## 3. Llena tu tabla de metadatos

Copia `plantillas/metadata_cuentos_ejemplo.csv` a la raíz del repo y renómbralo `metadata_cuentos.csv`. Pon un renglón por cada cuento, con el rango de edad para el que es:

```
archivo,titulo,autor,edad,fuente
cuento_001.txt,El patito feo,Hans Christian Andersen,0-5,Wikisource ES
cuento_002.txt,La pata de mono,W. W. Jacobs,15-17,Project Gutenberg
```

La columna `edad` debe ser uno de: `0-5`, `6-8`, `9-11`, `12-14`, `15-17`, `18+`. Si no sabes el autor, pon `Anonimo`.

## 4. Genera tu CSV (el paso que hace la magia)

```bash
python scripts/procesar_cuentos.py --usuario TU_USUARIO
```

(Tu usuario es el que aparece en `asignaciones.csv`, por ejemplo `angel_reyes`.) El script automáticamente limpia el texto, cuenta las palabras y descarta lo demasiado corto o largo, le calcula una huella para detectar repetidos, y arma tu archivo en `datos/cuentos/parciales/parcial_TU_USUARIO.csv`. En la consola te dice si descartó algo y por qué.

**Qué obtienes:** ese CSV es tu aporte. Tiene una fila por cuento con título, autor, edad, número de palabras, fuente, tu nombre, la huella y el texto completo.

## 5. Revisa y sube

```bash
python scripts/validar_csv.py datos/cuentos/parciales/parcial_TU_USUARIO.csv
```

Si no marca errores, sube **solo ese CSV** al repo (los `.txt` no se suben). El ciclo de Git es: `git add .`, `git commit -m "cuentos de TU_USUARIO"`, `git push`.

## Errores comunes

- Dejar basura del original (índice, pies de página): el modelo aprende ese ruido. Limpia antes.
- Meter varias versiones del mismo cuento: crea sesgo. Si ves "Pinocho" tres veces, quédate con una.
- Mezclar idiomas: todo en español.
