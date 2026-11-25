"""
REQUERIMIENTOS:
    Python 3.9.10
    sqlite3
    re 
    os
    datetime
    smtplib 
    reportlab 4.2.5 (IMPORTANTE: requiere instalacion de la version indicada, por ejemplo via pip: pip install "reportlab==4.2.5")

NOTAS: Para comprobar el funcionamiento del SMTP se uso el servicio de etherealmail que NO envia los 
correos realmente y las cuentas son desechables por lo que las credenciales se pueden compartir sim mucho daño
para verificar que el mensaje se envio:
    vaya a "https://ethereal.email/" y use
        usuario: "neil.langosh40@ethereal.email"
        contraseña: "7GqMT1wPm6jEHGkVwh"
    RETIRE LAS COMILLAS DE USUARIO, CONTRASEÑA Y LA PAGINA WEB 
si desea comprobar en realidad configure un servidor SMTP real en las lineas 441 a 444
"""
#importacion de librerias 

import sqlite3 #control de la base de datos
from sqlite3 import Error #control de errores en la conexion u operaciones de la base de datos
from datetime import date, timedelta #permite usar la fecha del sistema y darle formato segun se requiera
import re #manejo de expresiones regulares (para validar cadenas)
import os #funciones del systema base, la usamos para parar la ejecucion del programa y limpiar la pantalla
import smtplib #libreria para enviar correos via SMTP
from email.message import EmailMessage #libreria para formatear mensajes de correo electronico
from reportlab.lib.styles import getSampleStyleSheet #contiene los estilos estandar de reportlab (generador del pdf)
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer #permite generar reportes, por ejemplo en PDF

#variables globales
CONTROL = True #El programa se mantiene ejecutando mientras verdera

#expresiones regulares
SOLO_TEXTO = re.compile(r"^(?=.{1,50}$)[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]+(?: [a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]+)*$") #permite validar cadenas no vacias de hasta 50 caracteres, solo letras (incluyendo ñ y tildes) y espacios (no inicial ni final)
SOLO_EMAIL = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,5}$") #permite validar correos electronicos
SOLO_TELEF = re.compile(r"^(?:\+57\s?)?(?:3\d{9}|60[1-8]\d{7})$") #permite validar telefonos COLOMBIANOS
SOLO_ADDRS = re.compile(r"^[a-zA-Z]+\s+\d+[a-zA-Z]?\s*#?\s*\d+\s*-?\s*\d+$") #permite validar direcciones en formato colombia
TEXTO_LARG = re.compile(r"^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑüÜ .,:;!?¿¡()\-–—]{1,150}$") #permite validar cadenas no vacias de hasta 150 caracteres, alfanumericas con espacios, tildes y signos de puntuacion

#control de la base de datos (conexion)
def conectar():
    """Crea el objeto de conexion de la base de datos"""
    try:
        con = sqlite3.connect("ParcialDos.db")
        print("conectado")
        return con
    except Error:
        print(Error)

#funciones auxiliares
def validar_dato(regex, nombre_campo):
    """valida que el dato ingresado por el usuario pase la expresion regular correspondiente,
    si no lo hace muestra un error y solicita el dato nuevamente"""

    while True: #el usuario debe ingresar un dato valido para poder continuar
        text = f"Por favor digite {nombre_campo}: "
        error = f"CAMPO INVALIDO, por favor digite un {nombre_campo} valido!\n "
        
        dato = input(text)

        if regex.fullmatch(dato): #valida que el dato coincida con la expresion regular
            # print(f"dato valido:\n dato -> {dato} \n nombre campo: {nombre_campo}") #Linea de prueba
            return dato
        else: #Si no coincide muestra un error y vulve a ejecutar la funcion
            print(error) 




#Creacion de tablas base de datos
def crear_tablas(DB_con):
    """Revisa si existen las tablas requeridas en la base de datos, si no existen las crea"""

    #cursor (base de datos)
    cursor = DB_con.cursor()

    #tabla libros
    query = "CREATE TABLE IF NOT EXISTS libros( " \
        "identificador  NOT NULL, " \
        "titulo text NOT NULL, " \
        "autor text NOT NULL, " \
        "genero text NOT NULL, " \
        "fechaPublicacion date NOT NULL, " \
        "estado text NOT NULL, " \
        "PRIMARY KEY(identificador))"
    #print(query)
    cursor.execute(query)

    #tabla usuarios
    query = "CREATE TABLE IF NOT EXISTS usuarios( " \
        "identificacion text NOT NULL, " \
        "nombres TEXT NOT NULL, " \
        "apellidos TEXT NOT NULL, " \
        "direccion TEXT NOT NULL, " \
        "telefono TEXT NOT NULL, " \
        "email TEXT NOT NULL, " \
        "PRIMARY KEY(identificacion))"
    #print(query)
    cursor.execute(query)

    #tabla prestamos (la clave primaria queda con autoincremento y claves foraneas hacia usuarios y libros actualizacion y eliminacion en cascada)
    query = "CREATE TABLE IF NOT EXISTS prestamos( " \
            "id INTEGER PRIMARY KEY AUTOINCREMENT, " \
            "identificacionUsuario TEXT NOT NULL, " \
            "identificacionLibro TEXT NOT NULL, " \
            "fechaInicio DATE NOT NULL, " \
            "fechaDevolucion DATE, " \
            "estado TEXT NOT NULL, " \
            "FOREIGN KEY (identificacionUsuario) REFERENCES usuarios(identificacion) " \
            "   ON UPDATE CASCADE ON DELETE CASCADE, " \
            "FOREIGN KEY (identificacionLibro) REFERENCES libros(identificador) " \
            "   ON UPDATE CASCADE ON DELETE CASCADE)" \
            
    #print(query)
    cursor.execute(query)
    DB_con.commit()


#MODULO USUARIO
def usuario_nuevo(DB_con):
    """Ingresa un nuevo usuario a la base de datos, valida los datos ingresados
       por medio de expresiones regulares"""

    #cursor (base de datos)
    cursor = DB_con.cursor()

    #recibiendo datos
    identificacion = validar_dato(re.compile(r"^[1-9]\d{5,11}$"), "numero de identificacion")
    nombres = validar_dato(SOLO_TEXTO, "nombre")
    apellidos = validar_dato(SOLO_TEXTO, "apellido")
    direccion = validar_dato(SOLO_ADDRS, "direccion")
    telefono = validar_dato(SOLO_TELEF, "telefono")
    email = validar_dato(SOLO_EMAIL, "correo electronico")

    query = f"""
        INSERT INTO usuarios (
            identificacion,
            nombres,
            apellidos,
            direccion,
            telefono,
            email
        ) VALUES (
            '{identificacion}',
            '{nombres}',
            '{apellidos}',
            '{direccion}',
            '{telefono}',
            '{email}'
        )
        """
    cursor.execute(query)
    if cursor.rowcount == 1:
        DB_con.commit()
        print("Usuario agregado con exito")
    else:
        print("No se pudo crear el usuario!")

    os.system("pause") #darle tiempo al usuario para que pueda leer el mensaje

def actualizar_info_usuario(DB_con):
    """Ingresa un nuevo usuario a la base de datos, valida los datos ingresados
       por medio de expresiones regulares"""

    #cursor (base de datos)
    cursor = DB_con.cursor()

    #recibiendo datos
    identificacion = validar_dato(re.compile(r"^[1-9]\d{5,11}$"), "numero de identificacion")

    # Validar que el usuario exista
    cursor.execute(f"SELECT identificacion FROM usuarios WHERE identificacion ='{identificacion}'")

    usuario = cursor.fetchone()

    if usuario is None:
        print("\n Error: El usuario no existe en la base de datos!\n")
        return
    
    direccion = validar_dato(SOLO_ADDRS, "direccion")
    telefono = validar_dato(SOLO_TELEF, "telefono")
    email = validar_dato(SOLO_EMAIL, "correo electronico")

    query = f"""
        UPDATE usuarios SET
            direccion = '{direccion}',
            telefono = '{telefono}',
            email = '{email}'
        WHERE identificacion = '{identificacion}'
        """
    cursor.execute(query)
    if cursor.rowcount == 1:
        DB_con.commit()
        print("Datos de usuario modificados con exito")
    else:
        print("Error: No se actualizaron los datos!")

    os.system("pause")

def consultar_usuario(DB_con):
    """Consulta la informacion actualizada de un usuario por su numero de documento"""

    #cursor (base de datos)
    cursor = DB_con.cursor()

    #recibiendo datos
    identificacion = validar_dato(re.compile(r"^[1-9]\d{5,11}$"), "numero de identificacion")

    # Validar que el usuario exista
    cursor.execute( f"SELECT * FROM usuarios WHERE identificacion = '{identificacion}'")

    usuario = cursor.fetchone()
    id, nombres, apellidos, direccion, telefono, email = usuario
    print("\n=======================================\n DATOS DEL USUARIO\n---------------------------------------")
    print("Identificacion: ", id)
    print("Nombre: ", nombres)
    print("Apellido: ", apellidos)
    print("Direccion: ", direccion)
    print("Telefono: ", telefono)
    print("Correo electronico: ", email)
    print("=======================================\n")

    os.system("pause")

#Modulo libros
def libro_nuevo(DB_con):
    """Ingresa un nuevo libro a la base de datos, valida los datos ingresados
       por medio de expresiones regulares"""

    # cursor (base de datos)
    cursor = DB_con.cursor()

    # recibiendo datos
    identificador = validar_dato(re.compile(r"^[a-zA-Z0-9]{3,25}$"), "identificador")
    titulo = validar_dato(TEXTO_LARG, "titulo")
    autor = validar_dato(SOLO_TEXTO, "autor")
    genero = validar_dato(SOLO_TEXTO, "genero")
    fechaPublicacion = validar_dato(
        re.compile(r"^\d{4}-\d{2}-\d{2}$"), "fecha de publicacion (AAAA-MM-DD):"
    )
    estado = "Disponible"

    query = f"""
        INSERT INTO libros (
            identificador,
            titulo,
            autor,
            genero,
            fechaPublicacion,
            estado
        ) VALUES (
            '{identificador}',
            '{titulo}',
            '{autor}',
            '{genero}',
            '{fechaPublicacion}',
            '{estado}'
        )
        """

    cursor.execute(query)

    if cursor.rowcount == 1:
        DB_con.commit()
        print("Libro agregado con exito")
    else:
        print("No se pudo crear el libro!")

    os.system("pause")

def actualizar_estado_libro(DB_con):
    """Actualiza el estado de un libro en la base de datos"""

    # cursor (base de datos)
    cursor = DB_con.cursor()

    # Recibiendo identificador
    identificador = validar_dato(re.compile(r"^[a-zA-Z0-9.,]{3,25}$"), "identificador del libro")

    # Validar que el libro exista
    cursor.execute(f"SELECT identificador FROM libros WHERE identificador = '{identificador}'")

    libro = cursor.fetchone()

    if libro is None:
        print("\nError: El libro no existe en la base de datos!\n")
        os.system("pause")
        return

    # Seleccionar nuevo estado
    while True:
        estado = input("Seleccione el nuevo estado del libro:\n  1. Disponible\n  2. Prestado\n  3. No disponible\n\nSu respuesta: ")

        if estado == '1' or estado == '2' or estado == '3':
            estado = int(estado)
            break
        else:
            print("Error: Debe ingresar un numero entre 1 y 3!")

    # Asociar numero con estado
    estados = {
        1: "Disponible",
        2: "Prestado",
        3: "En mantenimiento"
    }

    estado = estados[estado]

    # Actualizar estado
    query = f"UPDATE libros SET estado = '{estado}' WHERE identificador = '{identificador}'"

    cursor.execute(query)

    if cursor.rowcount == 1:
        DB_con.commit()
        print("\nEstado del libro actualizado con exito")
    else:
        print("\nError: No se pudo actualizar el estado!")

    os.system("pause")

def consultar_disponibilidad_libro(DB_con):
    """Consulta e imprime el estado (la disponibilidad) de un libro"""

    # cursor (base de datos)
    cursor = DB_con.cursor()

    identificador = validar_dato(re.compile(r"^[a-zA-Z0-9.,]{3,25}$"), "identificador libro")
    cursor.execute(f"SELECT estado FROM libros WHERE identificador = '{identificador}'")
    libro = cursor.fetchone()

    # Verificar existencia e imprimir resultado
    if libro is None:
        print("\nError: El libro no existe en la base de datos!")
    else:
        print(f"\nEstado del libro: {libro[0]}")

    os.system("pause")

def consultar_datos_libro(DB_con):
    """Consulta la informacion actualizada de un libro por su identificador"""

    # cursor (base de datos)
    cursor = DB_con.cursor()

    identificador = validar_dato(re.compile(r"^[a-zA-Z0-9.,]{3,25}$"), "identificador libro")

    cursor.execute( f"SELECT * FROM libros WHERE identificador = '{identificador}'")
    libro = cursor.fetchone()

    if libro is None:
        print("\nError: El libro no existe en la base de datos!")
    else:
        id, titulo, autor, genero, fechaPublicacion, estado = libro

        print("\n=======================================")
        print("DATOS DEL LIBRO")
        print("---------------------------------------")
        print(" Identificador: ", id)
        print(" Titulo: ", titulo)
        print(" Autor: ", autor)
        print(" Genero: ", genero)
        print(" Fecha de publicacion: ", fechaPublicacion)
        print(" Estado: ", estado)
        print("=======================================\n")

    os.system("pause")

#MODULO DE PDF y CORREOS

def generar_comprobante_prestamo(DB_con, idPrestamo):
    """Genera un comprobante PDF y lo envia al correo del usuario"""

    cursor = DB_con.cursor()

    # Consultar informacion del prestamo, usuario y libro
    query = f"""
        SELECT prestamos.id, usuarios.nombres, usuarios.apellidos,
            usuarios.direccion, usuarios.telefono, usuarios.email,
            libros.titulo, libros.autor,
            prestamos.fechaInicio, prestamos.fechaDevolucion,
            prestamos.estado
        FROM prestamos
            INNER JOIN usuarios
                ON prestamos.identificacionUsuario = usuarios.identificacion
            INNER JOIN libros
                ON prestamos.identificacionLibro = libros.identificador
        WHERE prestamos.id = {idPrestamo}
    """

    cursor.execute(query)
    datos = cursor.fetchone()

    if datos is None:
        print("Error: No se encontro el prestamo!")
        return
    
    id, nombres, apellidos, direccion, telefono, email, titulo, autor, fechaInicio, fechaDevolucion, estado = datos

    nombre = f"{nombres} {apellidos}"

    # Crear carpeta para guardar comprobantes
    os.makedirs("comprobantes", exist_ok=True)
    rutaPDF = "comprobantes/comprobante_{}.pdf".format(id)

    estilos = getSampleStyleSheet()  # Obtener estilos estandar de la libreia reportlab

    # Ensamblar el PDF
    contenido = []
    contenido.append(Paragraph("COMPROBANTE DE PRESTAMO", estilos["Title"]))
    contenido.append(Paragraph(f"""
        <b>Numero de prestamo:</b> {id}<br/>
        <b>Usuario:</b> {nombre}<br/>
        <b>Direccion:</b> {direccion}<br/>
        <b>Telefono:</b> {telefono}<br/>
        <b>Correo:</b> {email}""",
        estilos["Normal"]
    ))
    contenido.append(Spacer(1, 15))
    contenido.append(Paragraph("INFORMACION DEL LIBRO", estilos["Heading2"]))
    contenido.append(Paragraph(f"""
        <b>Titulo:</b> {titulo}<br/>
        <b>Autor:</b> {autor}<br/>
        <b>Fecha de inicio:</b> {fechaInicio}<br/>
        <b>Fecha de devolucion:</b> {fechaDevolucion}
        """, 
        estilos["Normal"]
    ))

    contenido.append(Spacer(1, 15))
    contenido.append(Paragraph(f"<b>Estado del prestamo:</b> {estado}", estilos["Heading2"]))

    # Generar PDF
    documento = SimpleDocTemplate(rutaPDF)
    documento.build(contenido)

    # Configuracion SMTP para pruebas usando etherealmail (para ver los mensajes usar las credenciales en la pagina web https://ethereal.email/, no envia realmente)
    SMTP_HOST = "smtp.ethereal.email" #NOTA IMPORTANTE: requiere starttsl() (cifrado de mensajes)
    SMTP_PORT = 587
    SMTP_USER = "neil.langosh40@ethereal.email"
    SMTP_PASSWORD = "7GqMT1wPm6jEHGkVwh"

    # Construir correo
    mensaje = EmailMessage()

    mensaje["Subject"] = f"Comprobante de prestamo #{id}"
    mensaje["From"] = SMTP_USER
    mensaje["To"] = email
    mensaje.set_content(f"Comprobante de prestamo libro: #{id}.")

    # Adjuntar comprobante PDF
    with open(rutaPDF, "rb") as archivo: #usando un bloque with para no tener que cerrar el archivo y ebitar errores raros
        mensaje.add_attachment(archivo.read(), maintype="application", subtype="pdf", filename=f"comprobante_{id}.pdf" )

    # Enviar correo
    try: #usando bloque try y with para que un error de envio no mate el entero programa y no quede abierto el SMTP
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as servidor:
            servidor.starttls()
            servidor.login(SMTP_USER, SMTP_PASSWORD)
            servidor.send_message(mensaje)

        print(f"Comprobante de perstamo enviado a {email}")
    except Exception as e:
        print("Error al enviar el correo: {}".format(e))


#MODULO PRESTAMOS

def prestamo_nuevo(DB_con):
    """Registra un nuevo prestamo, verifica que el usuario no tenga
       prestamos vigentes y que el libro este disponible"""

    # cursor (base de datos)
    cursor = DB_con.cursor()

    # Recibiendo identificacion del usuario
    identificacion = validar_dato(re.compile(r"^[1-9]\d{5,11}$"), "numero de identificacion del usuario")

    # Validar que el usuario exista
    cursor.execute(f"SELECT identificacion FROM usuarios WHERE identificacion = '{identificacion}'")

    usuario = cursor.fetchone()

    if usuario is None:
        print("\nError: El usuario no existe en la base de datos!\n")
        os.system("pause")
        return

    # Verificar que el usuario no tenga prestamos vigentes
    cursor.execute(f"SELECT id FROM prestamos WHERE identificacionUsuario = '{identificacion}' AND estado = 'vigente'")

    prestamo = cursor.fetchone()

    if prestamo is not None:
        print("\nError: El usuario ya tiene un prestamo vigente!\n")
        os.system("pause")
        return

    # Recibiendo identificador del libro
    identificador = validar_dato(re.compile(r"^[a-zA-Z0-9.,]{3,25}$"), "identificador del libro")

    # Validar que el libro exista y consultar su estado
    cursor.execute(f"SELECT estado FROM libros WHERE identificador = '{identificador}'")

    libro = cursor.fetchone()

    if libro is None:
        print("\nError: El libro no existe en la base de datos!\n")
        os.system("pause")
        return

    # Verificar disponibilidad del libro
    if libro[0] != "Disponible":
        print("\nError: El libro no se encuentra disponible!\n")
        os.system("pause")
        return

    # Calcular fechas del prestamo y formatearlas al requerimiento (fecha devolucion se calcula como 7 dias despues para no dejar el campo NULL)
    fechaInicio = date.today()
    fechaDevolucion = fechaInicio + timedelta(days=7)
    fechaInicio = fechaInicio.strftime("%d/%m/%Y")
    fechaDevolucion = fechaDevolucion.strftime("%d/%m/%Y")

    # Registrar prestamo
    query = f"""
        INSERT INTO prestamos (
            identificacionUsuario,
            identificacionLibro,
            fechaInicio,
            fechaDevolucion,
            estado
        ) VALUES (
            '{identificacion}',
            '{identificador}',
            '{fechaInicio}',
            '{fechaDevolucion}',
            'vigente'
        )
    """

    cursor.execute(query)

    if cursor.rowcount == 1:

        id_prestamo = cursor.lastrowid #recuperando la clave primaria del prestamo

        # Actualizar estado del libro
        cursor.execute(f"UPDATE libros SET estado = 'Prestado' WHERE identificador = '{identificador}'")
        DB_con.commit()

        print("\n=======================================")
        print(f"PRESTAMO {id_prestamo} REGISTRADO CON EXITO")
        print("---------------------------------------")
        print("Usuario: ", identificacion)
        print("Libro: ", identificador)
        print("Fecha de inicio: ", fechaInicio)
        print("Fecha de devolucion: ", fechaDevolucion)
        print("Estado: vigente")
        print("=======================================\n")

        generar_comprobante_prestamo(DB_con, id_prestamo)

    else:
        DB_con.rollback() #agregado para evitar congelar la DB cuando falla un prestamo
        print("\nError: No se pudo registrar el prestamo!")

    os.system("pause")

def registrar_devolucion(DB_con):
    """Registra la devolucion de un prestamo mediante su identificador
       actualiza el estado del libro, la fecha de devolucion y el estad odel prestamo"""

    # cursor (base de datos)
    cursor = DB_con.cursor()

    # Recibienfo el identificador del prestamo y validandolo
    identificador = validar_dato( re.compile(r"^[1-9]\d*$"), "identificador del prestamo")

    # Verificar que el prestamo exista y este vigente
    cursor.execute(f"SELECT identificacionLibro FROM prestamos WHERE id = {identificador} AND estado = 'vigente'")
    prestamo = cursor.fetchone()

    if prestamo is None:
        print("\nError: El prestamo no existe o ya fue devuelto!\n")
        os.system("pause")
        return

    identificadorLibro = prestamo[0] # Obtener identificador del libro

    # Obtener fecha actual y darle el formato
    fechaDevolucion = date.today().strftime("%d/%m/%Y")

    # Actualizar estado y fecha de devolucion del prestamo
    query = f"""
        UPDATE prestamos SET
            fechaDevolucion = '{fechaDevolucion}',
            estado = 'devuelto' 
        WHERE id = {identificador}
    """
    cursor.execute(query)

    # Actualizar disponibilidad del libro
    cursor.execute(f"UPDATE libros SET estado = 'Disponible' WHERE identificador = '{identificadorLibro}'")
    DB_con.commit()

    print("DEVOLUCION REGISTRADA CON EXITO")

    os.system("pause")


def consultar_prestamos_usuario(DB_con):
    """Consulta el  estado de los prestamos de un usuario"""

    # cursor (base de datos)
    cursor = DB_con.cursor()

    # Recibiendo identificacion
    identificacion = validar_dato(re.compile(r"^[1-9]\d{5,11}$"), "numero de identificacion")

    # Consultar informacion del usuario y verificar que este existe
    cursor.execute( f"SELECT identificacion, nombres, apellidos FROM usuarios WHERE identificacion = '{identificacion}'")
    usuario = cursor.fetchone()

    if usuario is None:
        print("\nError: El usuario no existe en la base de datos!\n")
        os.system("pause")
        return

    # Consultar historico de prestamos
    query = f"""
        SELECT prestamos.id, libros.titulo, prestamos.estado
        FROM prestamos
        INNER JOIN libros
            ON prestamos.identificacionLibro = libros.identificador
        WHERE prestamos.identificacionUsuario = '{identificacion}'
        ORDER BY prestamos.id
        """
    cursor.execute(query)
    prestamos = cursor.fetchall()

    # Mostrar informacion
    id, nombres, apellidos = usuario

    print("\n======================================================")
    print("ESTADO DE PRESTAMOS POR USUARIO")
    print("-------------------------------------------------------")
    print("ID: ", id)
    print("Nombre: ", nombres, apellidos)
    print("------------------------------------------------------")

    if not prestamos: #si no hay prestamos imprimir el error
        print("El usuario no tiene prestamos registrados.")
    else: #si se encuentran prestamos imprimirlos en una tablita
        print("{:<10} {:<30} {:<15}".format("ID", "LIBRO", "ESTADO" ))

        for prestamo in prestamos:
            idPrestamo, titulo, estado = prestamo

            print("{:<10} {:<30} {:<15}".format( idPrestamo, titulo, estado ))

    print("======================================================\n")

    os.system("pause")

#menus
def menu():
    """Menu principal, permite al usuario seleccionar entre los distintos modulos del programa (libros, usuarios y prestamos)"""

    os.system("cls")#borrando la pantalla para que se vea bonito

    txt = "Digite: \n 1) Para modulo de usuario \n 2) Para modulo libros\
         \n 3) Para modulo prestamos \n 4) Para salir del programa \n\nSU RESPUESTA: "
    
    a = input(txt)
    if not(a == '1' or a == '2' or a == '3' or a =='4' ): #verificando que la entrada ingresada sea valida
        print("\nDigite una opcion valida!\n")
        return(0)
    else:
        return int(a)

def menu_usuarios():
    """permite seleccionar entre las distintas funciones del modulo de usuario, valida la entrada"""

    os.system("cls")#borrando la pantalla para que se vea bonito

    txt = "Digite: \n 1) Para crear un usuario nuevo \n 2) Para actualizar informacion de contacto\
          \n 3) Para consultar informacion vigente de un usuario \n 4) Para volver al menu principal\
          \n\nSU RESPUESTA: "
    a = input(txt)
    if not(a == '1' or a == '2' or a == '3' or a =='4' ): #verificando la validez de la entrada
        print("\nDigite una opcion valida!\n")
        return(0)
    else:
        return int(a)

def menu_libros():
    """permite seleccionar entre las distintas funciones del modulo de libros, valida la entrada"""

    os.system("cls") #borrando la pantalla para que se vea bonito

    txt = "Digite: \n 1) Para registrar un libro \n 2) Para actualizar estado de un libro\
          \n 3) Para consultar disponibilidad de un libro \n 4) Para consultar datos vigentes de un libro\
          \n 5) Para volver al menu principal\n\nSU RESPUESTA: "
    a = input(txt)
    if not(a == '1' or a == '2' or a == '3' or a =='4' or a == '5' ): #verificando la validez de la entrada
        print("\nDigite una opcion valida!\n")
        return(0)
    else:
        return int(a)
    

def menu_prestamos():
    """permite seleccionar entre las distintas funciones del modulo de prestamos, valida la entrada del usuario"""

    os.system("cls")#borrando la pantalla para que se vea bonito

    txt = "Digite: \n 1) Registrar prestamo\n 2) Registrar devolucion de un libro\
          \n 3) Connsultar estado prestamos por ususario\n 4) Para volver al menu principal\
          \n\nSU RESPUESTA: "
    a = input(txt)
    if not(a == '1' or a == '2' or a == '3' or a =='4' ): #verificando la validez de la entrada
        print("\nDigite una opcion valida!\n")
        return(0)
    else:
        return int(a)


# main 
def main():
    global CONTROL #Cierra el programa cuando falsa
    
    subcontrol = False #Cierra el menu seleccionado cuando falsa

    conn = conectar()
    crear_tablas(conn) 

    while CONTROL:
        a = menu()
        if a == 1: #Se selecciono el modulo usuarios
            subcontrol = True
            print("\n****** MODULO USUARIOS ******")

            while subcontrol: #repite el submenu del modulo usuarios hasta que el cliente solicite salir
                opcion = int(menu_usuarios())
                if opcion == 1:
                    usuario_nuevo(conn)
                elif opcion == 2:
                    actualizar_info_usuario(conn)
                elif opcion == 3:
                    consultar_usuario(conn)
                elif opcion == 4:
                    subcontrol = False
                elif opcion == 0:
                    pass
                else:
                    print("\nError, entrada invalida!\n")

        elif a == 2: #Se selecciono el modulo libros
            subcontrol = True 
            print("\n****** MODULO LIBROS ******")
            
            while subcontrol: #Repite el submenu de libros hasta que el cliente solicite salir
                opcion = int(menu_libros())
                if opcion == 1:
                    libro_nuevo(conn)
                elif opcion == 2:
                    actualizar_estado_libro(conn)
                elif opcion == 3:
                    consultar_disponibilidad_libro(conn)
                elif opcion == 4:
                    consultar_datos_libro(conn)
                elif opcion == 5:
                    subcontrol = False
                elif opcion == 0:
                    pass
                else:
                    print("\nError, entrada invalida!\n")

        elif a == 3:
            subcontrol = True
            print("\n****** MODULO PRESTAMOS ******")
            
            while subcontrol:
                opcion = int(menu_prestamos())
                if opcion == 1:
                    prestamo_nuevo(conn)
                elif opcion == 2:
                    registrar_devolucion(conn)
                elif opcion == 3:
                    consultar_prestamos_usuario(conn)
                elif opcion == 4:
                    subcontrol = False
                elif opcion == 0:
                    pass
                else:
                    print("\nError, entrada invalida!\n")
            
        elif a == 4:
            CONTROL = False
            conn.close()
        elif a == 0:
            pass # implica que el usuario digito una entrada invalida, el mensaje de error se muestra en la funcion menu().
        else:
            print("Error, entrada no reconocida") #implica que el usuario digito algo invalido que no fue detectado por la validacion.


main()