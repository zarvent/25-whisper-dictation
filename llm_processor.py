#!/usr/bin/env python3
"""
Procesador de texto usando Perplexity Sonar API
Optimizado para refinamiento de prompts con contexto web
"""

import sys
import os
import logging
from pathlib import Path
import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

# Configurar logging
# Esto creará el directorio 'logs' si no existe.
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'llm.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
# Esto creará el archivo .env si no existe
env_path = Path(__file__).parent / '.env'
if not env_path.exists():
    env_path.touch()
load_dotenv(env_path)

# Configuración
API_KEY = os.getenv("PERPLEXITY_API_KEY")
MODEL = os.getenv("LLM_MODEL", "sonar-pro")
TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

# Cargar prompt del sistema
PROMPTS_DIR = Path(__file__).parent / 'prompts'
try:
    with open(PROMPTS_DIR / 'refine_system.txt', 'r', encoding='utf-8') as f:
        SYSTEM_PROMPT = f.read().strip()
except FileNotFoundError:
    logger.error(f"Error: No se encontró el archivo de prompt en {PROMPTS_DIR / 'refine_system.txt'}")
    sys.exit(1)


class PerplexityProcessor:
    """Procesador usando Perplexity Sonar API"""
    
    def __init__(self):
        self.api_key = API_KEY
        if not self.api_key:
            raise ValueError("La variable de entorno PERPLEXITY_API_KEY no está configurada.")
        self.model = MODEL
        self.temperature = TEMPERATURE
        self.base_url = "https://api.perplexity.ai/chat/completions"
        logger.info(f"Inicializado Perplexity con modelo {self.model}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def refine(self, text: str) -> str:
        logger.info(f"Procesando {len(text)} caracteres con Perplexity")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            "temperature": self.temperature,
            "max_tokens": 2048,
            "search_domain_filter": [],
            "return_citations": False
        }
        
        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()['choices'][0]['message']['content'].strip()
        
        logger.info(f"Resultado: {len(result)} caracteres")
        return result


def main():
    if len(sys.argv) < 2:
        logger.error("No se proporcionó texto de entrada")
        sys.exit(1)
    
    input_text = sys.argv[1]
    
    try:
        processor = PerplexityProcessor()
        refined_text = processor.refine(input_text)
        
        # Imprimir solo el resultado a stdout
        print(refined_text, end='')
        
    except Exception as e:
        logger.exception(f"Error procesando texto: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
