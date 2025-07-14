from flask import Flask, render_template, request, jsonify
from app.ai_agent import generate_job_summary
# from app.sheets import store_to_gsheet  # Implement later

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return render_template('agent_form.html')

@app.route('/generate', methods=['POST'])
def generate():
    user_input = request.form.get("job_info", "")
    summary_json = generate_job_summary(user_input)
    # Optionally store in Google Sheet
    # store_to_gsheet(summary_json)
    return jsonify({"summary": summary_json})

# For Render
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)

