# Actra

**macOS computer-use AI agent** — understands your goals, plans the actions, executes them on your Mac, and verifies the results.

## Quick Start

### Prerequisites

- macOS with Python 3.12+
- Gemini API key

### Setup

```bash
# Clone and enter
cd Actra

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install
pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your GEMINI_API_KEY
```

### Grant macOS Permissions

Actra needs these permissions in **System Settings → Privacy & Security**:

1. **Accessibility** — for UI automation and inspection
2. **Screen Recording** — for screenshots (grant to your Terminal app)

### Run

```bash
# Single command
actra "Open Safari and search for iQOO 15"

# Interactive mode
actra --interactive
```

## Architecture

```
User Goal → Planner → Tool Selection → macOS Execution → Observation → Verification
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for details.

## Project Status

**Phase 1** — Laptop-only prototype on macOS.
