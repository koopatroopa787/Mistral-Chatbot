# Universal AI Chatbot 🤖

<div align="center">

![Universal AI Chatbot](https://img.shields.io/badge/Universal%20AI-Chatbot-blueviolet?style=for-the-badge)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B.svg)](https://streamlit.io/)

**One unified interface for all your favorite AI models**

Supporting OpenAI • Anthropic Claude • Google Gemini • Mistral AI • MCP Servers

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## 🌟 Overview

Universal AI Chatbot is a comprehensive, multi-model AI assistant that provides a single, elegant interface to interact with multiple AI providers. Switch seamlessly between OpenAI's GPT models, Anthropic's Claude, Google's Gemini, and Mistral AI - all from one application.

### Why Universal AI Chatbot?

- **🎯 Multi-Provider Support**: Use any AI model from OpenAI, Anthropic, Google, or Mistral
- **🔌 MCP Integration**: Connect to Model Context Protocol servers for extended capabilities
- **📚 Document Intelligence**: Index and search documents with semantic understanding
- **💬 Advanced Chat Features**: Real streaming, conversation history, export/import
- **⚙️ Highly Configurable**: Customize every aspect to match your workflow
- **🎨 Modern UI**: Beautiful, responsive interface built with Streamlit

## ✨ Features

### 🎯 Multi-Model AI Support

Switch between AI providers and models on the fly:

- **OpenAI**: GPT-4o, GPT-4 Turbo, GPT-3.5, O1-preview, O1-mini
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Opus, Haiku
- **Google**: Gemini 2.0 Flash, Gemini 1.5 Pro, Flash
- **Mistral AI**: Large, Medium, Small, Codestral

### 🔌 MCP Server Integration

Connect to Model Context Protocol (MCP) servers to extend your AI's capabilities:

- Custom tool integration
- External data source connections
- Real-time health monitoring
- Easy configuration management

### 📚 Document Intelligence

- **Semantic Search**: Find relevant information using natural language
- **Auto-Indexing**: Automatically process and index documents
- **Multiple Formats**: Support for PDF, TXT, MD, CSV, JSON, code files
- **Context-Aware**: AI responses informed by your documents

### 💬 Advanced Conversation Features

- **Real Streaming**: See responses as they're generated
- **Conversation Management**: Save, load, export, and import conversations
- **History Tracking**: Maintain conversation context across sessions
- **Token Usage**: Monitor token consumption in real-time

### ⚙️ Flexible Configuration

- **Per-Provider Settings**: Configure each AI provider independently
- **Custom System Prompts**: Define specialized AI behavior
- **Parameter Tuning**: Adjust temperature, max tokens, and more
- **Persistent Settings**: Your preferences saved across sessions

### 📊 Additional Features

- Response grading and evaluation (from original project)
- Structured conversation flows
- Report generation
- Multi-page interface with intuitive navigation

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- API keys for your preferred AI provider(s):
  - [OpenAI API Key](https://platform.openai.com/api-keys)
  - [Anthropic API Key](https://console.anthropic.com/)
  - [Google AI API Key](https://makersuite.google.com/app/apikey)
  - [Mistral AI API Key](https://console.mistral.ai/)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/koopatroopa787/Mistral-Chatbot.git
   cd Mistral-Chatbot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

4. **Run the application**:
   ```bash
   streamlit run Home.py
   ```

5. **Configure providers**:
   - Open http://localhost:8501 in your browser
   - Configure your AI providers in the sidebar
   - Start chatting!

## 📖 Documentation

### Project Structure

```
Universal-AI-Chatbot/
│
├── Home.py                      # Main landing page
├── app.py                       # Legacy entry point
│
├── src/                         # Source code
│   ├── providers/               # AI provider implementations
│   │   ├── base.py             # Base provider interface
│   │   ├── openai_provider.py # OpenAI integration
│   │   ├── anthropic_provider.py # Anthropic integration
│   │   ├── google_provider.py  # Google Gemini integration
│   │   ├── mistral_provider.py # Mistral AI integration
│   │   └── factory.py          # Provider factory
│   │
│   ├── mcp/                    # MCP server integration
│   │   ├── client.py           # MCP client
│   │   └── manager.py          # MCP manager
│   │
│   ├── config/                 # Configuration management
│   │   └── settings.py         # Settings class
│   │
│   └── utils/                  # Utility functions
│       ├── conversation.py     # Conversation management
│       └── logging_config.py   # Logging setup
│
├── pages/                      # Streamlit pages
│   ├── 1_chat.py              # Main chat interface
│   ├── 2_conversation_flow.py # Conversation flows
│   ├── 3_conversations.py     # Saved conversations
│   ├── 4_document_index.py    # Document management
│   ├── 5_reports.py           # Report generation
│   ├── 6_response_grading.py  # Response evaluation
│   └── 7_settings.py          # App settings
│
├── config/                     # Configuration files
│   ├── settings.json          # App settings
│   ├── settings.example.json  # Example settings
│   ├── mcp_servers.json       # MCP server configs
│   └── mcp_servers.example.json # Example MCP config
│
├── conversations/              # Saved conversations
├── conversation_flows/         # Conversation flow templates
├── grading_template/          # Response grading templates
├── logs/                      # Application logs
│
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

### Configuration

#### Provider Setup

Configure AI providers via the web interface or by editing `config/settings.json`:

```json
{
  "providers": {
    "openai": {
      "name": "openai",
      "api_key": "your-key-here",
      "default_model": "gpt-4o-mini",
      "enabled": true
    }
  }
}
```

#### MCP Server Setup

Configure MCP servers in `config/mcp_servers.json`:

```json
{
  "servers": [
    {
      "name": "my-mcp-server",
      "url": "http://localhost:8080",
      "api_key": null,
      "enabled": true
    }
  ]
}
```

### Usage Examples

#### Basic Chat

1. Navigate to the **Chat** page
2. Select your preferred provider and model
3. Type your message and press Enter
4. Watch the AI respond in real-time (if streaming is enabled)

#### Document Context

1. Go to **Document Index** page
2. Upload documents or index a folder
3. Return to **Chat** page
4. Enable "Use indexed documents" in sidebar
5. Ask questions about your documents

#### Conversation Management

1. Have a conversation in the Chat page
2. Click **Save** in the sidebar to save the conversation
3. Go to **Conversations** page to view/load saved chats
4. Export conversations for backup or sharing

#### Switching Models

You can switch between providers and models at any time:

```
User: What is quantum computing?
[Using GPT-4o]
Assistant: Quantum computing is...

[Switch to Claude 3.5 Sonnet]
User: Can you explain that differently?
[Using Claude 3.5 Sonnet]
Assistant: Let me rephrase that...
```

### Advanced Features

#### MCP Server Integration

Connect to MCP servers to extend capabilities:

1. Configure server in `config/mcp_servers.json`
2. Enable MCP in settings
3. View server status in Chat page
4. Use MCP tools in conversations

#### Custom System Prompts

Define specialized AI behavior:

```
You are an expert Python programmer. When answering questions:
- Provide working code examples
- Explain your reasoning
- Follow PEP 8 style guidelines
```

#### Response Grading

Evaluate responses for educational purposes:

1. Go to **Response Grading** page
2. Configure grading criteria
3. Use `/grade` command in chat
4. Receive detailed feedback

## 🔧 Development

### Adding a New Provider

1. Create a new provider class in `src/providers/`:

```python
from .base import BaseProvider, Message, ChatResponse

class CustomProvider(BaseProvider):
    def get_available_models(self):
        return ["model-1", "model-2"]

    def chat(self, messages, model, **kwargs):
        # Implementation
        pass

    def stream_chat(self, messages, model, **kwargs):
        # Implementation
        pass
```

2. Register in `src/providers/factory.py`:

```python
from .custom_provider import CustomProvider

class ProviderFactory:
    _providers = {
        # ...
        "custom": CustomProvider,
    }
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

### Code Style

This project follows PEP 8 style guidelines. Format code with:

```bash
pip install black isort
black .
isort .
```

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Run tests**: `pytest tests/`
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

Please read [contribute.md](contribute.md) for details on our code of conduct and development process.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [OpenAI](https://openai.com/) - GPT models
- [Anthropic](https://www.anthropic.com/) - Claude models
- [Google AI](https://ai.google/) - Gemini models
- [Mistral AI](https://mistral.ai/) - Mistral models
- [Streamlit](https://streamlit.io/) - Web framework
- All open-source contributors and libraries

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/koopatroopa787/Mistral-Chatbot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/koopatroopa787/Mistral-Chatbot/discussions)
- **Email**: Open an issue for support questions

## 🗺️ Roadmap

### Upcoming Features

- [ ] More AI providers (Cohere, AI21, etc.)
- [ ] Voice input/output support
- [ ] Image generation integration
- [ ] Plugin system for custom extensions
- [ ] Multi-user support
- [ ] Cloud deployment templates
- [ ] Mobile-responsive design improvements
- [ ] Conversation analytics dashboard

## 📊 Version History

### Version 2.0.0 (Current)

Major rewrite with multi-provider support:

- ✨ Support for OpenAI, Anthropic, Google, and Mistral
- 🔌 MCP server integration
- 💾 Enhanced conversation management
- 🎨 Modern, redesigned UI
- 🔧 Improved configuration system
- 📊 Real streaming support
- 🏗️ Modular architecture

### Version 1.0.0

Initial release:

- Basic Mistral AI chatbot
- Document indexing
- Response grading
- Conversation flows

---

<div align="center">

**Made with ❤️ by [koopatroopa787](https://github.com/koopatroopa787)**

⭐ Star this repo if you find it useful!

[Report Bug](https://github.com/koopatroopa787/Mistral-Chatbot/issues) •
[Request Feature](https://github.com/koopatroopa787/Mistral-Chatbot/issues)

</div>
