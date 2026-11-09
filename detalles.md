# Generador de plantillas para la preparación de la Liturgia de la Palabra

## Contexto
En la Liturgia de la Palabra (en el contexto católico y del Camino Neocatecumenal), para prepararla, se va a una palabra en concreto del vocabulario de León Dufour y se seleccionan 4 citas bíblicas: una proveniente de los libros históricos (desde el pentateuco hasta los libros de antes de Isaías), otra de los profetas (de Isaías a Zacarías), otro de las cartas (todo el Nuevo Testamento excepto los Evangelios) y, finalmente, una cita del Evangelio.
Esto puede llegar a contemplarse en distintos diccionarios para clasificarlas.

### Libros excluídos
Esta es la lista de libros que no se trabajan:
- Eclesiástico
- Job
- Salmos
- Proverbios
- Eclesiastés
- Cantar de los Cantares
- Sabiduría
- Eclesiástico
- Apocalípsis
Se puede hacer como una especie de diccionario para que se contemplen las abreviaturas y nombres completos para que no se incluyan.

## Presentación y formato
Se debe de generar como documento en formato excel con las siguientes columnas:
- Históricos: contiene las citas bíblicas de los históricos del Antiguo Testamento. No se incluyen los libros de los profetas que van desde Isaías hasta Zacarías ni el resto de libros excluídos para la Liturgia.
- Columna vacía sin título: sirve para poner la votación personal.
- Columna vacía sin título: para incluir la suma de las votaciones.
- Profetas: contiene las citas bíblicas del Antiguo Testamento de los libros que van desde Isaías hasta Zacarías.
- Columna vacía sin título: sirve para poner la votación personal.
- Columna vacía sin título: para incluir la suma de las votaciones.
- Cartas: contiene las citas bíblicas del Nuevo Testamento excepto los Evangelios y el Apocalípsis.
- Columna vacía sin título: sirve para poner la votación personal.
- Columna vacía sin título: para incluir la suma de las votaciones.
- Evangelios: contiene las citas bíblicas relacionadas con los Evangelios.
- Columna vacía sin título: sirve para poner la votación personal.
- Columna vacía sin título: para incluir la suma de las votaciones.

## Exportación a PDF
De forma opcional, el documento se puede exportar también a PDF. El PDF debe incluir:
- Un título con el formato `PALABRA: PALABRA_ESCOGIDA`.
- La tabla con las citas de la primera pestaña del Excel.
- Debajo, la tabla de la pestaña «Equipo».

## ¿Cómo se extraen las citas bíblicas?
Supongamos que queremos extraer la palabra "Árbol". Para ello, la herramienta debe de hacer un curl de esta web: "https://leon-dufour.com/palabra/arbol". Dicha web debe de ser definida como parámetro de entrada por parte del usuario o, bien, que el usuario ponga la palabra directamente (se puede comprobar con un grep que el input no empieza por "http"). Con el HTML que se obtiene, se debe de ir al div data-panel="citas".

### Reglas
- Excluir las citas provenientes de los libros exlcuidos.
- Si hay un solapamiento, se debe de excluir la cita más corta. Por ejemplo, si hay una cita que es "Gen 3,22" y otra que es "Gen 3,22ss", se excluye la primera y se conserva la segunda. Otro ejemplo podría ser que hay cuatro citas: "Mt 24,32", "Mt 24,30-33", "Mt 24,32-35" y "Mt 24,36"; se debería de eliminar "Mt 24,32" en este ejemplo por ser redundante. En el caso de los otros solapes, se deben de unificar formando la cita "Mt 24,30-35" y conservando "Mt 24,36".
- Las citas deben de quedar ordenadas por orden de aparición en el curl que se realiza. De forma opcional (con `--ordenar`), se pueden ordenar alfabéticamente las citas de cada columna.
