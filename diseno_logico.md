# Diseño lógico — sistema de biblioteca

## Objetivo y alcance

Administrar libros, usuarios y préstamos desde una consola de Python. El sistema registra y consulta información, controla la disponibilidad, registra devoluciones y genera y envía un comprobante individual. El diseño usa funciones y tipos básicos; el programa principal no define clases propias ni utiliza una interfaz gráfica.

El alcance responde al archivo `Proyecto.docx`. Las muestras y el reintento de correo complementan los requisitos y no sustituyen las funciones solicitadas. Las condiciones de sustentación y entrega del enunciado dependen del docente y del grupo.

## Entidades y relaciones

| Entidad | Identificador | Información | Relaciones |
| --- | --- | --- | --- |
| Libro | Identificador único | Título, autor, género, fecha de publicación y estado | Puede aparecer en varios préstamos históricos. |
| Usuario | Documento único | Nombre, apellido, dirección, teléfono y correo electrónico | Puede tener varios préstamos históricos. |
| Préstamo | Número único asignado por el sistema | Documento del usuario, identificador del libro, fechas de inicio y devolución pactada y marca de devolución | Se relaciona con un usuario y un libro existentes. |

Un usuario puede tener **máximo un préstamo sin devolver** y un libro solo puede estar en un préstamo sin devolver. La fecha de devolución registrada es la pactada; el sistema no guarda la fecha real de entrega.

## Estados y reglas de negocio

### Libro

- **Disponible:** puede prestarse o cambiarse a mantenimiento.
- **En mantenimiento:** no puede prestarse; desde la actualización de estado puede volver a disponible.
- **Prestado:** lo asigna el sistema al registrar un préstamo. Se cambia a disponible cuando se registra la devolución.

El enunciado pide actualizar el estado, pero no establece quién asigna cada estado. Como decisión de diseño, no se permite marcar manualmente un libro como prestado: se requiere un préstamo asociado. Un libro nuevo inicia disponible.

### Préstamo

El estado se calcula al consultar y al generar el comprobante:

1. **Devuelto:** se registró la devolución.
2. **Vencido:** no se ha devuelto y la fecha pactada es anterior al día actual.
3. **Vigente:** no se ha devuelto y la fecha pactada es hoy o posterior.

La especificación prohíbe prestar a usuarios con préstamos **vigentes**. No indica qué hacer con préstamos vencidos: el sistema adopta la regla adicional de impedir un nuevo préstamo mientras exista cualquiera sin devolver, incluso vencido. La fecha de inicio se toma del reloj del equipo. La devolución pactada puede ser igual o posterior a la fecha de inicio; el enunciado no define un plazo máximo ni cuándo comienza el vencimiento.

## Procesos principales

### Registro de libro y usuario

1. Recibir y validar los datos obligatorios.
2. Verificar que el identificador o documento no esté repetido.
3. Guardar la entidad. El libro queda disponible.

### Registro de préstamo

1. Recibir documento, identificador de libro y fecha de devolución; establecer la fecha de inicio como la fecha actual.
2. Validar fecha, existencia del usuario y libro, disponibilidad y ausencia de préstamos sin devolver.
3. Guardar el préstamo y marcar el libro prestado en una misma transacción.
4. Generar el PDF e intentar enviarlo al correo registrado. Si falla esta etapa, el préstamo ya guardado permanece y puede reintentarse el comprobante.

### Devolución

1. Buscar el número del préstamo y mostrar sus datos y estado.
2. Si ya fue devuelto, informar al usuario. Si no, permitir confirmar o cancelar.
3. Al confirmar, registrar la devolución y cambiar el libro a disponible en una misma transacción.

### Consultas

Se consulta el libro por identificador y el usuario por documento. El historial completo de préstamos por usuario se recorre en páginas de hasta 100 registros, desde los más recientes. Las muestras generales de libros, usuarios y préstamos se limitan a 100 y no permiten recorrer el resto; son ayudas adicionales para encontrar identificadores.

## Validación de datos

- Campos obligatorios: texto imprimible de 1 a 120 caracteres, normalizado a mayúsculas.
- Documento y teléfono: entre 1 y 30 dígitos, conservados como texto para mantener ceros iniciales.
- Número de préstamo: entero positivo válido para SQLite.
- Fechas digitadas: formato exacto `dd/mm/aaaa` y fecha de calendario válida; internamente se guardan como `aaaa-mm-dd`.
- Correo: se comprueba una estructura admitida por el programa; no se verifica que la dirección exista. También se guarda en mayúsculas.
- Identificadores: se comparan en mayúsculas con normalización Unicode; la tilde se conserva (`CAFE` y `CAFÉ` son distintos).

## Comprobante y correo

Por cada préstamo se genera un PDF con el encabezado de usuario y número de préstamo; el cuerpo con título, autor y fechas; y el estado al final. El programa guarda el PDF en `comprobantes/` y lo adjunta al correo. El enunciado exige generar y enviar el comprobante, pero no especifica el diseño visual ni una opción de reintento. La opción de reintento es una función de apoyo.

Al generar nuevamente el comprobante se utilizan los datos actuales del usuario y libro y el estado actual del préstamo; no se conserva una copia histórica inmutable. El envío depende de la configuración SMTP y de la conexión a internet.
