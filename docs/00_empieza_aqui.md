# 00 · Empieza aquí

Bienvenido al proyecto. Esta guía es para que en cinco minutos entiendas qué estamos haciendo, por qué, y qué te toca a ti. Si solo vas a leer un archivo, que sea este.

## Contexto del proyecto

Este es el proyecto grupal de la materia y **vale el 50% de la calificación**, así que pesa mucho. Además del código y los datos, hay una parte de **exposición**: tenemos que presentar el tema, así que avisamos con tiempo cuando nos toque. Lo dejamos con casi dos meses y medio de anticipación porque es pesado y la recolección de datos toma tiempo.

Una advertencia que hizo el profe: cuidado con la **complejidad computacional**. Mientras más largos sean los textos (novelas enteras) y más grandes las imágenes, más caro y lento es entrenar. Por eso mantenemos los cuentos en un rango razonable de longitud y las imágenes chicas (64x64).

## Qué estamos construyendo

Un sistema que genera cuentos ilustrados. Le pedimos un cuento de cierta temática y nos devuelve dos cosas: el texto del cuento y una imagen que lo ilustra, las dos de la misma temática. Para lograrlo afinamos con LoRA dos modelos ya preentrenados sobre nuestros datos: el de cuentos a partir de un modelo de lenguaje en español (Llama-3.1) y el de ilustraciones a partir de Stable Diffusion (no es ChatGPT ni usamos ningún servicio externo). En los dos casos el trabajo y los datos son nuestros.

## Por qué los datos son lo más importante

Los dos modelos parten de una base ya preentrenada, pero el estilo lo aprenden solo de **nuestros** ejemplos: el de ilustraciones afina Stable Diffusion para que dibuje con el estilo plano de nuestras imágenes, y el de cuentos afina un modelo que ya sabe español para que narre como queremos. En los dos casos, si les damos pocos ejemplos, o repetidos, o de mala calidad, el resultado sale malo. Por eso el trabajo grande de todos no es programar, sino conseguir muchos cuentos e imágenes, variados y bien etiquetados. Esa es la parte que el profe dijo que es la más difícil, y tiene razón: lo difícil es coordinarnos para no juntar lo mismo.

## Cómo nos repartimos el trabajo

Lo hacemos por igual: todos hacemos lo mismo. Cada persona recolecta cuentos y también ilustraciones, en la misma cantidad (1,000 de cada uno). No hay un grupo que solo busca texto y otro que solo busca imágenes; cada quien aporta de las dos cosas.

## Por qué clasificamos por temática

A cada cuento e imagen le ponemos una etiqueta de temática: de qué trata. La lista es cerrada: `espacio`, `animales`, `piratas`, `magia_y_brujas`, `monstruos_y_criaturas`, `princesas_y_castillos`, `naturaleza_y_bosques`, `mar_y_oceano`, `robots_y_tecnologia`, `dinosaurios_y_prehistoria`, `fantasmas_y_misterio`, `heroes_y_aventuras`. Esa etiqueta es lo que después le dice al modelo qué cuento escribir y qué imagen dibujar, y es lo que conecta los dos modelos: usan la misma temática, así el cuento y el dibujo quedan del mismo tema.

## El estilo de las ilustraciones es común para todos

Aunque cada quien tiene una temática distinta, **todas las ilustraciones comparten un mismo estilo visual**: ilustración digital plana, a color, estilo caricatura/animación. Esto lo pidió el profe (definir un tipo de ilustración) y además ayuda al modelo a aprender. El detalle del estilo está en `docs/03`.

## Qué te toca a ti

1. Busca tu nombre en `coordinacion/asignaciones.csv`. Verás tu temática y de qué fuentes te toca sacar cuentos e imágenes. Te asignamos fuentes distintas a las de tus compañeros para que no junten lo mismo.
2. Reúne 1,000 cuentos siguiendo `docs/02_recoleccion_cuentos.md`.
3. Reúne 1,000 ilustraciones siguiendo `docs/03_recoleccion_ilustraciones.md`.
4. Pasa ambas cosas por su script, que te deja un archivo CSV limpio, y súbelo al repo.

Eso es tu parte. Cuando todos terminemos, unimos lo de cada quien, entrenamos los modelos y analizamos resultados (eso lo explican `docs/05` y `docs/06`).

## Una expectativa honesta

Aun afinando con LoRA modelos ya entrenados (Llama-3.1 para los cuentos y Stable Diffusion para las imágenes), los resultados serán modestos: cuentos cortos y a veces con errores, e ilustraciones que pueden variar en calidad y consistencia. Eso es normal y está bien: el proyecto se califica por armar todo el sistema funcionando de punta a punta y por la coordinación de los datos, no por competir con las IA comerciales que se entrenaron con millones de ejemplos.
