from datetime import datetime, timedelta
from urllib.parse import quote
from config import PLANS

def calculate_plan_dates(plan_type):
    plan = PLANS.get(plan_type)
    if not plan:
        return None, None
    created = datetime.now()
    expires = created + timedelta(days=plan['days'])
    return created.isoformat(), expires.isoformat()

def get_data_limit(plan_type):
    plan = PLANS.get(plan_type)
    if not plan or plan['data_limit_mb'] is None:
        return None
    return plan['data_limit_mb'] * 1024 * 1024

def format_bytes(bytes_val):
    if bytes_val is None:
        return "Ilimitado"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} TB"

def generate_share_message(key, plan):
    name = key.get('client_name', 'Cliente')
    url = key['access_url']
    expires = key['expires_at'][:10]
    
    if plan['data_limit_mb'] is None:
        data_text = "ILIMITADO"
    else:
        data_text = str(plan['data_limit_mb']) + " MB"
    
    message = "VPN PREMIUM - Acceso Configurado\n\n"
    message += "Cliente: " + name + "\n"
    message += "Plan: " + plan['name'] + "\n"
    message += "Datos: " + data_text + "\n"
    message += "Duracion: " + str(plan['days']) + " dias\n"
    message += "Precio: " + str(plan['price']) + " CUP\n\n"
    message += "Tu clave de acceso:\n"
    message += url + "\n\n"
    message += "Valido hasta: " + expires + "\n"
    message += "Soporte: [Tu contacto]"
    
    return message
