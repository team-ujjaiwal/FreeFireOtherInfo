from flask import Flask, request, jsonify
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii
import requests
import back_pb2  # Importing back_pb2
import basics_pb2  # Importing basics_pb2 (required by back_pb2)
from secret import key, iv  # Make sure to have these in your secret.py

app = Flask(__name__)

def encrypt_aes(hex_data, key, iv):
    key = key.encode()[:16]
    iv = iv.encode()[:16]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_data = pad(bytes.fromhex(hex_data), AES.block_size)
    encrypted_data = cipher.encrypt(padded_data)
    return binascii.hexlify(encrypted_data).decode()

def get_credentials(region):
    region = region.upper()
    if region == "IND":
        return "3942040791", "EDD92B8948F4453F544C9432DFB4996D02B4054379A0EE083D8459737C50800B"
    elif region in ["NA", "BR", "SAC", "US"]:
        return "uid", "password"
    else:
        return "uid", "password"

def get_jwt_token(region):
    uid, password = get_credentials(region)
    jwt_url = f"https://jwt-aditya.vercel.app/token?uid={uid}&password={password}"
    response = requests.get(jwt_url)
    if response.status_code != 200:
        return None
    return response.json()

@app.route('/player-info', methods=['GET'])
def main():
    uid = request.args.get('uid')
    region = request.args.get('region')

    if not uid or not region:
        return jsonify({"error": "Missing 'uid' or 'region' query parameter"}), 400

    try:
        saturn_ = int(uid)
    except ValueError:
        return jsonify({"error": "Invalid UID"}), 400

    jwt_info = get_jwt_token(region)
    if not jwt_info or 'token' not in jwt_info:
        return jsonify({"error": "Failed to fetch JWT token"}), 500

    api = jwt_info['serverUrl']
    token = jwt_info['token']

    # Example usage of back_pb2
    backpack_res = back_pb2.CSGetBackpackRes()
    backpack_res.wallet.coins = 1000  # Example value
    
    # Example usage of basics_pb2
    selected_items = basics_pb2.SelectedItems()
    selected_items.avatar_id = 123  # Example value

    # Convert protobuf to bytes
    protobuf_data = backpack_res.SerializeToString()
    hex_data = binascii.hexlify(protobuf_data).decode()
    encrypted_hex = encrypt_aes(hex_data, key, iv)

    headers = {
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)',
        'Connection': 'Keep-Alive',
        'Expect': '100-continue',
        'Authorization': f'Bearer {token}',
        'X-Unity-Version': '2018.4.11f1',
        'X-GA': 'v1 1',
        'ReleaseVersion': 'OB49',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    try:
        response = requests.post(f"{api}/GetPlayerPersonalShow", headers=headers, data=bytes.fromhex(encrypted_hex))
        response.raise_for_status()
    except requests.RequestException as e:
        return jsonify({"error": f"Failed to contact game server: {str(e)}"}), 502

    # Process response (example)
    try:
        # Here you would parse the response using your protobuf definitions
        # For demonstration, we'll just return a success message
        return jsonify({
            "status": "success",
            "message": "Request processed successfully",
            "sample_data": {
                "coins": backpack_res.wallet.coins,
                "avatar_id": selected_items.avatar_id
            },
            "credit": "@Ujjaiwal"
        })
    except Exception as e:
        return jsonify({"error": f"Failed to parse response: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)