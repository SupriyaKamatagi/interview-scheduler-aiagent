# interview_schedule/agent.py
# Main ADK agent file
# 'adk web' automatically picks up root_agent from here

import os
import sys
import uuid
import json
import re
import asyncio
from google.adk.agents import Agent
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from tools import log_interview
#from interview_schedule.tools import log_interview
from google.genai import types

# Add parent folder to path so we can import tools.py and telegram_bot.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from tools import create_mcp_session, get_toolset
from telegram_bot import (
    build_app,
    store_pending,
    send_confirmation_request,
    wait_for_decision,
)

load_dotenv()

TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Create MCP session once when agent loads 
# MCP_URL = create_mcp_session()
MCP_URL, MCP_HEADERS = create_mcp_session()


# Helper: run a one-off agent task 
async def run_task(instruction: str, prompt: str) -> str:
    """
    Spins up a temporary LlmAgent with the MCP toolset,
    runs it with the given prompt, returns text response.
    """
    #toolset = get_toolset(MCP_URL)
    toolset = get_toolset(MCP_URL, MCP_HEADERS)
    agent = LlmAgent(
        name="TaskAgent",
        model="gemini-2.5-flash",
        tools=[toolset],
        instruction=instruction,
    )
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name="InterviewScheduler",
        session_service=session_service
    )
    
    sess = await session_service.create_session(
        app_name="InterviewScheduler",
        user_id="user1"
    )

    msg = types.Content(
        role="user",
        parts=[types.Part(text=prompt)]
    )
    result = ""
    async for event in runner.run_async(
        user_id="user1",
        session_id=sess.id,
        new_message=msg
    ):
        if event.is_final_response():
            result = event.content.parts[0].text
    return result


# Core workflow function 
async def process_interviews() -> str:
    """
    Full interview scheduling workflow:
    1. Scan Gmail for interview request emails
    2. Check Calendar for free slots 
    3. Ask user via Telegram buttons
    4. Confirm / Reschedule / Cancel based on response
    """
    summary = []

    # STEP 1: Scan Gmail + Calendar
    scan_result = await run_task(
        instruction="""
        Scan Gmail for unread interview emails and check Google Calendar.
        Return ONLY a raw JSON array, no explanation, no markdown fences.
        """,
        prompt="""
        1. Search Gmail for UNREAD emails containing any of these keywords:
           interview, schedule a call, meeting request, can we meet, hiring.
        2. For each matching email extract:
           name, email, subject, proposed_time (if mentioned).
        3. Check Google Calendar free/busy slots for next 3 working days,
           8am to 8pm IST. Find the earliest available 1-hour slot.
        4. Return a JSON array like this:
        [
          {
            "name": "John Doe",
            "email": "john@company.com",
            "subject": "Interview Request",
            "slot_date": "Tuesday, 8 April 2025",
            "slot_time": "10:00 AM"
          }
        ]
        Return empty array [] if no matching emails found.
        Return ONLY the raw JSON array. Nothing else.
        """
    )

    # Parse agent response safely
    try:
        match = re.search(r'\[.*\]', scan_result, re.DOTALL)
        interviews = json.loads(match.group()) if match else []
    except Exception as e:
        return f"⚠️ Could not parse Gmail scan response: {e}"

    if not interviews:
        return "✅ No new interview request emails found in Gmail."

    # STEP 2: Handle each interview interactively
    tg_app = build_app()
    await tg_app.initialize()
    await tg_app.start()
    await tg_app.updater.start_polling()

    try:
        for interview in interviews:
            interview_id = str(uuid.uuid4())[:8]
            store_pending(interview_id)

            # Send Telegram confirmation buttons
            await send_confirmation_request(
                tg_app,
                TELEGRAM_CHAT_ID,
                interview_id,
                {
                    "name":    interview.get("name", "Unknown"),
                    "email":   interview.get("email", ""),
                    "subject": interview.get("subject", ""),
                    "date":    interview.get("slot_date", ""),
                    "time":    interview.get("slot_time", ""),
                }
            )

            # Wait for user to tap a button (up to 5 minutes)
            decision = await wait_for_decision(interview_id, timeout=300)

            if decision == "confirm":
                await run_task(
                    instruction="Create Google Calendar events and send email invites. Then send Telegram notifications.",
                    prompt=f"""
                    1. Create a Google Calendar event:
                       Title: Interview with {interview['name']}
                       Date: {interview['slot_date']}
                       Time: {interview['slot_time']} IST
                       Duration: 1 hour
                       Attendee: {interview['email']}
                       Enable Google Meet conference link.
                       Send email invite to attendee.
                    2. Send Telegram message to {TELEGRAM_CHAT_ID}:
                       ✅ *Interview Booked!*
                       👤 *With:* {interview['name']} (`{interview['email']}`)
                       🗓️ {interview['slot_date']} at {interview['slot_time']} IST
                       📨 Calendar invite sent to candidate.
                    """
                )
                summary.append(f"✅ Booked: {interview['name']} on {interview['slot_date']} at {interview['slot_time']}")
                log_interview(
                    company=interview.get("name", "Unknown"),   # or parse company name if available
                    role=interview.get("subject", "Unknown"),   # subject line often has role info
                    interview_date=interview.get("slot_date", ""),
                    duration_in_minutes=60                      # fixed 1 hour, or parse if variable
                )

            elif decision == "reschedule":
                await run_task(
                    instruction="Send professional emails via Gmail. Send Telegram notifications.",
                    prompt=f"""
                    1. Send email via Gmail to {interview['email']}:
                       Subject: Re: {interview['subject']} — Requesting Alternative Timings
                       Body: Polite 3-4 sentence email saying the proposed time
                       doesn't work, kindly requesting 2-3 alternative slots
                       at their convenience. Sign off as: Hiring Team
                    2. Send Telegram message to {TELEGRAM_CHAT_ID}:
                       🔄 *Reschedule email sent!*
                       👤 To: {interview['name']} (`{interview['email']}`)
                       📨 Asked for alternative timings.
                    """
                )
                summary.append(f"🔄 Reschedule email sent to: {interview['name']}")

            elif decision == "cancel":
                await run_task(
                    instruction="Send professional emails via Gmail. Send Telegram notifications.",
                    prompt=f"""
                    1. Send email via Gmail to {interview['email']}:
                       Subject: Re: {interview['subject']} — Regarding Our Meeting
                       Body: Warm, polite 3-4 sentence email thanking them for
                       their interest and time, informing them we will not be
                       moving forward with scheduling a meeting at this time.
                       Wish them well. Sign off as: Hiring Team
                    2. Send Telegram message to {TELEGRAM_CHAT_ID}:
                       ❌ *Rejection email sent.*
                       👤 To: {interview['name']} (`{interview['email']}`)
                       📨 Politely declined the meeting.
                    """
                )
                summary.append(f"❌ Rejection email sent to: {interview['name']}")

            elif decision == "timeout":
                summary.append(f"⏰ No response within 5 min for: {interview['name']} — skipped")

    finally:
        await tg_app.updater.stop()
        await tg_app.stop()
        await tg_app.shutdown()

    return "\n".join(summary)


# ADK root_agent
# adk web looks for this variable specifically
# It handles the chat UI conversation

async def handle_user_message(user_input: str) -> str:
    """Routes user chat messages to the right action."""
    keywords = [
        "check", "gmail", "interview", "email",
        "schedule", "run", "start", "scan"
    ]
    if any(word in user_input.lower() for word in keywords):
        return await process_interviews()
    return (
        "👋 Hi! I'm your Interview Scheduling Agent.\n\n"
        "I can:\n"
        "• Check Gmail for interview request emails\n"
        "• Find free slots on your Google Calendar\n"
        "• Ask you via Telegram to confirm / reschedule / cancel\n"
        "• Auto-book or send appropriate emails\n\n"
        "Just say: **'Check my Gmail for interview requests'** to get started!"
    )

import os
model=os.getenv("MODEL", "gemini-2.5-flash")

root_agent = LlmAgent(
    name="InterviewSchedulerAgent",
    model=model,
    tools=[get_toolset(MCP_URL, MCP_HEADERS)],
    instruction=f"""
    You are an interview scheduling assistant with access to Gmail,
    Google Calendar, and Telegram via Composio MCP Tool Router.

    When the user asks you to check emails or schedule interviews:
    - Search Gmail for unread interview request emails
    - Check Google Calendar for free slots (next 3 days, 8am-8pm IST)
    - Send Telegram confirmation buttons to chat ID {TELEGRAM_CHAT_ID}
    - Wait for user response
    - Based on response: book event / send reschedule email / send rejection email
    - Report back what was done

    Always be concise and professional. If user ask anything apart for interview scheduler say its out of your scope.
    Timezone: Asia/Kolkata (IST).
    Use Markdown formatting in Telegram messages.
    Use "Exit" to exit.
    """,
)
