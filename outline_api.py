import requests
import urllib3

# Desactivar warnings de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OutlineManager:
    def __init__(self, api_url):
        self.api_url = api_url.rstrip('/')
    
    def _request(self, method, endpoint, data=None):
        url = f"{self.api_url}/{endpoint}"
        try:
            if method == 'GET':
                response = requests.get(url, verify=False, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, verify=False, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, verify=False, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, verify=False, timeout=10)
            
            response.raise_for_status()
            return response.json() if response.text else {}
        except Exception as e:
            print(f"Error Outline API: {e}")
            return None
    
    def get_all_keys(self):
        result = self._request('GET', 'access-keys')
        return result.get('accessKeys', []) if result else []
    
    def create_key(self, name=None, data_limit_bytes=None):
        data = {}
        if name:
            data['name'] = name
        if data_limit_bytes:
            data['dataLimit'] = {'bytes': data_limit_bytes}
        return self._request('POST', 'access-keys', data)
    
    def delete_key(self, key_id):
        return self._request('DELETE', f'access-keys/{key_id}')
    
    def rename_key(self, key_id, new_name):
        return self._request('PUT', f'access-keys/{key_id}/name', {'name': new_name})
    
    def set_data_limit(self, key_id, bytes_limit):
        return self._request('PUT', f'access-keys/{key_id}/data-limit', {
            'limit': {'bytes': bytes_limit}
        })
    
    def get_metrics(self):
        return self._request('GET', 'metrics/transfer')
