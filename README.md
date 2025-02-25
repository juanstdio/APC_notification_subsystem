# APC BackUPS 1500 - Subsistema de Notificaciones

## Master_GH

Este script ha sido diseñado para gestionar el registro de usuarios en una tabla de la base de datos y enviar notificaciones mediante una tarea programada (cron job). A continuación, se describen sus características principales:

- **Propósito**: Controla exclusivamente el contenido que se enviará a los usuarios.
- **Gestión de datos**: 
  - Si un usuario ingresa el mismo valor varias veces, la base de datos está configurada para evitar duplicados.
  - Si se introduce información incorrecta o no válida, el script falla, ya que aún no cuenta con un manejador para procesar mensajes de cualquier tipo.

---

## Offline_enviar_notific

Este script se desarrolló para probar modificaciones en consultas SQL destinadas a obtener información de la base de datos en el subsistema de notificaciones.

### Detalles Técnicos
- **Base de Datos**: MariaDB (compatible con MySQL), alojada en una Raspberry Pi 3B.
- **Esquema de la Base de Datos**:
  - `notification_system.observaciones_meteorologicas_ref`: Tabla con un identificador referencial único por ciudad.
  - `SMN.observaciones_meteorologicas`: Tabla con datos meteorológicos del Servicio Meteorológico Nacional (SMN), actualizada cada hora.
  - `notification_system.notificaciones`: Registra datos de notificaciones, incluyendo `user_id`, solicitudes y más.
  - `juanserver.saltogrande_explotacion`: Contiene información en tiempo real de Salto Grande, actualizada cada hora y 22 minutos.

---

## Enviar_notificaciones_prod

Este script está configurado para ejecutarse mediante un cronjob cada hora (al segundo 5) y enviar notificaciones previamente definidas por los usuarios a través del bot.

### Características
- **Ejecución**: Programada para el segundo 5 de cada hora.
- **Funcionalidad**: Envía notificaciones configuradas por los usuarios.
- **Base**: Variante de `offline_enviar_notific`, con la integración de la librería `telebot` para enviar mensajes por Telegram.

---
