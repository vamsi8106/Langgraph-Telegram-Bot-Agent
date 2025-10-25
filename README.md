# Karan Bot - Summit Q&A Assistant

An intelligent Telegram Q&A chatbot designed to assist attendees with information about summits and events. Built with LangGraph, OpenAI, and a sophisticated multi-tiered memory system to provide accurate, context-aware answers about event details, schedules, speakers, venues, and more.

[![Python 3.13+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Karan Bot is a specialized Q&A assistant that helps summit attendees by answering questions about:
- Event schedules and timingsSpeaker information and sessions etc ..

The bot uses advanced AI to understand natural language questions and provide accurate, helpful responses based on summit documentation and past interactions.

## Key Features

### Intelligent Q&A System
- **Natural Language Understanding** - Ask questions in plain English
- **Context-Aware Responses** - Remembers conversation history for follow-up questions
- **Multi-Source Knowledge** - Draws from event documentation, schedules, and FAQs
- **Smart Caching** - Instantly retrieves answers to frequently asked questions

### Memory Architecture
- **Short-term Memory (Redis)** - Maintains conversation context during active chats
- **Long-term Memory (Chroma Vector Store)** - Semantic search across all summit information
- **Durable History (PostgreSQL)** - Complete record of all Q&A interactions
- **QA Cache** - Fast retrieval of common questions and answers

### Features
- **Multi-User Support** - Handles multiple attendees simultaneously
- **Scalable Architecture** - Built to serve large summit audiences
- **Monitoring & Analytics** - Track popular questions and user engagement
- **Voice Responses** - Optional text-to-speech via ElevenLabs

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Running the Bot](#running-the-bot)
- [Testing](#testing)
- [Monitoring & Analytics](#monitoring--analytics)
- [Credits](#credits)
- [License](#license)

## Prerequisites

### Required Software
- **Python 3.13+** (tested with `uv` package manager)
- **Redis ≥ 6.0** (for caching and session management)
- **PostgreSQL ≥ 14** (for conversation history)
- **Git** (for version control)

### Required API Keys
- **OpenAI API Key** - For natural language understanding ([Get one here](https://platform.openai.com/api-keys))
- **Telegram Bot Token** - From [@BotFather](https://t.me/botfather) to create your bot
- **ElevenLabs API Key** - For voice responses ([Sign up here](https://elevenlabs.io/))

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/vamsi8106/Langgraph-Telegram-Bot-Agent.git
cd Langgraph-Telegram-Bot-Agent
```

### 2. Set Up Python Environment

Using `uv` (recommended):
```bash
# Install uv if you haven't already
pip install uv

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv sync
```

Or using standard `venv`:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -U pip
pip install -e .
```

### 3. Start Required Services

#### Option A: Using Docker

#### Option B: Local Installation

**Redis:**
```bash

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server
```
**PostgreSQL:**
```bash

# Ubuntu/Debian
sudo apt-get install postgresql-14
sudo systemctl start postgresql

# Create database and user
createuser karan1 --pwprompt  # Enter password: karan1
createdb -O karan1 karandb1
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

**Minimal required configuration:**
```env
# OpenAI (Required)
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini

# Telegram (Required)
TOKEN_BUDGET_RECENT_TURNS=8
TELEGRAM_BOT_TOKEN=your-bot-token-here

# Database (Required)
database_url=postgresql+psycopg://karan1:karan1@localhost:5432/karandb1

# Redis (Required)
redis_host=localhost
redis_port=6379

# QA Cache (Recommended for fast responses)
QA_CACHE_ENABLED=true
QA_CACHE_TTL_SECONDS=21600

ELEVENLABS_API_KEY=your-elevenlabs-key
TELEGRAM_BOT_TOKEN=your-bot-token
SERVICE_NAME=karan-bot
ENABLE_PROMETHEUS=true
PROMETHEUS_PORT=9000
ENABLE_JSON_LOGS=true
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_TTL_SECONDS=86400
WINDOW_SIZE=30
QA_CACHE_ENABLED=true
QA_CACHE_TTL_SECONDS=86400

```

### 5. Initialize Database

```bash
# Run database migrations
alembic upgrade head
```

### 6. Run the Bot

```bash
# Start the bot
uv run --active karan-bot-telegram
```

You should see:
```
INFO","name":app.telegram","msg":"Starting Telegram polling
```

🎉 **Success!** Open Telegram and ask your bot questions about the summit!

```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

```

### Test Categories

- **Unit Tests** - Individual component testing
- **Integration Tests** - End-to-end Q&A workflows

## 📊 Monitoring & Analytics

### Setup

Navigate to the monitoring directory and start the services:

```bash
cd monitoring
docker-compose up -d
```

This initializes Grafana and Prometheus for observability.

### Performance Metrics

You can view raw metrics at:

**Prometheus:** `http://localhost:9090`  
**Application Metrics:** `http://localhost:9000/metrics`

**Key metrics tracked:**
- **RPS** (Requests Per Second)
- **LLM Calls** (OpenAI API invocations)
- **P95 Latency** (95th percentile response time)
- **Process Memory** (Memory consumption)

### Real-time Dashboard

Access Grafana at `http://localhost:3000`

**Loading the Dashboard:**
1. Login to Grafana (default: admin/admin)
2. Go to Dashboards → Import
3. Upload the dashboard file: `monitoring/grafana/dashboards/karan_bot_overview.json`
4. Select Prometheus as the data source
5. Click Import

**After setup, the dashboard will display:**

![Karan Bot Monitoring Dashboard](./docs/images/dashboard_preview.png)


## 📜 Credits

This summit Q&A bot was built based on concepts and architecture patterns from:

**[Mastering LangGraph: The Ultimate Guide](https://theneuralmaze.substack.com/p/mastering-langgraph-the-ultimate)** by The Neural Maze

The tutorial provided foundational knowledge on LangGraph state machines, memory management, and conversational AI patterns that were adapted and extended for this summit assistance use case.


### Technologies & Frameworks

- **[LangGraph](https://github.com/langchain-ai/langgraph)** - State machine framework for conversational AI
- **[LangChain](https://github.com/langchain-ai/langchain)** - LLM application framework
- **[OpenAI](https://platform.openai.com/)** - GPT models for natural language understanding
- **[Python Telegram Bot](https://python-telegram-bot.org/)** - Telegram bot framework
- **[ChromaDB](https://www.trychroma.com/)** - Vector database for semantic search
- **[Redis](https://redis.io/)** - In-memory caching and session storage
- **[PostgreSQL](https://www.postgresql.org/)** - Conversation history and analytics
- **[ElevenLabs](https://elevenlabs.io/)** - Text-to-speech for voice responses
- **[Prometheus](https://prometheus.io/)** - Metrics and monitoring
- **[OpenTelemetry](https://opentelemetry.io/)** - Distributed tracing

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Resources

- LangChain documentation and examples for conversational AI patterns
- Redis caching strategies for high-performance Q&A systems
- Vector database best practices from the Chroma community
- Telegram Bot API documentation and community examples

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Karan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## 🤝 Contributing

Contributions are welcome! If you'd like to improve the bot:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Areas for Contribution

- Additional language support
- New document format parsers
- Enhanced analytics dashboards
- Performance optimizations
- Better error handling
- UI improvements for reports
- Integration with event platforms (Eventbrite, Hopin, etc.)

---

**Built with ❤️ to help make summit experiences better for everyone**

For questions, issues, or feature requests about this bot, please [open an issue](https://github.com/yourusername/karan-bot/issues).

**Found this helpful? ⭐ Star the repo and share with other event organizers!**
