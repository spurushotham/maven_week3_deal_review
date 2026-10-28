from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "dataset"
POLICY_DIR = DATASET_DIR / "policies"
CATALOG_PATH = DATASET_DIR / "policy_catalog.json"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2:1b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
POLICY_TOP_K = int(os.getenv("POLICY_TOP_K", "4"))
USE_SEMANTIC_RETRIEVAL = os.getenv("USE_SEMANTIC_RETRIEVAL", "false").lower() == "true"
USE_LLM_ANALYSIS = os.getenv("USE_LLM_ANALYSIS", "false").lower() == "true"
