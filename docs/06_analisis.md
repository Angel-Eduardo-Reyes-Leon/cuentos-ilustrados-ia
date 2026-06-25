# 06 · Post-análisis

Tenemos dos análisis: uno mira lo que recolectó cada quien (para revisar que el dataset esté sano) y otro mira lo que genera el modelo (para confirmar que inventa y no copia). Los dos usan solo matplotlib y dejan sus resultados en la carpeta `analisis/`.

## Análisis de contribuciones

```bash
python scripts/analizar_contribuciones.py
```

Lee los dos datasets maestros y produce:

- `resumen_por_persona.csv` — por cada quien: cuántos cuentos y cuántas ilustraciones aportó, palabras promedio de sus cuentos, cuántas temáticas distintas cubrió y la entropía de esas temáticas.
- `reporte.md` — totales del proyecto, vocabulario único, riqueza léxica y la lista de quién va por debajo de la cuota de 1,000.
- Gráficas: muestras por persona, longitud de los cuentos y muestras por temática.

La entropía de temáticas mide qué tan repartido está el aporte entre temas; sirve para vigilar que el dataset no se amontone en un par de temáticas. La riqueza léxica (palabras únicas entre palabras totales) avisa si hay mucha repetición, señal de poca variedad. Las dos cosas nos ayudan a detectar a tiempo si el dataset se está sesgando, que es lo que arruina la generalización.

## Análisis de lo generado (control de copia)

```bash
python scripts/analizar_generados.py --generado cuentos_generados.txt
```

Guarda en `cuentos_generados.txt` los cuentos que produce el notebook del generador (`modelos/entrenar_llama_lora_colab.ipynb`, Paso 7), separados por una línea `=====`, y pásalo a este script.

Mide qué porcentaje de los grupos de palabras del cuento generado aparece igualito en el dataset de entrenamiento. Si el solapamiento es alto (más del 50%), el modelo está memorizando en vez de inventar, exactamente el problema que el profe mencionó al hablar de datos repetidos. Un modelo sano genera con solapamiento bajo.

Los dos análisis se complementan: si el de contribuciones detecta dataset repetido o sesgado, el de generados lo confirma cuando el modelo empieza a copiar.
