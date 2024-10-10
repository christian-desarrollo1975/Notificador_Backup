
# Importamos librerías
import os
import time
import smtplib
import ssl
import configparser
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def configuraciones():
    
    """
    Lee y devuelve las configuraciones.
    """

    # Crear un objeto ConfigParser
    config = configparser.ConfigParser()

    # Leer el archivo de configuración estableciendo una ruta absoluta con r ..... (r'config.ini')
    config.read(r'config.ini')

    """script_dir = os.path.dirname(os.path.abspath(__file__)) # Obtener la ruta del directorio donde se encuentra el script
    config_path = os.path.join(script_dir, 'config.ini') # Construir la ruta completa al archivo config.ini  
    config.read(config_path) # Leer el archivo de configuración"""

    



    # Acceder a los parámetros
    # Cliente
    cliente = config['Account']['client']
    # Ruta de la DB
    backup_path = config['Backup']['path']
    # Opción: Asegurar que las barras estén correctamente escapadas
    backup_path = backup_path.replace("\\", "/")  # o usa "\\\\" para barras dobles

    email_origin = config['Email']['email_origin']
    email_destination = config['Email']['email_destination']
    email_cc = config['Email']['email_cc'] if config['Email']['email_cc'] else None
    email_cco = config['Email']['email_cco'] if config['Email']['email_cco'] else None

    # Obtener la variable de entorno para la clave del correo
    email_password = os.getenv(config['Email']['env_variable_key'])

    # Obtiene el nombre del archivo JSON que se genera para guardar log del backup
    json_file_path = config['Json']['path']

    return cliente, backup_path, email_origin, email_destination, email_cc, email_cco, email_password, json_file_path



def enviar_correo(email_origin, email_password, email_destino, asunto, cuerpo):
    # Crear el mensaje de correo
    msg = MIMEText(cuerpo)
    msg['Subject'] = asunto
    
    msg['From'] = email_origin
    msg['To'] = email_destino

    # Enviar el correo
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(email_origin, email_password)
            server.sendmail(email_origin, [email_destino], msg.as_string())
        print("Correo enviado con éxito.")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")



def verificar_backup(cliente, ruta_backup, email_origin, email_password, email_destino ,json_file_path):
    # Verificar si el archivo de backup existe
    if os.path.exists(ruta_backup):
        # Obtener el tamaño en GB y la fecha de creación/modificación
        tamano_actual = os.path.getsize(ruta_backup) / (1024 * 1024 * 1024)
        timestamp_actual = os.path.getmtime(ruta_backup)
        fecha_actual = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp_actual))
        codigo_backup = "backup_ok" # inicializador de código

        # Leer el archivo JSON o crear uno nuevo si no existe
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as file:
                registros_backup = json.load(file)
        else:
            registros_backup = []

        # Verificar el último registro (si existe)
        if registros_backup:
            ultimo_registro = registros_backup[-1]  # tomo el último backup registrado
            tamano_anterior = ultimo_registro['tamano_gb']
            fecha_anterior = ultimo_registro['fecha']
            codigo_backup = ultimo_registro['codigo_backup']

            # Comparar tamaño y fecha del backup actual con el anterior
            if tamano_actual > tamano_anterior and fecha_actual >= fecha_anterior:
                codigo_backup = "ok"
            else:
                # Hay ERROR
                # Inicializamos el código de error
                codigo_backup = "Error"
                # Detectamos si hay un problema con el tamaño
                if tamano_actual <= tamano_anterior:
                    codigo_backup += " - Size <= "
    
                # Detectamos si hay un problema con la fecha
                if fecha_actual < fecha_anterior:
                    codigo_backup += " - Fecha <= "

            # Preparar el asunto y cuerpo del correo
            asunto = f"ERROR al verificar Backup en {cliente}"
            
            # Definimos un ancho fijo para cada columna
            col_ancho_1 = 20
            col_ancho_2 = 35
            col_ancho_3 = 35
            # Generamos el cuerpo del mensaje con las columnas alineadas
            cuerpo = (
                f"El backup actual no cumple con los criterios de verificación:\n\n"
                f"{'Descripción'.ljust(col_ancho_1)}{'Valor Actual'.ljust(col_ancho_2)}{'Valor Anterior'.ljust(col_ancho_3)}\n"
                f"{'-' * (col_ancho_1 + col_ancho_2 + col_ancho_3)}\n"
                f"{'Tamaño'.ljust(col_ancho_1)}{f'{tamano_actual:.2f} GB'.ljust(col_ancho_2)}{f'{tamano_anterior:.2f} GB'.ljust(col_ancho_3)}\n"
                f"{'Fecha'.ljust(col_ancho_1)}{f'{fecha_actual}'.ljust(col_ancho_2)}{f'{fecha_anterior}'.ljust(col_ancho_3)}\n"
                f"{'-' * (col_ancho_1 + col_ancho_2 + col_ancho_3)}\n"
                f"Resultado: {codigo_backup}\n"
            )
          
            # Llamada para enviar el correo de advertencia
            enviar_correo(email_origin, email_password, email_destino, asunto, cuerpo)


        # Actualizar o añadir el registro actual en el archivo JSON
        nuevo_registro = {"tamano_gb": tamano_actual, "fecha": fecha_actual, "codigo_backup":codigo_backup }
        registros_backup.append(nuevo_registro)

        # Guardar el nuevo registro en el archivo JSON
        with open(json_file_path, 'w') as file:
            json.dump(registros_backup, file, indent=4)

        return {"existe": True, "tamano_gb": tamano_actual, "fecha": fecha_actual, "codigo_backup":codigo_backup}
    else:
        return {"existe": False}
    


def main():

    # Llamar a la función configuraciones para obtener todas las configuraciones necesarias
    cliente, backup_path, email_origin, email_destination, email_cc, email_cco, email_password, json_file_path = configuraciones()

    # Pasar los valores a la función verificar_backup
    verificar_backup(cliente, backup_path, email_origin, email_password, email_destination, json_file_path)


if __name__ == "__main__":
    main()