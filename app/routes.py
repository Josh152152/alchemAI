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
    # Accept job_info from HTML form or JSON body
    job_info = request.form.get("job_info")
    if not job_info:
        data = request.get_json(silent=True)
        if data:
            job_info = data.get("job_info") or data.get("history")
        if not job_info:
            return jsonify({"error": "No job_info provided"}), 400

    # Guarantee job_info is always a string for OpenAI API
    if isinstance(job_info, list):
        job_info = "\n".join(str(m) for m in job_info if isinstance(m, str))
    elif not isinstance(job_info, str):
        return jsonify({"error": "Invalid job_info format"}), 400

    # --- DEBUG PRINTS ---
    print("job_info received:", job_info)

    # Send as a single message to OpenAI
    ai_reply = generate_job_summary(job_info)

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
