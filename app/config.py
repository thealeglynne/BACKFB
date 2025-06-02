# config.py

import os

# API Keys and Configuration (valores por defecto si no están en ENV)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "5f7dbe7e7ce70029c6cddd738417a3e4132d6e47")
JSON_BIN_ID = os.getenv("JSON_BIN_ID", "682f27e08960c979a59f5afe")
JSON_BIN_API_KEY = os.getenv("JSON_BIN_API_KEY", "$2a$10$AFjAT/OLBCOFkqO83WSIbO9w31.wq.9YRPvSPZoz4xizM66bT3t6S")
CONTEXTO_GLOBAL_FILE = "contexto_global.json"
