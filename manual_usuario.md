# Manual de usuario — sistema de biblioteca

## 1. Objetivo

Este programa permite registrar y consultar libros y usuarios, controlar préstamos y devoluciones, consultar el estado de los préstamos y generar comprobantes PDF enviados por correo. Funciona mediante menús de texto en IDLE o en una terminal.

## 2. Antes de comenzar

Se necesita Python **3.9.10** y los archivos del proyecto. No es necesario instalar paquetes adicionales. Mantenga `proyecto_entrega_1.py` y la configuración de correo en la carpeta `proyecto_entrega_1`.

La base se llama `BaseDeDatosAplicacion.db`. SQLite la busca en el **directorio de trabajo**, que puede ser distinto de la carpeta del archivo Python. Inicie Python o IDLE con `proyecto_entrega_1` como directorio de trabajo; de lo contrario podría abrir o crear otra base. Si no existe la base en ese directorio, el programa la crea con tablas vacías. Las tablas existentes con esos mismos nombres deben tener la estructura del programa; no se convierten automáticamente.

### Configurar el correo una vez por equipo

1. En la carpeta del programa, copie `configuracion_correo.ejemplo.json` y llame a la copia `configuracion_correo.json`, si este último archivo aún no existe.
2. Abra la copia con un editor de texto. Complete `host`, `puerto`, `usuario`, `clave` y `remitente`. La cuenta de Gmail preparada usa `smtp.gmail.com`, puerto `587` y su propia contraseña de aplicación.
3. Guarde la contraseña de aplicación dentro de las comillas del campo `clave`, sin los espacios visuales que pudiera mostrar Google. Mantenga la sintaxis JSON; no comparta la contraseña por chat.
4. Guarde el archivo. IDLE podrá leerlo en las próximas ejecuciones. Si existen variables de entorno SMTP completas, estas tienen prioridad sobre el archivo.

La contraseña queda **legible** en el archivo local: limite el acceso a su cuenta del equipo y no lo incluya en la entrega ni en archivos compartidos. El archivo de ejemplo no necesita contener una contraseña. El correo requiere internet y una cuenta SMTP habilitada; el servicio receptor puede dirigir el mensaje a Spam.

## 3. Abrir y salir

En IDLE, abra `proyecto_entrega_1.py` y seleccione **Run > Run Module** o presione **F5**. Asegúrese de que el directorio de trabajo sea `proyecto_entrega_1`. También puede abrir una terminal en esa carpeta y ejecutar:

```text
python proyecto_entrega_1.py
```

Use `python3` en lugar de `python` si así se llama Python en su equipo. En el menú principal, digite `1` para Libros, `2` para Usuarios o `3` para Préstamos. Digite el número y presione Enter. `0` regresa al menú anterior o cierra el programa desde el menú principal. En operaciones individuales puede cancelar cuando se ofrezca esa opción.

## 4. Datos y restricciones

- Los datos de texto se capturan en mayúsculas automáticamente; se permiten tildes. Los identificadores con y sin tilde son distintos.
- Ningún campo solicitado puede quedar vacío. Los textos admiten hasta 120 caracteres imprimibles.
- Documento y teléfono: solo dígitos, entre 1 y 30, sin espacios ni signos. Los ceros iniciales se conservan.
- Las fechas se digitan como `dd/mm/aaaa`, por ejemplo `05/07/2026`. La fecha debe existir; el programa solicita nuevamente un dato inválido.
- El correo debe tener una estructura aceptada, como `PERSONA@EJEMPLO.COM`. Verifique que la dirección exista y reciba mensajes. Se almacena en mayúsculas; algunos servidores podrían distinguirlas en la parte anterior a `@`.
- El identificador de libro y el documento del usuario no pueden repetirse; los números de préstamo son asignados automáticamente.

## 5. Módulo de libros

1. **Registrar libro:** seleccione `1`, ingrese identificador, título, autor, género y fecha de publicación. El libro queda disponible.
2. **Actualizar estado:** seleccione `2` e ingrese el identificador. Vea el estado actual y, si corresponde, digite `1` para cambiar entre disponible y mantenimiento o `0` para cancelar. Un libro prestado se libera registrando la devolución.
3. **Consultar disponibilidad:** seleccione `3` e ingrese el identificador para ver título y estado.
4. **Consultar datos:** seleccione `4` e ingrese el identificador para ver todos los datos vigentes del libro.
5. **Muestra del catálogo:** seleccione `5` para ver hasta 100 libros con identificador, título, autor y estado. La muestra no representa necesariamente todo el catálogo.

## 6. Módulo de usuarios

1. **Crear usuario:** seleccione `1` e ingrese documento, nombre, apellido, dirección, teléfono y correo.
2. **Actualizar contacto:** seleccione `2` e ingrese el documento. El sistema muestra los valores actuales. Seleccione `1` para dirección, `2` para teléfono, `3` para correo o `0` para cancelar. Se cambia un dato por operación.
3. **Consultar usuario:** seleccione `3` e ingrese el documento para ver sus datos actuales.
4. **Muestra de usuarios:** seleccione `4` para ver hasta 100 documentos y nombres; puede haber más usuarios que no aparecen en la muestra.

## 7. Módulo de préstamos

1. **Registrar préstamo:** seleccione `1`, ingrese el documento del usuario y el identificador del libro. El sistema muestra la fecha de inicio tomada del equipo; digite la fecha de devolución, igual o posterior al inicio. Si las validaciones se cumplen, muestra el número del préstamo, guarda el PDF en `comprobantes/` e intenta enviarlo automáticamente. Anote el número.
2. **Registrar devolución:** seleccione `2` y digite el número. Revise usuario, libro y estado; digite `1` para confirmar o `0` para cancelar. El libro queda disponible al confirmar.
3. **Consultar préstamos de usuario:** seleccione `3` y digite el documento. Se muestra el historial del más reciente al más antiguo en páginas de hasta 100. Si hay más, digite `1` para continuar o `0` para volver.
4. **Generar y enviar comprobante nuevamente:** seleccione `4` y digite el número para reintentar la generación y el envío con la información actual del préstamo.
5. **Muestra de préstamos:** seleccione `5` para ver hasta 100 préstamos recientes con número, documento, libro y estado.

Un préstamo sin devolver está **vigente** hasta el día de devolución pactado, inclusive, y **vencido** desde el día siguiente. Una devolución registrada cambia el estado a **devuelto**. El programa no presta a un usuario que tenga otro préstamo sin devolver, sea vigente o vencido; el libro también debe estar disponible.

## 8. Ejemplo completo de uso

1. En Libros → `1`, registre el libro `EJ001`, título `EJEMPLO`, autor `AUTOR`, género `NOVELA` y fecha `01/01/2020`.
2. En Usuarios → `1`, registre documento `10001`, nombre, apellido, dirección, teléfono y un correo real al que tenga acceso.
3. En Préstamos → `1`, ingrese `10001` y `EJ001`. Revise la fecha de inicio mostrada y digite una fecha de devolución igual o posterior, por ejemplo el día siguiente.
4. Anote el número mostrado. Verifique el PDF en `comprobantes/` y el mensaje en la cuenta destinataria, incluida la carpeta de Spam.
5. Consulte el historial con Préstamos → `3` y documento `10001`.
6. Para devolverlo, use Préstamos → `2`, digite el número y confirme con `1`. El libro vuelve a disponible.

Use identificadores que no existan ya en su base. Las direcciones `example.com` de los datos ficticios no sirven para comprobar la recepción real.

## 9. Problemas frecuentes

| Mensaje o situación | Qué revisar |
| --- | --- |
| Registro o usuario no encontrado | Compruebe el identificador o documento; consulte la muestra del módulo. Verifique también el directorio de trabajo y la base usada. |
| Identificador duplicado | Use uno diferente o consulte el registro existente. |
| Libro en préstamo o mantenimiento | Consulte su estado. Registre la devolución si está prestado o cambie de mantenimiento a disponible cuando corresponda. |
| Usuario con préstamo sin devolver | Consulte el historial y registre la devolución antes de solicitar otro libro. |
| Fecha inválida o anterior al inicio | Escriba una fecha real como `05/07/2026`, igual o posterior al inicio. Revise el reloj del equipo. |
| No fue posible generar o enviar el comprobante | El préstamo permanece registrado. Revise permisos de la carpeta, configuración JSON, cuenta y contraseña de aplicación, internet y servidor SMTP; luego reintente desde Préstamos → `4`. Si el PDF no se generó, no habrá archivo para ese intento. |
| El correo no aparece en Recibidos | Revise Spam y que el usuario tenga el correo correcto. «Enviado» por el programa no garantiza que el destinatario lo haya recibido. |
| Error de acceso a la base | Compruebe permisos, que no esté bloqueada y que el directorio de trabajo sea el esperado. No reemplace una base existente sin respaldo. |

El programa usa los datos actuales al regenerar un comprobante. No elimina registros ni ofrece modificar datos bibliográficos distintos del estado.
