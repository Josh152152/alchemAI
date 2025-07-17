from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from app.ai_agent import generate_job_summary
import json
import requests
import os

# Firebase Admin imports
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials, firestore

app = Flask(__name__)

# CORS config: restrict to your Webflow origin and allow credentials (cookies, auth headers)
CORS(app, resources={r"/*": {"origins": "https://alchemai.webflow.io"}}, supports_credentials=True)

# Load Firebase credentials JSON from environment variable
firebase_creds_json = os.getenv("FIREBASE_CREDENTIALS")
if not firebase_creds_json:
    raise Exception("Missing FIREBASE_CREDENTIALS environment variable")

try:
    cred_dict = json.loads(firebase_creds_json)
    print("Firebase credentials JSON loaded successfully.")
except Exception as e:
    print("Failed to parse Firebase credentials JSON:", e)
    raise

cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route('/', methods=['GET'])
def home():
    return render_template('agent_form.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    message_history = data.get("history") or None
    if not message_history and "job_info" in data:
        job_info = data["job_info"]
        if isinstance(job_info, str):
            message_history = [{"role": "user", "content": job_info}]
        else:
            message_history = job_info

    if not message_history:
        return jsonify({"error": "No job_info or history provided"}), 400

    print("message_history received:", message_history)

    ai_reply = generate_job_summary(message_history)

    stored = False
    summary_json = None
    try:
        summary_json = json.loads(ai_reply)
        user_uid = data.get("uid")
        if user_uid:
            doc_ref = db.collection("job_descriptions").document(user_uid)
            doc_ref.set(summary_json, merge=True)
            stored = True
    except Exception as e:
        print("JSON decode or Firestore store failed:", str(e))
        summary_json = None

    print("AI reply:", ai_reply)
    print("Summary JSON:", summary_json)
    print("Saved to Firestore:", stored)

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

# Firestore-based conversation persistence

@app.route('/load-conversation', methods=['POST'])
def load_conversation():
    data = request.get_json()
    uid = data.get('uid')
    if not uid:
        return jsonify({"error": "Missing uid"}), 400

    try:
        doc_ref = db.collection("conversations").document(uid)
        doc = doc_ref.get()
        if doc.exists:
            return jsonify({"conversation": doc.to_dict().get("conversation", [])})
        else:
            return jsonify({"conversation": []})
    except Exception as e:
        return jsonify({"error": f"Failed to load conversation: {str(e)}"}), 500

@app.route('/save-conversation', methods=['POST'])
def save_conversation():
    data = request.get_json()
    uid = data.get('uid')
    conversation = data.get('conversation')
    if not uid or conversation is None:
        return jsonify({"error": "Missing uid or conversation"}), 400

    try:
        doc_ref = db.collection("conversations").document(uid)
        doc_ref.set({"conversation": conversation})
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": f"Failed to save conversation: {str(e)}"}), 500

# New route to load structured job info from Firestore

@app.route('/load-job-info', methods=['POST'])
def load_job_info():
    data = request.get_json()
    uid = data.get('uid')
    if not uid:
        return jsonify({"error": "Missing uid"}), 400
    try:
        doc_ref = db.collection("job_descriptions").document(uid)
        doc = doc_ref.get()
        if doc.exists:
            return jsonify({"job_info": doc.to_dict()})
        else:
            return jsonify({"job_info": {}})
    except Exception as e:
        return jsonify({"error": f"Failed to load job info: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
