# telegram_bot.py
# Handles interactive Telegram buttons
# Sends confirmation request to user
# Waits for Yes / Reschedule / Cancel response

import os
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Stores user decisions keyed by interview_id
# None = waiting, "confirm"/"reschedule"/"cancel" = decided
pending_decisions = {}

def store_pending(interview_id: str):
    """Register a new pending decision for an interview."""
    pending_decisions[interview_id] = None


async def send_confirmation_request(app, chat_id: str, interview_id: str, details: dict):
    """
    Sends a Telegram message with 3 inline buttons:
    ✅ Confirm | 🔄 Reschedule | ❌ Cancel
    """
    text = (
        f"📨 *New Interview Request Detected!*\n\n"
        f"👤 *Candidate:* {details['name']} \n"
        f"📧 *Email:* `{details['email']}`\n"
        f"📝 *Subject:* {details['subject']}\n\n"
        f"📅 *Suggested Schedule:*\n"
        f"🗓️ *Date:* {details['date']}\n"
        f"🕐 *Time:* {details['time']} IST\n"
        f"⏱️ *Duration:* 1 hour\n\n"
        f"*Are you okay with this schedule?*"
    )

    keyboard = [
        [InlineKeyboardButton(
            "✅ Yes, Confirm",
            callback_data=f"confirm:{interview_id}"
        )],
        [InlineKeyboardButton(
            "🔄 Reschedule — ask for alternatives",
            callback_data=f"reschedule:{interview_id}"
        )],
        [InlineKeyboardButton(
            "❌ Don't want this meeting",
            callback_data=f"cancel:{interview_id}"
        )],
    ]

    await app.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Called when user taps a button on Telegram."""
    query = update.callback_query
    await query.answer()  # removes loading spinner on button

    action, interview_id = query.data.split(":", 1)
    pending_decisions[interview_id] = action

    messages = {
        "confirm":    "✅ *Confirmed!* Booking the interview and sending calendar invite...",
        "reschedule": "🔄 *Got it!* Sending reschedule email to interviewer...",
        "cancel":     "❌ *Noted.* Sending polite rejection email to interviewer...",
    }

    await query.edit_message_text(
        messages.get(action, "Processing..."),
        parse_mode="Markdown"
    )


async def wait_for_decision(interview_id: str, timeout: int = 300) -> str:
    """
    Polls every second until user taps a button.
    Returns the decision string or 'timeout' after 5 minutes.
    """
    for _ in range(timeout):
        decision = pending_decisions.get(interview_id)
        if decision is not None:
            return decision
        await asyncio.sleep(1)
    return "timeout"


def build_app() -> Application:
    """Builds the Telegram bot Application with button handler registered."""
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CallbackQueryHandler(button_handler))
    return app