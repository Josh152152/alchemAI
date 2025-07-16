import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# Use the secret path provided by Render
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('/etc/secrets/creds.json', scope)
client = gspread.authorize(creds)

# Main job data sheet
sheet = client.open_by_key('10WTvkXQqCUes7BQ_pPygzpllLhV9SNiy2dMDL73IOIY').sheet1

FIELDS = [
    "job_title", "responsibilities", "compensation_range", "benefits", "work_life_balance",
    "company_culture", "team_size", "ideal_candidate_profile", "required_skills", "growth_opportunity",
    "company_values", "workspace_type", "unique_perks", "hiring_timeline", "candidate_type", "key_projects",
    "probation_details", "experience_level", "working_schedule", "location_preferences", "certifications"
]

def store_to_gsheet(job_json):
    """Append a new row to the GSheet with the latest JD data."""
    if isinstance(job_json, str):
        job_json = json.loads(job_json)
    values = [job_json.get(field, "") for field in FIELDS]
    sheet.append_row(values)

# Sheet for storing conversations; make sure this sheet exists in your GSheet file
conversation_sheet = client.open_by_key('10WTvkXQqCUes7BQ_pPygzpllLhV9SNiy2dMDL73IOIY').worksheet("Conversations")

def save_conversation_for_user(uid, conversation):
    """
    Save conversation for a user to the sheet.
    Stores JSON string of conversation in column 2, uid in column 1.
    """
    try:
        all_uids = conversation_sheet.col_values(1)
        if uid in all_uids:
            row_index = all_uids.index(uid) + 1
        else:
            row_index = len(all_uids) + 1
            conversation_sheet.update_cell(row_index, 1, uid)
        conversation_sheet.update_cell(row_index, 2, json.dumps(conversation))
    except Exception as e:
        print(f"Error saving conversation for uid {uid}: {e}")
        raise e

def load_conversation_for_user(uid):
    """
    Load conversation for a user from the sheet.
    Returns list of conversation messages or empty list if none found.
    """
    try:
        all_uids = conversation_sheet.col_values(1)
        if uid in all_uids:
            row_index = all_uids.index(uid) + 1
            conv_json = conversation_sheet.cell(row_index, 2).value
            if conv_json:
                return json.loads(conv_json)
        return []
    except Exception as e:
        print(f"Error loading conversation for uid {uid}: {e}")
        return []
