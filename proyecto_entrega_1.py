"""Pruebas ejecutables con unittest y únicamente la biblioteca estándar."""
import contextlib
import datetime
import importlib.util
import io
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ARCHIVO = Path(__file__).resolve().parent.parent / 'proyecto_entrega_1.py'
spec = importlib.util.spec_from_file_location('biblioteca', ARCHIVO)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


def probar_entrada(funcion, valores):
    salida = io.StringIO()
    with patch('builtins.input', side_effect=valores), contextlib.redirect_stdout(salida):
        resultado = funcion()
    return resultado, salida.getvalue()


def base():
    con = app.conectar(':memory:')
    con.executemany('INSERT INTO usuarios VALUES (?, ?, ?, ?, ?, ?)', [
        ('1', 'ANA', 'PÉREZ', 'CALLE 1', '123', 'ANA@EJEMPLO.COM'),
        ('2', 'LUIS', 'DÍAZ', 'CALLE 2', '456', 'LUIS@EJEMPLO.COM')])
    con.executemany('INSERT INTO libros VALUES (?, ?, ?, ?, ?, ?)', [
        ('L1', 'LIBRO UNO', 'AUTOR', 'CIENCIA', '2020-01-01', 'disponible'),
        ('L2', 'LIBRO DOS', 'AUTOR', 'CIENCIA', '2020-01-01', 'disponible'),
        ('L3', 'TERCERO', 'AUTOR', 'CIENCIA', '2020-01-01', 'en mantenimiento')])
    con.commit()
    return con


class Validacion(unittest.TestCase):
    def test_texto_obligatorio_mayusculas_y_limite(self):
        valor, mensaje = probar_entrada(lambda: app.texto('Nombre'), ['', 'a'*121, 'ana pérez'])
        self.assertEqual(valor, 'ANA PÉREZ')
        self.assertIn('valor válido', mensaje)

    def test_documento_y_telefono(self):
        valor, mensaje = probar_entrada(lambda: app.digitos('Documento'), ['abc', '-1', '1.2', '1 2', '1'*31, '00123'])
        self.assertEqual(valor, '00123')
        self.assertIn('dígitos', mensaje)

    def test_fecha_formato_y_calendario(self):
        valor, mensaje = probar_entrada(lambda: app.fecha('Fecha'), ['1/01/2024', '31/02/2024', '29/02/2023', '29/02/2024'])
        self.assertEqual(valor, '2024-02-29')
        self.assertIn('dd/mm/aaaa', mensaje)
        self.assertEqual(app.fecha_visible(valor), '29/02/2024')

    def test_numero_prestamo(self):
        valor, mensaje = probar_entrada(app.numero_prestamo, ['0', '-1', '1.5', '²', '9223372036854775808', '2'])
        self.assertEqual(valor, 2)
        self.assertIn('entero positivo', mensaje)

    def test_correo(self):
        valor, mensaje = probar_entrada(app.pedir_correo, ['a@b', 'a..b@example.com', 'a@-ejemplo.com', 'ana@example.com'])
        self.assertEqual(valor, 'ANA@EXAMPLE.COM')
        self.assertIn('correo válido', mensaje)


class Flujo(unittest.TestCase):
    def setUp(self):
        self.con = base()

    def tearDown(self):
        self.con.close()

    def test_cancelar_capturas_vuelve_al_menu_sin_guardar(self):
        casos = [
            (app.registrar_prestamo, ['/cancelar']),
            (app.registrar_prestamo, ['1', '/CANCELAR']),
            (app.registrar_prestamo, ['1', 'L1', 'fecha incorrecta', '/cancelar']),
            (app.registrar_libro, ['NUEVO', 'TITULO', '/cancelar']),
            (app.registrar_usuario, ['3', 'ANA', 'PEREZ', 'CALLE', '123', '/cancelar']),
            (app.consultar_libro, ['/cancelar']),
            (app.registrar_devolucion, ['0', '/cancelar']),
            (app.consultar_prestamos, ['/cancelar']),
        ]
        for funcion, datos in casos:
            with self.subTest(funcion=funcion.__name__, datos=datos):
                opciones = {'1': ('Operación', lambda: funcion(self.con))}
                _, salida = probar_entrada(lambda: app.menu(self.con, 'PRUEBA', opciones), ['1'] + datos + ['0'])
                self.assertIn('Operación cancelada', salida)
                self.assertEqual(self.con.execute('SELECT count(*) FROM prestamos').fetchone()[0], 0)
                self.assertEqual(self.con.execute('SELECT count(*) FROM libros').fetchone()[0], 3)
                self.assertEqual(self.con.execute('SELECT count(*) FROM usuarios').fetchone()[0], 2)
                self.assertEqual(self.con.execute("SELECT estado FROM libros WHERE id='L1'").fetchone()[0], 'disponible')

    def test_cero_sigue_siendo_dato_valido(self):
        self.assertEqual(probar_entrada(lambda: app.digitos('Documento'), ['0'])[0], '0')
        self.assertEqual(probar_entrada(lambda: app.texto('Identificador'), ['0'])[0], '0')

    def test_mensajes_de_cancelacion_por_operacion(self):
        casos = [
            ('LIBROS', '1', app.registrar_libro, ['/cancelar'], 'No se registró el libro.'),
            ('LIBROS', '2', app.actualizar_estado, ['/cancelar'], 'No se actualizó el estado del libro.'),
            ('LIBROS', '3', lambda con: app.consultar_libro(con, True), ['/cancelar'], 'No se consultó la disponibilidad del libro.'),
            ('LIBROS', '4', app.consultar_libro, ['/cancelar'], 'No se consultaron los datos del libro.'),
            ('USUARIOS', '1', app.registrar_usuario, ['/cancelar'], 'No se registró el usuario.'),
            ('USUARIOS', '2', app.actualizar_contacto, ['1', '1', '/cancelar'], 'No se actualizaron los datos de contacto.'),
            ('USUARIOS', '3', app.consultar_usuario, ['/cancelar'], 'No se consultaron los datos del usuario.'),
            ('PRÉSTAMOS', '1', app.registrar_prestamo, ['1', 'L1', '/cancelar'], 'No se registró el préstamo.'),
            ('PRÉSTAMOS', '2', app.registrar_devolucion, ['/cancelar'], 'No se registró la devolución.'),
            ('PRÉSTAMOS', '3', app.consultar_prestamos, ['/cancelar'], 'No se consultaron los préstamos del usuario.'),
            ('PRÉSTAMOS', '4', lambda con: app.comprobante(con, app.numero_prestamo()), ['/cancelar'], 'No se generó ni se envió nuevamente el comprobante.'),
        ]
        for titulo, opcion, funcion, datos, mensaje in casos:
            with self.subTest(titulo=titulo, opcion=opcion):
                opciones = {opcion: ('Operación', lambda: funcion(self.con))}
                _, salida = probar_entrada(lambda: app.menu(self.con, titulo, opciones), [opcion] + datos + ['0'])
                self.assertIn(mensaje, salida)

    def test_mensajes_al_cancelar_confirmacion(self):
        _, salida = probar_entrada(lambda: app.actualizar_estado(self.con), ['L1', '0'])
        self.assertIn('No se actualizó el estado del libro.', salida)
        _, salida = probar_entrada(lambda: app.actualizar_contacto(self.con), ['1', '0'])
        self.assertIn('No se actualizaron los datos de contacto.', salida)
        numero = app.crear_prestamo(self.con, '1', 'L1', '2026-01-01', '2026-01-02')
        _, salida = probar_entrada(lambda: app.registrar_devolucion(self.con), [str(numero), '0'])
        self.assertIn('No se registró la devolución.', salida)

    def test_creacion_consulta_y_actualizacion(self):
        probar_entrada(lambda: app.registrar_libro(self.con), ['lib4', 'titulo', 'autor', 'género', '01/01/2020'])
        libro = self.con.execute("SELECT * FROM libros WHERE id='LIB4'").fetchone()
        self.assertEqual(libro['titulo'], 'TITULO')
        _, salida = probar_entrada(lambda: app.consultar_libro(self.con), ['lib4'])
        self.assertIn('TITULO', salida)
        probar_entrada(lambda: app.actualizar_estado(self.con), ['lib4', 'x', '1'])
        self.assertEqual(self.con.execute("SELECT estado FROM libros WHERE id='LIB4'").fetchone()[0], 'en mantenimiento')
        probar_entrada(lambda: app.registrar_usuario(self.con), ['003', 'maria', 'lopez', 'carrera 5', '0123', 'm@example.com'])
        probar_entrada(lambda: app.actualizar_contacto(self.con), ['003', '1', 'calle 9'])
        probar_entrada(lambda: app.actualizar_contacto(self.con), ['003', '2', '098'])
        probar_entrada(lambda: app.actualizar_contacto(self.con), ['003', '3', 'nuevo@example.com'])
        _, salida = probar_entrada(lambda: app.consultar_usuario(self.con), ['003'])
        self.assertIn('CALLE 9', salida)
        self.assertIn('NUEVO@EXAMPLE.COM', salida)

    def test_actualizar_estado_muestra_estado_y_transiciones_validas(self):
        _, salida = probar_entrada(lambda: app.actualizar_estado(self.con), ['L1', '2', '0'])
        self.assertIn('Estado actual del libro: disponible', salida)
        self.assertIn('1. Cambiar a en mantenimiento', salida)
        self.assertIn('Digite 1 para cambiar el estado o 0 para cancelar.', salida)
        self.assertEqual(self.con.execute("SELECT estado FROM libros WHERE id='L1'").fetchone()[0], 'disponible')
        _, salida = probar_entrada(lambda: app.actualizar_estado(self.con), ['L3', '1'])
        self.assertIn('Estado actual del libro: en mantenimiento', salida)
        self.assertIn('1. Cambiar a disponible', salida)
        self.assertEqual(self.con.execute("SELECT estado FROM libros WHERE id='L3'").fetchone()[0], 'disponible')
        app.crear_prestamo(self.con, '1', 'L1', '2026-01-01', '2026-01-10')
        _, salida = probar_entrada(lambda: app.actualizar_estado(self.con), ['L1'])
        self.assertIn('Estado actual del libro: prestado', salida)
        self.assertIn('Registre la devolución', salida)
        self.assertEqual(self.con.execute("SELECT estado FROM libros WHERE id='L1'").fetchone()[0], 'prestado')

    def test_contacto_muestra_valores_y_permanece_sin_cambios_al_cancelar(self):
        _, salida = probar_entrada(lambda: app.actualizar_contacto(self.con), ['1', 'X', '0'])
        for valor in ('CALLE 1', '123', 'ANA@EJEMPLO.COM', 'Digite 1, 2, 3', 'Cambio cancelado'):
            self.assertIn(valor, salida)
        usuario = self.con.execute("SELECT * FROM usuarios WHERE documento='1'").fetchone()
        self.assertEqual((usuario['direccion'], usuario['telefono'], usuario['correo']), ('CALLE 1', '123', 'ANA@EJEMPLO.COM'))
        probar_entrada(lambda: app.actualizar_contacto(self.con), ['1', '2', '999'])
        usuario = self.con.execute("SELECT * FROM usuarios WHERE documento='1'").fetchone()
        self.assertEqual((usuario['direccion'], usuario['telefono'], usuario['correo']), ('CALLE 1', '999', 'ANA@EJEMPLO.COM'))

    def test_devolucion_muestra_estado_y_permanece_sin_cambios_al_cancelar(self):
        numero = app.crear_prestamo(self.con, '1', 'L1', '2020-01-01', '2020-01-02')
        _, salida = probar_entrada(lambda: app.registrar_devolucion(self.con), [str(numero), 'x', '0'])
        self.assertIn('Estado actual del préstamo: vencido', salida)
        self.assertIn('LIBRO UNO', salida)
        self.assertIn('Devolución cancelada', salida)
        self.assertEqual(self.con.execute('SELECT devuelto FROM prestamos WHERE numero=?', (numero,)).fetchone()[0], 0)
        _, salida = probar_entrada(lambda: app.registrar_devolucion(self.con), [str(numero), '1'])
        self.assertIn('Devolución registrada', salida)
        _, salida = probar_entrada(lambda: app.registrar_devolucion(self.con), [str(numero)])
        self.assertIn('Estado actual del préstamo: devuelto', salida)
        self.assertIn('ya fue devuelto', salida)

    def test_comparaciones_en_mayusculas_y_registro_anterior(self):
        self.con.execute("INSERT INTO libros VALUES (?, ?, ?, ?, ?, ?)",
                         ('anterior1', 'ANTERIOR', 'AUTOR', 'GENERO', '2020-01-01', 'disponible'))
        self.con.commit()
        _, salida = probar_entrada(lambda: app.consultar_libro(self.con), ['ANTERIOR1'])
        self.assertIn('ANTERIOR', salida)
        with self.assertRaises(ValueError):
            probar_entrada(lambda: app.registrar_libro(self.con),
                          ['anterior1', 'otro', 'autor', 'genero', '01/01/2020'])
        n = app.crear_prestamo(self.con, '1', 'ANTERIOR1', '2026-01-01', '2026-01-02')
        self.assertEqual(app.datos_prestamo(self.con, n)['libro_id'], 'anterior1')

    def test_identificadores_con_tildes_y_registros_anteriores(self):
        self.con.execute('INSERT INTO libros VALUES (?, ?, ?, ?, ?, ?)',
                         ('café1', 'TÍTULO', 'AUTOR', 'GÉNERO', '2020-01-01', 'disponible'))
        self.con.commit()
        for identificador in ('CAFÉ1', 'café1', 'cafe\u03011'):
            _, salida = probar_entrada(lambda: app.consultar_libro(self.con), [identificador])
            self.assertIn('TÍTULO', salida)
        with self.assertRaises(ValueError):
            probar_entrada(lambda: app.registrar_libro(self.con),
                           ['CAFÉ1', 'OTRO', 'AUTOR', 'GENERO', '01/01/2020'])
        numero = app.crear_prestamo(self.con, '1', 'CAFÉ1', '2026-01-01', '2026-01-02')
        self.assertEqual(app.datos_prestamo(self.con, numero)['libro_id'], 'café1')
        with contextlib.redirect_stdout(io.StringIO()): app.devolver(self.con, numero)
        self.assertEqual(self.con.execute('SELECT estado FROM libros WHERE id=?', ('café1',)).fetchone()[0], 'disponible')
        _, salida = probar_entrada(lambda: app.consultar_libro(self.con), ['CAFE1'])
        self.assertIn('Registro no encontrado', salida)

    def test_catalogo_vacio_y_con_libros(self):
        con_vacia = app.conectar(':memory:')
        try:
            with contextlib.redirect_stdout(io.StringIO()) as salida:
                app.listar_libros(con_vacia)
            self.assertIn('No hay libros registrados', salida.getvalue())
        finally:
            con_vacia.close()
        with contextlib.redirect_stdout(io.StringIO()) as salida:
            app.listar_libros(self.con)
        texto = salida.getvalue()
        for dato in ('L1', 'LIBRO UNO', 'AUTOR', 'disponible', 'L3', 'en mantenimiento'):
            self.assertIn(dato, texto)

    def test_catalogo_limitado_a_100(self):
        self.con.executemany('INSERT INTO libros VALUES (?, ?, ?, ?, ?, ?)',
            [('X%03d' % i, 'TITULO %03d' % i, 'AUTOR', 'GENERO', '2020-01-01', 'disponible')
             for i in range(150)])
        self.con.commit()
        with contextlib.redirect_stdout(io.StringIO()) as salida:
            app.listar_libros(self.con)
        lineas = salida.getvalue().splitlines()
        self.assertEqual(sum(linea.startswith('Identificador:') for linea in lineas), 100)
        self.assertIn('máximo 100', salida.getvalue())
        self.assertNotIn('X149', salida.getvalue())

    def test_muestras_usuarios_y_prestamos(self):
        vacia = app.conectar(':memory:')
        try:
            with contextlib.redirect_stdout(io.StringIO()) as salida:
                app.listar_usuarios(vacia)
                app.listar_prestamos(vacia)
            self.assertIn('No hay usuarios', salida.getvalue())
            self.assertIn('No hay préstamos', salida.getvalue())
        finally:
            vacia.close()
        self.con.executemany('INSERT INTO usuarios VALUES (?, ?, ?, ?, ?, ?)',
                             [(str(i), 'NOMBRE', 'APELLIDO', 'CALLE', '123', 'A@B.CO') for i in range(3, 154)])
        self.con.executemany('INSERT INTO prestamos(documento, libro_id, fecha_inicio, fecha_devolucion, devuelto) VALUES (?, ?, ?, ?, 1)',
                             [('1', 'L1', '2020-01-01', '2020-01-02') for _ in range(150)])
        self.con.commit()
        for funcion, prefijo in [(app.listar_usuarios, 'Documento:'), (app.listar_prestamos, 'Préstamo:')]:
            with self.subTest(funcion=funcion.__name__), contextlib.redirect_stdout(io.StringIO()) as salida:
                funcion(self.con)
                lineas = salida.getvalue().splitlines()
                self.assertEqual(sum(linea.startswith(prefijo) for linea in lineas), 100)
                self.assertIn('máximo 100', salida.getvalue())
        with contextlib.redirect_stdout(io.StringIO()) as salida:
            app.listar_prestamos(self.con)
        self.assertIn('Préstamo: 150 | Documento: 1 | Libro: L1 - LIBRO UNO | Estado: devuelto', salida.getvalue())
        self.assertNotIn('Préstamo: 1 |', salida.getvalue())
        _, salida = probar_entrada(lambda: app.consultar_prestamos(self.con), ['1', '0'])
        self.assertEqual(sum(linea.startswith('Préstamo ') for linea in salida.splitlines()), 100)
        self.assertIn('Préstamo 150 |', salida)
        self.assertNotIn('Préstamo 1 |', salida)

    def test_historial_completo_por_paginas(self):
        self.con.executemany('INSERT INTO prestamos(documento, libro_id, fecha_inicio, fecha_devolucion, devuelto) VALUES (?, ?, ?, ?, 1)',
                             [('1', 'L1', '2020-01-01', '2020-01-02') for _ in range(201)])
        self.con.commit()
        _, salida = probar_entrada(lambda: app.consultar_prestamos(self.con), ['1', 'invalido', '1', '1'])
        lineas = [linea for linea in salida.splitlines() if linea.startswith('Préstamo ')]
        self.assertEqual(len(lineas), 201)
        self.assertEqual(len(set(lineas)), 201)
        self.assertIn('Préstamo 201 |', lineas[0])
        self.assertIn('Préstamo 1 |', lineas[-1])
        self.assertIn('Página 3', salida)
        self.assertIn('Digite 1 para continuar o 0 para volver.', salida)
        self.assertIn('Fin del historial', salida)

    def test_historial_vacio_y_pagina_exacta(self):
        _, salida = probar_entrada(lambda: app.consultar_prestamos(self.con), ['1'])
        self.assertIn('no tiene préstamos', salida)
        self.con.executemany('INSERT INTO prestamos(documento, libro_id, fecha_inicio, fecha_devolucion, devuelto) VALUES (?, ?, ?, ?, 1)',
                             [('1', 'L1', '2020-01-01', '2020-01-02') for _ in range(100)])
        self.con.commit()
        _, salida = probar_entrada(lambda: app.consultar_prestamos(self.con), ['1'])
        self.assertEqual(sum(linea.startswith('Préstamo ') for linea in salida.splitlines()), 100)
        self.assertIn('Fin del historial', salida)

    def test_inicio_prestamo_es_fecha_actual(self):
        manana = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%d/%m/%Y')
        with patch.object(app, 'comprobante') as comprobante:
            _, salida = probar_entrada(lambda: app.registrar_prestamo(self.con), ['1', 'L1', '01/01/1900', manana])
        fila = self.con.execute('SELECT * FROM prestamos').fetchone()
        self.assertEqual(fila['fecha_inicio'], datetime.date.today().isoformat())
        self.assertIn('Fecha de inicio del préstamo:', salida)
        self.assertIn('igual o posterior', salida)
        comprobante.assert_called_once()

    def test_prestamos_sin_indices_adicionales(self):
        indices = self.con.execute("SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL").fetchall()
        self.assertEqual(indices, [])
        self.con.execute("INSERT INTO prestamos(documento, libro_id, fecha_inicio, fecha_devolucion) VALUES (?, ?, ?, ?)",
                         ('1', 'L1', '2026-01-01', '2026-01-02'))
        self.con.commit()
        # Aun si el estado del libro fue alterado fuera del programa, no se presta dos veces.
        with self.assertRaisesRegex(ValueError, 'libro está en préstamo'):
            app.crear_prestamo(self.con, '2', 'L1', '2026-01-01', '2026-01-02')
        with self.assertRaisesRegex(ValueError, 'usuario tiene un préstamo'):
            app.crear_prestamo(self.con, '1', 'L2', '2026-01-01', '2026-01-02')

    def test_restricciones_prestamo_y_devolucion(self):
        n = app.crear_prestamo(self.con, '1', 'L1', '2026-01-01', '2026-01-10')
        fila = app.datos_prestamo(self.con, n)
        self.assertEqual(app.estado_prestamo(fila, datetime.date(2026, 1, 10)), 'vigente')
        self.assertEqual(app.estado_prestamo(fila, datetime.date(2026, 1, 11)), 'vencido')
        for usuario, libro in [('1', 'L2'), ('2', 'L1'), ('2', 'L3'), ('9', 'L2'), ('2', 'NO')]:
            with self.subTest(usuario=usuario, libro=libro), self.assertRaises(ValueError):
                app.crear_prestamo(self.con, usuario, libro, '2026-01-01', '2026-01-10')
        with self.assertRaises(ValueError):
            app.crear_prestamo(self.con, '2', 'L2', '2026-01-10', '2026-01-01')
        self.assertEqual(self.con.execute('SELECT count(*) FROM prestamos').fetchone()[0], 1)
        with contextlib.redirect_stdout(io.StringIO()): app.devolver(self.con, n)
        self.assertEqual(app.estado_prestamo(app.datos_prestamo(self.con, n)), 'devuelto')
        self.assertEqual(self.con.execute("SELECT estado FROM libros WHERE id='L1'").fetchone()[0], 'disponible')
        with self.assertRaises(ValueError): app.devolver(self.con, n)
        self.assertIsNotNone(app.crear_prestamo(self.con, '1', 'L2', '2026-01-01', '2026-01-10'))

    def test_claves_foraneas_y_sql_injection(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute("INSERT INTO prestamos(documento,libro_id,fecha_inicio,fecha_devolucion) VALUES (?, ?, ?, ?)", ('9', 'L1', '2026-01-01', '2026-01-02'))
        self.con.rollback()
        _, salida = probar_entrada(lambda: app.consultar_libro(self.con), ["L1' OR '1'='1"])
        self.assertIn('no encontrado', salida)
        self.assertEqual(self.con.execute('SELECT count(*) FROM libros').fetchone()[0], 3)

    def test_duplicados_y_recuperacion_menu(self):
        entradas = ['1', '1', 'otro', 'autor', 'calle', '123', 'a@b.co', '1', '3', 'nuevo', 'usuario', 'calle', '123', 'a@b.co', '0']
        opciones = {'1': ('Registrar', lambda: app.registrar_usuario(self.con))}
        _, salida = probar_entrada(lambda: app.menu(self.con, 'USUARIOS', opciones), entradas)
        self.assertIn('duplicado', salida)
        self.assertIsNotNone(self.con.execute("SELECT 1 FROM usuarios WHERE documento='3'").fetchone())

    def test_pdf_y_envio_simulado(self):
        n = app.crear_prestamo(self.con, '1', 'L1', '2026-01-01', '2026-01-10')
        fila = app.datos_prestamo(self.con, n)
        with tempfile.TemporaryDirectory() as tmp, patch.object(app, 'COMPROBANTES', Path(tmp)):
            pdf = app.pdf_comprobante(fila)
            contenido = pdf.read_bytes()
            for valor in (b'%PDF-1.4', b'ANA', b'LIBRO UNO', b'01/01/2026', b'10/01/2026', b'%%EOF'):
                self.assertIn(valor, contenido)
            config = {'BIBLIOTECA_SMTP_HOST':'smtp.example.com', 'BIBLIOTECA_SMTP_USUARIO':'test@example.com', 'BIBLIOTECA_SMTP_CLAVE':'prueba', 'BIBLIOTECA_SMTP_PUERTO':'587'}
            with patch.dict(os.environ, config, clear=True), patch.object(app.smtplib, 'SMTP') as smtp:
                app.enviar_comprobante(fila, pdf)
                conexion = smtp.return_value.__enter__.return_value
                conexion.starttls.assert_called_once()
                correo = conexion.send_message.call_args.args[0]
                self.assertEqual(correo['To'], 'ANA@EJEMPLO.COM')
                self.assertEqual(next(correo.iter_attachments()).get_payload(decode=True), contenido)

    def test_configuracion_local_persistente_y_precedencia_entorno(self):
        n = app.crear_prestamo(self.con, '1', 'L1', '2026-01-01', '2026-01-10')
        fila = app.datos_prestamo(self.con, n)
        with tempfile.TemporaryDirectory() as tmp, patch.object(app, 'COMPROBANTES', Path(tmp)):
            ruta = app.pdf_comprobante(fila)
            archivo = Path(tmp) / 'configuracion_correo.json'
            archivo.write_text(json.dumps({'host': 'smtp.example.com', 'puerto': 587,
                                            'usuario': 'cuenta@example.com', 'clave': 'clave-ficticia'}), encoding='utf-8')
            with patch.object(app, 'CONFIGURACION_CORREO', archivo), patch.dict(os.environ, {}, clear=True), patch.object(app.smtplib, 'SMTP') as smtp:
                app.enviar_comprobante(fila, ruta)
                smtp.assert_called_once_with('smtp.example.com', 587, timeout=20)
                smtp.return_value.__enter__.return_value.login.assert_called_once_with('cuenta@example.com', 'clave-ficticia')
            entorno = {'BIBLIOTECA_SMTP_HOST': 'otro.example.com', 'BIBLIOTECA_SMTP_USUARIO': 'otro@example.com', 'BIBLIOTECA_SMTP_CLAVE': 'otra-clave'}
            with patch.object(app, 'CONFIGURACION_CORREO', archivo), patch.dict(os.environ, entorno, clear=True), patch.object(app.smtplib, 'SMTP') as smtp:
                app.enviar_comprobante(fila, ruta)
                smtp.assert_called_once_with('otro.example.com', 587, timeout=20)
            archivo.write_text('{invalido', encoding='utf-8')
            with patch.object(app, 'CONFIGURACION_CORREO', archivo), patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(ValueError): app.enviar_comprobante(fila, ruta)

    def test_fallo_de_correo_conserva_prestamo(self):
        n = app.crear_prestamo(self.con, '1', 'L1', '2026-01-01', '2026-01-10')
        with tempfile.TemporaryDirectory() as tmp, patch.object(app, 'COMPROBANTES', Path(tmp)), patch.dict(os.environ, {}, clear=True):
            with contextlib.redirect_stdout(io.StringIO()) as salida: app.comprobante(self.con, n)
            self.assertIn('préstamo se conserva', salida.getvalue())
            self.assertTrue((Path(tmp) / ('prestamo_%s.pdf' % n)).exists())
            self.assertEqual(self.con.execute("SELECT estado FROM libros WHERE id='L1'").fetchone()[0], 'prestado')


class Ejecucion(unittest.TestCase):
    def test_ejecucion_completa_por_consola(self):
        # Se ejecuta en un directorio temporal; nunca usa la base real del proyecto.
        entradas = '\n'.join(['error', '1', '1', 'L1', 'Libro', 'Autor', 'Ciencia',
                              '31/02/2026', '01/01/2020', '0', '2', '1', 'abc', '123',
                              'Ana', 'Perez', 'Calle 1', '123', 'ana@example.com', '0',
                              '3', '1', '123', 'L1', '01/01/1900',
                              (datetime.date.today() + datetime.timedelta(days=1)).strftime('%d/%m/%Y'), '3', '123', '2', 'a', '1', '1', '0', '0', ''])
        with tempfile.TemporaryDirectory() as tmp:
            copia = Path(tmp) / 'aplicacion.py'
            copia.write_text(ARCHIVO.read_text(encoding='utf-8'), encoding='utf-8')
            entorno = {k: v for k, v in os.environ.items() if not k.startswith('BIBLIOTECA_SMTP_')}
            resultado = subprocess.run([sys.executable, str(copia)], input=entradas,
                                       text=True, cwd=tmp, env=entorno,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
            self.assertEqual(resultado.returncode, 0, resultado.stderr)
            for mensaje in ('opción válida', 'fecha válida', 'igual o posterior',
                            'Préstamo registrado', 'Devolución registrada'):
                self.assertIn(mensaje, resultado.stdout)
            with sqlite3.connect(str(Path(tmp) / 'BaseDeDatosAplicacion.db')) as con:
                self.assertEqual(con.execute('SELECT titulo, estado FROM libros').fetchone(), ('LIBRO', 'disponible'))
                self.assertEqual(con.execute('SELECT devuelto FROM prestamos').fetchone()[0], 1)


if __name__ == '__main__':
    unittest.main()
