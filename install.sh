#!/usr/bin/env bash
set -euo pipefail

# Obsidian RAG — Mac installer
# Requires: macOS, Homebrew

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${GREEN}==>${NC} $*"; }
warn()    { echo -e "${YELLOW}warn:${NC} $*"; }
die()     { echo -e "${RED}error:${NC} $*" >&2; exit 1; }

# ── 1. Homebrew ───────────────────────────────────────────────────────────────
if ! command -v brew &>/dev/null; then
  info "Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
  info "Homebrew already installed"
fi

# ── 2. uv ─────────────────────────────────────────────────────────────────────
if ! command -v uv &>/dev/null; then
  info "Installing uv..."
  brew install uv
else
  info "uv already installed ($(uv --version))"
fi

# ── 3. Ollama ─────────────────────────────────────────────────────────────────
if ! command -v ollama &>/dev/null; then
  info "Installing Ollama..."
  brew install ollama
else
  info "Ollama already installed"
fi

# Start Ollama in background if not running
if ! ollama list &>/dev/null 2>&1; then
  info "Starting Ollama..."
  ollama serve &>/tmp/ollama.log &
  sleep 3
fi

# ── 4. Pull required models ───────────────────────────────────────────────────
info "Pulling embedding model: nomic-embed-text"
ollama pull nomic-embed-text

info "Pulling generation model: gemma3:4b"
ollama pull gemma3:4b

# ── 5. Python dependencies ────────────────────────────────────────────────────
info "Installing Python dependencies..."
uv sync

# ── 6. .env setup ─────────────────────────────────────────────────────────────
if [ ! -f .env ]; then
  info "Creating .env from .env.example..."
  cp .env.example .env
  warn "Edit .env and set OBSIDIAN_RAG_VAULT_PATH to your Obsidian vault path"
else
  info ".env already exists"
fi

# Check vault path is set
VAULT_PATH=$(grep -E '^OBSIDIAN_RAG_VAULT_PATH=' .env | cut -d'=' -f2 | tr -d '"' || true)
if [ -z "$VAULT_PATH" ] || [ "$VAULT_PATH" = "/path/to/your/obsidian/vault" ]; then
  warn "OBSIDIAN_RAG_VAULT_PATH is not set in .env"
  warn "Edit .env, then run: make reindex && make query QUERY=\"your question\""
  exit 0
fi

if [ ! -d "$VAULT_PATH" ]; then
  warn "Vault path does not exist: $VAULT_PATH"
  warn "Check OBSIDIAN_RAG_VAULT_PATH in .env"
  exit 0
fi

# ── 7. Index vault ────────────────────────────────────────────────────────────
info "Indexing vault: $VAULT_PATH"
make reindex

echo ""
echo -e "${GREEN}✓ Installation complete!${NC}"
echo ""
echo "Usage:"
echo "  make query QUERY=\"your question\""
echo "  make query QUERY=\"your question\" --debug   # show timing breakdown"
echo "  make reindex                                 # re-index after vault changes"
