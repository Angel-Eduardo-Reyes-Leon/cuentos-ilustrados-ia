# 03 · Recolección de ilustraciones

Igual que con los cuentos, aquí dejas tus imágenes listas y subes un CSV. Tu meta son 1,000 ilustraciones de la temática que te tocó. Recolectamos cuentos e ilustraciones por igual, así que esta parte es tan importante como la de texto.

## El estilo es común para todos (esto es importante)

El profe pidió que definamos un tipo de ilustración. Para todo el proyecto usamos **un mismo estilo visual**, sin importar la temática de cada quien:

- **Tipo:** ilustración digital plana, a color, estilo caricatura/animación (tipo clipart). Elegimos este estilo porque es el más abundante y fácil de encontrar gratis (Openclipart, Pixabay, Wikimedia Commons) y porque es un estilo coherente que el modelo (Stable Diffusion + LoRA) aprende bien. Nada de fotografías, ni pinturas al óleo, ni renders 3D realistas, ni grabados antiguos.
- **Marco / formato:** imagen preferentemente cuadrada, con el sujeto centrado y un fondo simple o de un solo color. Sin texto encima, sin marcas de agua, sin collage de varias viñetas.
- **Complejidad:** baja o media. Un personaje o una escena clara, formas simples y colores planos. Evita ilustraciones súper recargadas, porque hacen más difícil que el modelo aprenda un estilo limpio.

Mantener este estilo común es lo que hace que el modelo de imágenes aprenda algo coherente en vez de una mezcla confusa.

## 1. Confirma tu asignación

En `coordinacion/asignaciones.csv` busca tu **temática** y tu **fuente de ilustraciones** (es distinta a la de tus compañeros, para no repetir). Las fuentes están en `docs/04_fuentes.md`. Usa solo imágenes libres o de dominio público.

## 2. Prepara tu carpeta

Crea una carpeta `mis_ilustraciones/` en la raíz del repo (tampoco se sube). Guarda ahí tus imágenes. Sirven `.png`, `.jpg` o `.jpeg`, y deben medir al menos 64x64 píxeles.

```
mis_ilustraciones/
├── img_001.png
├── img_002.png
└── ...
```

Las imágenes deben ser de tu temática y respetar el estilo común descrito arriba.

## 3. Llena tu tabla de metadatos

Copia `plantillas/metadata_ilustraciones_ejemplo.csv` a la raíz como `metadata_ilustraciones.csv`, un renglón por imagen:

```
archivo,tematica,descripcion,fuente
img_001.png,espacio,cohete y planetas a color estilo plano,Openclipart
img_002.png,piratas,barco pirata caricatura,Pixabay
```

La `descripcion` es una frase corta de lo que se ve. (El script registra solo el estilo común del proyecto automáticamente, no tienes que escribirlo.)

## 4. Indexa tus imágenes

```bash
python scripts/procesar_ilustraciones.py --usuario TU_USUARIO
```

El script revisa que cada imagen sea válida, anota su tamaño, le calcula una huella para detectar repetidas y arma `datos/ilustraciones/parciales/parcial_TU_USUARIO.csv`. Te avisa si descartó alguna (corrupta, muy chica o repetida).

Qué obtienes: un CSV que es el índice de tus imágenes (nombre, temática, estilo, tamaño, descripción, fuente, tu nombre y la huella). Las imágenes en sí no van al CSV ni a GitHub: las juntamos todas en una carpeta compartida por Drive llamada `imagenes/`, que es de donde el modelo las leerá al entrenar.

## 5. Sube tu CSV y tus imágenes

Sube el CSV al repo con Git (`git add .`, `git commit -m "ilustraciones de TU_USUARIO"`, `git push`). Sube las imágenes a la carpeta compartida del Drive del equipo, no a GitHub (pesan demasiado).
