# Script usado para testear los cambios en las queries SQL para 
# obtener informacion de la DB en el subsistema de notificaciones. 
# Hecho por Juan Blanc, aburrido, febrero 2025

# Importante, la DB es MariaDB (MySQL) Corriendo en una raspi3b
# Esquema en la DB
# Instancia | Tabla
# notification_system.observaciones_meteorologicas_ref  --> Tabla que contiene un ID único para cada ciudad.
# SMN.observaciones_meteorologicas --> Tabla que contiene información provista por el SMN, actualiza cada hora
# notification_system.notificaciones --> Tabla que contiene información sobre las notificaciones, user_id, que pidio, entre otros
# juanserver.saltogrande_explotacion --> Datos en tiempo real de salto grande, actualiza cada hora y 22 minutos, VIVA el PHP de salto grande !
#
#
#

import mysql.connector
import paramiko
import os

# Configuración de la base de datos (ajustar según tus credenciales)
DB_CONFIG = {
    'host': 'mariadb.local',  # Cambiar según el server de prod
    'user': 'noti_guy',
    'password': 'quepassword',
    'database': 'notification_system' # esto no importa, pero hay que espeficarlo
}

def obtener_datos_ciudad(ciudad_id):
    """Obtiene datos meteorológicos de una ciudad específica."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        query = "select SMO.*, TIMESTAMPDIFF(HOUR, STR_TO_DATE(CONCAT(SMO.fecha, ' ', SMO.hora), '%Y-%m-%d %H:%i:%s'),        NOW()) AS horas_transcurridas FROM notification_system.observaciones_meteorologicas_ref SMNREF        left join SMN.observaciones_meteorologicas SMO on SMNREF.ciudad=SMO.ciudad        where SMNREF.id = '"+ ciudad_id + "'; "
        print(query)  # para debug, gracias fernandez
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

def procesar_notificaciones():
    try:
        # Conectar a la base de datos 
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Obtener todas las notificaciones activas
        query = "SELECT id, chat_id, que_necesita, ciudad FROM notification_system.notificaciones WHERE enabled = 1"
        cursor.execute(query)
        notificaciones = cursor.fetchall()
        # como son notificaciones offline, van a aparecer por consola
        for notificacion in notificaciones:
            id_notif, chat_id, que_necesita, ciudad = notificacion
            print(f"\nProcesando notificación ID {id_notif} para chat_id {chat_id}")

            if que_necesita == 'imagen':
                try:
                    # Establecer la conexión SSH
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect('raspi2b.local', username='olaf', password='maestro')

                    # Descargar el archivo remoto
                    sftp = ssh.open_sftp()
                    remote_file_path = '/home/juan/00cammesa/demanchart/grafico_demanda_predespacho.png'
                    local_file_path = os.path.join(os.getcwd(), 'grafico_demanda_predespacho.png')
                    sftp.get(remote_file_path, local_file_path)
                    sftp.close()
                    ssh.close()
                    print(f"Imagen descargada en {local_file_path}")

                except paramiko.SSHException as e:
                    print("SSH roto: " + str(e))
                except FileNotFoundError as e:
                    print("No hay archivo: " + str(e))
                except Exception as e:
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
                        print(respuesta)
                    else:
                        print("No hay datos disponibles en este momento.")

                except mysql.connector.Error as e:
                    print(f"Error en la base de datos: {e}")

            elif que_necesita == 'clima':
                print(ciudad)
                resultado = procesar_clima(ciudad)
                print(resultado)

        cursor.close()
        conn.close()

    except mysql.connector.Error as e:
        print(f"Error al conectar con la base de datos: {e}")
    except Exception as e:
        print(f"Error general: {e}")

if __name__ == "__main__":
    procesar_notificaciones()
