import openai
import os

def get_agent_prompt():
    with open("jobad_agent_prompt.yaml", "r") as f:
        return f.read()

def generate_job_summary(history):
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Ensure history is a list of messages; insert system prompt at the start
    if not isinstance(history, list):
        # If single string, treat as first user message
        history = [{"role": "user", "content": str(history)}]

    # Prepend the system prompt
    messages = [{"role": "system", "content": get_agent_prompt()}] + history

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.2
    )
    return response.choices[0].message.content
