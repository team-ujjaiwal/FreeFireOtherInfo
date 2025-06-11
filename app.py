from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii
from flask import Flask, request, jsonify
import time
import back_pb2  # Now works with basics_pb2.py in same directory
from secret import key, iv

app = Flask(__name__)

def create_player_data(user_id):
    """Creates player data using back_pb2 protobuf structure"""
    # Initialize the main response object
    response = back_pb2.CSGetBackpackRes()
    
    # 1. Wallet Information
    wallet = response.wallet
    wallet.coins = 5000 + (user_id % 5000)
    wallet.gems = 100 + (user_id % 50)
    wallet.gop_gems = 50 + (user_id % 20)
    wallet.total_topup = 10000 + (user_id % 10000)
    wallet.last_topup_time = int(time.time()) - (3600 * 24 * (user_id % 30))
    
    # 2. Selected Items
    selected = response.selected_items
    selected.avatar = 1000 + (user_id % 10)
    selected.weapon = 2000 + (user_id % 20)
    selected.pet_id = 3000 + (user_id % 5)
    
    # 3. Inventory Items
    for i in range(3):
        item = response.items.add()
        item.id = 10000 + (user_id % 1000) + i
        item.cnt = 1 + (user_id % 5)
        item.item_type = back_pb2.ItemType.Value(f'ItemType_{["AVATAR", "WEAPON", "PET"][i%3]}')
        item.item_status = back_pb2.ItemStatus.PERMANENT if user_id % 2 else back_pb2.ItemStatus.INEXPIRE
    
    # 4. Weapon Skins
    skin = response.weapon_skin_stat.add()
    skin.weapon_skin_id = 5000 + (user_id % 100)
    skin.weapon_name = f"Skin_{user_id % 10}"
    skin.rights.add(key=1, value=100)  # Example PUint32KeyVal usage
    
    # 5. Coins Out Game
    coins = response.coins_out_game
    coins.coins_weekly = 1000 + (user_id % 500)
    coins.next_refresh_time = int(time.time()) + 86400
    
    return response

def protobuf_to_dict(pb_data):
    """Converts protobuf to Python dict"""
    return {
        "wallet": {
            "coins": pb_data.wallet.coins,
            "gems": pb_data.wallet.gems,
            "gop_gems": pb_data.wallet.gop_gems,
            "total_topup": pb_data.wallet.total_topup,
            "last_topup_time": pb_data.wallet.last_topup_time
        },
        "selected_items": {
            "avatar": pb_data.selected_items.avatar,
            "weapon": pb_data.selected_items.weapon,
            "pet_id": pb_data.selected_items.pet_id
        },
        "inventory": [
            {
                "id": item.id,
                "count": item.cnt,
                "type": back_pb2.ItemType.Name(item.item_type),
                "status": back_pb2.ItemStatus.Name(item.item_status)
            } for item in pb_data.items
        ],
        "weapon_skins": [
            {
                "id": skin.weapon_skin_id,
                "name": skin.weapon_name,
                "rights": {r.key: r.value for r in skin.rights}
            } for skin in pb_data.weapon_skin_stat
        ],
        "weekly_coins": {
            "amount": pb_data.coins_out_game.coins_weekly,
            "refresh_time": pb_data.coins_out_game.next_refresh_time
        }
    }

def encrypt_data(protobuf_message):
    """Encrypts protobuf with AES-CBC"""
    serialized = protobuf_message.SerializeToString()
    cipher = AES.new(key.encode()[:16], AES.MODE_CBC, iv.encode()[:16])
    return binascii.hexlify(cipher.encrypt(pad(serialized, AES.block_size)).decode()

@app.route('/player-data', methods=['GET'])
def get_player_data():
    """Endpoint serving both JSON and encrypted protobuf data"""
    try:
        user_id = int(request.args['uid'])
    except (KeyError, ValueError):
        return jsonify({"error": "Valid 'uid' parameter required"}), 400
    
    # Generate data
    pb_response = create_player_data(user_id)
    
    # Build response
    return jsonify({
        "json_data": protobuf_to_dict(pb_response),
        "encrypted_data": encrypt_data(pb_response),
        "metadata": {
            "timestamp": int(time.time()),
            "api_version": "1.0",
            "credit": "@Ujjaiwal"
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)