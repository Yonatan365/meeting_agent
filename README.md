# Meeting Agent

A YAML-based calendar bot for scheduling meetings.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create your `.env` file with your OpenAI API key:
   ```bash
   cp .env .env.local  # optional backup
   ```
   
   Then edit `.env` and replace `your_openai_api_key_here` with your actual OpenAI API key.

## Usage

### Streamlit Web Interface
```bash
streamlit run app.py
```

### Command Line Interface
```bash
python -m asyncio chat_cli.py
```

### Direct Python Script
```bash
python calendar_bot.py
```

## Files

- `calendar_bot.py` - Main bot logic with calendar functions
- `app.py` - Streamlit web interface
- `chat_cli.py` - Command line interface
- `calendar.yml` - YAML database for calendar data
- `.env` - Environment variables (not in git)
- `requirements.txt` - Python dependencies
