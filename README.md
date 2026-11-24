# Proyecto de biblioteca — entrega 1

Aplicación de consola para administrar libros, usuarios y préstamos. Se implementa con funciones y tipos básicos, sin clases propias ni interfaz gráfica, siguiendo la estrategia de persistencia SQLite del archivo `ejemplo1.py`. Requiere Python 3.9 o posterior; no necesita instalar paquetes.

## Ejecución

Abra IDLE con `POO2026/proyecto_entrega_1` como directorio de trabajo, abra `proyecto_entrega_1.py` y seleccione **Run > Run Module** (F5). También puede ejecutarlo desde una terminal situada en `POO2026/proyecto_entrega_1`:

```sh
python3 proyecto_entrega_1.py
```

El programa utiliza `BaseDeDatosAplicacion.db`, la base de datos de la carpeta `POO2026/proyecto_entrega_1`. Ejecuta el programa con `POO2026/proyecto_entrega_1` como directorio de trabajo: SQLite busca el nombre de la base de datos en ese directorio. Si se ejecuta desde otro directorio, SQLite puede crear allí otra base con el mismo nombre. Los comprobantes se guardan en la carpeta `comprobantes/` junto al programa. No se borran las tablas existentes; se crean las tablas del proyecto si aún no existen.

## Manual de usuario y casos de uso

El menú principal contiene Libros, Usuarios y Préstamos; 0 regresa o termina. Todos los datos son obligatorios y las fechas se introducen como `dd/mm/aaaa`.

1. **Registrar libro:** en Libros, opción 1, digite identificador único, título, autor, género y fecha de publicación. El libro inicia disponible. Las opciones 3 y 4 consultan disponibilidad o todos sus datos por identificador. Si no conoce el identificador, use la opción 5 para consultar una muestra del catálogo: muestra el identificador, título, autor y estado de hasta 100 libros, ordenados por título e identificador. No muestra necesariamente todos los libros registrados.
2. **Actualizar estado:** en Libros, opción 2, ingrese el identificador. Se muestra el estado actual y, si está disponible o en mantenimiento, se ofrece cambiar al otro estado con 1 o cancelar con 0. Si está prestado, se indica que debe registrarse la devolución en el módulo de préstamos.
3. **Registrar usuario:** en Usuarios, opción 1, ingrese documento único, nombre, apellido, dirección, teléfono y correo. La opción 2 muestra los datos de contacto actuales y permite elegir uno para modificarlo o cancelar; repita la operación si desea modificar otro. La 3 consulta el registro vigente. La opción 4 muestra hasta 100 usuarios con documento y nombre, ordenados por apellido, nombre y documento.
4. **Registrar préstamo:** registre primero el usuario y el libro. En Préstamos, opción 1, indique documento, identificador del libro y fechas de inicio y devolución. La devolución no puede ser anterior al inicio. El programa asigna un número, marca el libro prestado, crea el PDF e intenta enviarlo al correo registrado. Un usuario con cualquier préstamo sin devolver, incluso vencido, no puede recibir otro; el libro debe estar disponible.
5. **Registrar devolución:** en Préstamos, opción 2, ingrese el número del préstamo. Se muestran el usuario, el libro y el estado actual; seleccione 1 para confirmar la devolución o 0 para cancelar. Al confirmar, el estado pasa a devuelto y el libro a disponible. Una devolución no puede registrarse dos veces.
6. **Consultar préstamos:** en Préstamos, opción 3, ingrese el documento para consultar todo el historial y sus estados, ordenados del más reciente al más antiguo. Cada página muestra hasta 100 préstamos; digite 1 para ver la siguiente o 0 para volver. Un préstamo sin devolver está vencido desde el día posterior a la fecha de devolución; el día de devolución sigue vigente.
7. **Reintentar comprobante:** en Préstamos, opción 4, ingrese el número para generar nuevamente el PDF con los datos actuales y volver a intentar su envío. Esto también permite obtener el comprobante después de registrar una devolución. La opción 5 muestra hasta 100 préstamos más recientes con número, documento, libro y estado para encontrar sus identificadores.

Si falla la generación o el envío, el préstamo permanece guardado y se muestra un aviso; si el PDF se generó antes del fallo, también permanece guardado. La generación y el envío del comprobante no deshacen un préstamo ya registrado.

## Configuración del correo

Antes de abrir Python o IDLE, configure las variables de entorno de una cuenta SMTP autorizada. Por ejemplo, en macOS o Linux:

```sh
export BIBLIOTECA_SMTP_HOST='smtp.ejemplo.com'
export BIBLIOTECA_SMTP_PUERTO='587'
export BIBLIOTECA_SMTP_USUARIO='usuario@ejemplo.com'
export BIBLIOTECA_SMTP_CLAVE='contraseña_o_clave_de_aplicacion'
export BIBLIOTECA_SMTP_REMITENTE='usuario@ejemplo.com'
python3 proyecto_entrega_1/proyecto_entrega_1.py
```

El puerto predeterminado es 587 y usa STARTTLS; el 465 usa SSL. El remitente es opcional y por defecto es el usuario SMTP. Algunos proveedores exigen una contraseña de aplicación. No incluya credenciales en el código ni comparta la base de datos y los comprobantes sin protegerlos: contienen datos personales. Para IDLE, inícielo desde el mismo entorno que tenga estas variables. Sin configuración o conexión SMTP se genera el PDF, pero no se envía; configure el servicio y use la opción de reintento.

## Relación entre opciones y especificación

| Menú y opción | Relación con `Proyecto.docx` |
| --- | --- |
| Libros 1: Registrar libro | Solicitada expresamente: registrar un nuevo libro. |
| Libros 2: Actualizar estado | Solicitada expresamente. Mostrar el estado actual, ofrecer el cambio pertinente y permitir cancelar son decisiones de interacción. La asignación automática de prestado se explica más abajo. |
| Libros 3: Consultar disponibilidad | Solicitada expresamente. |
| Libros 4: Consultar datos | Solicitada expresamente: consultar datos vigentes del libro. |
| Libros 5: Muestra del catálogo | Función de apoyo acordada para encontrar identificadores; el documento no la exige ni define la forma de descubrirlos. |
| Usuarios 1: Crear usuario | Solicitada expresamente. |
| Usuarios 2: Actualizar contacto | Solicitada expresamente. Mostrar los datos actuales, modificar un campo a la vez y cancelar son decisiones de interacción. |
| Usuarios 3: Consultar usuario | Solicitada expresamente: consultar información vigente. |
| Usuarios 4: Muestra de usuarios | Función de apoyo acordada para encontrar documentos; el documento no la exige. |
| Préstamos 1: Registrar préstamo | Solicitada expresamente; incluye la generación y el intento de envío del comprobante exigido. |
| Préstamos 2: Registrar devolución | Solicitada expresamente. Mostrar el estado y permitir confirmar o cancelar son decisiones de interacción. |
| Préstamos 3: Consultar préstamos de usuario | Solicitada expresamente para conocer el estado de sus préstamos. El historial completo se consulta en páginas de hasta 100 préstamos. |
| Préstamos 4: Generar y enviar nuevamente | Función de apoyo para reintentar el comprobante cuando se requiera; el enunciado exige generarlo y enviarlo, pero no describe el reintento. |
| Préstamos 5: Muestra de préstamos | Función de apoyo acordada para encontrar números de préstamo; el documento no la exige. |
| Opción 0: Volver, salir o cancelar | Navegación y control de la operación; el documento exige menús, pero no prescribe sus opciones de salida. |

Las muestras de los tres módulos tienen un límite de 100 acordado para evitar cargar todos los registros; no permiten recorrer los registros restantes. La decisión de tratar como impedimento cualquier préstamo sin devolver, incluido uno vencido, es más restrictiva que la frase del enunciado «No se prestan libros a usuarios con préstamos vigentes»: el documento no especifica qué hacer con los préstamos vencidos. El cálculo de vencimiento desde el día siguiente a la fecha pactada y el inicio de un libro como disponible también son decisiones de diseño ante detalles no definidos en el enunciado.

## Diseño lógico y técnico

- **Libros:** identificador, título, autor, género, fecha de publicación y estado. Un libro comienza disponible, puede pasar a mantenimiento y vuelve a disponible; un préstamo lo marca prestado y su devolución lo libera. Por decisión de diseño, el estado prestado no se asigna manualmente: así no queda un libro marcado como prestado sin un préstamo asociado. El enunciado solicita actualizar el estado, pero no establece expresamente esta restricción.
- **Usuarios:** documento, nombre, apellido y datos de contacto. El documento identifica cada usuario.
- **Préstamos:** número autogenerado, documento de usuario, identificador de libro, fechas y marca de devolución. Las claves foráneas relacionan los registros. Índices únicos impiden más de un préstamo abierto por libro o usuario.
- **Estado:** se calcula al consultar: devuelto si se registró la devolución; vencido si sigue abierto después de la fecha pactada; vigente en los demás casos. La fecha de devolución es la fecha pactada, no se guarda la fecha real de entrega.
- **Proceso de préstamo:** validar fechas y existencia, comprobar usuario sin préstamo abierto y libro disponible, insertar préstamo y cambiar estado del libro en una transacción. Luego generar y enviar el comprobante. La devolución también actualiza ambos registros en una transacción.
- **Diseño físico:** SQLite almacena las tablas `libros`, `usuarios` y `prestamos` en `BaseDeDatosAplicacion.db`. Las fechas se guardan en formato ISO para su comparación y se presentan en formato solicitado. Se usan consultas SQL parametrizadas. El PDF de una página se construye con la biblioteca estándar; `smtplib` y `email` permiten enviarlo. La información del comprobante se toma de los registros actuales al generarlo; no es una fotografía histórica de datos de contacto.
- **Alcance:** se permiten fechas de inicio pasadas o futuras, pues el enunciado no las restringe; todo préstamo sin devolver reserva el libro desde su registro. No hay edición de los datos bibliográficos salvo el estado, ni eliminación, porque el enunciado no las solicita.

### Validación y estandarización de datos

Los textos digitados se guardan en mayúsculas, admiten hasta 120 caracteres imprimibles y se normalizan también al buscar; los identificadores de libros pueden contener letras y números. Para conservar los ceros iniciales, el documento y el teléfono se almacenan como texto, pero se solicitan únicamente con dígitos (entre 1 y 30, sin espacios ni signos). El número de préstamo es un entero positivo. Las opciones del menú deben ser una de las mostradas. Ante un dato vacío o inválido, el programa explica el formato y vuelve a solicitarlo. Las fechas deben ser reales y tener el formato exacto `dd/mm/aaaa`; la devolución no puede ser anterior al inicio.

El correo también se convierte a mayúsculas por el estándar solicitado. Algunos servidores de correo pueden distinguir mayúsculas en la parte anterior a `@`; confirme que la dirección estandarizada funciona con el proveedor destinatario. Los datos guardados en versiones anteriores no se modifican automáticamente; las búsquedas de identificadores de libro admiten diferencias de mayúsculas y minúsculas ASCII.


## Pruebas automáticas

Desde la carpeta `POO2026`, ejecute con Python 3.9.10:

```sh
python3 -m unittest discover -s proyecto_entrega_1/pruebas -v
```

Las pruebas usan bases de datos en memoria o una carpeta temporal y no modifican `BaseDeDatosAplicacion.db`. Cubren entradas inválidas, fechas, altas y consultas, reglas de préstamo y devolución, consultas parametrizadas, PDF, errores de correo y un recorrido por los menús. El envío SMTP se simula; para verificar la entrega real se necesita un servidor y una cuenta configurados. La ejecución automática reproduce la consola, pero no comprueba la interfaz de IDLE. Ninguna batería de pruebas puede garantizar ausencia total de fallos.

### Uso de mayúsculas y componentes de Python

Las capturas de texto se convierten con `upper()` antes de validarlas y almacenarlas; las opciones del menú también se normalizan. Las búsquedas de identificadores emplean `UPPER()` en SQLite para comparar sin depender de mayúsculas ASCII. Las fechas y los números no tienen mayúsculas. Los estados internos de la base se mantienen con los valores definidos en su estructura. Los datos previos no se convierten automáticamente y `UPPER()` de SQLite solo convierte letras ASCII: un identificador antiguo con letras acentuadas en minúscula puede requerir una corrección manual. Python sí convierte a mayúsculas los caracteres acentuados al capturar datos nuevos.

`os` es parte de Python y se usa únicamente para leer las variables de configuración SMTP; no se necesita para conectar la base de datos. Las credenciales no se convierten a mayúsculas porque pueden distinguirlas. `Path(__file__).resolve().parent` obtiene la carpeta que contiene el programa, y se usa para guardar los comprobantes junto a él; no define la ubicación de la base de datos. `PRAGMA foreign_keys = ON` activa la comprobación de las relaciones de SQLite en cada conexión: así un préstamo no puede apuntar a un usuario o libro inexistente.

La consulta del catálogo es una función adicional de apoyo: el enunciado exige consultar disponibilidad y datos vigentes, y no prohíbe mostrar una muestra de libros.

Las muestras de libros, usuarios y préstamos se limitan en SQLite a 100 registros y no representan necesariamente la totalidad de los datos. La consulta del historial por usuario permite recorrer todos sus préstamos en páginas de hasta 100.
