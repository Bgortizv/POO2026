# Sistema de gestión de biblioteca

## 1. Descripción general

Este programa es una aplicación de consola para administrar una
biblioteca. Permite registrar y consultar usuarios, registrar libros,
actualizar su estado y gestionar los préstamos y las devoluciones.

El sistema utiliza una base de datos SQLite almacenada localmente en el
archivo `ParcialDos.db`. Al iniciar, establece la conexión y crea las
tablas necesarias si todavía no existen.

Las funciones principales se organizan en tres módulos:

-   **Usuarios:** registro de usuarios, actualización de sus datos de
    contacto y consulta de su información.
-   **Libros:** registro de libros, actualización de su estado y
    consulta de disponibilidad o información general.
-   **Préstamos:** registro de préstamos, registro de devoluciones y
    consulta del historial de préstamos de un usuario.

Al registrar un préstamo, el sistema comprueba que el usuario exista,
que no tenga otro préstamo vigente y que el libro esté disponible. La
fecha de devolución prevista se calcula a siete días de la fecha de
inicio. Después de registrar el préstamo, se genera un comprobante PDF y
se intenta enviarlo al correo electrónico del usuario.

El comprobante se guarda en la carpeta `comprobantes`, que se crea
automáticamente si no existe.

## 2. Requerimientos del programa

### 2.1. Requerimientos de software

-   Python **3.9.10**.
-   SQLite, mediante el módulo `sqlite3` incluido en la biblioteca
    estándar de Python.
-   Módulos de biblioteca estándar:
    -   `re`: validación de datos mediante expresiones regulares.
    -   `os`: operaciones del sistema, como limpiar o pausar la consola
        y crear carpetas.
    -   `datetime`: manejo de fechas.
    -   `smtplib`: conexión y envío de mensajes por SMTP.
    -   `email.message`: construcción del mensaje de correo.
-   ReportLab **4.2.5**, para generar los comprobantes PDF.

### 2.2. Instalación

1.  Instalar Python 3.9.10.

2.  Abrir una terminal en la carpeta del proyecto.

3.  Instalar la versión requerida de ReportLab:

    ``` bash
    python -m pip install "reportlab==4.2.5"
    ```

No es necesario instalar SQLite ni los demás módulos mencionados, ya que
forman parte de la biblioteca estándar de Python.

### 2.3. Ejecución

Desde la terminal, ubicarse en la carpeta que contiene el archivo del
programa y ejecutar:

``` bash
python parcial2.py
```

El nombre del comando debe ajustarse al nombre real con el que se haya
guardado el archivo.

En el primer inicio se crea automáticamente `ParcialDos.db` y se generan
las tablas que no existan. En ejecuciones posteriores se utiliza la
misma base de datos, conservando los registros almacenados.

El programa utiliza comandos de consola como `cls` y `pause`, pensados
para Windows.

### 2.4. Configuración y prueba del correo

La función de comprobantes utiliza SMTP con una cuenta de prueba de
Ethereal Email. Este servicio permite inspeccionar los mensajes de
prueba, pero **no entrega los correos al destinatario real**.

Para revisar un mensaje enviado por la aplicación, se puede ingresar en
<https://ethereal.email/> con las credenciales de prueba incluidas en el
código fuente. Las credenciales deben tratarse como datos de
configuración de prueba y no reutilizarse en un entorno real.

Para utilizar un servidor SMTP real, deben reemplazarse los parámetros
`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER` y `SMTP_PASSWORD` dentro de
`generar_comprobante_prestamo()`, de acuerdo con los datos suministrados
por el proveedor de correo. También debe verificarse la configuración de
seguridad y autenticación exigida por dicho servidor.

## 3. Diseño lógico: estructura de la base de datos

La base de datos se denomina `ParcialDos.db` y está compuesta por tres
tablas: `usuarios`, `libros` y `prestamos`.

### 3.1. Tabla `usuarios`

Almacena los datos de identificación y contacto de cada usuario.

  ------------------------------------------------------------------------
  Campo              Tipo              Restricción       Descripción
  ------------------ ----------------- ----------------- -----------------
  `identificacion`   TEXT              Clave primaria,   Número de
                                       NOT NULL          identificación
                                                         del usuario.

  `nombres`          TEXT              NOT NULL          Nombres del
                                                         usuario.

  `apellidos`        TEXT              NOT NULL          Apellidos del
                                                         usuario.

  `direccion`        TEXT              NOT NULL          Dirección de
                                                         residencia.

  `telefono`         TEXT              NOT NULL          Número de
                                                         contacto.

  `email`            TEXT              NOT NULL          Correo
                                                         electrónico.
  ------------------------------------------------------------------------

La identificación es única y se utiliza para relacionar al usuario con
sus préstamos.

### 3.2. Tabla `libros`

Almacena la información bibliográfica y el estado de cada libro.

  --------------------------------------------------------------------------
  Campo                Tipo              Restricción       Descripción
  -------------------- ----------------- ----------------- -----------------
  `identificador`      ---               Clave primaria,   Código único del
                                         NOT NULL          libro.

  `titulo`             TEXT              NOT NULL          Título del libro.

  `autor`              TEXT              NOT NULL          Autor del libro.

  `genero`             TEXT              NOT NULL          Género literario.

  `fechaPublicacion`   DATE              NOT NULL          Fecha de
                                                           publicación.

  `estado`             TEXT              NOT NULL          Estado actual del
                                                           libro.
  --------------------------------------------------------------------------

Los estados que maneja la aplicación son `Disponible`, `Prestado` y
`En mantenimiento`. Al registrar un libro nuevo, su estado inicial es
`Disponible`.

### 3.3. Tabla `prestamos`

Registra cada operación de préstamo y su estado.

  -------------------------------------------------------------------------------
  Campo                     Tipo              Restricción       Descripción
  ------------------------- ----------------- ----------------- -----------------
  `id`                      INTEGER           Clave primaria,   Identificador
                                              AUTOINCREMENT     único del
                                                                préstamo.

  `identificacionUsuario`   TEXT              NOT NULL, clave   Identificación
                                              foránea           del usuario que
                                                                recibe el libro.

  `identificacionLibro`     TEXT              NOT NULL, clave   Identificador del
                                              foránea           libro prestado.

  `fechaInicio`             DATE              NOT NULL          Fecha de inicio
                                                                del préstamo.

  `fechaDevolucion`         DATE              Puede ser NULL    Fecha de
                                              según la          devolución
                                              definición        registrada o
                                                                prevista.

  `estado`                  TEXT              NOT NULL          Estado del
                                                                préstamo:
                                                                `vigente` o
                                                                `devuelto`.
  -------------------------------------------------------------------------------

Las claves foráneas relacionan `prestamos.identificacionUsuario` con
`usuarios.identificacion` y `prestamos.identificacionLibro` con
`libros.identificador`. En la definición se especifican las acciones
`ON UPDATE CASCADE` y `ON DELETE CASCADE`.

### 3.4. Relaciones entre tablas

-   **Usuarios 1:N Préstamos:** un usuario puede tener varios préstamos
    registrados a lo largo del tiempo; cada préstamo pertenece a un
    usuario.
-   **Libros 1:N Préstamos:** un libro puede aparecer en distintos
    préstamos a lo largo del tiempo; cada préstamo corresponde a un
    libro.
-   **Préstamos:** funciona como tabla de relación entre usuarios y
    libros y conserva el historial de las operaciones.

Representación simplificada:

``` text
USUARIOS                         LIBROS
----------------------           ----------------------
PK identificacion                PK identificador
   nombres                          titulo
   apellidos                        autor
   direccion                        genero
   telefono                         fechaPublicacion
   email                            estado
       |                                |
       | 1                              | 1
       |                                |
       +---------- N PRESTAMOS N -------+
                  ----------------------
                  PK id
                  FK identificacionUsuario
                  FK identificacionLibro
                     fechaInicio
                     fechaDevolucion
                     estado
```

**Observación sobre las fechas:** aunque las columnas están declaradas
como `DATE`, las funciones de préstamo guardan las fechas como cadenas
con formato `DD/MM/AAAA`. SQLite permite almacenar estos valores, pues 
las guarda en realidad como texto plano.

## 4. Casos de uso

Los siguientes casos corresponden a las opciones funcionales de los
submenús. Se excluyen las opciones para volver al menú principal y salir
del programa.

### 4.1. Módulo de usuarios

#### CU-01. Registrar usuario

-   **Opción del menú:** Usuarios → 1. Crear un usuario nuevo.
-   **Precondiciones:**
    -   Existe la base de datos y hay una conexión activa.
-   **Datos de entrada:**
    -   Número de identificación.
    -   Nombres.
    -   Apellidos.
    -   Dirección.
    -   Teléfono.
    -   Correo electrónico.
-   **Proceso:**
    1.  Solicita los datos del usuario.
    2.  Valida cada entrada mediante expresiones regulares.
    3.  Inserta el registro en la tabla `usuarios`.
    4.  Si la inserción afecta una fila, confirma la transacción y
        muestra un mensaje de éxito.
-   **Datos de salida:**
    -   Mensaje de confirmación si el registro se realiza.
    -   Mensaje de error si no se puede crear el usuario.
-   **Poscondiciones:**
    -   Si la operación tiene éxito, el usuario queda almacenado en
        `usuarios`.
    -   Si falla, no se confirma la inserción.

#### CU-02. Actualizar información de contacto

-   **Opción del menú:** Usuarios → 2. Actualizar información de
    contacto.
-   **Precondiciones:**
    -   la base de datos existe y hay una coneccion activa.
    -   El usuario que se desea modificar debe estar registrado.
-   **Datos de entrada:**
    -   Número de identificación del usuario.
    -   Nueva dirección.
    -   Nuevo teléfono.
    -   Nuevo correo electrónico.
-   **Proceso:**
    1.  Solicita y valida el número de identificación.
    2.  Busca al usuario en la tabla `usuarios`.
    3.  Si no existe, informa el error y termina la operación.
    4.  Si existe, solicita los nuevos datos de contacto y los valida.
    5.  Actualiza únicamente `direccion`, `telefono` y `email`.
    6.  Confirma los cambios si se actualizó una fila.
-   **Datos de salida:**
    -   Mensaje de actualización exitosa o mensaje de error.
-   **Poscondiciones:**
    -   Si la operación tiene éxito, los datos de contacto quedan
        actualizados.
    -   La identificación, los nombres y los apellidos permanecen sin
        cambios.

#### CU-03. Consultar información de usuario

-   **Opción del menú:** Usuarios → 3. Consultar información vigente de
    un usuario.
-   **Precondiciones:**
    -   El programa está en ejecución y conectado a la base de datos.
    -   El usuario debe estar registrado.
-   **Datos de entrada:**
    -   Número de identificación.
-   **Proceso:**
    1.  Solicita y valida el número de identificación.
    2.  Busca el registro correspondiente en `usuarios`.
    3.  Recupera los datos y los presenta en pantalla.
-   **Datos de salida:**
    -   Identificación, nombres, apellidos, dirección, teléfono y correo
        electrónico.
-   **Poscondiciones:**
    -   La base de datos no se modifica.
    -   El usuario obtiene la información almacenada para la
        identificación consultada.

### 4.2. Módulo de libros

#### CU-04. Registrar libro

-   **Opción del menú:** Libros → 1. Registrar un libro.
-   **Precondiciones:**
    -  La base de datos existe y hay una conexion activa.
-   **Datos de entrada:**
    -   Identificador del libro.
    -   Título.
    -   Autor.
    -   Género.
    -   Fecha de publicación.
-   **Proceso:**
    1.  Solicita los datos del libro.
    2.  Valida las entradas mediante expresiones regulares.
    3.  Asigna automáticamente el estado `Disponible`.
    4.  Inserta el registro en la tabla `libros`.
    5.  Confirma la transacción si la inserción afecta una fila.
-   **Datos de salida:**
    -   Mensaje de registro exitoso o mensaje de error.
-   **Poscondiciones:**
    -   Si la operación tiene éxito, el libro queda registrado con
        estado `Disponible`.
    -   Si falla, la inserción no se confirma.

#### CU-05. Actualizar estado de un libro

-   **Opción del menú:** Libros → 2. Actualizar estado de un libro.
-   **Precondiciones:**
    -   La base de datos existe y hay una conexion activa.
    -   El libro debe existir.
-   **Datos de entrada:**
    -   Identificador del libro.
    -   Nuevo estado, seleccionado entre:
        1.  Disponible.
        2.  Prestado.
        3.  En mantenimiento.
-   **Proceso:**
    1.  Solicita y valida el identificador.
    2.  Comprueba que el libro exista.
    3.  Solicita el nuevo estado y valida que la opción sea de 1 a 3.
    4.  Convierte la opción seleccionada al texto correspondiente.
    5.  Actualiza el campo `estado` del libro y confirma la transacción.
-   **Datos de salida:**
    -   Mensaje de actualización exitosa o mensaje de error.
-   **Poscondiciones:**
    -   Si la operación tiene éxito, el libro queda con el nuevo estado.
    -   Los demás datos del libro no se modifican.

#### CU-06. Consultar disponibilidad de un libro

-   **Opción del menú:** Libros → 3. Consultar disponibilidad de un
    libro.
-   **Precondiciones:**
    -   La base de datos existe y hay una conexion activa.
-   **Datos de entrada:**
    -   Identificador del libro.
-   **Proceso:**
    1.  Solicita y valida el identificador.
    2.  Consulta el campo `estado` en la tabla `libros`.
    3.  Informa si el libro no existe o muestra el estado encontrado.
-   **Datos de salida:**
    -   Estado del libro (`Disponible`, `Prestado` o `En mantenimiento`)
        o mensaje de inexistencia.
-   **Poscondiciones:**
    -   La base de datos no se modifica.

#### CU-07. Consultar datos de un libro

-   **Opción del menú:** Libros → 4. Consultar datos vigentes de un
    libro.
-   **Precondiciones:**
    -   El libro debe existir para obtener sus datos.
-   **Datos de entrada:**
    -   Identificador del libro.
-   **Proceso:**
    1.  Solicita y valida el identificador.
    2.  Busca el registro en `libros`.
    3.  Si existe, muestra todos sus campos; de lo contrario, informa
        que no existe.
-   **Datos de salida:**
    -   Identificador, título, autor, género, fecha de publicación y
        estado.
-   **Poscondiciones:**
    -   La base de datos no se modifica.

### 4.3. Módulo de préstamos

#### CU-08. Registrar préstamo

-   **Opción del menú:** Préstamos → 1. Registrar préstamo.
-   **Precondiciones:**
    -   El usuario debe estar registrado.
    -   El usuario no debe tener otro préstamo con estado `vigente`.
    -   El libro debe estar registrado y tener estado `Disponible`.
-   **Datos de entrada:**
    -   Identificación del usuario.
    -   Identificador del libro.
-   **Proceso:**
    1.  Solicita y valida la identificación del usuario.
    2.  Comprueba que el usuario exista.
    3.  Consulta si tiene un préstamo vigente. Si lo tiene, cancela la
        operación.
    4.  Solicita y valida el identificador del libro.
    5.  Comprueba que el libro exista y esté disponible.
    6.  Calcula la fecha de inicio con la fecha actual y la fecha
        prevista de devolución siete días después.
    7.  Inserta el préstamo con estado `vigente`.
    8.  Recupera el identificador generado automáticamente para el
        préstamo.
    9.  Cambia el estado del libro a `Prestado` y confirma los cambios.
    10. Muestra los datos principales del préstamo y llama a
        `generar_comprobante_prestamo()` para crear el PDF e intentar
        enviarlo por correo.
-   **Datos de salida:**
    -   Identificador del préstamo.
    -   Identificación del usuario y del libro.
    -   Fecha de inicio y fecha prevista de devolución.
    -   Estado del préstamo.
    -   Comprobante PDF en la carpeta `comprobantes`.
    -   Mensaje sobre el resultado del intento de envío del correo.
-   **Poscondiciones:**
    -   Si el registro tiene éxito, se crea un préstamo `vigente` y el
        libro pasa a estado `Prestado`.
    -   Si falla la inserción, se ejecuta `rollback()` para revertir la
        transacción.
    -   La generación o el envío del comprobante se realiza después de
        confirmar el préstamo; un fallo de correo no equivale a deshacer
        el préstamo.

#### CU-09. Registrar devolución

-   **Opción del menú:** Préstamos → 2. Registrar devolución de un
    libro.
-   **Precondiciones:**
    -   Debe existir un préstamo con el identificador indicado y estado
        `vigente`.
-   **Datos de entrada:**
    -   Identificador numérico del préstamo.
-   **Proceso:**
    1.  Solicita y valida el identificador del préstamo.
    2.  Busca el préstamo y comprueba que esté vigente.
    3.  Obtiene el identificador del libro asociado.
    4.  Registra la fecha actual como fecha de devolución.
    5.  Cambia el estado del préstamo a `devuelto`.
    6.  Cambia el estado del libro a `Disponible`.
    7.  Confirma los cambios y muestra un mensaje de éxito.
-   **Datos de salida:**
    -   Mensaje de devolución registrada o mensaje indicando que el
        préstamo no existe o ya fue devuelto.
-   **Poscondiciones:**
    -   El préstamo queda con estado `devuelto` y fecha de devolución
        actualizada.
    -   El libro asociado queda con estado `Disponible`.

#### CU-10. Consultar préstamos de un usuario

-   **Opción del menú:** Préstamos → 3. Consultar estado de préstamos
    por usuario.
-   **Precondiciones:**
    -   El usuario debe estar registrado.
-   **Datos de entrada:**
    -   Número de identificación del usuario.
-   **Proceso:**
    1.  Solicita y valida la identificación.
    2.  Comprueba que el usuario exista.
    3.  Consulta los préstamos asociados a la identificación y obtiene
        el título del libro mediante una unión (inner join) con la tabla `libros`.
    4.  Ordena los resultados por identificador de préstamo y los
        presenta en pantalla.
    5.  Si no hay registros, informa que el usuario no tiene préstamos
        registrados.
-   **Datos de salida:**
    -   Identificación y nombre del usuario.
    -   Para cada préstamo: identificador, título del libro y estado.
    -   Mensaje informativo si no existen préstamos.
-   **Poscondiciones:**
    -   La base de datos no se modifica.

## 5. Diseño técnico: funciones implementadas

### 5.1. Conexión y funciones auxiliares

  -------------------------------------------------------------------------
  Función                               Descripción
  ------------------------------------- -----------------------------------
  `conectar()`                          Abre una conexión con la base de
                                        datos SQLite `ParcialDos.db`.
                                        Devuelve el objeto de conexión para
                                        que las demás funciones puedan
                                        ejecutar consultas.

  `validar_dato(regex, nombre_campo)`   Solicita un dato por consola y lo
                                        compara con la expresión regular
                                        recibida. Si no cumple el patrón,
                                        muestra un error y vuelve a
                                        solicitarlo; si es válido, devuelve
                                        la cadena ingresada.

  `crear_tablas(DB_con)`                Crea las tablas `libros`,
                                        `usuarios` y `prestamos` si no
                                        existen. Define sus claves
                                        primarias y las claves foráneas de
                                        préstamos, y confirma la creación
                                        con `commit()`.
  -------------------------------------------------------------------------

### 5.2. Módulo de usuarios

  -----------------------------------------------------------------------
  Función                             Descripción
  ----------------------------------- -----------------------------------
  `usuario_nuevo(DB_con)`             Solicita identificación, nombres,
                                      apellidos, dirección, teléfono y
                                      correo; valida los campos e inserta
                                      el nuevo usuario en la tabla
                                      `usuarios`.

  `actualizar_info_usuario(DB_con)`   Busca un usuario por identificación
                                      y, si existe, actualiza su
                                      dirección, teléfono y correo
                                      electrónico.

  `consultar_usuario(DB_con)`         Busca un usuario por identificación
                                      y muestra sus datos personales y de
                                      contacto.
  -----------------------------------------------------------------------

### 5.3. Módulo de libros

  ------------------------------------------------------------------------------
  Función                                    Descripción
  ------------------------------------------ -----------------------------------
  `libro_nuevo(DB_con)`                      Solicita y valida los datos
                                             bibliográficos, asigna el estado
                                             inicial `Disponible` e inserta el
                                             libro en `libros`.

  `actualizar_estado_libro(DB_con)`          Comprueba la existencia de un
                                             libro, solicita uno de los tres
                                             estados permitidos y actualiza su
                                             campo `estado`.

  `consultar_disponibilidad_libro(DB_con)`   Busca un libro por identificador y
                                             muestra únicamente su estado o un
                                             mensaje si no existe.

  `consultar_datos_libro(DB_con)`            Consulta y muestra todos los datos
                                             almacenados de un libro
                                             identificado por su código.
  ------------------------------------------------------------------------------

### 5.4. Módulo de préstamos y comprobantes

  ----------------------------------------------------------------------------------------
  Función                                              Descripción
  ---------------------------------------------------- -----------------------------------
  `prestamo_nuevo(DB_con)`                             Verifica la existencia del usuario,
                                                       que no tenga un préstamo vigente y
                                                       que el libro exista y esté
                                                       disponible. Calcula las fechas,
                                                       registra el préstamo, actualiza el
                                                       estado del libro, obtiene el ID
                                                       generado y solicita la generación
                                                       del comprobante.

  `registrar_devolucion(DB_con)`                       Busca un préstamo vigente por su
                                                       ID. Registra la fecha actual como
                                                       devolución, cambia el préstamo a
                                                       `devuelto` y devuelve el libro al
                                                       estado `Disponible`.

  `consultar_prestamos_usuario(DB_con)`                Consulta el historial de préstamos
                                                       de un usuario mediante una unión
                                                       entre `prestamos` y `libros`.
                                                       Muestra el ID, el título y el
                                                       estado de cada préstamo.

  `generar_comprobante_prestamo(DB_con, idPrestamo)`   Consulta los datos del préstamo,
                                                       del usuario y del libro mediante
                                                       `INNER JOIN`; genera un PDF con
                                                       ReportLab en la carpeta
                                                       `comprobantes`, construye un correo
                                                       con el archivo adjunto e intenta
                                                       enviarlo mediante SMTP con
                                                       STARTTLS.
  ----------------------------------------------------------------------------------------

### 5.5. Menús y control del programa

  -----------------------------------------------------------------------
  Función                             Descripción
  ----------------------------------- -----------------------------------
  `menu()`                            Presenta el menú principal y valida
                                      que la opción ingresada sea una de
                                      las disponibles. Devuelve el número
                                      seleccionado o `0` si la entrada no
                                      es válida.

  `menu_usuarios()`                   Presenta las opciones del módulo de
                                      usuarios y devuelve la selección
                                      validada.

  `menu_libros()`                     Presenta las opciones del módulo de
                                      libros y devuelve la selección
                                      validada.

  `menu_prestamos()`                  Presenta las opciones del módulo de
                                      préstamos y devuelve la selección
                                      validada.

  `main()`                            Es el punto de entrada y
                                      coordinador general. Abre la
                                      conexión, crea las tablas, muestra
                                      el menú principal, dirige la
                                      ejecución a los submenús y llama a
                                      la función correspondiente. Al
                                      seleccionar salir, cierra la
                                      conexión.
  -----------------------------------------------------------------------

### 5.6. Variables y validaciones globales

El programa utiliza la variable global `CONTROL` para mantener activo el
ciclo principal hasta que el usuario selecciona la opción de salir.

También define expresiones regulares reutilizables:

  -----------------------------------------------------------------------
  Expresión                           Uso
  ----------------------------------- -----------------------------------
  `SOLO_TEXTO`                        Valida nombres, apellidos, autores
                                      y géneros: letras, espacios y
                                      caracteres acentuados, con un
                                      máximo de 50 caracteres.

  `SOLO_EMAIL`                        Valida la estructura general de una
                                      dirección de correo electrónico.

  `SOLO_TELEF`                        Valida números telefónicos
                                      colombianos móviles o fijos, con
                                      prefijo `+57` opcional.

  `SOLO_ADDRS`                        Valida direcciones con una
                                      estructura básica de nomenclatura
                                      colombiana.

  `TEXTO_LARG`                        Valida textos de hasta 150
                                      caracteres, utilizados
                                      principalmente para títulos.
  -----------------------------------------------------------------------

Además, algunas funciones utilizan expresiones regulares específicas
para validar identificaciones, códigos de libros, fechas e
identificadores de préstamos.

## 6. Consideraciones y limitaciones conocidas

-   La validación de fechas de publicación comprueba el formato
    pero no verifica por sí sola que la fecha exista en el calendario.
-   La aplicación utiliza consultas SQL construidas mediante cadenas
    f-string. Haciendolas vulnerables a ataques SQL (mojor seria usar
    'prepared statements').
-   Los comandos `cls` y `pause` dependen de la consola de Windows.
-   El envío de correo está configurado inicialmente para pruebas con
    Ethereal Email; no representa una entrega real al usuario.
-   La activación efectiva de claves foráneas en SQLite requiere
    habilitarlas en la conexión mediante `PRAGMA foreign_keys = ON`, 
    sentencia que por facilidad del desarroyo se omite.
