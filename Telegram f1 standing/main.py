import os
from dotenv import load_dotenv

# Load environment variables BEFORE any other imports
print('Loading environment variables...')
load_dotenv()
print('Environment variables loaded.')
print(f"Gemini API Key loaded: {'GEMINI_API_KEY' in os.environ}")

# Import other modules AFTER loading environment variables
from telegram_bot import start_bot
from sse_server import start_sse_server

def main():
    print('Starting SSE server...')
    start_sse_server()
    print('SSE server started.')

    print('Starting Telegram bot...')
    start_bot()
    print('Telegram bot started.')

if __name__ == '__main__':
    print('Running main()...')
    main()
    print('main() finished.')