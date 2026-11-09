# Plantilla para la preparación de la Liturgia de la Palabra

Herramienta que genera un archivo Excel con las citas bíblicas del
[vocabulario de León Dufour](https://leon-dufour.com), clasificadas en
**Históricos**, **Profetas**, **Cartas** y **Evangelios**. Cada bloque incluye
dos columnas vacías para la votación personal y la suma de votaciones.

## Uso rápido

Desde la raíz del repositorio, sin instalar nada más que Python:

```bash
python3 -m liturgia "Árbol"
```

Genera `arbol.xlsx` en el directorio actual. También puedes pasar una URL
completa o elegir el archivo de salida:

```bash
python3 -m liturgia "https://leon-dufour.com/palabra/arbol"
python3 -m liturgia "Acción de gracias" -o accion_de_gracias.xlsx
```

### Opciones

```text
uso: liturgia-palabra [-h] [-o SALIDA] [--html HTML] [--timeout TIMEOUT]
                      [-a] [--pdf] [--version] entrada

  entrada              Palabra a consultar o URL completa de leon-dufour.com
  -o, --salida         Ruta del archivo .xlsx de salida
  --html               Usa un archivo HTML local en lugar de descargar la página
  --timeout            Tiempo máximo de descarga en segundos (por defecto: 30)
  -a, --ordenar        Ordena alfabéticamente las citas de cada columna
                       (por defecto se conserva el orden de aparición)
  --pdf                Exporta también el documento a PDF con el mismo nombre
                       que el .xlsx
  --version            Muestra la versión de la herramienta
```

Para ordenar las citas de cada columna alfabéticamente en lugar de mantener el
orden de aparición en la página:

```bash
python3 -m liturgia "Árbol" --ordenar
```

El argumento `--html` resulta útil para trabajar sin conexión o para probar la
herramienta con una página guardada:

```bash
python3 -m liturgia arbol --html tests/fixtures/arbol.html -o arbol.xlsx
```

### Exportación a PDF

Con `--pdf` se genera, junto al `.xlsx`, un PDF con el mismo nombre base:

```bash
python3 -m liturgia "Árbol" --pdf
```

El PDF incluye el título `PALABRA: Árbol`, la tabla de citas de la primera hoja
y, debajo, la tabla de la pestaña **Equipo**. También respeta `--ordenar`.

## Instalación como comando

Si prefieres tener el comando `liturgia-palabra` disponible en el sistema:

```bash
pipx install .
# o bien
python3 -m pip install --user .
```

Después:

```bash
liturgia-palabra "Árbol"
```

## Ejecutables autónomos (sin Python)

El repositorio incluye un flujo de GitHub Actions que genera ejecutables para
Linux, macOS y Windows. Para publicar una versión:

```bash
git tag v1.0.0
git push origin v1.0.0
```

El flujo ejecuta los tests, compila los tres ejecutables y los adjunta a la
release del tag. También se puede lanzar manualmente desde la pestaña
**Actions**; en ese caso los binarios quedan como artefactos descargables.

## Generar el Excel desde GitHub Actions

Si no quieres instalar nada, puedes generar la plantilla directamente desde
GitHub:

1. Abre la pestaña **Actions** del repositorio.
2. Selecciona el workflow **generate-excel**.
3. Pulsa **Run workflow**, escribe la palabra o URL en `entrada` y marca
   `ordenar` si quieres que las citas se ordenen alfabéticamente. Marca `pdf`
   si además quieres el documento en PDF.
4. Al terminar la ejecución, descarga el artifact **liturgia-excel**.
5. Descomprime el archivo: dentro estarán el `.xlsx` y, si lo pediste, el
   `.pdf`.

Los artifacts se conservan durante 30 días. Para lanzar un workflow manualmente
hace falta tener permisos de escritura sobre el repositorio.

Los usuarios externos sin permisos de escritura no pueden lanzar el workflow en
este repositorio. Como alternativa, pueden hacer un **fork** y ejecutar
`generate-excel` desde la pestaña Actions de su propio fork. Para descargar los
artifacts es necesario tener una cuenta de GitHub e iniciar sesión.

## Por qué el versionado no es un problema

- **Cero dependencias externas en tiempo de ejecución**: todo usa la biblioteca
  estándar de Python (`urllib`, `html.parser`, `zipfile`, `xml`, etc.).
- No hay que instalar `openpyxl`, `pandas`, `requests` ni fijar versiones de
  paquetes que puedan entrar en conflicto.
- El único requisito es **Python 3.8 o superior**.
- Para quien no tenga Python, los ejecutables autónomos de las releases
  incluyen el intérprete y no requieren instalación.

## Columnas del Excel

| Columna | Encabezado | Contenido |
| --- | --- | --- |
| A | **Históricos** | Citas históricas |
| B | **P** | Votación personal (vacía) |
| C | **T** | Suma de votaciones (vacía) |
| D | **Profetas** | Citas proféticas |
| E | **P** | Votación personal (vacía) |
| F | **T** | Suma de votaciones (vacía) |
| G | **Cartas** | Citas de las cartas |
| H | **P** | Votación personal (vacía) |
| I | **T** | Suma de votaciones (vacía) |
| J | **Evangelios** | Citas evangélicas |
| K | **P** | Votación personal (vacía) |
| L | **T** | Suma de votaciones (vacía) |

Los anchos de columna se ajustan automáticamente al contenido más largo,
incluidos los encabezados. Las columnas `P` y `T` quedan estrechas porque solo
contienen votos. La primera fila queda fija al desplazarse. Todas las celdas de
las tablas tienen bordes finos, de modo que se imprimen correctamente.

### Pestaña «Equipo»

El libro incluye una segunda hoja llamada **Equipo** para repartir las tareas
de la celebración:

| Fila | Contenido |
| --- | --- |
| 1 | Monición ambiental (celda combinada) |
| 3 | Cabeceras: **Lectura**, **Cita bíblica más votada**, **Monición** y **Proclamación** |
| 4-7 | Una fila por categoría: Históricos, Profetas, Cartas y Evangelios |

Las tres primeras filas quedan fijas al desplazarse.

## Reglas aplicadas

- **Libros excluidos**: Eclesiástico, Job, Salmos, Proverbios, Eclesiastés,
  Cantar de los Cantares, Sabiduría y Apocalipsis. Se reconocen tanto nombres
  completos como abreviaturas (por ejemplo, `Eclo`, `Sal`, `Prov`, `Ap`).
- **Citas contenidas**: si una cita está incluida en otra, se descarta la más
  corta. Por ejemplo, de `Gen 3,22` y `Gen 3,22ss` se conserva `Gen 3,22ss`.
- **Solapamientos parciales**: se unifican. Por ejemplo, `Mt 24,30-33` y
  `Mt 24,32-35` pasan a ser `Mt 24,30-35`.
- **Orden**: se respeta el orden de aparición en la página. La cita unificada
  ocupa la posición de la primera cita que la genera. Con `--ordenar`, las citas
  de cada columna se ordenan alfabéticamente (sin distinguir mayúsculas ni
  acentos).
- **Marcas de paralelos**: se conservan tal cual aparecen en la web (por
  ejemplo, `Mt 7,16-20 p`).

## Cómo funciona

1. Construye la URL a partir de la palabra (`https://leon-dufour.com/palabra/<palabra>`)
   o usa la URL indicada.
2. Descarga el HTML.
3. Localiza el bloque `div[data-panel="citas"]`.
4. Extrae las citas. Se prioriza el JSON `data-citas` que ya clasifica las
   citas por categorías; si no está disponible, se leen los atributos
   `data-cita` y se clasifican por libro.
5. Filtra los libros excluidos y aplica las reglas de solapamiento.
6. Escribe el `.xlsx` directamente, sin dependencias externas y, si se indica
   `--pdf`, genera también el PDF con las dos tablas.

## Tests

El proyecto sigue TDD. Para ejecutar la suite:

```bash
python3 -m unittest discover -s tests -v
```

La suite cubre el catálogo de libros, el análisis de citas, las reglas de
solapamiento, la extracción del HTML, la generación del Excel y del PDF, y la
CLI.

## Estructura

```text
liturgia/
  books.py       Catálogo de libros, abreviaturas y exclusiones
  citations.py   Análisis, unión y deduplicación de citas
  parser.py      Extracción de citas del HTML
  fetch.py       Descarga y construcción de URLs
  excel.py       Escritura del .xlsx sin dependencias
  pdf.py         Generación del PDF sin dependencias
  cli.py         Interfaz de línea de comandos
tests/           Tests unitarios y fixture HTML
packaging/       Punto de entrada para PyInstaller
```
