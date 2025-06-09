---
title: Soccer MCP Server
sdk: gradio
sdk_version: 5.33.0
app_file: soccer_mcp_server.py
pinned: true
emoji: ⚽
python_version: 3.12
tags:
- mcp-server-track
---

# Soccer MCP Server

A Python-based server for managing soccer-related data and operations.

## Getting Started

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd soccer-mcp-server
   ```

2. Create and activate a virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install the package in development mode:
   ```bash
   uv pip install -e ".[dev]"
   ```


## Development

### Running Tests

```bash
uv run pytest
```

### Code Formatting

```bash
uv run black .
uv run isort .
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
