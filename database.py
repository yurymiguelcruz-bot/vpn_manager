import sqlite3
import json
from datetime import datetime, timedelta
from config import DATABASE_PATH, PLANS

class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabla de claves VPN
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vpn_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_id TEXT UNIQUE,
                access_url TEXT,
                name TEXT,
                client_name TEXT,
                client_phone TEXT,
                client_telegram TEXT,
                plan_type TEXT,
                created_at TIMESTAMP,
                expires_at TIMESTAMP,
                data_limit_bytes INTEGER,
                payment_status TEXT DEFAULT 'pending',
                notes TEXT,
                is_active BOOLEAN DEFAULT 1,
                expired_limit_applied BOOLEAN DEFAULT 0,
                created_by TEXT DEFAULT 'admin'
            )
        ''')
        
        # Tabla de historial
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_id TEXT,
                bytes_transferred INTEGER,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de usuarios (para login)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'admin',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Crear usuario admin por defecto (contraseña: admin123)
        import bcrypt
        cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
        if cursor.fetchone()[0] == 0:
            password_hash = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()
            cursor.execute('''
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, ?)
            ''', ('admin', password_hash, 'admin'))
            print("Usuario admin creado: admin / admin123")
        
        # Tabla de auditoría
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                target TEXT,
                user TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_key(self, key_data):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO vpn_keys (
                key_id, access_url, name, client_name, client_phone,
                client_telegram, plan_type, created_at, expires_at,
                data_limit_bytes, payment_status, notes, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            key_data['key_id'], key_data['access_url'], key_data.get('name', ''),
            key_data.get('client_name', ''), key_data.get('client_phone', ''),
            key_data.get('client_telegram', ''), key_data['plan_type'],
            key_data['created_at'], key_data['expires_at'],
            key_data.get('data_limit_bytes'), key_data.get('payment_status', 'pending'),
            key_data.get('notes', ''), key_data.get('created_by', 'admin')
        ))
        
        conn.commit()
        conn.close()
        return True
    
    def get_all_keys(self):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM vpn_keys ORDER BY created_at DESC')
        keys = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return keys
    
    def get_key_by_id(self, key_id):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM vpn_keys WHERE key_id = ?', (key_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def update_key(self, key_id, updates):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        fields = []
        values = []
        for key, value in updates.items():
            fields.append(f"{key} = ?")
            values.append(value)
        values.append(key_id)
        
        query = f"UPDATE vpn_keys SET {', '.join(fields)} WHERE key_id = ?"
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        return True
    
    def delete_key(self, key_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM vpn_keys WHERE key_id = ?', (key_id,))
        conn.commit()
        conn.close()
        return True
    
    def get_expired_keys(self):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            SELECT * FROM vpn_keys 
            WHERE expires_at < ? AND is_active = 1 AND expired_limit_applied = 0
        ''', (now,))
        keys = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return keys
    
    def mark_expired_limit_applied(self, key_id):
        return self.update_key(key_id, {
            'expired_limit_applied': 1,
            'data_limit_bytes': 1048576  # 1MB
        })
    
    def get_user(self, username):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def log_audit(self, action, target, user):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO audit_log (action, target, user) VALUES (?, ?, ?)
        ''', (action, target, user))
        conn.commit()
        conn.close()

# Instancia global
db = Database()
