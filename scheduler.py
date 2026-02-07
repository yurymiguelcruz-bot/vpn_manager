import schedule
import time
import threading
from datetime import datetime
from database import db
from outline_api import outline

class Scheduler:
    def __init__(self, outline_api):
        self.outline = outline_api
        self.running = False
    
    def check_expired(self):
        print(f"[{datetime.now()}] Verificando claves expiradas...")
        expired = db.get_expired_keys()
        
        for key in expired:
            try:
                # Limitar a 1MB en Outline
                self.outline.set_data_limit(key['key_id'], 1048576)
                db.mark_expired_limit_applied(key['key_id'])
                db.update_key(key['key_id'], {'is_active': 0, 'payment_status': 'expired'})
                print(f"✓ Expirada: {key['name']}")
            except Exception as e:
                print(f"✗ Error con {key['key_id']}: {e}")
    
    def sync_usage(self):
        try:
            metrics = self.outline.get_metrics()
            if metrics and 'bytesTransferredByUserId' in metrics:
                for key_id, bytes_used in metrics['bytesTransferredByUserId'].items():
                    # Guardar en historial
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO usage_history (key_id, bytes_transferred)
                        VALUES (?, ?)
                    ''', (key_id, bytes_used))
                    conn.commit()
                    conn.close()
        except Exception as e:
            print(f"Error sincronizando uso: {e}")
    
    def run(self):
        while self.running:
            schedule.run_pending()
            time.sleep(60)
    
    def start(self):
        if self.running:
            return
        
        self.running = True
        
        # Programar tareas
        schedule.every(5).minutes.do(self.check_expired)
        schedule.every(10).minutes.do(self.sync_usage)
        
        # Ejecutar inmediatamente
        self.check_expired()
        
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()
        print("✓ Scheduler iniciado")
    
    def stop(self):
        self.running = False
