from datetime import datetime, timedelta
import imaplib
import email
import os
from email.header import decode_header
from dotenv import load_dotenv
from conexiondb import *
import locale

#Set locale to español mexico
locale.setlocale(locale.LC_ALL, 'es_MX.UTF-8')
# Carga el archivo .env
load_dotenv()
usuario = os.getenv('USER')
password = os.getenv('PASS')

def get_first_text_block(email_message_instance):
    maintype = email_message_instance.get_content_maintype()
    if maintype == 'multipart':
        for part in email_message_instance.get_payload():
            if part.get_content_maintype() == 'text':
                return part.get_payload()
    elif maintype == 'text':
        return email_message_instance.get_payload()

def get_sender_email(email_message):
    # Obtener el remitente
    sender = email_message['From']
    # Analizar el remitente para obtener el correo electrónico
    sender_name, sender_email = email.utils.parseaddr(sender)
    return sender_email

def analyze_email(email_message):
    # Initialize date_and_time
    date_and_time = None

    # Obtener el correo electrónico del remitente
    sender_email = get_sender_email(email_message)
    print(f"Remitente: {sender_email}")

    # Obtener el asunto del correo
    subject = email_message['Subject'].lower()
    print(f"Asunto: {subject}")

    # Obtener el cuerpo del correo
    body_text = get_first_text_block(email_message)
    if body_text is None:
        # No se encontró un bloque de texto, manejar este caso
        body = ''
    else:
        body = body_text.lower()
    #print(f"Cuerpo del correo: {body}")

    # Buscar palabras clave
    if 'cancelar' in subject:
        action = 'canceló'
        #print(f"Acción: {action}")
        # Extraer la fecha y la hora de la cita
        try:
            # Buscar la parte de la fecha y la parte de la hora
            date_part, time_part = body.split(' y hora ')
            date_part = date_part.replace("cancelar cita del dia ", "")
            time_part = time_part.replace(".", "")
            #Eliminar caracteres de carro 
            time_part= time_part.strip()
            #print(f"Fecha: {date_part}")
            #print(f"Hora: {time_part}")

            # Convertir date_part a objeto datetime
            date_obj = datetime.strptime(date_part, '%A, %d de %B de %Y')
            #print(f"Fecha: {date_obj}")
            #pasamos a formato Y-M-D
            dateFormat = date_obj.strftime('%Y-%m-%d')
            print(f"Fecha: {dateFormat}")
            # Convertir time a un objeto datetime
            time_obj = datetime.strptime(time_part, '%H:%M')
            # Añadir 12 horas a time_obj
            time_obj += timedelta(hours=12)

            # Formatear time_obj en formato de 24 horas
            timeFormat = time_obj.strftime('%H:%M:%S')
            print(f"Hora: {timeFormat}")
            # Actualizar el registro en la base de datos
            try:
                connect = conexion.conexionDB()
                if connect.is_connected():
                    cursor = connect.cursor()
                    query = "UPDATE citas SET estado_cita = 'Cancelada' WHERE email_cliente = %s AND fecha = %s AND hora = %s AND estado_cita IS NULL"
                    values = (sender_email, dateFormat, timeFormat)
                    cursor.execute(query, values)
                    if cursor.rowcount > 0:
                        connect.commit()
                        print(f"Registro actualizado para {sender_email} en la fecha {dateFormat} a las {timeFormat}")
                    else:
                        print(f"No se encontró un registro para actualizar para {sender_email} en la fecha {dateFormat} a las {timeFormat}")
            except mysql.connector.Error as e:
                print(f"Error al actualizar el registro: {e}")
            finally:
                if connect.is_connected():
                    cursor.close()
                    connect.close()

        except ValueError as e:
            #print("Error al extraer la fecha y la hora de la cita")
            #IMPRIMIR EL ERROR
            print(e)
    elif 'confirmar' in subject or 'confirmar' in body:
        action = 'confirmó'
        #print(f"Acción: {action}")
    else:
        action = 'desconocida'

    return sender_email, action, date_and_time

def main():
    # Crear conexión
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    print("Conexión establecida")

    # Iniciar sesión
    imap.login(usuario, password)
    #print("Sesión iniciada")

    imap.select("INBOX")
    #print("Bandeja de entrada seleccionada")

    # INBOX PARA LEER LOS MENSAJES RECIBIDOS
    result, data = imap.search(None, "ALL")
    #print("Búsqueda de todos los mensajes completada")

    # BUSCAR TODOS LOS MENSAJES
    ids = data[0]  # data is a list.
    id_list = ids.split()  # ids is a space separated string
    print(f"Número de mensajes encontrados: {len(id_list)}")

    # Iterar a través de todos los correos electrónicos
    for email_id in id_list:
        print("*********************************************")
        print(f"Analizando mensaje con ID: {email_id}")
        result, data = imap.fetch(email_id, "(RFC822)")
        raw_email = data[0][1]
        email_message = email.message_from_bytes(raw_email)
        sender, action, date_time = analyze_email(email_message)
        
    imap.logout()
    print("Sesión cerrada")

if __name__ == "__main__":
    main()


