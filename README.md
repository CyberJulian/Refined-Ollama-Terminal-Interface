# Terminal AI

Terminal AI is a command-line interface (CLI) application that allows users to interact with AI models locally using the Ollama framework. It provides a rich user experience with features like model management, chat history, and multi-line input, all powered by the `rich` library for enhanced terminal visuals.

## Overview

Terminal AI simplifies the process of interacting with AI models in a terminal environment. Users can pull, remove, and chat with AI models, as well as view and manage past chat sessions. The application is designed to provide a seamless and intuitive experience for AI enthusiasts and developers.

## Features

- **Model Management**:
  - Pull AI models from the Ollama library.
  - Remove locally stored AI models.
  - View available models in a visually appealing table.

- **Chat Interface**:
  - Chat with AI models in real-time.
  - Multi-line input support for detailed queries.
  - Streamed AI responses with live updates.

- **Chat History**:
  - Save chat sessions with custom names.
  - View past chat sessions with timestamps and message previews.
  - Delete unwanted chat sessions.

- **Enhanced Terminal UI**:
  - Styled panels, tables, and markdown rendering using the `rich` library.
  - Real-time loading animations for model operations.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/CyberJulian/Refined-Ollama-Terminal-Interface.git
   cd Refined-Ollama-Terminal-Interface
   ```
2. Set up a Python virtual environment:
   ```bash
   python3 -m venv venv
   # Mac/Linux
   source venv/bin/activate
   # Windows
   venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Ensure the Ollama CLI is installed and configured - Visit [Ollama](https://ollama.com)'s website for installation instructions.

## Usage
1. Run the application:
   ```bash
   python3 TerminalAI.py
   ```
2. Follow the on-screen instructions to:
    - Pull a new AI model.
    - Remove an existing model.
    - View past chat sessions.
    - Start chatting with an AI model.
3. Use the following commands during a chat session:
    - '/multi-start': Enter multi-line input mode.
    - '/multi-end': Exit multi-line input mode.
    - 'exit': Quit current session or return to the main menu.

## Contributing
Please feel free to leave comments, recommendations, and contribute however you feel :)
