import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)
client = gspread.authorize(creds)
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
