from flask import Flask, render_template, request, jsonify, redirect, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta
import bcrypt
import jwt
import os

# Configuración
from config import OUTLINE_API_URL, PLANS, PAYMENT_STATUS, SECRET_KEY
from database import db
from outline_api import OutlineManager
from scheduler import Scheduler
from utils import *

# Inicializar
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Rate limiting (protección contra ataques)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour", "20 per minute"]
)

# Outline API
outline = OutlineManager(OUTLINE_API_URL)
scheduler = Scheduler(outline)

# ========== AUTENTICACIÓN SIMPLE ==========

def generate_token(username):
    return jwt.encode(
        {'username': username, 'exp': datetime.utcnow() + timedelta(hours=24)},
        SECRET_KEY,
        algorithm='HS256'
    )

def verify_token():
    token = request.cookies.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return None
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except:
        return None

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not verify_token():
            if request.is_json:
                return jsonify({'error': 'No autorizado'}), 401
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

# ========== RUTAS ==========

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.get_json() or request.form
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    user = db.get_user(username)
    if not user or not bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
        return jsonify({'success': False, 'error': 'Credenciales inválidas'}), 401
    
    # Generar token
    token = generate_token(username)
    
    response = make_response(jsonify({'success': True}))
    response.set_cookie('token', token, httponly=True, secure=True, samesite='Lax', max_age=86400)
    return response

@app.route('/logout', methods=['POST'])
def logout():
    response = make_response(jsonify({'success': True}))
    response.delete_cookie('token')
    return response

@app.route('/')
@login_required
def dashboard():
    keys = db.get_all_keys()[:10]
    stats = {
        'total': len(db.get_all_keys()),
        'active': sum(1 for k in keys if k['is_active']),
        'pending': sum(1 for k in keys if k['payment_status'] == 'pending')
    }
    
    for key in keys:
        key['plan_info'] = PLANS.get(key['plan_type'], {})
        key['is_expired'] = datetime.fromisoformat(key['expires_at']) < datetime.now()
    
    return render_template('dashboard.html', keys=keys, stats=stats, plans=PLANS)

@app.route('/keys')
@login_required
def keys_page():
    keys = db.get_all_keys()
    for key in keys:
        key['plan_info'] = PLANS.get(key['plan_type'], {})
        # Obtener uso actual
        try:
            metrics = outline.get_metrics()
            key['usage'] = metrics.get('bytesTransferredByUserId', {}).get(key['key_id'], 0) if metrics else 0
        except:
            key['usage'] = 0
    
    return render_template('keys.html', keys=keys, plans=PLANS, payment_statuses=PAYMENT_STATUS)

# ========== API ==========

@app.route('/api/create-key', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def create_key():
    data = request.json
    plan_type = data.get('plan_type', 'test')
    plan = PLANS.get(plan_type)
    
    if not plan:
        return jsonify({'success': False, 'error': 'Plan inválido'}), 400
    
    # Crear en Outline
    created_at, expires_at = calculate_plan_dates(plan_type)
    data_limit = get_data_limit(plan_type)
    
    outline_key = outline.create_key(data.get('name'), data_limit)
    if not outline_key:
        return jsonify({'success': False, 'error': 'Error al crear en Outline'}), 500
    
    # Guardar en DB
    key_data = {
        'key_id': outline_key['id'],
        'access_url': outline_key['accessUrl'],
        'name': data.get('name', ''),
        'client_name': data.get('client_name', ''),
        'client_phone': data.get('client_phone', ''),
        'client_telegram': data.get('client_telegram', ''),
        'plan_type': plan_type,
        'created_at': created_at,
        'expires_at': expires_at,
        'data_limit_bytes': data_limit,
        'payment_status': data.get('payment_status', 'pending'),
        'notes': data.get('notes', '')
    }
    
    db.create_key(key_data)
    db.log_audit('CREATE_KEY', outline_key['id'], verify_token()['username'])
    
    return jsonify({'success': True, 'key': key_data})

@app.route('/api/delete-key/<key_id>', methods=['DELETE'])
@login_required
def delete_key(key_id):
    outline.delete_key(key_id)
    db.delete_key(key_id)
    db.log_audit('DELETE_KEY', key_id, verify_token()['username'])
    return jsonify({'success': True})

@app.route('/api/share-key/<key_id>')
@login_required
def share_key(key_id):
    platform = request.args.get('platform', 'whatsapp')
    key = db.get_key_by_id(key_id)
    if not key:
        return jsonify({'error': 'No encontrado'}), 404
    
    plan = PLANS.get(key['plan_type'], {})
    message = generate_share_message(key, plan)
    
    if platform == 'whatsapp' and key.get('client_phone'):
        link = get_whatsapp_link(key['client_phone'], message)
    elif platform == 'telegram' and key.get('client_telegram'):
        link = get_telegram_link(key['client_telegram'], message)
    else:
        return jsonify({'success': True, 'message': message, 'copy_only': True})
    
    return jsonify({'success': True, 'link': link, 'message': message})

@app.route('/api/sync-keys', methods=['POST'])
@login_required
def sync_keys():
    outline_keys = outline.get_all_keys()
    local_keys = db.get_all_keys()
    local_ids = {k['key_id'] for k in local_keys}
    
    added = 0
    for ok in outline_keys:
        if ok['id'] not in local_ids:
            db.create_key({
                'key_id': ok['id'],
                'access_url': ok.get('accessUrl', ''),
                'name': ok.get('name', 'Sin nombre'),
                'plan_type': 'test',
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(days=1)).isoformat(),
                'payment_status': 'pending',
                'notes': 'Importado de Outline'
            })
            added += 1
    
    return jsonify({'success': True, 'added': added})

# ========== INICIO ==========

if __name__ == '__main__':
    scheduler.start()
    
    # Puerto para Railway (usa el que Railway asigne o 5000 por defecto)
    port = int(os.environ.get('PORT', 5000))
    
    # En Railway usar 0.0.0.0, en local puedes usar 127.0.0.1
    host = '0.0.0.0'
    
    print(f"🚀 Servidor iniciando en http://{host}:{port}")
    app.run(host=host, port=port, debug=False)
# Fix
