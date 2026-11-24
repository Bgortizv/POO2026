"""Gestión de biblioteca por consola. Python 3.9+, solo biblioteca estándar.

Diseño físico: SQLite conserva libros, usuarios y préstamos; el estado vencido
se calcula a partir de la fecha pactada. Los comprobantes se guardan en PDF.
"""
import os
import re
import sqlite3
import smtplib
import ssl
from datetime import date, datetime
from email.message import EmailMessage
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
BASE_DATOS = 'BaseDeDatosAplicacion.db'
COMPROBANTES = CARPETA / 'comprobantes'


def conectar(ruta=BASE_DATOS):
    conexion = sqlite3.connect(str(ruta))
    conexion.row_factory = sqlite3.Row
    conexion.execute('PRAGMA foreign_keys = ON')
    conexion.executescript('''
    CREATE TABLE IF NOT EXISTS libros (
        id TEXT PRIMARY KEY, titulo TEXT NOT NULL, autor TEXT NOT NULL,
        genero TEXT NOT NULL, fecha_publicacion TEXT NOT NULL,
        estado TEXT NOT NULL CHECK(estado IN ('disponible','prestado','en mantenimiento')));
    CREATE TABLE IF NOT EXISTS usuarios (
        documento TEXT PRIMARY KEY, nombre TEXT NOT NULL, apellido TEXT NOT NULL,
        direccion TEXT NOT NULL, telefono TEXT NOT NULL, correo TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS prestamos (
        numero INTEGER PRIMARY KEY AUTOINCREMENT,
        documento TEXT NOT NULL REFERENCES usuarios(documento),
        libro_id TEXT NOT NULL REFERENCES libros(id),
        fecha_inicio TEXT NOT NULL, fecha_devolucion TEXT NOT NULL,
        devuelto INTEGER NOT NULL DEFAULT 0 CHECK(devuelto IN (0,1)));
    CREATE UNIQUE INDEX IF NOT EXISTS prestamo_abierto_libro
        ON prestamos(libro_id) WHERE devuelto = 0;
    CREATE UNIQUE INDEX IF NOT EXISTS prestamo_abierto_usuario
        ON prestamos(documento) WHERE devuelto = 0;
    ''')
    return conexion


def texto(etiqueta):
    while True:
        valor = input(etiqueta + ': ').strip()
        valor = valor.upper()
        if valor and len(valor) <= 120 and all(c.isprintable() for c in valor):
            return valor
        print('Digite un valor válido de 1 a 120 caracteres imprimibles.')


def digitos(etiqueta):
    # Los números de documento y teléfono se conservan como texto para mantener ceros iniciales.
    while True:
        valor = texto(etiqueta + ' (solo dígitos)')
        if re.fullmatch(r'[0-9]{1,30}', valor):
            return valor
        print('Digite un valor válido: use entre 1 y 30 dígitos, sin espacios ni signos.')


def fecha(etiqueta):
    while True:
        valor = texto(etiqueta + ' (dd/mm/aaaa)')
        try:
            if not re.fullmatch(r'[0-9]{2}/[0-9]{2}/[0-9]{4}', valor):
                raise ValueError
            return datetime.strptime(valor, '%d/%m/%Y').date().isoformat()
        except ValueError:
            print('Digite una fecha válida en formato dd/mm/aaaa, por ejemplo 05/11/2026.')


def fecha_visible(valor):
    return date.fromisoformat(valor).strftime('%d/%m/%Y')


def correo_valido(valor):
    return bool(re.fullmatch(r'[A-Z0-9!#$%&*+/=?^_`{|}~-]+(?:\.[A-Z0-9!#$%&*+/=?^_`{|}~-]+)*@[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+', valor.upper()))


def pedir_correo():
    while True:
        valor = texto('Correo electrónico')
        if correo_valido(valor):
            return valor
        print('Digite un correo válido, por ejemplo USUARIO@EJEMPLO.COM.')


def mostrar(fila, etiquetas):
    if fila is None:
        print('Registro no encontrado.')
        return
    for campo, etiqueta in etiquetas:
        valor = fila[campo]
        if campo in ('fecha_publicacion', 'fecha_inicio', 'fecha_devolucion'):
            valor = fecha_visible(valor)
        print(f'{etiqueta}: {valor}')


ETIQUETAS_LIBRO = [('id','Identificador'), ('titulo','Título'), ('autor','Autor'),
                   ('genero','Género'), ('fecha_publicacion','Fecha de publicación'), ('estado','Estado')]
ETIQUETAS_USUARIO = [('documento','Documento'), ('nombre','Nombre'), ('apellido','Apellido'),
                     ('direccion','Dirección'), ('telefono','Teléfono'), ('correo','Correo')]


def registrar_libro(con):
    datos = (texto('Identificador'), texto('Título'), texto('Autor'), texto('Género'), fecha('Fecha de publicación'))
    if con.execute('SELECT 1 FROM libros WHERE UPPER(id) = UPPER(?)', (datos[0],)).fetchone():
        raise ValueError('Ya existe un libro con ese identificador.')
    con.execute("INSERT INTO libros VALUES (?, ?, ?, ?, ?, 'disponible')", datos)
    con.commit()
    print('Libro registrado como disponible.')


def actualizar_estado(con):
    identificador = texto('Digite el identificador del libro cuyo estado desea modificar')
    libro = con.execute('SELECT * FROM libros WHERE UPPER(id) = UPPER(?)', (identificador,)).fetchone()
    if not libro:
        print('Libro no encontrado.'); return
    print(f"Estado actual del libro: {libro['estado']}")
    if libro['estado'] == 'prestado':
        print('Registre la devolución en el módulo de préstamos para que el libro vuelva a estar disponible.')
        return
    nuevo_estado = 'en mantenimiento' if libro['estado'] == 'disponible' else 'disponible'
    print(f'1. Cambiar a {nuevo_estado}')
    print('0. Cancelar')
    while True:
        opcion = input('Digite 1 para cambiar el estado o 0 para cancelar: ').strip().upper()
        if opcion in ('0', '1'):
            break
        print('Digite 1 para cambiar el estado o 0 para cancelar.')
    if opcion == '0':
        print('Cambio cancelado.')
        return
    con.execute('UPDATE libros SET estado = ? WHERE id = ?', (nuevo_estado, libro['id']))
    con.commit()
    print('Estado actualizado.')


def consultar_libro(con, solo_estado=False):
    libro = con.execute('SELECT * FROM libros WHERE UPPER(id) = UPPER(?)', (texto('Digite el identificador del libro que desea consultar'),)).fetchone()
    mostrar(libro, [('id','Identificador'), ('titulo','Título'), ('estado','Estado')] if solo_estado else ETIQUETAS_LIBRO)


def listar_libros(con):
    """Muestra una muestra de hasta 100 libros para encontrar sus identificadores."""
    filas = con.execute('SELECT id, titulo, autor, estado FROM libros ORDER BY titulo, id LIMIT 100').fetchall()
    if not filas:
        print('No hay libros registrados en el catálogo.')
        return
    print('\nMUESTRA DEL CATÁLOGO (máximo 100 libros)')
    for libro in filas:
        print(f"Identificador: {libro['id']} | Título: {libro['titulo']} | Autor: {libro['autor']} | Estado: {libro['estado']}")


def registrar_usuario(con):
    datos = (digitos('Documento'), texto('Nombre'), texto('Apellido'), texto('Dirección'), digitos('Teléfono'), pedir_correo())
    con.execute('INSERT INTO usuarios VALUES (?, ?, ?, ?, ?, ?)', datos)
    con.commit()
    print('Usuario registrado.')


def actualizar_contacto(con):
    documento = digitos('Digite el documento del usuario cuyo contacto desea modificar')
    usuario = con.execute('SELECT * FROM usuarios WHERE UPPER(documento) = UPPER(?)', (documento,)).fetchone()
    if not usuario:
        print('Usuario no encontrado.'); return
    print(f"Usuario: {usuario['nombre']} {usuario['apellido']} | Documento: {usuario['documento']}")
    print(f"1. Modificar dirección actual: {usuario['direccion']}")
    print(f"2. Modificar teléfono actual: {usuario['telefono']}")
    print(f"3. Modificar correo actual: {usuario['correo']}")
    print('0. Cancelar')
    while True:
        opcion = input('Digite el número del dato que desea modificar o 0 para cancelar: ').strip().upper()
        if opcion in ('0', '1', '2', '3'):
            break
        print('Digite 1, 2, 3 o 0 para cancelar.')
    if opcion == '0':
        print('Cambio cancelado.'); return
    if opcion == '1':
        con.execute('UPDATE usuarios SET direccion = ? WHERE documento = ?',
                    (texto('Digite la nueva dirección'), usuario['documento']))
    elif opcion == '2':
        con.execute('UPDATE usuarios SET telefono = ? WHERE documento = ?',
                    (digitos('Digite el nuevo teléfono'), usuario['documento']))
    else:
        con.execute('UPDATE usuarios SET correo = ? WHERE documento = ?',
                    (pedir_correo(), usuario['documento']))
    con.commit()
    print('Contacto actualizado.')


def consultar_usuario(con):
    mostrar(con.execute('SELECT * FROM usuarios WHERE UPPER(documento) = UPPER(?)', (digitos('Digite el documento del usuario que desea consultar'),)).fetchone(), ETIQUETAS_USUARIO)


def listar_usuarios(con):
    """Muestra hasta 100 usuarios para localizar su número de documento."""
    filas = con.execute('SELECT documento, nombre, apellido FROM usuarios ORDER BY apellido, nombre, documento LIMIT 100').fetchall()
    if not filas:
        print('No hay usuarios registrados.')
        return
    print('\nMUESTRA DE USUARIOS (máximo 100 usuarios)')
    for usuario in filas:
        print(f"Documento: {usuario['documento']} | Nombre: {usuario['nombre']} {usuario['apellido']}")


def estado_prestamo(fila, hoy=None):
    if fila['devuelto']:
        return 'devuelto'
    return 'vencido' if date.fromisoformat(fila['fecha_devolucion']) < (hoy or date.today()) else 'vigente'


def crear_prestamo(con, documento, libro_id, inicio, devolucion):
    """Valida y registra préstamo y cambio de estado en una misma transacción."""
    if date.fromisoformat(devolucion) < date.fromisoformat(inicio):
        raise ValueError('La fecha de devolución no puede ser anterior a la de inicio.')
    with con:
        # Adquirir el bloqueo de escritura antes de comprobar disponibilidad.
        con.execute('BEGIN IMMEDIATE')
        usuario = con.execute('SELECT 1 FROM usuarios WHERE UPPER(documento) = UPPER(?)', (documento,)).fetchone()
        libro = con.execute('SELECT id, estado FROM libros WHERE UPPER(id) = UPPER(?)', (libro_id,)).fetchone()
        if not usuario:
            raise ValueError('Usuario no encontrado.')
        if not libro:
            raise ValueError('Libro no encontrado.')
        if libro['estado'] != 'disponible':
            raise ValueError('El libro no está disponible.')
        if con.execute('SELECT 1 FROM prestamos WHERE UPPER(documento) = UPPER(?) AND devuelto = 0', (documento,)).fetchone():
            raise ValueError('El usuario tiene un préstamo sin devolver.')
        cursor = con.execute('INSERT INTO prestamos(documento, libro_id, fecha_inicio, fecha_devolucion) VALUES (?, ?, ?, ?)',
                             (documento, libro['id'], inicio, devolucion))
        con.execute("UPDATE libros SET estado = 'prestado' WHERE UPPER(id) = UPPER(?)", (libro_id,))
        return cursor.lastrowid


def datos_prestamo(con, numero):
    return con.execute('''SELECT p.*, u.nombre, u.apellido, u.direccion, u.telefono, u.correo,
                          l.titulo, l.autor FROM prestamos p
                          JOIN usuarios u ON u.documento = p.documento
                          JOIN libros l ON l.id = p.libro_id WHERE p.numero = ?''', (numero,)).fetchone()


def pdf_comprobante(fila):
    """Construye un PDF de una página con Helvetica, sin dependencias externas."""
    COMPROBANTES.mkdir(exist_ok=True)
    lineas = ['COMPROBANTE DE PRESTAMO', '', f"Número de préstamo: {fila['numero']}",
              f"Usuario: {fila['nombre']} {fila['apellido']}", f"Dirección: {fila['direccion']}",
              f"Teléfono: {fila['telefono']}", f"Correo: {fila['correo']}", '',
              f"Título: {fila['titulo']}", f"Autor: {fila['autor']}",
              f"Fecha de inicio: {fecha_visible(fila['fecha_inicio'])}",
              f"Fecha de devolución: {fecha_visible(fila['fecha_devolucion'])}", '',
              f"Estado: {estado_prestamo(fila)}"]
    # Ajustar líneas largas para evitar que desborden la página.
    import textwrap
    lineas = [trozo for linea in lineas for trozo in (textwrap.wrap(linea, width=78, break_long_words=True) or [''])]
    operaciones = [b'BT /F1 11 Tf 45 800 Td 15 TL']
    for linea in lineas:
        contenido = linea.encode('cp1252', 'replace').replace(b'\\', b'\\\\').replace(b'(', b'\\(').replace(b')', b'\\)')
        operaciones.append(b'(' + contenido + b') Tj T*')
    operaciones.append(b'ET')
    flujo = b'\n'.join(operaciones)
    objetos = [b'<< /Type /Catalog /Pages 2 0 R >>', b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
               b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>',
               b'<< /Length ' + str(len(flujo)).encode() + b' >>\nstream\n' + flujo + b'\nendstream']
    pdf = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
    posiciones = [0]
    for indice, objeto in enumerate(objetos, 1):
        posiciones.append(len(pdf)); pdf.extend(f'{indice} 0 obj\n'.encode() + objeto + b'\nendobj\n')
    inicio_xref = len(pdf)
    pdf.extend(f'xref\n0 {len(posiciones)}\n0000000000 65535 f \n'.encode())
    for posicion in posiciones[1:]:
        pdf.extend(f'{posicion:010d} 00000 n \n'.encode())
    pdf.extend(f'trailer\n<< /Size {len(posiciones)} /Root 1 0 R >>\nstartxref\n{inicio_xref}\n%%EOF\n'.encode())
    ruta = COMPROBANTES / f'prestamo_{fila["numero"]}.pdf'
    ruta.write_bytes(pdf)
    return ruta


def enviar_comprobante(fila, ruta):
    host = os.environ.get('BIBLIOTECA_SMTP_HOST', '').strip()
    usuario = os.environ.get('BIBLIOTECA_SMTP_USUARIO', '').strip()
    clave = os.environ.get('BIBLIOTECA_SMTP_CLAVE', '')
    remitente = os.environ.get('BIBLIOTECA_SMTP_REMITENTE', usuario).strip()
    if not all((host, usuario, clave, remitente)):
        raise ValueError('Configure las variables SMTP indicadas en la documentación.')
    puerto = int(os.environ.get('BIBLIOTECA_SMTP_PUERTO', '587'))
    mensaje = EmailMessage()
    mensaje['Subject'] = f'Comprobante de préstamo {fila["numero"]}'
    mensaje['From'] = remitente
    mensaje['To'] = fila['correo']
    mensaje.set_content('Adjuntamos el comprobante de su préstamo bibliotecario.')
    mensaje.add_attachment(ruta.read_bytes(), maintype='application', subtype='pdf', filename=ruta.name)
    contexto = ssl.create_default_context()
    if puerto == 465:
        with smtplib.SMTP_SSL(host, puerto, timeout=20, context=contexto) as servidor:
            servidor.login(usuario, clave); servidor.send_message(mensaje)
    else:
        with smtplib.SMTP(host, puerto, timeout=20) as servidor:
            servidor.ehlo(); servidor.starttls(context=contexto); servidor.ehlo()
            servidor.login(usuario, clave); servidor.send_message(mensaje)


def comprobante(con, numero):
    fila = datos_prestamo(con, numero)
    if not fila:
        print('Préstamo no encontrado.'); return
    try:
        ruta = pdf_comprobante(fila)
        print('Comprobante generado:', ruta)
        enviar_comprobante(fila, ruta)
        print('Comprobante enviado a', fila['correo'])
    except (OSError, ValueError, smtplib.SMTPException):
        print('No fue posible generar o enviar el comprobante. Revise la configuración y vuelva a intentarlo.')
        print('El préstamo se conserva. Puede reintentar desde el menú de préstamos.')


def registrar_prestamo(con):
    documento = digitos('Digite el documento del usuario que solicita el préstamo')
    libro = texto('Digite el identificador del libro que desea prestar')
    inicio = fecha('Fecha de inicio')
    while True:
        devolucion = fecha('Fecha de devolución')
        if devolucion >= inicio:
            break
        print('Digite una fecha de devolución igual o posterior a la fecha de inicio (dd/mm/aaaa).')
    numero = crear_prestamo(con, documento, libro, inicio, devolucion)
    print('Préstamo registrado con número', numero)
    comprobante(con, numero)


def devolver(con, numero):
    with con:
        con.execute('BEGIN IMMEDIATE')
        fila = con.execute('SELECT * FROM prestamos WHERE numero = ?', (numero,)).fetchone()
        if not fila:
            raise ValueError('Préstamo no encontrado.')
        if fila['devuelto']:
            raise ValueError('El préstamo ya fue devuelto.')
        con.execute('UPDATE prestamos SET devuelto = 1 WHERE numero = ?', (numero,))
        con.execute("UPDATE libros SET estado = 'disponible' WHERE UPPER(id) = UPPER(?)", (fila['libro_id'],))
    print('Devolución registrada; libro disponible.')


def registrar_devolucion(con):
    numero = numero_prestamo('devolver')
    fila = datos_prestamo(con, numero)
    if not fila:
        print('Préstamo no encontrado.'); return
    estado = estado_prestamo(fila)
    print(f"Préstamo: {numero} | Usuario: {fila['nombre']} {fila['apellido']} | Libro: {fila['titulo']}")
    print(f'Estado actual del préstamo: {estado}')
    if estado == 'devuelto':
        print('El préstamo ya fue devuelto.'); return
    print('1. Registrar devolución y marcar el libro disponible')
    print('0. Cancelar')
    while True:
        opcion = input('Digite 1 para registrar la devolución o 0 para cancelar: ').strip().upper()
        if opcion in ('0', '1'):
            break
        print('Digite 1 para registrar la devolución o 0 para cancelar.')
    if opcion == '0':
        print('Devolución cancelada.'); return
    devolver(con, numero)


def numero_prestamo(operacion='consultar'):
    while True:
        valor = texto('Digite el número del préstamo que desea ' + operacion + ' (entero positivo)')
        # SQLite acepta enteros con signo de hasta 64 bits.
        if re.fullmatch(r'[0-9]{1,19}', valor) and 0 < int(valor) <= 9223372036854775807:
            return int(valor)
        print('Digite un número de préstamo válido: entero positivo hasta 9223372036854775807.')


def consultar_prestamos(con):
    documento = digitos('Digite el documento del usuario cuyos préstamos desea consultar')
    if not con.execute('SELECT 1 FROM usuarios WHERE UPPER(documento) = UPPER(?)', (documento,)).fetchone():
        print('Usuario no encontrado.'); return
    ultimo_numero = None
    pagina = 1
    while True:
        if ultimo_numero is None:
            filas = con.execute('''SELECT p.*, l.titulo FROM prestamos p JOIN libros l ON l.id = p.libro_id
                                   WHERE p.documento = ? ORDER BY p.numero DESC LIMIT 100''', (documento,)).fetchall()
        else:
            filas = con.execute('''SELECT p.*, l.titulo FROM prestamos p JOIN libros l ON l.id = p.libro_id
                                   WHERE p.documento = ? AND p.numero < ? ORDER BY p.numero DESC LIMIT 100''',
                                (documento, ultimo_numero)).fetchall()
        if not filas:
            print('El usuario no tiene préstamos.' if pagina == 1 else 'No hay más préstamos.')
            return
        print(f'Página {pagina}: hasta 100 préstamos, más recientes primero.')
        for fila in filas:
            print(f"Préstamo {fila['numero']} | {fila['titulo']} ({fila['libro_id']}) | "
                  f"{fecha_visible(fila['fecha_inicio'])} a {fecha_visible(fila['fecha_devolucion'])} | {estado_prestamo(fila)}")
        ultimo_numero = filas[-1]['numero']
        hay_mas = con.execute('SELECT 1 FROM prestamos WHERE documento = ? AND numero < ? LIMIT 1',
                              (documento, ultimo_numero)).fetchone()
        if not hay_mas:
            print('Fin del historial de préstamos.')
            return
        print('1. Ver los siguientes préstamos')
        print('0. Volver al menú')
        while True:
            opcion = input('Digite 1 para continuar o 0 para volver: ').strip().upper()
            if opcion in ('0', '1'):
                break
            print('Digite 1 para continuar o 0 para volver.')
        if opcion == '0':
            return
        pagina += 1


def listar_prestamos(con):
    """Muestra hasta 100 préstamos recientes, incluidos sus identificadores."""
    filas = con.execute('''SELECT p.*, l.titulo FROM prestamos p
                           JOIN libros l ON l.id = p.libro_id
                           ORDER BY p.numero DESC LIMIT 100''').fetchall()
    if not filas:
        print('No hay préstamos registrados.')
        return
    print('\nMUESTRA DE PRÉSTAMOS (máximo 100, más recientes primero)')
    for fila in filas:
        print(f"Préstamo: {fila['numero']} | Documento: {fila['documento']} | "
              f"Libro: {fila['libro_id']} - {fila['titulo']} | Estado: {estado_prestamo(fila)}")


def menu(con, titulo, opciones):
    while True:
        print('\n' + titulo)
        for clave, (descripcion, _) in opciones.items():
            print(f'{clave}. {descripcion}')
        print('0. Volver' if titulo != 'MENÚ PRINCIPAL' else '0. Salir')
        opcion = input('Digite el número de la opción: ').strip().upper()
        if opcion == '0':
            return
        if opcion not in opciones:
            print('Digite una opción válida de las mostradas en el menú.'); continue
        try:
            opciones[opcion][1]()
        except sqlite3.IntegrityError:
            con.rollback()
            print('No se pudo guardar: identificador duplicado o datos incompatibles.')
        except ValueError as error:
            con.rollback()
            print('No se pudo completar la operación:', error)
        except sqlite3.Error:
            con.rollback()
            print('No se pudo acceder a la base de datos. Intente nuevamente.')


def main():
    con = conectar()
    try:
        libros = {'1': ('Registrar libro', lambda: registrar_libro(con)),
                  '2': ('Actualizar estado', lambda: actualizar_estado(con)),
                  '3': ('Consultar disponibilidad', lambda: consultar_libro(con, True)),
                  '4': ('Consultar datos', lambda: consultar_libro(con)),
                  '5': ('Consultar muestra del catálogo (hasta 100 libros)', lambda: listar_libros(con))}
        usuarios = {'1': ('Crear usuario', lambda: registrar_usuario(con)),
                    '2': ('Actualizar contacto', lambda: actualizar_contacto(con)),
                    '3': ('Consultar usuario', lambda: consultar_usuario(con)),
                    '4': ('Consultar muestra de usuarios (hasta 100)', lambda: listar_usuarios(con))}
        prestamos = {'1': ('Registrar préstamo', lambda: registrar_prestamo(con)),
                     '2': ('Registrar devolución', lambda: registrar_devolucion(con)),
                     '3': ('Consultar préstamos de usuario', lambda: consultar_prestamos(con)),
                     '4': ('Generar y enviar comprobante nuevamente', lambda: comprobante(con, numero_prestamo('generar y enviar nuevamente'))),
                     '5': ('Consultar muestra de préstamos (hasta 100)', lambda: listar_prestamos(con))}
        menu(con, 'MENÚ PRINCIPAL', {'1': ('Libros', lambda: menu(con, 'LIBROS', libros)),
                                     '2': ('Usuarios', lambda: menu(con, 'USUARIOS', usuarios)),
                                     '3': ('Préstamos', lambda: menu(con, 'PRÉSTAMOS', prestamos))})
    except (EOFError, KeyboardInterrupt):
        print('\nPrograma finalizado.')
    finally:
        con.close()


if __name__ == '__main__':
    main()
