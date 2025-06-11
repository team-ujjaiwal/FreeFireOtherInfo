from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii
from flask import Flask, request, jsonify
import time
import back_pb2
import basics_pb2 as basics__pb2  # Using the back_pb2 protobuf definitions
from secret import key, iv

app = Flask(__name__)

def create_complete_response(user_id):
    """Create a complete response using back_pb2 protobuf definitions"""
    resp = back_pb2.CSGetBackpackRes()
    
    # Wallet information
    resp.wallet.coins = 5000 + (user_id % 5000)
    resp.wallet.gems = 100 + (user_id % 50)
    resp.wallet.gop_gems = 50 + (user_id % 20)
    resp.wallet.total_topup = 10000 + (user_id % 10000)
    resp.wallet.last_topup_time = int(time.time()) - (3600 * 24 * (user_id % 30))
    
    # Selected items
    resp.selected_items.avatar = 1000 + (user_id % 10)
    resp.selected_items.weapon = 2000 + (user_id % 20)
    resp.selected_items.pet_id = 3000 + (user_id % 5)
    
    # Add sample items
    for i in range(1, 4):
        item = resp.items.add()
        item.id = 10000 + (user_id % 1000) + i
        item.cnt = 1 + (user_id % 5)
        item.item_type = back_pb2.ItemType.Value(f'ItemType_{["AVATAR", "WEAPON", "PET"][i%3]}')
        item.item_status = back_pb2.ItemStatus.PERMANENT if user_id % 2 else back_pb2.ItemStatus.INEXPIRE
    
    # Add weapon skins
    skin = resp.weapon_skin_stat.add()
    skin.weapon_skin_id = 5000 + (user_id % 100)
    skin.weapon_name = f"Weapon_{user_id % 10}"
    
    # Add coins out game info
    resp.coins_out_game.coins_weekly = 1000 + (user_id % 500)
    resp.coins_out_game.next_refresh_time = int(time.time()) + 86400
    
    return resp

def protobuf_to_dict(pb_message):
    """Convert protobuf message to dictionary"""
    data = {
        "wallet": {
            "coins": pb_message.wallet.coins,
            "gems": pb_message.wallet.gems,
            "gop_gems": pb_message.wallet.gop_gems,
            "total_topup": pb_message.wallet.total_topup,
            "last_topup_time": pb_message.wallet.last_topup_time
        },
        "selected_items": {
            "avatar": pb_message.selected_items.avatar,
            "weapon": pb_message.selected_items.weapon,
            "pet_id": pb_message.selected_items.pet_id
        },
        "coins_out_game": {
            "coins_weekly": pb_message.coins_out_game.coins_weekly,
            "next_refresh_time": pb_message.coins_out_game.next_refresh_time
        },
        "items": [],
        "weapon_skins": []
    }
    
    for item in pb_message.items:
        data["items"].append({
            "id": item.id,
            "count": item.cnt,
            "type": back_pb2.ItemType.Name(item.item_type),
            "status": back_pb2.ItemStatus.Name(item.item_status)
        })
    
    for skin in pb_message.weapon_skin_stat:
        data["weapon_skins"].append({
            "skin_id": skin.weapon_skin_id,
            "name": skin.weapon_name
        })
    
    return data

def encrypt_protobuf(pb_message):
    """Encrypt the protobuf message using AES-CBC"""
    serialized = pb_message.SerializeToString()
    key_bytes = key.encode()[:16]
    iv_bytes = iv.encode()[:16]
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
    padded_data = pad(serialized, AES.block_size)
    encrypted_data = cipher.encrypt(padded_data)
    return binascii.hexlify(encrypted_data).decode()

@app.route('/player-data', methods=['GET'])
def player_data():
    """Endpoint returning player data in both JSON and encrypted protobuf formats"""
    uid = request.args.get('uid')
    region = request.args.get('region')

    if not uid:
        return jsonify({"error": "Missing 'uid' parameter"}), 400

    try:
        user_id = int(uid)
    except ValueError:
        return jsonify({"error": "Invalid UID format"}), 400

    # Create protobuf response
    pb_response = create_complete_response(user_id)
    
    # Prepare response
    response_data = {
        "json_data": protobuf_to_dict(pb_response),
        "encrypted_data": encrypt_protobuf(pb_response),
        "encryption_info": {
            "algorithm": "AES-CBC",
            "key_size": 128,
            "padding": "PKCS7"
        },
        "timestamp": int(time.time()),
        "credit": "@Ujjaiwal"
    }
    
    # Add region if provided
    if region:
        response_data['request_region'] = region.upper()

    return jsonify(response_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)