import openai
import os

def get_agent_prompt():
    with open("jobad_agent_prompt.yaml", "r") as f:
        return f.read()

def generate_job_summary(user_input):
    prompt = get_agent_prompt()
    # For OpenAI, provide both system prompt and user input
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input}
        ],
        temperature=0.2
    )
    # Get AI's structured JSON output
    return response['choices'][0]['message']['content']

