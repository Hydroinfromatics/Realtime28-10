import requests

credentials = {
    "username": "Kamlesh123",
    "password": "1234567"
}

headers = {
    "Content-Type": "application/json"
}

def generate_token(api_url):
    try:
        response = requests.post(f"{api_url}/get_token", json=credentials, headers=headers)
        if response.status_code == 200:
            return response.json().get("token")
        print(f"Failed to generate token: {response.status_code}")
        return None
    except Exception as e:
        print(f"Error generating token: {e}")
        return None

def fetch_data_from_api(api_url):
    try:
        token = generate_token(api_url)
        if not token:
            return None
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{api_url}/nallampatti_data", headers=headers)
        
        if response.status_code == 200:
            return response.json()
        print(f"Failed to fetch data: {response.status_code}")
        return None
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None