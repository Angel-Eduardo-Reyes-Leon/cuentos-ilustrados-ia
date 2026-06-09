# 06 · Post-análisis

Tenemos dos análisis: uno mira **lo que recolectó cada quien** (para revisar que el dataset esté sano) y otro mira **lo que genera el modelo** (para confirmar que inventa y no copia). Los dos usan solo matplotlib y dejan sus resultados en la carpeta `analisis/`.

## Análisis de contribuciones

```bash
python scripts/analizar_contribuciones.py
```

Lee los dos datasets maestros y produce:

- `resumen_por_persona.csv` — por cada quien: cuántos cuentos y cuántas ilustraciones aportó, palabras promedio de sus cuentos, cuántos rangos de edad distintos cubrió y la entropía de esos rangos.
- `reporte.md` — totales del proyecto, vocabulario único, riqueza léxica y la lista de quién va por debajo de la cuota de 600.
- Gráficas: muestras por persona, longitud de los cuentos y muestras por rango de edad.

La **entropía de edades** mide qué tan repartido está el aporte de cada quien entre rangos: si alguien tenía asignado un solo rango su entropía será baja, y eso está bien; lo que vigilamos es el balance global, que no todo el dataset se amontone en un par de edades. La **riqueza léxica** (palabras únicas entre palabras totales) avisa si hay mucha repetición, señal de poca variedad.

Sirve para detectar a tiempo si el dataset se está sesgando, que es justo lo que el profe advirtió que arruina la generalización.

## Análisis de lo generado (control de copia)

```bash
python scripts/analizar_generados.py --generado cuentos_generados.txt
```

Mide qué porcentaje de los grupos de palabras del cuento generado aparece igualito en el dataset de entrenamiento. Si el solapamiento es alto (más del 50%), el modelo está memorizando en vez de inventar, exactamente el problema que el profe mencionó al hablar de datos repetidos. Un modelo sano genera con solapamiento bajo.

Los dos análisis se complementan: si el de contribuciones detecta dataset repetido o sesgado, el de generados lo confirma cuando el modelo empieza a copiar.
