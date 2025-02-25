# APC BackUPS 1500 Subsistema de Notificaciones
### Master_GH:
Este script ha sido diseñado para registrar usuarios en una tabla de la base de datos.
Posteriormente, a estos usuarios se les envía una notificación mediante una tarea programada (cron job).
El propósito principal de este script es controlar exclusivamente el contenido que se enviará a los usuarios. 
En caso de que un usuario ingrese el mismo valor tres veces, esto no representa un inconveniente, ya que la base de datos está configurada para gestionar los datos y garantizar que no se generen duplicados.
Sin embargo, si un usuario introduce información incorrecta o no válida, el script generará un error y se detendrá,
dado que aún no se ha implementado un manejador para procesar mensajes de cualquier tipo.


### Offline_enviar_notifc
Este script fue desarrollado para probar modificaciones en las consultas SQL destinadas a la obtención de información desde la base de datos, específicamente en el subsistema de notificaciones. 
Detalles Técnicos Importantes:
Base de Datos: Se utiliza MariaDB (compatible con MySQL), alojada en una Raspberry Pi 3B.
Esquema de la Base de Datos:
notification_system.observaciones_meteorologicas_ref: Tabla que almacena un identificador único para cada ciudad.
SMN.observaciones_meteorologicas: Tabla con datos meteorológicos proporcionados por el Servicio Meteorológico Nacional (SMN), actualizada cada hora.
notification_system.notificaciones: Tabla que registra información sobre las notificaciones, incluyendo el identificador del usuario (user_id), las solicitudes realizadas y otros datos relevantes.
juanserver.saltogrande_explotacion: Tabla con información en tiempo real proveniente de Salto Grande, actualizada cada hora y 22 minutos. 

### enviar_notificaciones_prod
Este script está programado para ejecutarse mediante un cronjob una vez por hora, específicamente al segundo 5 de iniciada cada hora.
Su función es enviar, cuando corresponde, las notificaciones que los usuarios han configurado previamente a través del bot.
Se trata de una variante del script offline_enviar_notific, al que se le ha incorporado la librería telebot para habilitar el envío de mensajes mediante Telegram.
