# Configuración básica - EDITA ESTOS VALORES

# OBTÉN ESTO DE TU OUTLINE MANAGER:
# 1. Abre Outline Manager en tu PC
# 2. Ve a Settings (⚙️) → API Access
# 3. Copia la URL que termina en /xxxxxxxxxx
OUTLINE_API_URL = "https://152.206.139.47:57281/-6xTop0pkqOZhfNXpLMfxg"  # ← CAMBIA ESTO

# Configuración de la app
SECRET_KEY = "Outline2026*"
DATABASE_PATH = "/app/vpn_database.db"  # En Railway usará /app/

# Planes de VPN (precios en CUP - pesos cubanos)
PLANS = {
    "test": {
        "name": "Plan Test",
        "data_limit_mb": 1,        # 1 MB
        "days": 1,                  # 1 día
        "price": 0,
        "description": "1MB por 1 día - Prueba gratuita"
    },
    "semanal": {
        "name": "Plan Semanal",
        "data_limit_mb": None,      # None = Ilimitado
        "days": 7,                  # 7 días
        "price": 400,
        "description": "Consumo ILIMITADO por 7 días"
    },
    "mensual_30gb": {
        "name": "Plan 30GB",
        "data_limit_mb": 30720,     # 30 GB
        "days": 30,
        "price": 700,
        "description": "30GB por 30 días"
    },
    "mensual_ilimitado": {
        "name": "Plan Ilimitado",
        "data_limit_mb": None,      # Ilimitado
        "days": 30,
        "price": 1400,
        "description": "Consumo ILIMITADO por 30 días"
    }
}

# Estados de pago
PAYMENT_STATUS = {
    "pending": "⏳ Pendiente",
    "paid": "✅ Pagado",
    "expired": "❌ Expirado",
    "cancelled": "🚫 Cancelado"
}
