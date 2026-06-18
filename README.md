# 🧠 NeEvo — Next Evolution

> **An AI-powered desktop assistant that combines conversational AI with autonomous task execution.**

NeEvo is a Python-based desktop AI assistant that combines **LLM-powered conversations** with **intelligent multi-agent automation**. It allows users to chat naturally with an AI while also delegating real-world tasks such as sending emails, searching the web, and scheduling reminders.

Unlike traditional chatbots, NeEvo features an orchestration layer that analyzes user intent, routes requests to specialized agents, and executes actions automatically.

---

## ✨ Features

### 💬 Chat Mode

Interact naturally with the AI for:

* General conversations
* Questions & answers
* Brainstorming
* Coding assistance
* Explanations
* Problem solving

Powered by **Llama-3 (Groq API)** for fast and intelligent responses.

---

### 🤖 Agent Mode

Agent Mode enables NeEvo to perform real-world tasks on your behalf.

The LLM analyzes your request, determines the required action, and delegates it to the appropriate automation agent.

Example:

> "Email John that I'll be 15 minutes late tomorrow."

↓

* Intent Detection
* Email Agent Selected
* Email Generated
* Email Sent Automatically

---

## 🤖 Available Agents

### 📧 Email Agent

Automates Gmail interactions using natural language.

**Capabilities**

* Compose professional emails
* Send emails automatically
* Format email content
* Understand recipients and message intent

Example:

> "Send an email to Sarah thanking her for today's meeting."

---

### ⏰ Reminder Agent

Keeps track of scheduled reminders using a persistent local database.

**Capabilities**

* Create reminders
* Store reminders in SQLite
* Monitor upcoming reminders
* Notify users at scheduled times

Example:

> "Remind me to submit my report tomorrow at 9 AM."

---

### 🌐 Web Search Agent

Retrieves live information from the internet.

**Capabilities**

* Search the web
* Fetch current information
* Retrieve weather updates
* Answer real-time questions

Example:

> "What's the weather in Berlin today?"

---

## 🧠 How It Works

```
              User
                │
                ▼
        Tkinter Desktop UI
                │
                ▼
      LLM Intent Orchestrator
       (Llama-3 via Groq API)
                │
     ┌──────────┼───────────┐
     ▼          ▼           ▼
 Email Agent Reminder Agent Web Agent
     │          │           │
     └──────────┼───────────┘
                ▼
          SQLite Database
                │
                ▼
      Background Daemon Thread
```

The background engine continuously monitors scheduled reminders while allowing the UI to remain responsive.

---

## 🚀 Core Features

* 🧠 Intelligent LLM-powered task routing
* 💬 Dedicated Chat Mode
* 🤖 Autonomous Agent Mode
* 📧 Gmail email automation
* 🌐 Live web search and weather retrieval
* ⏰ Persistent reminder scheduling
* 🗄 SQLite-based local storage
* ⚡ Asynchronous background execution
* 🖥 Clean Tkinter desktop interface

---

## 🛠 Tech Stack

| Component        | Technology       |
| ---------------- | ---------------- |
| Language         | Python 3.11+     |
| LLM              | Llama-3          |
| API Provider     | Groq             |
| GUI              | Tkinter          |
| Database         | SQLite3          |
| Background Tasks | Python Threading |
| Environment      | python-dotenv    |

---

## 📂 Project Structure

neevo_ai_assistant/
│
├── core/
│   └── database.py          # Local SQLite database & state manager
│
├── tools/
│   ├── gmail_tool.py        # Email orchestration agent
│   ├── weather_tool.py      # Weather API & search agent
│   └── reminder_tool.py     # Local trigger & reminder tool
│
├── .env                     # Private API keys & passwords (Hidden from Git)
├── .gitignore               # Tells Git which files to ignore (.env, venv, caches)
├── config.py                # Secure configuration bridge to load environment variables
├── main.py                  # Project entry point & Tkinter Desktop interface
├── orchestrator.py          # AI Brain / Multi-agent router (Llama-3 integration)
├── README.md                # Main repository documentation page
└── requirements.txt         # List of required Python dependencies

## ⚙ Installation

Clone the repository

```bash
git clone https://github.com/Danish-ctrl/neevo_ai_assitant.git
cd neevo_ai_assitant
```

Create a virtual environment

```bash
python -m venv venv
```

Activate it

**Windows**

```bash
venv\Scripts\activate
```

**Linux / macOS**

```bash
source venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root.

Example:

```env
GROQ_API_KEY=your_api_key
EMAIL_ADDRESS=your_email
EMAIL_PASSWORD=your_app_password
WEATHER_API_KEY=your_api_key
```

Run the application

```bash
python main.py
```

---

### Chat Mode

> <img width="1912" height="1027" alt="image" src="https://github.com/user-attachments/assets/7b8d2a91-7b63-4bac-884a-c8c716db6b0d" />

> <img width="1913" height="1027" alt="image" src="https://github.com/user-attachments/assets/32cdacb5-06fe-44f6-8f09-8b6c27f6060c" />
 

### Agent Mode

> <img width="1921" height="1039" alt="image" src="https://github.com/user-attachments/assets/3b72737b-88ae-4f90-9245-7577a577f9e3" />


## 🔮 Planned Features

* Voice interaction
* Local AI model support
* Calendar integration
* File management agent
* Multi-step task execution
* Plugin architecture
* Additional automation agents

---

## 🤝 Contributing

Contributions, ideas, and feature requests are welcome.

Feel free to fork the repository, open an issue, or submit a pull request.

---

## 📄 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

**Danish**

GitHub: https://github.com/Danish-ctrl
