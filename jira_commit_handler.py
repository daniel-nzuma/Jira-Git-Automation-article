#!/usr/bin/env python3

import os
import re
import json
import subprocess
import requests
from dotenv import load_dotenv

# Load .env for credentials and config
load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")

auth = (JIRA_EMAIL, JIRA_API_TOKEN)
headers = {"Content-Type": "application/json"}

# Get the latest commit info
commit_msg = subprocess.check_output(["git", "log", "-1", "--pretty=%B"]).decode().strip()
commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
commit_author = subprocess.check_output(["git", "log", "-1", "--pretty=%an"]).decode().strip()

# Extract time spent from commit message (e.g., "#30" → "30m")
match = re.search(r'#(\d+)', commit_msg)
if match:
    time_spent = f"{match.group(1)}m"
    commit_msg = re.sub(r'#\d+', '', commit_msg).strip()
else:
    time_spent = "15m"

# Create Jira issue payload
issue_payload = {
    "fields": {
        "project": {"key": JIRA_PROJECT_KEY},
        "summary": commit_msg,
        "description": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "text": f"Commit `{commit_hash}` by {commit_author}",
                            "type": "text"
                        }
                    ]
                }
            ]
        },
        "issuetype": {"name": "Task"},
        "assignee": {"id": os.getenv("JIRA_ACCOUNT_ID")}
    }
}


# Create the Jira issue
print("📡 Creating Jira issue...")
response = requests.post(f"{JIRA_BASE_URL}/rest/api/3/issue", headers=headers, auth=auth, data=json.dumps(issue_payload))

if response.status_code != 201:
    print(f"❌ Failed to create Jira issue: {response.text}")
    exit(1)

issue_key = response.json()["key"]
print(f"✅ Created issue: {issue_key}")

# Log work
worklog_payload = {
    "timeSpent": time_spent,
    "comment": {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": f"Auto-logged from Git commit {commit_hash}"
                    }
                ]
            }
        ]
    }
}

print(f"🕒 Logging {time_spent} to {issue_key}...")
worklog_response = requests.post(
    f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/worklog",
    headers=headers,
    auth=auth,
    data=json.dumps(worklog_payload)
)

if worklog_response.status_code == 201:
    print("✅ Worklog added successfully.")
else:
    print(f"❌ Failed to log work: {worklog_response.text}")
