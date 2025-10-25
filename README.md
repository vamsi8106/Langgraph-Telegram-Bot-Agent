# Summit Q&A Assistant

An intelligent Telegram Q&A chatbot designed to assist attendees with information about summits and events. Built with LangGraph, OpenAI, and a sophisticated multi-tiered memory system to provide accurate, context-aware answers about event details, schedules, speakers, venues, and more.

[![Python 3.13+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

Karan Bot is a specialized Q&A assistant that helps summit attendees by answering questions about:
- Event schedules and timings
- Speaker information and sessions
- And more...

The bot uses advanced AI to understand natural language questions and provide accurate, helpful responses based on summit documentation and past interactions.

## 🌟 Key Features

### Intelligent Q&A System
- **Natural Language Understanding** - Ask questions in plain English
- **Context-Aware Responses** - Remembers conversation history for follow-up questions
- **Source Knowledge** - Draws from event documentation
- **Smart Caching** - Instantly retrieves answers to frequently asked questions

### Memory Architecture
- **Short-term Memory (Redis)** - Maintains conversation context during active chats
- **Long-term Memory (Chroma Vector Store)** - Semantic search across all summit information
- **Durable History (PostgreSQL)** - Complete record of all Q&A interactions
- **QA Cache** - Fast retrieval of common questions and answers

### Production Features
- **Multi-User Support** - Handles multiple attendees simultaneously
- **Scalable Architecture** - Built to serve large summit audiences
- **Monitoring & Analytics** - Track popular questions and user engagement
- **Voice Responses** - Text-to-speech via ElevenLabs

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Telegram Bot Setup](#telegram-bot-setup)
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

Edit the `.env` file with your configuration:

```env
# OpenAI (Required)
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini

# Telegram (Required)
TELEGRAM_BOT_TOKEN=your-bot-token-here
TOKEN_BUDGET_RECENT_TURNS=8

# Database (Required)
database_url=postgresql+psycopg://karan1:karan1@localhost:5432/karandb1

# Redis (Required)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_TTL_SECONDS=86400
WINDOW_SIZE=30

# QA Cache (Recommended for fast responses)
QA_CACHE_ENABLED=true
QA_CACHE_TTL_SECONDS=86400

# ElevenLabs (Optional)
ELEVENLABS_API_KEY=your-elevenlabs-key

# Monitoring (Optional)
SERVICE_NAME=karan-bot
ENABLE_PROMETHEUS=true
PROMETHEUS_PORT=9000
ENABLE_JSON_LOGS=true
```

## Database Setup

### Alembic (Schema Migrations)

You can skip Alembic for quick local dev (the app creates tables in `ENV=dev`). For prod/staging, use Alembic.

#### Initialize (first time)

```bash
alembic init alembic   # already present in repo; skip if exists
```

Check `alembic.ini` points to env var `DATABASE_URL` or to your config script.

#### Generate a revision

```bash
alembic revision --autogenerate -m "init tables"
```

#### Apply migrations

```bash
alembic upgrade head
```

> If models change, repeat: update models → `revision --autogenerate` → `upgrade head`.

## Telegram Bot Setup

1. Open **@BotFather** in Telegram.
2. `/start` → `/newbot` → follow prompts → copy **bot token**.
3. Put it in `.env` as `TELEGRAM_BOT_TOKEN`.
4. This project uses **polling** (no webhook needed). Ensure the machine has internet access.

> If you previously used this token elsewhere, stop other instances to avoid "conflict: terminated by other getUpdates request".

## Running the Bot

```bash
# Start the bot
uv run --active karan-bot-telegram
```

You should see:
```
INFO","name":app.telegram","msg":"Starting Telegram polling
```

🎉 **Success!** Open Telegram and ask your bot questions about the summit!

## Testing

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

## Monitoring & Analytics

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

![Karan Bot Monitoring Dashboard](./images/result.png)

The dashboard provides real-time insights into:
- Request rates and throughput
- LLM API call patterns
- Response latency percentiles (P50, P95, P99)
- Memory usage trends


## 📜 Credits

This summit Q&A bot was built based on concepts and architecture patterns from:

**[Mastering LangGraph: The Ultimate Guide](https://theneuralmaze.substack.com/p/mastering-langgraph-the-ultimate)** by The Neural Maze

The tutorial provided foundational knowledge on LangGraph state machines, memory management, and conversational AI patterns that were adapted and extended for this assistance use case.

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
- **[Grafana](https://grafana.com/)** - Realtime Dashboard


### Resources

- LangChain documentation and examples for conversational AI patterns
- Redis caching strategies for high-performance Q&A systems
- Vector database best practices from the Chroma community
- Telegram Bot API documentation and community examples

## 📄 License

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
