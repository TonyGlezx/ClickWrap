class TokenManager:
    AUTHORIZATION_URL_TEMPLATE = "https://app.clickup.com/api?client_id={client_id}&redirect_uri={redirect_uri}"
    TOKEN_URL = "https://api.clickup.com/api/v2/oauth/token"
    REDIRECT_URI = "localhost"

    def __init__(self, client_id, client_secret):
        self.CLIENT_ID = client_id
        self.CLIENT_SECRET = client_secret

    def get_token(self):
        token = self.get_token_from_storage()
        if not token:
            token = self.request_new_token()
        return token

    def get_token_from_storage(self):
        try:
            with open('token.txt', 'r') as file:
                return file.read().strip()
        except FileNotFoundError:
            return None

    def save_token_to_storage(self, token):
        with open('token.txt', 'w') as file:
            file.write(token)

    def request_new_token(self):
        auth_url = self.AUTHORIZATION_URL_TEMPLATE.format(client_id=self.CLIENT_ID, redirect_uri=self.REDIRECT_URI)
        print(f'Please go to {auth_url} and authorize access.')
        callback_url = input('Enter the full callback URL: ')
        code = callback_url.split("code=")[1]
        query = {
            "client_id": self.CLIENT_ID,
            "client_secret": self.CLIENT_SECRET,
            "code": code,
            "redirect_uri": self.REDIRECT_URI
        }
        retries = 3
        backoff_factor = 1.5
        for attempt in range(retries):
            try:
                response = requests.post(self.TOKEN_URL, params=query, timeout=60)
                response.raise_for_status()
                token_data = response.json()
                if 'access_token' in token_data:
                    self.save_token_to_storage(token_data['access_token'])
                    return token_data['access_token']
                else:
                    print("Error retrieving access token.")
                    return None
            except Exception as e:
                if attempt < retries - 1:
                    sleep_time = backoff_factor * (2 ** attempt)
                    time.sleep(sleep_time)
                    continue
                else:
                    print(f"Error connecting to the token endpoint: {e}")
                    return None