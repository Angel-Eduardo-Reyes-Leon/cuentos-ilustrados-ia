# Cuentos Ilustrados con IA

Este es el repositorio de nuestro proyecto grupal. Aquí vamos a construir, entre los 25, un sistema que **genera cuentos ilustrados con inteligencia artificial**: le decimos un rango de edad y nos devuelve un cuento escrito para esa edad junto con una ilustración que lo acompaña.

No usamos ChatGPT ni ningún generador ya hecho: **entrenamos nuestros propios modelos desde cero**. Por eso lo más importante del proyecto somos nosotros juntando y limpiando los datos. Un modelo solo puede ser tan bueno como los datos que le damos.

---

## ¿Por dónde empiezo? (lee esto primero)

1. Abre **`docs/00_empieza_aqui.md`**. En 5 minutos entiendes de qué va todo y cuál es tu papel.
2. Busca tu nombre en **`coordinacion/asignaciones.csv`**. Ahí está tu rango de edad y de qué fuentes te toca sacar tus cuentos e ilustraciones.
3. Sigue las dos guías de recolección: **`docs/02_recoleccion_cuentos.md`** y **`docs/03_recoleccion_ilustraciones.md`**.

Eso es todo lo que cada quien necesita para empezar. El resto del repo (entrenar el modelo, analizar) lo haremos después, en equipo.

---

## ¿Qué hace cada quien?

**Todos hacemos lo mismo:** cada persona recolecta cuentos **y** ilustraciones para el rango de edad que le tocó. La meta de cada quien es **600 cuentos y 600 ilustraciones**. Entre los 25 eso nos da unos 15,000 de cada uno, que es el mínimo que pidió el profe.

Clasificamos todo por **edad** porque queremos que el modelo aprenda a escribir e ilustrar distinto según para quién es el cuento: no es lo mismo uno para un niño de 4 años que uno para alguien de 16. Los rangos son: `0-5`, `6-8`, `9-11`, `12-14`, `15-17` y `18+`. Incluimos adolescentes y adultos a propósito, para tener variedad y que el modelo no se sesgue, justo como advirtió el profe.

---

## Cómo se arma todo (el flujo completo)

```
Cada quien junta cuentos (.txt) e ilustraciones (imagenes)
                       |
        los pasa por un script que los limpia y estandariza
                       |
            sube su CSV parcial (cuentos y/o ilustraciones)
                       |
   un coordinador une los CSV de todos y quita duplicados
                       |
        tenemos los dos datasets maestros listos
              /                          \
   entrenamos el modelo            analizamos cuanto y
   de cuentos y el de              que tan variado aporto
   ilustraciones                   cada quien
              \                          /
        generamos un cuento + su ilustracion por edad
                       |
       verificamos que el modelo no este copiando
```

---

## Mapa del repositorio (qué es cada cosa y para qué)

- **`docs/`** — todas las guías. Si tienes una duda de "¿cómo hago X?", la respuesta está aquí.
- **`coordinacion/asignaciones.csv`** — quién hace qué. Tu rango de edad y tus fuentes. Lo revisamos antes de empezar para no pisarnos.
- **`scripts/`** — los programas que corremos. Cada uno hace una sola cosa y su nombre lo dice.
- **`plantillas/`** — ejemplos de cómo llenar los CSV de metadatos.
- **`datos/cuentos/parciales/`** y **`datos/ilustraciones/parciales/`** — aquí va el CSV de cada persona. Es lo único de datos que subimos a GitHub.
- **`modelos/`** y **`analisis/`** — aquí caen los modelos entrenados y los reportes. Son pesados, así que **no se suben** (los compartimos por Drive); ver `.gitignore`.

### Para qué sirve cada script

- `procesar_cuentos.py` — convierte tus cuentos `.txt` en tu CSV parcial limpio. Resultado: `datos/cuentos/parciales/parcial_TU_USUARIO.csv`.
- `procesar_ilustraciones.py` — indexa tus imágenes con su edad y un hash. Resultado: tu CSV parcial de ilustraciones.
- `validar_csv.py` — revisa que tu CSV de cuentos esté bien antes de subirlo.
- `fusionar_cuentos.py` / `fusionar_ilustraciones.py` — (coordinador) unen los CSV de todos y quitan duplicados. Resultado: los datasets maestros.
- `entrenar_texto.py` / `generar_texto.py` — entrenan el modelo de cuentos y generan cuentos por edad.
- `entrenar_ilustraciones.py` / `generar_ilustracion.py` — entrenan el modelo de imágenes y generan ilustraciones por edad.
- `analizar_contribuciones.py` — saca estadísticas y gráficas de cuánto y qué tan variado aportó cada quien.
- `analizar_generados.py` — mide si el modelo está inventando o solo copiando lo que ya vio.

---

## El modelo, en corto

El de cuentos es una **red recurrente (LSTM) que lee y escribe carácter por carácter, condicionada por la edad**. Elegimos LSTM y no un transformer porque el profe pidió no usar GPT, y un transformer de generación es justo la arquitectura de GPT. El de ilustraciones es un **VAE condicional**, también por edad. La edad es el puente entre los dos: como ambos se condicionan con la misma etiqueta, el cuento y la ilustración salen pensados para la misma audiencia.

Detalles para entrenar en `docs/05_entrenamiento.md`.

---

## Requisitos

Python 3.8 o más. Para recolectar cuentos no necesitas instalar nada; para todo lo demás:

```
pip install -r requirements.txt
```

El entrenamiento completo conviene correrlo en Google Colab (GPU gratis).
