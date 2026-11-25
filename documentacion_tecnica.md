# Documentación técnica — sistema de biblioteca

## 1. Propósito y alcance

Solución para los módulos de libros, usuarios y préstamos de `Proyecto.docx`. La aplicación es un programa de consola ejecutable en Python 3.9.10, estructurado con funciones y sin clases definidas en el código principal. Utiliza SQLite y bibliotecas incluidas en Python. `ejemplo1.py` se tomó como referencia para la conexión y persistencia; el código de la entrega está en `proyecto_entrega_1.py`.

El documento del proyecto exige menú principal y submenús, manejo de registros y estados, comprobante PDF individual enviado por correo y documentación de diseño, usuario y técnica. El manual de usuario y el diseño lógico complementan este documento. Las opciones de muestras y reenvío son adicionales de apoyo, no requisitos explícitos.

## 2. Arquitectura y flujo

La ejecución directa inicia `main()`, que abre una conexión, prepara los diccionarios de opciones y llama a `menu()`. El menú dirige las llamadas a funciones de captura, validación y persistencia. La misma conexión se comparte entre operaciones y se cierra al salir mediante `finally`.

```text
main → menu → funciones de libros / usuarios / préstamos
                   ↓
             SQLite (tablas)
                   ↓
      comprobante → PDF local → servidor SMTP
```

Al registrar un préstamo, `registrar_prestamo()` captura los datos y llama a `crear_prestamo()`. Esa función valida y registra el préstamo y el estado del libro en una transacción. Tras confirmarse, `comprobante()` genera el PDF y llama a `enviar_comprobante()`. La escritura de PDF y el correo están fuera de la transacción; un fallo de envío no revierte el préstamo.

## 3. Diseño físico y persistencia

`conectar(ruta=BASE_DATOS)` abre `BaseDeDatosAplicacion.db`. El nombre relativo se resuelve respecto al **directorio de trabajo** de Python, no necesariamente al directorio del programa. SQLite crea el archivo si no existe. `CREATE TABLE IF NOT EXISTS` crea las tablas faltantes, pero no migra tablas existentes incompatibles. Para recibir la base esperada, ejecutar desde `proyecto_entrega_1`.

| Tabla | Campos y tipos SQLite | Restricciones |
| --- | --- | --- |
| `libros` | `id`, `titulo`, `autor`, `genero`, `fecha_publicacion`, `estado`: TEXT | `id` es clave primaria; datos obligatorios; estado limitado a disponible, prestado o en mantenimiento. |
| `usuarios` | `documento`, `nombre`, `apellido`, `direccion`, `telefono`, `correo`: TEXT | `documento` es clave primaria; demás datos obligatorios. Documento y teléfono son texto para conservar ceros iniciales. |
| `prestamos` | `numero`: INTEGER; `documento`, `libro_id`, `fecha_inicio`, `fecha_devolucion`: TEXT; `devuelto`: INTEGER | `numero` es clave primaria autogenerada; documento y libro son claves foráneas; `devuelto` vale 0 o 1. |

Las fechas se guardan como texto ISO `aaaa-mm-dd` y se muestran como `dd/mm/aaaa`. El estado del préstamo no se guarda: se calcula a partir de `devuelto`, la fecha pactada y la fecha actual. No se guarda la fecha real de devolución. `PRAGMA foreign_keys = ON` activa la comprobación de referencias en cada conexión. `row_factory = sqlite3.Row` permite acceder a las columnas por nombre.

El programa no crea índices adicionales para préstamos abiertos. SQLite puede crear estructuras internas para hacer cumplir las claves primarias. Las validaciones de préstamos abiertos se efectúan dentro de la transacción de la aplicación; cambios directos a la base pueden omitirlas. Los valores de entrada se pasan como parámetros SQL `?`, no se concatenan a las consultas.

## 4. Reglas, validación y decisiones de diseño

- El enunciado prohíbe prestar a un usuario con préstamo vigente. Como decisión adicional, el programa impide prestar si existe cualquier préstamo sin devolver, incluso vencido.
- Solo un libro disponible puede prestarse; el estado prestado se asigna al crear el préstamo y se libera mediante la devolución. Disponible y mantenimiento pueden cambiarse manualmente.
- La fecha de inicio es la fecha actual del equipo. La devolución pactada puede ser igual o posterior. Se considera vencido un préstamo abierto cuando la fecha pactada es anterior al día actual; si ya fue devuelto prevalece el estado devuelto. Estas precisiones no están definidas expresamente por el enunciado.
- Se normalizan capturas con Unicode NFC y mayúsculas. En la conexión se registra una función SQL `UPPER` basada en Python para comparar letras acentuadas. Los identificadores con y sin tilde son distintos. Los registros antiguos no se modifican automáticamente.
- Texto obligatorio de hasta 120 caracteres imprimibles; documento y teléfono de 1 a 30 dígitos conservados como texto; fecha de entrada exacta `dd/mm/aaaa`; número de préstamo positivo de hasta el máximo de entero de SQLite. El correo se valida por estructura, sin verificar existencia.
- Los menús y controles permiten cancelar determinadas operaciones; cada muestra general devuelve como máximo 100 registros. El historial de un usuario se recorre por páginas de 100 con el número de préstamo como referencia para continuar.

## 5. Transacciones y control de errores

`crear_prestamo()` usa `BEGIN IMMEDIATE` dentro de `with con`: adquiere el bloqueo de escritura antes de consultar y agrupa inserción y actualización del libro. `devolver()` emplea el mismo patrón para la marca de devolución y la liberación del libro. Si se produce una excepción en el bloque, se revierte la transacción; si termina correctamente, se confirma.

`menu()` captura `sqlite3.IntegrityError`, otros errores SQLite y `ValueError`, realiza `rollback()` y muestra un mensaje. `main()` captura interrupciones de entrada y cierra la conexión. `comprobante()` captura fallos de E/S, configuración y SMTP: conserva el préstamo y permite reintentar. El PDF puede haberse creado antes del fallo del envío; no se garantiza que el destinatario reciba el mensaje solo porque el servidor SMTP lo acepte.

## 6. PDF y envío de correo

`pdf_comprobante()` construye un PDF 1.4 de una página con Helvetica, usando bytes de la biblioteca estándar. Organiza los campos requeridos: número y contacto del usuario, título y autor, fechas y estado. Ajusta líneas largas; utiliza codificación `cp1252`, que admite tildes habituales del español, pero reemplaza caracteres que no puede representar. Guarda `comprobantes/prestamo_<número>.pdf` junto al programa. Al regenerarlo puede sobrescribir ese archivo y usa datos y estado actuales, no una fotografía histórica.

`enviar_comprobante()` usa `EmailMessage` para construir el mensaje y adjuntar el PDF; `smtplib` y `ssl` realizan el envío. Puerto 465 usa SMTP sobre SSL; otros puertos usan STARTTLS, por ejemplo 587. Se verifica el certificado mediante el contexto SSL predeterminado. La configuración completa en variables de entorno tiene prioridad sobre `configuracion_correo.json`, ubicado junto al código; consulte el manual para configurarlo.

**Credenciales:** el archivo local JSON contiene la contraseña en texto legible. No incluirlo en la entrega, repositorio ni carpetas compartidas; usar permisos adecuados y revocar la contraseña de aplicación si se expone. `.gitignore` ayuda a excluirlo de Git, pero no protege otras formas de copia. El archivo de ejemplo no contiene una contraseña real.

## 7. Funciones del programa

En la tabla, `con` es la conexión SQLite, `fila` es un registro o resultado consultado y `ruta` es una ubicación de archivo.

### Entrada, presentación y conexión

| Función | Parámetros y resultado | Propósito y funcionamiento |
| --- | --- | --- |
| `mayusculas(valor)` | Texto o `None` → texto normalizado o `None`. | Aplica normalización Unicode NFC y mayúsculas. También se registra como `UPPER` para las consultas. |
| `conectar(ruta=BASE_DATOS)` | Ruta opcional → conexión. | Abre SQLite, configura acceso por nombre y claves foráneas, registra `UPPER` y crea tablas faltantes. |
| `texto(etiqueta)` | Etiqueta → texto. | Solicita, recorta y normaliza entrada hasta que sea obligatoria, imprimible y de longitud válida. |
| `digitos(etiqueta)` | Etiqueta → cadena de dígitos. | Reutiliza `texto` y repite hasta aceptar entre 1 y 30 dígitos; conserva ceros. |
| `fecha(etiqueta)` | Etiqueta → fecha ISO como texto. | Pide formato exacto, valida el calendario y transforma la fecha para almacenamiento. |
| `fecha_visible(valor)` | Fecha ISO → texto `dd/mm/aaaa`. | Convierte una fecha guardada al formato de presentación. |
| `correo_valido(valor)` | Texto → booleano. | Valida la estructura con una expresión regular; no comprueba existencia del buzón. |
| `pedir_correo()` | Sin parámetros → correo normalizado. | Solicita el correo hasta que `correo_valido` lo acepte. |
| `mostrar(fila, etiquetas)` | Registro y pares campo/etiqueta → salida en consola. | Muestra los campos solicitados, convierte fechas y avisa si no hay registro. |

### Libros y usuarios

| Función | Parámetros y resultado | Propósito y funcionamiento |
| --- | --- | --- |
| `registrar_libro(con)` | Conexión; guarda un libro. | Captura los datos, verifica identificador y registra estado inicial disponible. |
| `actualizar_estado(con)` | Conexión; modifica o cancela. | Localiza el libro, muestra estado y ofrece transición entre disponible y mantenimiento. Requiere devolución si está prestado. |
| `consultar_libro(con, solo_estado=False)` | Conexión y opción de presentación. | Busca por identificador y muestra disponibilidad o datos completos mediante `mostrar`. |
| `listar_libros(con)` | Conexión; salida en consola. | Muestra una muestra ordenada de hasta 100 libros. |
| `registrar_usuario(con)` | Conexión; guarda un usuario. | Captura documento, nombre y contacto; SQLite rechaza claves duplicadas. |
| `actualizar_contacto(con)` | Conexión; modifica un campo o cancela. | Muestra los datos vigentes y permite actualizar dirección, teléfono o correo. |
| `consultar_usuario(con)` | Conexión; salida en consola. | Busca por documento y muestra datos del usuario. |
| `listar_usuarios(con)` | Conexión; salida en consola. | Muestra hasta 100 usuarios ordenados por apellido, nombre y documento. |

### Préstamos y comprobantes

| Función | Parámetros y resultado | Propósito y funcionamiento |
| --- | --- | --- |
| `estado_prestamo(fila, hoy=None)` | Préstamo y fecha opcional → estado textual. | Devuelve devuelto, vencido o vigente; `hoy` permite probar fechas y por defecto se usa la fecha del equipo. |
| `crear_prestamo(con, documento, libro_id, inicio, devolucion)` | Conexión, identificadores y fechas ISO → número. | Valida fechas, existencia y disponibilidad; guarda préstamo y estado del libro en una transacción. |
| `datos_prestamo(con, numero)` | Conexión y número → fila o `None`. | Relaciona préstamo, usuario y libro para recuperar los datos del comprobante. |
| `pdf_comprobante(fila)` | Datos del préstamo → ruta del PDF. | Construye el documento, crea la carpeta si falta y escribe el archivo. |
| `enviar_comprobante(fila, ruta)` | Datos y ruta del PDF; envía correo. | Lee configuración, prepara `EmailMessage`, adjunta el PDF y envía por SMTP cifrado. |
| `comprobante(con, numero)` | Conexión y número; genera e intenta enviar. | Busca datos, crea el PDF y envía; informa errores sin deshacer el préstamo. |
| `registrar_prestamo(con)` | Conexión; interacción por consola. | Captura identificadores y devolución, establece fecha actual, llama a `crear_prestamo` y después a `comprobante`. |
| `devolver(con, numero)` | Conexión y número; registra devolución. | Valida que exista y no esté devuelto; actualiza préstamo y libro en una transacción. |
| `registrar_devolucion(con)` | Conexión; interacción por consola. | Solicita número, muestra estado y permite confirmar o cancelar antes de llamar a `devolver`. |
| `numero_prestamo(operacion='consultar')` | Descripción opcional → entero. | Solicita un entero positivo dentro del rango de SQLite y repite si es inválido. |
| `consultar_prestamos(con)` | Conexión; salida paginada. | Consulta el historial del usuario y permite avanzar de 100 en 100 hasta el final. |
| `listar_prestamos(con)` | Conexión; salida en consola. | Muestra una muestra de hasta 100 préstamos recientes y su estado calculado. |

### Navegación

| Función | Parámetros y resultado | Propósito y funcionamiento |
| --- | --- | --- |
| `menu(con, titulo, opciones)` | Conexión, título y diccionario de opciones. | Muestra opciones, valida la selección, ejecuta la acción asociada y controla errores. |
| `main()` | Sin parámetros. | Conecta, configura los menús, inicia la navegación y cierra la conexión. El bloque `if __name__ == '__main__'` evita iniciar el menú cuando se importa el módulo. |

## 8. Bibliotecas y constantes

Todas son de la biblioteca estándar: `os` (variables de entorno), `json` (archivo de configuración), `re` (validaciones), `sqlite3` (base), `smtplib` y `ssl` (correo), `unicodedata` (normalización), `datetime` (fechas), `email.message.EmailMessage` (mensaje y adjunto), `pathlib.Path` (rutas) y `textwrap` (ajuste de texto PDF).

`CARPETA` corresponde al directorio del archivo Python; `COMPROBANTES` y `CONFIGURACION_CORREO` se construyen desde él. `BASE_DATOS` es un nombre relativo al directorio de trabajo. `ETIQUETAS_LIBRO` y `ETIQUETAS_USUARIO` relacionan nombres de columnas con textos para mostrarlos al usuario.

## 9. Pruebas y límites

Desde `POO2026` se ejecutan las pruebas con:

```sh
python3 -m unittest discover -s proyecto_entrega_1/pruebas -v
```

Las pruebas emplean bases en memoria o directorios temporales y no deben modificar la base de trabajo. Cubren validaciones, claves primarias y foráneas, normalización, consultas, reglas de negocio, transacciones, historial paginado, PDF, SMTP simulado y ejecución por consola. El envío real fue probado por el usuario con una cuenta de Gmail y llegó al destinatario en Spam; la clasificación depende del servidor receptor. Las pruebas automáticas no garantizan ausencia total de fallos ni reproducen IDLE o un servidor SMTP real.

La aplicación principal no crea clases; el archivo auxiliar de pruebas utiliza clases de `unittest` para organizar los casos. Si el docente interpreta la restricción de «no crear clases nuevas» como aplicable también a archivos auxiliares, debe confirmarse antes de incluir las pruebas en la entrega.
