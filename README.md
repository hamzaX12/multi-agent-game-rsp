# Rock-Paper-Scissors Multi-Agent System

A Docker-based multi-agent simulation where three autonomous agents play Rock-Paper-Scissors, managed by a central Evaluator agent using the ejabberd XMPP server.

## Features
* **4 Agents:** 1 Evaluator (Referee) and 3 Players.
* **Game Logic:** 3-Way Rock-Paper-Scissors logic (including draw handling).
* **Protocol:** XMPP (Extensible Messaging and Presence Protocol) via `slixmpp`.
* **Infrastructure:** Fully containerized using Docker and Docker Compose.

## Prerequisites

- Docker
- Docker Compose
- Python 3.x (for the setup script)

## Getting Started

Follow these steps to set up and run the simulation:

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd <repository-folder>
