import os
from datetime import datetime
import uuid
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from f1_data_fetcher import get_f1_standings
from google_sheets import create_f1_standings_sheet
from gmail_sender import send_email
from sse_server import update_standings
from models import MessageContext, F1Standings, Driver
from llm_handler import LLMHandler

llm_handler = LLMHandler()

async def start_command(update, context):
    await update.message.reply_text('Hello! I am your F1 standings bot. Use /standings to get current F1 standings.')

async def help_command(update, context):
    await update.message.reply_text('Available commands:\n/start - Start the bot\n/help - Show this help message\n/standings - Get F1 standings')

async def standings_command(update, context):
    await update.message.reply_text('Fetching F1 standings...')
    
    # Get standings
    standings = get_f1_standings()
    if not standings:
        await update.message.reply_text('Sorry, could not fetch F1 standings.')
        return
    
    # Create drivers list for MessageContext
    drivers = [
        Driver(
            position=standing['position'],
            driver_name=standing['driver'],
            points=standing['points']
        ) for standing in standings
    ]
    
    # Create F1Standings object
    f1_standings = F1Standings(
        timestamp=datetime.now(),
        standings=drivers,
        last_updated=datetime.now()
    )
    
    # Create MessageContext
    message_context = MessageContext(
        message_id=str(uuid.uuid4()),
        message_type="F1_STANDINGS_UPDATE",
        content=f1_standings
    )
    
    # Update SSE server with new standings using MCP
    update_standings(message_context)
    
    # Get LLM analysis
    print("Requesting LLM analysis...")
    analysis = await llm_handler.analyze_standings(message_context)
    if analysis:
        print("Successfully received LLM analysis")
    else:
        print("Failed to get LLM analysis")
    
    # Format standings for Telegram message
    message = "🏎 Current F1 Driver Standings 🏎\n\n"
    for standing in standings:
        position = standing['position']
        driver = standing['driver']
        points = standing['points']
        
        # Add emoji based on position
        if position == "1":
            emoji = "🥇"
        elif position == "2":
            emoji = "🥈"
        elif position == "3":
            emoji = "🥉"
        else:
            emoji = "🏎"
            
        message += f"{emoji} {position}. {driver} - {points} points\n"
    
    # Add LLM analysis if available
    if analysis:
        message += "\n📊 Analysis:\n" + analysis
    
    # Send standings in chat
    await update.message.reply_text(message)
    
    # Create Google Sheet
    print("Creating Google Sheet...")
    sheet_url = create_f1_standings_sheet(standings)
    if not sheet_url:
        print("Failed to create Google Sheet")
        await update.message.reply_text('Sorry, could not create Google Sheet.')
        return
    print(f"Successfully created Google Sheet: {sheet_url}")
    
    # Send email
    print("Sending email with standings sheet link...")
    email_content = f"""Here's the link to F1 standings sheet:\n{sheet_url}
    
Analysis:
{analysis if analysis else 'No analysis available'}"""
    
    if send_email("F1 Standings Update", email_content):
        print("Successfully sent email with standings and analysis")
        await update.message.reply_text('F1 standings have also been saved to Google Sheets and sent to your email!')
    else:
        print("Failed to send email")
        await update.message.reply_text('F1 standings saved to Google Sheets but email sending failed.')

async def handle_message(update, context):
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