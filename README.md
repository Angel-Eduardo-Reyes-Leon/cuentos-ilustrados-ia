# Cuentos Ilustrados con IA

Este es el repositorio de nuestro proyecto grupal. Aquí vamos a construir, entre los 25, un sistema que **genera cuentos ilustrados con inteligencia artificial**: le decimos una temática (por ejemplo, espacio) y nos devuelve un cuento de esa temática junto con una ilustración que lo acompaña.

No usamos ChatGPT. El modelo de **ilustraciones lo entrenamos desde cero**, y el de **cuentos parte de un transformer en español ya entrenado (un T5, que no es un GPT) que nosotros afinamos** con nuestro dataset. En los dos casos los datos y el trabajo son nuestros, y un modelo solo puede ser tan bueno como los datos que le damos: por eso recolectar y limpiar bien los cuentos e ilustraciones sigue siendo lo más importante.

---

## ¿Por dónde empiezo? (lee esto primero)

1. Abre **`docs/00_empieza_aqui.md`**. En 5 minutos entiendes de qué va todo y cuál es tu papel.
2. Busca tu nombre en **`coordinacion/asignaciones.csv`**. Ahí está tu temática y de qué fuentes te toca sacar tus cuentos e ilustraciones.
3. Sigue las dos guías de recolección: **`docs/02_recoleccion_cuentos.md`** y **`docs/03_recoleccion_ilustraciones.md`**.

Eso es todo lo que cada quien necesita para empezar. El resto del repo (entrenar el modelo, analizar) lo haremos después, en equipo.

---

## ¿Qué hace cada quien?

**Todos hacemos lo mismo y en partes iguales.** No hay un equipo solo de cuentos y otro solo de imágenes: cada persona recolecta cuentos **y** ilustraciones por igual. La meta de cada quien es **1,000 cuentos y 1,000 ilustraciones**. Entre los 25 eso nos da unos 25,000 de cada uno, holgadamente por encima de los 15,000 que pidió el profe como mínimo (y él mismo dijo que probablemente harían falta más, así que apuntamos alto).

Clasificamos todo por **temática**: el cuento trata de algo concreto (espacio, piratas, animales…). La temática es lo que después le decimos al modelo para que genere, y es lo que conecta los dos modelos: tanto el cuento como la ilustración se condicionan con la misma temática para que peguen entre sí.

Temáticas (lista cerrada): `espacio`, `animales`, `piratas`, `magia_y_brujas`, `monstruos_y_criaturas`, `princesas_y_castillos`, `naturaleza_y_bosques`, `mar_y_oceano`, `robots_y_tecnologia`, `dinosaurios_y_prehistoria`, `fantasmas_y_misterio`, `heroes_y_aventuras`.

---

## Cómo se arma todo (el flujo completo)

```
Cada quien junta cuentos (.txt) e ilustraciones (imagenes) por igual
                       |
        los pasa por un script que los limpia y estandariza
                       |
            sube su CSV parcial (de cuentos y de ilustraciones)
                       |
   un coordinador une los CSV de todos y quita duplicados
                       |
        tenemos los dos datasets maestros listos
              /                          \
   entrenamos el modelo            analizamos cuanto y
   de cuentos y el de              que tan variado aporto
   ilustraciones                   cada quien
              \                          /
      generamos un cuento + su ilustracion de la misma tematica
                       |
       verificamos que el modelo no este copiando
```

---

## Mapa del repositorio (qué es cada cosa y para qué)

- **`docs/`** — todas las guías. Si tienes una duda de "¿cómo hago X?", la respuesta está aquí.
- **`coordinacion/asignaciones.csv`** — quién hace qué. Tu temática y tus fuentes. Lo revisamos antes de empezar para no pisarnos.
- **`scripts/`** — los programas que corremos. Cada uno hace una sola cosa y su nombre lo dice.
- **`plantillas/`** — ejemplos de cómo llenar los CSV de metadatos.
- **`datos/cuentos/parciales/`** y **`datos/ilustraciones/parciales/`** — aquí va el CSV de cada persona. Es lo único de datos que subimos a GitHub.
- **`modelos/`** y **`analisis/`** — aquí caen los modelos entrenados y los reportes. Son pesados, así que **no se suben** (los compartimos por Drive); ver `.gitignore`.

### Para qué sirve cada script

- `procesar_cuentos.py` — convierte tus cuentos `.txt` en tu CSV parcial limpio. Resultado: `datos/cuentos/parciales/parcial_TU_USUARIO.csv`.
- `procesar_ilustraciones.py` — indexa tus imágenes con su temática y un hash. Resultado: tu CSV parcial de ilustraciones.
- `validar_csv.py` — revisa que tu CSV de cuentos esté bien antes de subirlo.
- `fusionar_cuentos.py` / `fusionar_ilustraciones.py` — (coordinador) unen los CSV de todos y quitan duplicados. Resultado: los datasets maestros.
- `entrenar_texto.py` / `generar_texto.py` — entrenan el modelo de cuentos y generan cuentos por temática.
- `entrenar_ilustraciones.py` / `generar_ilustracion.py` — entrenan el modelo de imágenes y generan ilustraciones por temática.
- `analizar_contribuciones.py` — saca estadísticas y gráficas de cuánto y qué tan variado aportó cada quien.
- `analizar_generados.py` — mide si el modelo está inventando o solo copiando lo que ya vio.

---

## El modelo, en corto

El de cuentos es un **Transformer T5 en español ya preentrenado, que nosotros afinamos (fine-tuning)** con nuestro dataset, condicionado por la temática. El profe nos autorizó a usar transformers; no implementamos un GPT, partimos de un modelo que ya sabe español y lo especializamos en generar cuentos. Es seq2seq: le damos la temática como entrada y produce el cuento como salida. El de ilustraciones sí es nuestro **VAE condicional entrenado desde cero**, también por temática. La temática es el puente entre los dos: como ambos se condicionan con la misma etiqueta, el cuento y la ilustración salen del mismo tema.

Detalles para entrenar en `docs/05_entrenamiento.md`.

---

## Requisitos

Python 3.8 o más. Para recolectar cuentos no necesitas instalar nada; para todo lo demás:

```
pip install -r requirements.txt
```

El entrenamiento completo conviene correrlo en Google Colab (GPU gratis).
