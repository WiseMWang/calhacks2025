# MailMind 🤖📧

> Send emails through natural conversation with AI

MailMind is an AI-powered email assistant built on the Model Context Protocol (MCP). Simply chat with GPT-4 to compose and send emails - no app switching, no complex interfaces. Just describe what you want to say, and MailMind handles the rest.

**Built at CalHacks 2025** by Miles Wang, Alex Toohey, and Nathan Tran

---

##  Features

- **Natural Language Email Composition** - Tell the AI what you want to say in plain English
- **Context-Aware Conversations** - Build emails across multiple messages; the AI remembers everything
- **Intelligent Reasoning** - GPT-4 understands diverse scenarios: meeting requests, follow-ups, thank-yous, introductions
- **MCP Architecture** - Built on the Model Context Protocol for standardized LLM-tool integration
- **Direct Gmail Integration** - Secure OAuth 2.0 authentication with your Google account

##  Architecture

```
┌─────────────────┐
│  Web Frontend   │  (HTML/CSS/JS - Chat Interface)
└────────┬────────┘
         │
┌────────┴────────┐
│   Flask Host    │  (Backend + OpenAI Integration)
└────────┬────────┘
         │
┌────────┴────────┐
│   MCP Server    │  (Tool Registry + JSON-RPC)
└────────┬────────┘
         │
┌────────┴────────┐
│   Gmail API     │  (Google Workspace)
└─────────────────┘
```

**Tech Stack:**
- Python 3.12 with `uv` package manager
- Flask (web server)
- OpenAI GPT-4o-mini (LLM reasoning)
- Model Context Protocol (tool calling)
- Google Gmail API (email operations)
- OAuth 2.0 (secure authentication)

---

##  Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- OpenAI API key
- Google Cloud Project with Gmail API enabled

### 1. Clone the Repository

```bash
git clone https://github.com/WiseMWang/calhacks2025.git
cd calhacks2025
```

### 2. Install Dependencies

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

### 3. Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-...
```

### 4. Set Up Google OAuth

#### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the **Gmail API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Gmail API"
   - Click "Enable"

#### Step 2: Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Configure consent screen if prompted:
   - User Type: External
   - Add your email as a test user
4. Application type: **Desktop app**
5. Download the JSON file
6. Rename it to `credentials.json` and place it in the project root

**Important:** `credentials.json` contains your OAuth client secret. Never commit this to git!

#### Step 3: First-Time Authentication

The first time you run the app, you'll be prompted to authenticate:

```bash
# This will open your browser for Google login
uv run python server/mcp_server.py
```

Follow the OAuth flow in your browser. This creates a `token.json` file that stores your refresh token for future use.

### 5. Run MailMind

```bash
# Start the Flask server
uv run python host/app.py
```

Open your browser to `http://localhost:5000`

---

##  Usage Examples

**Simple email:**
```
You: Send an email to john@example.com with subject "Meeting Tomorrow"
     and tell him we're meeting at 2pm in the conference room.
```

**Multi-turn conversation:**
```
You: Send an email to the team
AI: Sure! Who should I send it to?
You: team@company.com
AI: Got it. What's the subject?
You: Project Update
AI: And what would you like to say?
You: Tell them the demo went great and thank them for their hard work
AI: [Sends email] ✓ Email sent successfully!
```

**Natural language scenarios:**
```
You: Follow up with Sarah about the proposal we discussed last week
You: Send a thank you email to the CalHacks organizers
You: Invite the team to Friday's demo at 3pm
```

---

##  Project Structure

```
calhacks2025/
├── host/
│   ├── app.py              # Flask backend (OpenAI + MCP integration)
│   ├── templates/
│   │   └── index.html      # Chat interface
│   └── static/
│       ├── styles.css      # Responsive styling
│       └── script.js       # Frontend logic
├── server/
│   ├── mcp_server.py       # MCP protocol implementation
│   ├── tools/
│   │   └── gmail_tools.py  # Gmail API operations
│   └── auth/
│       └── google_oath.py  # OAuth 2.0 flow
├── mcp/                    # MCP SDK (for reference)
├── .env.example            # Environment variable template
├── .gitignore
├── pyproject.toml          # Python dependencies
└── README.md
```

---

##  How It Works

1. **User Input** → Frontend sends message to Flask `/api/chat` endpoint
2. **Conversation Context** → Flask retrieves session history from memory
3. **LLM Reasoning** → GPT-4 receives message + conversation history + available MCP tools
4. **Tool Decision** → LLM decides whether to call `send_email` tool or ask for more info
5. **MCP Execution** → Flask spawns MCP server subprocess, sends JSON-RPC tool call request
6. **Gmail API** → MCP server executes Gmail API call with OAuth credentials
7. **Response** → Result flows back through MCP → Flask → Frontend → User

**Key Innovation:** Session-based conversation memory allows building emails incrementally across multiple messages, creating a natural chat experience.

---

##  Security Notes

- **Never commit** `credentials.json`, `token.json`, or `.env` to git
- The `.gitignore` is configured to exclude these files
- Regenerate OAuth credentials if accidentally exposed
- Use environment variables for all sensitive data

---

##  Known Limitations

- Currently spawns a new MCP server process per request (works for MVP, not optimal for production)
- Conversation history stored in-memory (resets on server restart)
- Only supports sending emails (not reading, searching, or managing)
- Single user session model

---

##  Future Enhancements

### Short-term
- [ ] Google Calendar integration (schedule meetings)
- [ ] Google Sheets integration (data queries)
- [ ] Email reading and search capabilities
- [ ] Email templates for common scenarios

### Production-ready
- [ ] Persistent MCP connection using SDK's `ClientSession`
- [ ] Redis-backed conversation storage
- [ ] Connection pooling for performance
- [ ] Async architecture (Quart/FastAPI)
- [ ] Multi-user authentication
- [ ] Rate limiting and monitoring

### Advanced AI
- [ ] Smart scheduling ("Find a time that works for everyone")
- [ ] Email summarization
- [ ] Action extraction from emails

---

## Contributing

This is a hackathon project, but we welcome improvements! Feel free to:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

##  License

MIT License - feel free to use this project for learning and inspiration!

---

##  Acknowledgments

- Built at **CalHacks 2025**
- Powered by [Anthropic's Model Context Protocol](https://modelcontextprotocol.io/)
- Uses [OpenAI's GPT-4](https://openai.com/)
- Integrates with [Google Gmail API](https://developers.google.com/gmail/api)

---

##  Contact

**Team:**
- Alex Toohey
- Miles Wang 
- Nathan Tran

**Project Link:** [https://devpost.com/software/mailmind-mcp-powered-ai-gmail-assistant-calhacks-fall-25](https://devpost.com/software/mailmind-mcp-powered-ai-gmail-assistant-calhacks-fall-25?ref_content=user-portfolio&ref_feature=in_progress)

