# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Development Commands

### Local Development
```powershell
# Setup virtual environment and install dependencies
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Run the bot locally
python bot.py

# Alternative: Run using the batch script (Windows)
run.bat
```

### Environment Configuration
Set up environment variables before running:
```powershell
$env:TELEGRAM_BOT_TOKEN="your_bot_token_from_botfather"
$env:OPENROUTER_API_KEY="your_openrouter_api_key"
$env:MODEL_NAME="tngtech/deepseek-r1t2-chimera:free"  # Optional, defaults to this
```

### Deployment Commands
The bot supports multiple deployment platforms:

**Railway**: Uses `start.py` as entry point with `Procfile`
**Scalingo**: Uses `scalingo_start.py` with `Procfile.scalingo` 
**Heroku/Render**: Uses `web: python bot.py` from `Procfile`
**Vercel**: Configured via `vercel.json` (though not ideal for long-running bots)

## Architecture Overview

### Core Components

**Main Bot Logic (`bot.py`)**
- Single-file architecture containing all bot functionality
- Async/await pattern using `python-telegram-bot` library
- Modular command handlers for different bot features
- In-memory user data storage (no database)

**Configuration (`config.py`)**
- Centralized configuration constants
- AI model settings and prompts
- Currently stores sensitive tokens directly (should use environment variables)

**Entry Points**
- `bot.py`: Direct execution for local development
- `start.py`: Production entry point with environment validation
- `scalingo_start.py`: Scalingo-specific startup script

### Key Features Architecture

**Role-Playing System**
- Command-based RP actions (`/hug`, `/kiss`, etc.) defined in `RP_ACTIONS` dictionary
- User experience/leveling system with in-memory storage
- Generic `handle_rp_action()` function processes all RP commands

**AI Integration**
- OpenRouter API integration via `call_openrouter()` function
- System prompts for roleplay personality in `config.py`
- Handles both command-based (`/ai`) and direct message AI responses
- Async processing to prevent blocking

**File Generation System**
- AI-powered file creation supporting multiple formats (txt, csv, json, html, py, etc.)
- `generate_file_content()` function with type-specific prompts
- In-memory file creation using `io.BytesIO`

**Text-to-Speech**
- Google Translate TTS integration via `text_to_speech()` function
- Support for multiple languages (ru, en, es, fr, de, it, pt, ja, ko, zh)
- 200 character limit for TTS processing

### Data Flow

1. **Command Processing**: Telegram updates → Command handlers → Feature-specific functions
2. **AI Requests**: User input → `call_openrouter()` → OpenRouter API → Formatted response
3. **User Data**: In-memory dictionary storage (`user_data`) with XP/level tracking
4. **File Operations**: AI content generation → BytesIO buffer → Telegram document upload

### Deployment Architecture

**Multi-Platform Support**
- Different entry points for various hosting platforms
- Environment variable validation in production entry points
- Platform-specific configuration files (railway.json, scalingo.json, etc.)

**Dependencies**
- `python-telegram-bot==21.6`: Core Telegram bot framework
- `requests`: HTTP requests for OpenRouter API and TTS
- `python-dotenv`: Environment variable management (though not actively used in main code)
- `urllib3`: HTTP client dependency

### Important Implementation Notes

**Security Considerations**
- API keys are hardcoded in `bot.py` and `config.py` (line 12-13 in bot.py)
- Production deployments should use environment variables exclusively
- No input sanitization for AI prompts

**Limitations**
- No persistent database - user data lost on restart  
- In-memory storage limits scalability
- No rate limiting on AI API calls
- Hardcoded Russian language in many user-facing messages

**Error Handling**
- Basic try/catch around API calls with fallback messages
- Timeout handling for OpenRouter requests (60 seconds)
- TTS failure gracefully handled with error messages

### Development Workflow

When adding new features:
1. Add command handlers to `main()` function (around line 530)
2. Implement async handler functions following existing patterns
3. Update help text and command descriptions
4. Test locally using `python bot.py`
5. Deploy using platform-specific entry points

For AI-related changes:
- Modify system prompts in `config.py`
- Adjust model parameters in `AI_CONFIG` dictionary
- Test with different OpenRouter models by changing `MODEL_NAME`