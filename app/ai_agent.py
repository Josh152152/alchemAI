import openai
import os

def get_agent_prompt():
    with open("jobad_agent_prompt.yaml", "r") as f:
        return f.read()

def generate_job_summary(user_input):
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": get_agent_prompt()},
            {"role": "user", "content": user_input}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content
