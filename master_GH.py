# Este script ha sido diseñado para registrar usuarios en una tabla de la base de datos.
# Posteriormente, a estos usuarios se les envía una notificación mediante una tarea programada (cron job).
# El propósito principal de este script es controlar exclusivamente el contenido que se enviará a los usuarios. 
# En caso de que un usuario ingrese el mismo valor tres veces, esto no representa un inconveniente, ya que la base de datos está configurada para gestionar los datos y garantizar que no se generen duplicados.
# Sin embargo, si un usuario introduce información incorrecta o no válida, el script generará un error y se detendrá,
# dado que aún no se ha implementado un manejador para procesar mensajes de cualquier tipo.
# Hecho por Juan Blanc, aburrido, febrero 2025


# Importante, la DB es MariaDB (MySQL) Corriendo en una raspi3b
# Esquema en la DB
# Instancia | Tabla
# notification_system.notificaciones --> Tabla que contiene información sobre las notificaciones, que pidio, entre otros
# otras tablas no se usan
#
#


import telebot
import mysql.connector
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup,InlineKeyboardButton
from telebot import types
from datetime import datetime



# Configuración del bot de Telegram
TOKEN = "TOKEN TOKEN"
bot = telebot.TeleBot(TOKEN)

# Configuración de la base de datos
DB_CONFIG = {
    "host": "mariadb.local",
    "user": "noti_guy",
    "password": "quepassword",
    "database": "notification_system"
}

def conectar_db():
    return mysql.connector.connect(**DB_CONFIG)

# Diccionario sencillo para almacenar respuestas temporales de los usuarios
datos_usuarios = {}

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    datos_usuarios[chat_id] = {}
    bot.send_message(chat_id, "Bienvenido🚀! ¿Qué tipo de información deseas recibir?\n☀️ clima -- Provisto por el SMN, para 117 ciudades del país.\n🌊 datos_operativos -- Datos Operativos de Salto Grande (última hora)\n︎⚡︎ imagen -- Consumo actual de energía a nivel país priovisto por CAMMESA, comparándola con la estimada (predespacho)", reply_markup=menu_tipo_datos())

# Menús de selección
def menu_tipo_datos():
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    opciones = ["clima", "imagen", "datos_operativos"]
    for opcion in opciones:
        markup.add(KeyboardButton(opcion))
    return markup

def obtener_ciudades():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, ciudad FROM notification_system.observaciones_meteorologicas_ref order by ciudad asc ;")
    ciudades = {fila[1]: fila[0] for fila in cursor.fetchall()}  # Diccionario {nombre_ciudad: id}
    cursor.close()
    conn.close()
    return ciudades

def menu_ciudad():
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True) #mas vale que scrollee 
    ciudades = obtener_ciudades()
    for ciudad in ciudades.keys():
        markup.add(KeyboardButton(ciudad))
    return markup

def menu_horarios():
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    horarios = ["4AM", "5AM", "6AM", "10AM", "3PM", "4PM", "5PM", "7PM", "9PM"]
    for horario in horarios:
        markup.add(KeyboardButton(horario))
    return markup

def menu_si_no():
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(KeyboardButton("Sí"), KeyboardButton("No"))
    return markup

def menu_medio():
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    opciones = ["radio", "tv", "diario", "streaming", "ninguno"]
    for opcion in opciones:
        markup.add(KeyboardButton(opcion))
    return markup

# Flujo de registro de usuario
@bot.message_handler(func=lambda message: message.text in ["clima", "imagen", "datos_operativos"])
def seleccionar_tipo_datos(message):
    chat_id = message.chat.id
    datos_usuarios[chat_id]["que_necesita"] = message.text
    bot.send_message(chat_id, "🌆 Selecciona tu ciudad:", reply_markup=menu_ciudad())

@bot.message_handler(func=lambda message: message.text in obtener_ciudades().keys())
def seleccionar_ciudad(message):
    chat_id = message.chat.id
    datos_usuarios[chat_id]["ciudad"] = obtener_ciudades()[message.text]  # Guardar ID en lugar del nombre, nos va a servir mas adelante
    bot.send_message(chat_id, "⌚¿A qué hora queres recibir el mensaje?", reply_markup=menu_horarios())

@bot.message_handler(func=lambda message: message.text in ["4AM", "5AM", "6AM", "10AM", "3PM", "4PM", "5PM", "7PM", "9PM"])
def seleccionar_horario(message):
    chat_id = message.chat.id
    # esto es horrible, perdón Stallman
    horarios_convertidos = {
        "4AM": "04:00:00",
        "5AM": "05:00:00",
        "6AM": "06:00:00",
        "10AM": "10:00:00",
        "3PM": "15:00:00",
        "4PM": "16:00:00",
        "5PM": "17:00:00",
        "7PM": "19:00:00",
        "9PM": "21:00:00"
    }
    #datos_usuarios[chat_id]["confirmacion_de_envio"] = horarios_convertidos[message.text]
    datos_usuarios[chat_id]["confirmacion_de_envio"] = datetime.now().strftime("%Y-%m-%d") + " " + horarios_convertidos[message.text]
    bot.send_message(chat_id, "🆔 ¿Sos usuario VIP?", reply_markup=menu_si_no())

@bot.message_handler(func=lambda message: message.text in ["Sí", "No"])
def seleccionar_vip(message):
    chat_id = message.chat.id
    # esto fue implementado pero nunca tuvo un fin, solo para poner VIP (Vino y Pastillas)
    datos_usuarios[chat_id]["VIP"] = message.text == "Sí"
    bot.send_message(chat_id, "🗞️¿Perteneces a un medio periodístico?️", reply_markup=menu_medio())

@bot.message_handler(func=lambda message: message.text in ["radio", "tv", "diario", "streaming", "ninguno"])
def seleccionar_medio(message):
    chat_id = message.chat.id
    datos_usuarios[chat_id]["medio_periodistico"] = message.text
    guardar_en_db(chat_id)
    bot.send_message(chat_id, "🎉🎉Tu registro ha sido completado. ¡Gracias!")

def guardar_en_db(chat_id):
    datos = datos_usuarios[chat_id]
    conn = conectar_db()
    cursor = conn.cursor()
    #print("QUE ELIGIO?") # Log, gracias fernandez
    #print(datos["ciudad"])
    query = """
    INSERT INTO notificaciones (chat_id, enabled, que_necesita, ciudad, confirmacion_de_envio, VIP, medio_periodistico)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE que_necesita=VALUES(que_necesita), ciudad=VALUES(ciudad), confirmacion_de_envio=VALUES(confirmacion_de_envio), VIP=VALUES(VIP), medio_periodistico=VALUES(medio_periodistico);
    """
    valores = (chat_id, True, datos["que_necesita"], datos["ciudad"], datos["confirmacion_de_envio"], datos["VIP"], datos["medio_periodistico"])
    
    cursor.execute(query, valores)
    conn.commit()
    cursor.close()
    conn.close()

@bot.message_handler(commands=['mis_notificaciones'])
def mis_notificaciones(message):
    chat_id = message.chat.id
    conn = conectar_db()
    cursor = conn.cursor()
    # traemos solo las notificaciones habilitadas para ese usuario en especifico
    cursor.execute("SELECT que_necesita AS 'Pedido', medio_periodistico AS 'Plataforma',time(confirmacion_de_envio) as 'Enviar a' FROM notificaciones WHERE chat_id = %s and enabled='1' ;", (chat_id,))
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    #armamos un bello string para enviarle 
    if resultados:
        respuesta = "Tus notificaciones:\n" + "\n".join([f"➡️Pedido: {r[0]} (Medio: {r[1]}) Hora: {r[2]}" for r in resultados])
    else:
        respuesta = "😱 No tenes notificaciones habilitadas..."
    
    bot.send_message(chat_id, respuesta)
    
@bot.message_handler(commands=['quitar_suscripcion'])
def quitar_suscripcion(message):
    chat_id = message.chat.id
    conn = conectar_db()
    cursor = conn.cursor()
    # siempre hay un cheto arrepentido
    query = """
    SELECT que_necesita, TIME(confirmacion_de_envio) AS hora_envio, MIN(medio_periodistico) AS medio_ejemplo, COUNT(*) AS cantidad
    FROM notificaciones 
    WHERE chat_id = %s AND enabled = 1 
    GROUP BY que_necesita, TIME(confirmacion_de_envio);
    """
    cursor.execute(query, (chat_id,))
    resultados = cursor.fetchall()
    print(f"Notificaciones encontradas para chat_id {chat_id}: {resultados}")
    cursor.close()
    conn.close()

    if not resultados:
        bot.send_message(chat_id, "😱 No tenes notificaciones habilitadas para remover.")
        return
    # creamos un selector inline para que elimine sus notificaciones
    markup = InlineKeyboardMarkup()
    for resultado in resultados:
        que_necesita, hora_envio, medio_ejemplo, cantidad = resultado
        texto_boton = f"{que_necesita} ({medio_ejemplo}) - {hora_envio} ({cantidad} suscripción{'es' if cantidad > 1 else ''})"
        callback_data = f"quitar|{que_necesita}|{hora_envio}"  # Usamos | como separador, el guion bajo rompia todo
        markup.add(InlineKeyboardButton(text=texto_boton, callback_data=callback_data))

    bot.send_message(chat_id, "⌨ Seleccioná la notificación para remover:", reply_markup=markup)
    # si el chat responde, sigue lo de abajo
@bot.callback_query_handler(func=lambda call: call.data.startswith('quitar|'))
def manejar_quitar_suscripcion(call):
    chat_id = call.message.chat.id
    partes = call.data.split('|')
    que_necesita = partes[1]
    hora_envio = partes[2]  # La hora no incluye partes adicionales, tuki
    print(f"Intentando quitar: chat_id={chat_id}, que_necesita={que_necesita}, hora_envio={hora_envio}")

    try:
        conn = conectar_db()
        cursor = conn.cursor()
        query = """
        UPDATE notificaciones 
        SET enabled = 0 
        WHERE chat_id = %s AND que_necesita = %s AND TIME(confirmacion_de_envio) = %s AND enabled = 1;
        """
        cursor.execute(query, (chat_id, que_necesita, hora_envio))
        cantidad_afectada = cursor.rowcount
        print(f"Filas afectadas: {cantidad_afectada}")
        conn.commit()
        cursor.close()
        conn.close()

        if cantidad_afectada > 0:
            bot.answer_callback_query(call.id, f" ‼ Suscripción eliminada exitosamente ({cantidad_afectada} afectada{'s' if cantidad_afectada > 1 else ''}).")
            bot.edit_message_text(f"‼ Suscripción eliminada ({cantidad_afectada} afectada{'s' if cantidad_afectada > 1 else ''}).", chat_id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "No se pudo eliminar la suscripción🛸🛸🛸.")
            bot.edit_message_text("No se pudo eliminar la suscripción🛸", chat_id, call.message.message_id)

    except mysql.connector.Error as e:
        bot.answer_callback_query(call.id, "Error al eliminar la suscripción.")
        bot.send_message(chat_id, f"Error en la base de datos: {e}")
        print(f"Error en la base de datos: {e}")
        
bot.polling()
