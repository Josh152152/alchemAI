from flask import Flask, render_template, request, jsonify
from app.ai_agent import generate_job_summary
from app.sheets import store_to_gsheet
import json

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return render_template('agent_form.html')

@app.route('/generate', methods=['POST'])
def generate():
    # Default: no message history yet
    message_history = None

    # Prefer JSON body (for multi-turn chat)
    data = request.get_json(silent=True)
    if data and "history" in data:
        message_history = data["history"]
    else:
        # Fall back to form data (single-shot form)
        job_info = request.form.get("job_info")
        if job_info:
            message_history = [{"role": "user", "content": job_info}]
    
    if not message_history:
        return jsonify({"error": "No job_info or history provided"}), 400

    # --- DEBUG PRINTS ---
    print("message_history received:", message_history)

    # Send full conversation to OpenAI
    ai_reply = generate_job_summary(message_history)

    # Try to extract structured JSON from the agent's reply and store to GSheet if present
    stored = False
    try:
        summary_json = json.loads(ai_reply)
        store_to_gsheet(summary_json)
        stored = True
    except Exception as e:
        print("JSON decode or GSheet store failed:", str(e))
        summary_json = None  # Not a structured summary yet

    print("AI reply:", ai_reply)
    print("Summary JSON:", summary_json)
    print("Saved to GSheet:", stored)

    return jsonify({
        "reply": ai_reply,
        "saved": stored,
        "summary": summary_json
    })

# For Render local debug only
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
