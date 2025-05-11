# F1 Standings Telegram Bot & Real-time Analysis

This project is a sophisticated Telegram bot that provides real-time Formula 1 standings, detailed analysis via a Large Language Model (LLM), integration with Google Sheets for data storage, email notifications, and a Server-Sent Events (SSE) endpoint for live updates.

## Features

*   **Telegram Bot Interface**:
    *   Get current F1 driver standings on demand.
    *   User-friendly commands (`/start`, `/help`, `/standings`).
*   **LLM-Powered Analysis**:
    *   In-depth analysis of F1 standings, including points gaps, championship battle insights, and performance trends, powered by Google's Gemini model.
*   **Google Sheets Integration**:
    *   Automatically updates a Google Sheet with the latest F1 standings.
    *   Provides a shareable link to the Google Sheet.
*   **Email Notifications**:
    *   Sends email notifications containing the F1 standings, LLM analysis, and a link to the Google Sheet.
*   **Real-time SSE Server**:
    *   Exposes an SSE endpoint (`/stream`) for clients to receive live F1 standings updates.
    *   Includes a REST endpoint (`/standings`) to fetch the latest standings.
    *   Implements FastMCP (Fictitious Awesome Speedy Transfer Message Control Protocol) compliance for message context and tracing.
*   **Modular Design**:
    *   Clear separation of concerns with dedicated modules for data fetching, Telegram bot logic, LLM interaction, Google Sheets, email sending, and SSE server.

## Tech Stack & Key Modules

*   **Python 3.x**
*   **Telegram Bot Framework**: `python-telegram-bot`
*   **LLM**: Google Gemini (`google-generativeai`)
*   **Web Framework (SSE Server)**: Flask
*   **Email**: `yagmail` (for Gmail)
*   **Google Sheets API**: (Likely `gspread` or `google-api-python-client` - assumed based on `google_sheets.py`)
*   **Data Fetching**: (Likely `requests` or `httpx` - assumed based on `f1_data_fetcher.py`)
*   **Environment Management**: `python-dotenv` (assumed for `.env` file)
*   **Data Modeling**: `pydantic` (implied by `models.py` and FastMCP compliance)

## Setup and Installation

### Prerequisites

*   Python 3.8+
*   pip (Python package installer)
*   Git

### Installation Steps

1.  **Clone the repository (Example):**
    ```bash
    git clone <your-repository-url>
    cd <your-repository-directory>
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    Create a `requirements.txt` file with all necessary packages (see example below) and run:
    ```bash
    pip install -r requirements.txt
    ```

    **Example `requirements.txt`:**
    ```
    python-telegram-bot
    google-generativeai
    Flask
    yagmail
    python-dotenv
    # Add other libraries like gspread, requests, pydantic if not already covered
    ```

4.  **Set up Environment Variables:**
    Create a `.env` file in the root directory of the project and add the following environment variables with your actual credentials:

    ```env
    TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    GMAIL_USER="YOUR_GMAIL_EMAIL_ADDRESS"
    GMAIL_APP_PASSWORD="YOUR_GMAIL_APP_PASSWORD" # Use an App Password if 2FA is enabled
    RECIPIENT_EMAIL="EMAIL_ADDRESS_TO_RECEIVE_NOTIFICATIONS"

    # Add any Google Cloud/Sheets API credentials if needed, e.g.,
    # GOOGLE_APPLICATION_CREDENTIALS="path/to/your/google-credentials.json"
    ```
    *Ensure your Gmail account is configured to allow "less secure app access" or preferably use an App Password if you have 2-Factor Authentication enabled.*

## Usage

1.  **Run the main application:**
    The primary entry point is likely `main.py` (or `telegram_bot.py` if it also starts the SSE server).
    ```bash
    python main.py
    ```
    This should start the Telegram bot polling and the SSE server.

2.  **Interact with the Telegram Bot:**
    *   Open Telegram and search for your bot.
    *   Send `/start` to initiate a conversation.
    *   Send `/standings` to get the latest F1 standings, LLM analysis, and a Google Sheet link.
    *   Send `/help` for a list of commands.

3.  **Access the SSE Stream:**
    *   Open a browser or use a client like `curl` to connect to `http://localhost:5000/stream` (or the configured host/port for the SSE server).
    *   You will receive live updates as they become available.

4.  **Fetch Standings via REST API:**
    *   Access `http://localhost:5000/standings` to get the latest standings in JSON format.

## Project Structure (Key Files)