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
    plan_name = plan['name']
    url = key['access_url']
    
    data_text = "📊 ILIMITADO" if plan['data_limit_mb'] is None else f"📊 {plan['data_limit_mb']} MB"
    
    message = f"""🚀 *VPN PREMIUM - Acceso Configurado*

👤 *Cliente:* {name}
📋 *Plan:* {plan_name}
{data_text}
⏳ *Duración:* {plan['days']} días
💰 *Precio:* {plan['price']} CUP

🔗 *Tu clave de acceso:*
