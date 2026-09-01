# Full Stack AI Desktop Assistant (Local LLM)

This project demonstrates advanced LLM orchestration by leveraging **Ollama** and the **qwen3:1.7b** model locally. 

The core philosophy of this project is to utilize open-source resources to build powerful, zero-cost AI solutions that run completely on-device, ensuring privacy and blazing-fast performance.

## Prerequisites
- Windows Machine
- GPU with a minimum of 2GB VRAM
- Internet connection (for the initial setup to download dependencies)

## One-Click Setup (New!)

I've completely automated the installation process so you don't have to manually install a dozen dependencies. 

Just double-click **`start.bat`** in the root directory!

The script will automatically:
1. Verify/Install **Node.js**.
2. Verify/Install **Ollama** and automatically pull the `qwen3:1.7b` model.
3. Verify/Install **uv** (the lightning-fast Python package manager).
4. Launch the FastAPI backend and Vite frontend in dedicated windows.
5. Open your default web browser to the application.

> **Note**: For manual setup, you can still run `uv run uvicorn main:app --port 8080` in the `be` directory and `npm run dev` in the `fe/chat-bot` directory.

## Tech Stack 

**Frontend**
- Vite + React + TypeScript 

**Backend**
- Python + FastAPI + SQLite

**AI / LLM**
- Ollama, LangGraph, LangChain

## Features

- **Normal Chat**: Fast, local inference using Qwen3.
- **Desktop Integrations**:
  - View System Information
  - Take a screenshot 
- **Context Summarization**: Manually trigger a summary of the conversation to save context window tokens.
- **Session History (New!)**: Chat histories are stored in a local SQLite database using LangGraph Checkpointers.
- **Auto-Generating Titles (New!)**: When starting a new chat, the local LLM automatically reads your first message and generates a smart 5-word title for the session in the background!

## Design Intentions

- **LangGraph Architecture**: Used LangGraph to establish a robust foundation for state management. This allows seamless integration of SQLite for maintaining chat histories and opens the door for future features like time-travel and long-term memory.
- **Class-Based Backend**: The entire application uses class-based architecture to effectively manage state variables across methods.
- **Local Models**: Ollama models are used exclusively so that there is absolutely $0 cost to run this application on any device.

## Future Integrations

- Interruptable voice chat for a dynamic two-way conversation.
- Speech-to-text integrations.