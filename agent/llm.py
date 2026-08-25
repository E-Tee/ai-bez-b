"""Клиент LLM: роль -> список моделей, упала одна — берём следующую."""
import os
import logging
from openai import OpenAI
from agent.budget import spend

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Проверка обязательных переменных окружения
def _check_env():
    required = ["SERVERSPACE_BASE_URL", "SERVERSPACE_API_KEY"]
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        raise RuntimeError(f"Отсутствуют обязательные переменные окружения: {', '.join(missing)}")
    logger.info("Все обязательные переменные окружения найдены")

_check_env()

client = OpenAI(
    base_url=os.getenv("SERVERSPACE_BASE_URL"),
    api_key=os.getenv("SERVERSPACE_API_KEY"),
)

# Точные ID моделей проверь в панели! Если "model not found" —
# подставь имена ровно как в их доке.
ROLES = {
    "planner": ["qwen/qwen3-next-80b-a3b-thinking", "deepseek/deepseek-v4-flash"],
    "writer": ["moonshotai/kimi-k2.7-code", "deepseek/deepseek-v4-flash"],
    "critic": ["deepseek/deepseek-v4-flash"],
    "editor": ["deepseek/deepseek-v4-flash", "qwen/qwen3-next-80b-a3b-thinking"],
}


def ask(role, prompt, system=""):
    for model in ROLES[role]:
        try:
            r = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            )
            spend(model, r.usage.prompt_tokens, r.usage.completion_tokens)
            logger.info(f"[llm] ответил: {model}")
            return r.choices[0].message.content
        except Exception as e:
            logger.warning(f"[llm] {model} не вывез: {e}")
    raise RuntimeError("Все модели легли. Проверь ключ, base_url и интернет.")