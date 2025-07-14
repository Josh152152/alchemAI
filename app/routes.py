from flask import Flask, render_template, request, jsonify
from app.ai_agent import generate_job_summary
from app.sheets import store_to_gsheet

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return render_template('agent_form.html')

@app.route('/generate', methods=['POST'])
def generate():
    # Accept job_info from HTML form
    job_info = request.form.get("job_info")
    if not job_info:
        # If no job_info found, try JSON (for backwards compatibility)
        data = request.get_json(silent=True)
        if data:
            job_info = data.get("job_info") or data.get("history")
        if not job_info:
            return jsonify({"error": "No job_info provided"}), 400

    # Wrap single job_info in a message history (if it's just a string)
    if isinstance(job_info, str):
        message_history = [job_info]
    else:
        message_history = job_info

    ai_reply = generate_job_summary(message_history)

    # Try to extract structured JSON from the agent's reply and store to GSheet if present
    stored = False
    import json
    try:
        summary_json = json.loads(ai_reply)
        store_to_gsheet(summary_json)
        stored = True
    except Exception:
        summary_json = None  # Not a structured summary yet

    return jsonify({
        "reply": ai_reply,
        "saved": stored,
        "summary": summary_json
    })

# For Render local debug only
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
