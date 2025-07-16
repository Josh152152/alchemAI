from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from app.ai_agent import generate_job_summary
from app.sheets import store_to_gsheet
import json
import requests

# Firebase Admin imports
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize Firebase Admin SDK with your service account key file
cred = credentials.Certificate("firebase-credentials.json")
firebase_admin.initialize_app(cred)

@app.route('/', methods=['GET'])
def home():
    return render_template('agent_form.html')

@app.route('/generate', methods=['POST'])
def generate():
    message_history = None

    data = request.get_json(silent=True)
    if data:
        if "history" in data:
            message_history = data["history"]
        elif "job_info" in data:
            # Wrap single job_info string into chat format if needed
            if isinstance(data["job_info"], str):
                message_history = [{"role": "user", "content": data["job_info"]}]
            else:
                message_history = data["job_info"]
    else:
        job_info = request.form.get("job_info")
        if job_info:
            message_history = [{"role": "user", "content": job_info}]

    if not message_history:
        return jsonify({"error": "No job_info or history provided"}), 400

    print("message_history received:", message_history)

    ai_reply = generate_job_summary(message_history)

    stored = False
    try:
        summary_json = json.loads(ai_reply)
        store_to_gsheet(summary_json)
        stored = True
    except Exception as e:
        print("JSON decode or GSheet store failed:", str(e))
        summary_json = None

    print("AI reply:", ai_reply)
    print("Summary JSON:", summary_json)
    print("Saved to GSheet:", stored)

    return jsonify({
        "reply": ai_reply,
        "saved": stored,
        "summary": summary_json
    })

@app.route('/verify-turnstile', methods=['POST'])
def verify_turnstile():
    data = request.get_json()
    token = data.get('token')
    secret_key = "0x4AAAAAABlQdjkFDmHwSHVnMuQ4TvW1Nsk"  # Your Cloudflare Turnstile secret key

    if not token:
        return jsonify({"success": False, "error": "Missing token"}), 400

    verify_url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    payload = {
        'secret': secret_key,
        'response': token
    }

    response = requests.post(verify_url, data=payload)
    result = response.json()

    if result.get("success"):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": result.get("error-codes", "Unknown error")}), 400

@app.route('/verify-token', methods=['POST'])
def verify_token():
    data = request.get_json()
    id_token = data.get('idToken')
    if not id_token:
        return jsonify({"message": "Missing ID token"}), 400

    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        return jsonify({"message": "Token valid", "uid": uid})
    except Exception as e:
        return jsonify({"message": f"Invalid token: {str(e)}"}), 401

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
