import os
from datetime import datetime
import uuid
import asyncio # Added import
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from f1_data_fetcher import get_f1_standings
from google_sheets import create_f1_standings_sheet
from gmail_sender import send_email
from sse_server import update_standings
from models import MessageContext, F1Standings, Driver
from llm_handler import LLMHandler

llm_handler = LLMHandler()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! I am your F1 standings bot. Use /standings to get current F1 standings.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Available commands:\n/start - Start the bot\n/help - Show this help message\n/standings - Get F1 standings')

async def standings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        standings_data = get_f1_standings() # This is List[Dict[str, str]]

        if not standings_data:
            await update.message.reply_text("No standings data found or an error occurred retrieving it.")
            return

        trace_id = str(uuid.uuid4())
        
        drivers_objects = [
            Driver(
                position=standing['position'],
                driver_name=standing['driver'],
                points=standing['points'],
                trace_id=trace_id,
                mcp_version="1.0"
            ) for standing in standings_data
        ]
        
        f1_standings_obj = F1Standings(
            timestamp=datetime.now(),
            standings=drivers_objects,
            last_updated=datetime.now(),
            trace_id=trace_id,
            metadata={"update_type": "telegram_command"},
            mcp_version="1.0"
        )
        
        message_context_for_llm = MessageContext(
            message_id=str(uuid.uuid4()),
            message_type="F1_STANDINGS_ANALYSIS",
            content=f1_standings_obj, # Pass the F1Standings object
            trace_id=trace_id,
            metadata={"analysis_type": "real_time"},
            mcp_version="1.0"
        )
        
        update_standings(standings_data)
        
        telegram_response_text = "Current F1 Standings:\n\n"
        for driver_obj in drivers_objects:
            telegram_response_text += f"{driver_obj.position}. {driver_obj.driver_name}: {driver_obj.points} points\n"
        
        # Get LLM analysis
        llm_analysis_text = None
        try:
            analysis_result = await llm_handler.analyze_standings(message_context_for_llm)
            if analysis_result:
                llm_analysis_text = analysis_result
                telegram_response_text += "\n\nAI Analysis:\n" + llm_analysis_text
            else:
                telegram_response_text += "\n\nAI Analysis not available at the moment."
        except Exception as llm_error:
            print(f"Error in LLM analysis: {llm_error}")
            telegram_response_text += "\n\nError retrieving AI analysis."

        sheet_url = None
        try:
            sheet_url = create_f1_standings_sheet(standings_data)
            if sheet_url:
                telegram_response_text += f"\n\nView detailed standings: {sheet_url}"
            else:
                telegram_response_text += "\n\nCould not retrieve Google Sheet URL."
                print("Google Sheet creation returned no URL.")
        except Exception as sheet_error:
            print(f"Error creating Google Sheet: {sheet_error}")
            telegram_response_text += "\n\nError creating Google Sheet."
        
        # Prepare email content
        email_subject = "F1 Standings Update & Analysis"
        email_content_body = "The F1 standings have been updated.\n\n"

        if sheet_url:
            email_content_body += f"You can view the Google Sheet here: {sheet_url}\n\n"
        else:
            email_content_body += "Google Sheet link is not available.\n\n"

        if llm_analysis_text:
            email_content_body += "AI Analysis:\n" + llm_analysis_text
        else:
            email_content_body += "AI Analysis is not available at the moment."

        # Send email
        try:
            # Only attempt to send email if there's something to send (e.g., sheet_url or analysis)
            if sheet_url or llm_analysis_text:
                email_sent = send_email(
                    subject=email_subject,
                    content=email_content_body
                )
                if email_sent:
                    print("Standings update email with Google Sheet link and/or analysis sent successfully.")
                else:
                    print("Failed to send standings update email (send_email returned False).")
            else:
                print("Skipping email: No Google Sheet URL and no LLM analysis available.")

        except Exception as email_error:
            print(f"Error calling send_email function: {email_error}")
        
        await update.message.reply_text(telegram_response_text)
        
    except Exception as e:
        print(f"Error in standings command: {e}")
        await update.message.reply_text("Sorry, there was an error fetching the standings.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Please use /standings to get F1 standings.')

def start_bot():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("No token found! Make sure to set TELEGRAM_BOT_TOKEN in .env file")
    
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('standings', standings_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Starting bot polling...")
    app.run_polling(poll_interval=3)