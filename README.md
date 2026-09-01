# Local LLM Demonstration 

```
This project is to demonstrate my LLM orchestration skills by leveraging ollama and qwen3:1.7b parameter model. 

The main motto of this project is to make use of open source resources and build AI solutions that works fast and delivers large.

```
## Prerequisites
- Windows Machine
- GPU with minimum of 2GB VRAM
- Ollama desktop
- Internet connection on UV sync

## Setup 

- Pull this build and always create a branch from master
- Run uv sync
- Post this you don't need internet 
- Run the main.py file using `uv run python be/main.py`
- Run `cd fe`
- Run `npm install`
- Run `npm run dev`
- This should start the frontend and backend 


## Stacks 

**frontend**
- Vite + React + TypeScript 

**backend**
- Python + FastAPI

**LLM**
- ollama, LangGraph

## Functionalities

This is a chatbot that has the following features

- Normal Chat
- View System Information
- Take a screenshot 
- Summarize context

## Design Intentions

- Used LangGraph even though there weren't any explicit usecase for the graphs, I will use LangGraph so that I can integrate a database and maintain chat histories. I can make use of the time travel and long term memory features in the future
- Entire application will be using class based code. The intention is to use the state variables across methods. 
- ollama models are used so that there is 0 cost on any device

## Future Integrations

- Will be conducting a research on interruptable voice chat to have a too and fro conversation
- Will also look into speech to text integrations