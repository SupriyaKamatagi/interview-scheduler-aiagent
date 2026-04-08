# tools.py
# Connects to Composio MCP Tool Router
# Gives agent access to Gmail + Calendar + Telegram
# through a single secure MCP URL

import os
from google.cloud import bigquery
from dotenv import load_dotenv
from composio import Composio
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StreamableHTTPConnectionParams
)

load_dotenv()

COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY")
COMPOSIO_USER_ID = os.getenv("COMPOSIO_USER_ID")

def create_mcp_session():
    """
    Creates a Composio Tool Router session.
    Returns a single MCP URL that gives access
    to Gmail, Google Calendar, and Telegram.
    """
    print(" Connecting to Composio MCP Tool Router...")
    client = Composio(api_key=COMPOSIO_API_KEY)

    session = client.create(user_id=COMPOSIO_USER_ID)

    

    print(" Composio MCP session ready")
    return session.mcp.url, session.mcp.headers

    #return session.mcp_url

def get_toolset(mcp_url: str, mcp_headers: dict) -> MCPToolset:
    """
    Wraps the MCP URL + headers into an ADK-compatible toolset.
    This gets passed into the LlmAgent as tools=[toolset].
    """
    return MCPToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=mcp_url,
            headers=mcp_headers
        )
    )


def log_interview(company: str, role: str, interview_date: str, duration_in_minutes: int):
    client = bigquery.Client(project=os.getenv("PROJECT_ID"))
    table_id = f"{os.getenv('PROJECT_ID')}.{os.getenv('BIGQUERY_DATASET')}.{os.getenv('BIGQUERY_TABLE')}"

    rows_to_insert = [{
        "company": company,
        "role": role,
        "interview_date": interview_date,
        "duration_in_minutes": duration_in_minutes
    }]
    errors = client.insert_rows_json(table_id, rows_to_insert)
    if errors:
        print("BigQuery insert errors:", errors)
    else:
        print("Interview logged successfully.")
