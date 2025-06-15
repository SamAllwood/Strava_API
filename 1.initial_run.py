import requests
import json
from dotenv import load_dotenv
import os

# Ensure .env file exists in the script directory
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if not os.path.exists(env_path):
    with open(env_path, "w") as f:
        f.write("")  # Create an empty .env file if it doesn't exist


load_dotenv()  # Loads variables from .env into environment

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
AUTHORIZATION_CODE = os.getenv('AUTHORIZATION_CODE')
print(f"CLIENT_ID: {CLIENT_ID}")
print(f"CLIENT_SECRET: {CLIENT_SECRET}")
print(f"AUTHORIZATION_CODE: {AUTHORIZATION_CODE}")

def save_tokens_to_env(access_token, refresh_token, env_path=None):
    if env_path is None:
        # Always use the .env file in the same directory as this script
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    print(f"Saving tokens to {env_path}")
    print(f"Access token: {access_token}")
    print(f"Refresh token: {refresh_token}")
    # Read existing lines
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
    else:
        lines = []

    # Prepare new lines
    new_lines = []
    found_access = found_refresh = False
    for line in lines:
        if line.startswith("STRAVA_ACCESS_TOKEN="):
            new_lines.append(f"STRAVA_ACCESS_TOKEN={access_token}\n")
            found_access = True
        elif line.startswith("STRAVA_REFRESH_TOKEN="):
            new_lines.append(f"STRAVA_REFRESH_TOKEN={refresh_token}\n")
            found_refresh = True
        else:
            new_lines.append(line)
    if not found_access:
        new_lines.append(f"STRAVA_ACCESS_TOKEN={access_token}\n")
    if not found_refresh:
        new_lines.append(f"STRAVA_REFRESH_TOKEN={refresh_token}\n")

    # Write back
    with open(env_path, "w") as f:
        f.writelines(new_lines)
        
def exchange_code_for_tokens(client_id, client_secret, code):
    response = requests.post(
        url='https://www.strava.com/oauth/token',
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'grant_type': 'authorization_code'
        }
    )
    response_data = response.json()
    print(json.dumps(response_data, indent=4))
    # Print the accepted scope
    if 'scope' in response_data:
        print(f"\nAccepted scope: {response_data['scope']}")
    else:
        print("\nNo scope returned in response.")
    if 'refresh_token' in response_data:
        save_tokens_to_env(response_data['access_token'], response_data['refresh_token'])
        print("\nYour refresh_token and access_tokens are saved for future use!")
    else:
        print("\nError exchanging code for tokens.")

if __name__ == '__main__':
    exchange_code_for_tokens(CLIENT_ID, CLIENT_SECRET, AUTHORIZATION_CODE)