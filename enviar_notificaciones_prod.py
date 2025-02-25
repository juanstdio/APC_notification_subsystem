# script que se ejecuta en cronjob una vez por hora (al segundo 5 de empezada la hora) para enviar (si corresponde)
# los avisos que los usuarios han especificado mediante el bot.
# es una variación del script "offline_enviar_notific", nada menos que se le ha agregado la librería telebot para enviar los mensajes por Telegram.
# Hecho por Juan Blanc, aburrido, febrero 2025

# Importante, la DB es MariaDB (MySQL) Corriendo en una raspi3b
# Esquema en la DB
# Instancia | Tabla
# notification_system.observaciones_meteorologicas_ref  --> Tabla que contiene un ID único para cada ciudad.
# SMN.observaciones_meteorologicas --> Tabla que contiene información provista por el SMN, actualiza cada hora
# notification_system.notificaciones --> Tabla que contiene información sobre las notificaciones, user_id, que pidio, entre otros
# juanserver.saltogrande_explotacion --> Datos en tiempo real de salto grande, actualiza cada hora y 22 minutos, VIVA el PHP de salto grande !
#

import mysql.connector
import paramiko
import os
import telebot
from datetime import datetime

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'mariadb.local',
    'user': 'noti_guy',
    'password': 'quepassword',
    'database': 'notification_system'
}

# Configuración de Telegram (ajusta tu token)
tb = telebot.TeleBot('TOKEN TOKEN')  # Reemplaza con tu token

def obtener_datos_ciudad(ciudad_id):
    """Obtiene datos meteorológicos de una ciudad específica."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        query = "SELECT SMO.*, TIMESTAMPDIFF(HOUR, STR_TO_DATE(CONCAT(SMO.fecha, ' ', SMO.hora), '%Y-%m-%d %H:%i:%s'), NOW()) AS horas_transcurridas FROM notification_system.observaciones_meteorologicas_ref SMNREF left join SMN.observaciones_meteorologicas SMO on SMNREF.ciudad=SMO.ciudad where SMNREF.id ='"+ ciudad_id + "';"
        cursor.execute(query)
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()
        return resultado
    except mysql.connector.Error as e:
        print("Error en la base de datos:", e)
        return None

def procesar_clima(ciudad_id):
    """Procesa y formatea los datos meteorológicos."""
    def limpiar(valor, unidad=""):
        if valor in [None, "None", "none"]:
            return "❗Sin datos❗"
        return f"{valor}{unidad}".strip()

    datos = obtener_datos_ciudad(ciudad_id)
    if datos:
        mensaje = (
            f"🌍 Ciudad: {limpiar(datos['ciudad'])}\n"
            f"📅 Hora y Fecha de Muestra: {limpiar(datos['fecha'])} {limpiar(datos['hora'])} ({limpiar(datos['horas_transcurridas'], ' h atrás💾')})\n"
            f"☁️ Nubes: {limpiar(datos['nubes'])}\n"
            f"🔭 Visibilidad: {limpiar(datos['visibilidad'])}\n"
            f"🌡️ Temperatura: {limpiar(datos['temperatura'], ' °C')}\n"
            f"🥵*Sensación térmica* {limpiar(datos['sensacion_termica'], ' °C')}\n"
            f"💧 Humedad: {limpiar(datos['humedad'], ' %')}\n"
            f"🌬️ Viento: {limpiar(datos['direccion_viento'], ' km/h')}\n"
            f"📈 Presión: {limpiar(str(datos['presion']).replace('/', '').strip(), ' hPa')}"
        )
    else:
        mensaje = "⚠️ No se encontraron datos para esta ciudad."
    return mensaje

def validar_hora(hora_notificacion):
    """Valida si la hora de la notificación coincide con la hora actual del sistema."""
    hora_actual = datetime.now().hour  # Hora actual en formato 24h
    if hora_notificacion == hora_actual:
        print(f"Validación de hora OK: Hora notificación ({hora_notificacion}) coincide con hora actual ({hora_actual})")
        return True
    else:
        print(f"Validación de hora FALLIDA: Hora notificación ({hora_notificacion}) NO coincide con hora actual ({hora_actual})")
        return False


def procesar_notificaciones():
    try:
        # Conectar a la base de datos
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Obtener todas las notificaciones activas
        query = "SELECT id, chat_id, que_necesita, ciudad, HOUR(confirmacion_de_envio) AS hora_envio FROM notification_system.notificaciones WHERE enabled = 1"
        cursor.execute(query)
        notificaciones = cursor.fetchall()

        for notificacion in notificaciones:
            id_notif, chat_id, que_necesita, ciudad, hora_envio = notificacion
            print(f"\nProcesando notificación ID {id_notif} para chat_id {chat_id}") #para log y debug
            print(f"\n{id_notif}, {chat_id}, {que_necesita}, {ciudad}, {hora_envio}") #mas log y debug
            # Validar si es la hora correcta para enviar
            if validar_hora(hora_envio):
                if que_necesita == 'imagen':
                    try:
                        ssh = paramiko.SSHClient()
                        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        ssh.connect('raspi2b.local', username='olaf', password='vikingo')
                        sftp = ssh.open_sftp()
                        remote_file_path = '/home/juan/00cammesa/demanchart/grafico_demanda_predespacho.png'
                        local_file_path = os.path.join(os.getcwd(), 'grafico_demanda_predespacho.png')
                        sftp.get(remote_file_path, local_file_path)
                        sftp.close()
                        ssh.close()

                        with open(local_file_path, 'rb') as img:
                            tb.send_photo(chat_id, img)
                        print(f"Imagen enviada a chat_id {chat_id}")

                    except paramiko.SSHException as e:
                        tb.send_message(chat_id, "SSH roto: " + str(e))
                        print("SSH roto: " + str(e))
                    except FileNotFoundError as e:
                        tb.send_message(chat_id, "No hay archivo: " + str(e))
                        print("No hay archivo: " + str(e))
                    except Exception as e:
                        tb.send_message(chat_id, "ERROR FATAL: " + str(e))
                        print("ERROR FATAL: " + str(e))

                elif que_necesita == 'datos_operativos':
                    try:
                        conn_data = mysql.connector.connect(**DB_CONFIG)
                        cursor_data = conn_data.cursor()

                        query_data = """
                        SELECT HORA_FECHA_REPORTE, MaquinasDisp, MaquinasActivas, PotI, PotRotante, ETotal, Temperatura, avgCotaEmbalse, avgCotaRestitu
                        FROM juanserver.saltogrande_explotacion
                        ORDER BY idsaltogrande_explotacion DESC
                        LIMIT 1;
                        """

                        cursor_data.execute(query_data)
                        result = cursor_data.fetchone()
                        cursor_data.close()
                        conn_data.close()

                        if result:
                            hora_reporte, maquinas_disp, maquinas_activas, pot_i, pot_rotante, etotal, temperatura, altura_lago, altura_rio = result
                            temperatura = temperatura.replace('Â', '').replace(',', '.')

                            respuesta = (f"Datos Operativos Salto Grande\n"
                                         f"⏱ Fecha y Hora: {hora_reporte}\n"
                                         f"⚙ Máquinas Disponibles: {maquinas_disp}\n"
                                         f"💡Máquinas Activas: {maquinas_activas}\n"
                                         f"⚡Potencia Instantánea: {pot_i}\n"
                                         f"⚡Potencia Rotante: {pot_rotante}\n"
                                         f"🔋Energía generada en lo que va del día: {etotal}\n"
                                         f"🌡 Temperatura exterior: {temperatura}\n"
                                         f"🏊 Altura Lago: {altura_lago}\n"
                                         f"🚣 Altura Río: {altura_rio}")
                            tb.send_message(chat_id, respuesta)
                            print(f"Datos operativos enviados a chat_id {chat_id}")
                        else:
                            tb.send_message(chat_id, "No hay datos disponibles en este momento.")
                            print("No hay datos disponibles en este momento.")

                    except mysql.connector.Error as e:
                        tb.send_message(chat_id, f"Error en la base de datos: {e}")
                        print(f"Error en la base de datos: {e}")

                elif que_necesita == 'clima':
                    resultado = procesar_clima(ciudad)
                    tb.send_message(chat_id, resultado)
                    print(f"Datos de clima enviados a chat_id {chat_id}")
            else:
                print(f"Notificación ID {id_notif} no procesada por horario incorrecto.")
        cursor.close()
        conn.close()
    except mysql.connector.Error as e:
        print(f"Error al conectar con la base de datos: {e}")
    except Exception as e:
        print(f"Error general: {e}")

if __name__ == "__main__":
    procesar_notificaciones()
