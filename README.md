# Mistral AI Chatbot

<div align="center">

![Mistral AI Chatbot Logo](https://img.shields.io/badge/Mistral%20AI-Chatbot-4B7BEC?style=for-the-badge&logo=mistral&logoColor=white)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B.svg)](https://streamlit.io/)
[![Mistral AI](https://img.shields.io/badge/Mistral%20AI-API-5c5470.svg)](https://mistral.ai/)

</div>

A comprehensive multi-page chatbot application powered by Mistral AI with advanced features including document processing, context-aware responses, response grading, structured conversation flows, and more.

## ✨ Features

- 🤖 **Interactive Chat Interface**: Clean, user-friendly web interface using Streamlit
- 🧠 **Multiple AI Models**: Support for various Mistral AI models with configurable parameters
- 📚 **Advanced Document Processing**:
  - Document indexing and semantic search
  - Automatic document summarization
  - Keyword extraction for improved context
  - Hierarchical chunking for better structure preservation
- 📝 **Response Grading System**:
  - Evaluate and score responses
  - Customizable grading criteria
  - Template-based evaluation
  - Educational use cases
- 🔄 **Structured Conversation Flows**:
  - Multi-stage conversation structures
  - Stage-specific system prompts
  - Guided user interactions
  - Visual flow editor
- 📊 **Report Generation**:
  - Conversation summaries
  - Document analysis reports
  - Custom report formats
- 💾 **Conversation Management**:
  - Save and load conversations
  - Export and import functionality
  - Search through conversation history
- ⚙️ **Customizable Settings**:
  - Model selection and parameters
  - Document processing options
  - Interface preferences

## 🖼️ Screenshots

<div align="center">
    <p><i>Screenshots will appear here</i></p>
</div>

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Mistral AI API key ([Get one here](https://mistral.ai/))

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

3. **Set your Mistral API key**:
   ```bash
   # On Windows
   set MISTRAL_API_KEY=your_api_key_here

   # On Linux/Mac
   export MISTRAL_API_KEY=your_api_key_here
   ```

### Usage

Start the application:
```bash
streamlit run Home.py
```

The application will open in your default web browser at http://localhost:8501

## 🧩 Project Structure

```
Mistral-Chatbot/
│
├── Home.py                      # Main landing page
│
├── pages/                       # Streamlit pages
│   ├── 1_Chat.py                # Chat interface
│   ├── 2_Document_Index.py      # Document management
│   ├── 3_Settings.py            # App configuration
│   ├── 4_Conversations.py       # Saved conversations
│   ├── 5_Reports.py             # Report generation
│   ├── 6_Response_Grading.py    # Response evaluation
│   └── 7_Conversation_Flows.py  # Conversation structures
│
├── helper_functions.py          # Utility functions
├── index_functions.py           # Document indexing functionality
├── document_processor.py        # Advanced document processing
├── response_grader.py           # Response grading functionality
├── conversation_flow.py         # Conversation flow management
│
├── .streamlit/                  # Streamlit configuration
│   └── config.toml              # UI configuration
│
├── conversation_flows/          # Saved conversation flows
│   └── README.md                # Documentation
│
├── grading_templates/           # Response grading templates
│   └── README.md                # Documentation
│
├── requirements.txt             # Python dependencies
├── LICENSE                      # MIT License
├── .gitignore                   # Git ignore file
└── README.md                    # This file
```

## 📋 Feature Details

### Document Processing

The document processing system extracts text from various file types, generates summaries, identifies keywords, and breaks content into hierarchical chunks for more natural retrieval.

**Supported File Types**:
- Text files (.txt, .md)
- CSV files (.csv)
- JSON files (.json)
- PDF files (.pdf)
- Code files (.py, .js, .html, .css)

### Response Grading

The response grading feature evaluates user responses based on customizable criteria, providing:
- Numerical scores (1-10)
- Qualitative feedback
- Identified strengths and weaknesses
- Suggested improvements

**Use Cases**:
- Educational assessment
- Interview preparation
- Content quality evaluation
- Self-improvement

### Conversation Flows

Conversation flows allow for structured interactions with defined stages, each with specific system prompts and transition rules:

1. **Customer Support Flow**: Guide users through problem identification, troubleshooting, and resolution
2. **Interview Flow**: Structure job interviews with appropriate questions for each phase
3. **Custom Flows**: Create your own flows for specific use cases

## 🌐 Deployment Options

### Local Installation

Follow the installation steps above to run the application locally.

### Streamlit Community Cloud

You can easily deploy this application to Streamlit Community Cloud:

1. Fork this repository to your GitHub account
2. Sign up at [share.streamlit.io](https://share.streamlit.io/)
3. Create a new app pointing to your forked repository
4. Add your Mistral API key to the app's secrets
   - Go to Advanced settings > Secrets
   - Add `MISTRAL_API_KEY = "your_api_key_here"`
5. Deploy the app

### Docker Deployment

A Dockerfile is provided for containerized deployment:

```bash
# Build the Docker image
docker build -t mistral-chatbot .

# Run the container
docker run -p 8501:8501 -e MISTRAL_API_KEY=your_api_key_here mistral-chatbot
```

Access the application at http://localhost:8501

## 💻 Advanced Usage

### Chat Commands

- **Regular chat**: Simply type your message and press Enter
- **Search command**: `search: your query` - Search indexed documents
- **Grade command**: `/grade your response` - Grade a response
- **Flow commands**:
  - `/flow flow_id` - Start a conversation flow
  - `/flow-status` - Show current flow status
  - `/flow-end` - End the current flow

### API Integration

You can integrate this chatbot with your own applications using the Mistral AI API. The code provides examples of:
- Chat completion requests
- Embedding generation
- Structured prompting

### Custom Templates

The application supports several types of templates:
- **Grading templates**: Define criteria for response evaluation
- **Flow templates**: Define structured conversation patterns
- **Report templates**: Define formats for generated reports

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an issue.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.


## 🙏 Acknowledgements

- [Mistral AI](https://mistral.ai/) for their powerful language models
- [Streamlit](https://streamlit.io/) for the interactive web framework
- All open-source contributors and libraries used in this project

## 📧 Contact

For questions, feedback, or support, please [open an issue](https://github.com/koopatroopa787/Mistral-Chatbot/issues) on GitHub.

---

<div align="center">
Made with ❤️ by <a href="https://github.com/koopatroopa787">koopatroopa787</a>
</div>
