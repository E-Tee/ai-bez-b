"""Клиент LLM: роль -> список моделей, упала одна — берём следующую."""
import os
from openai import OpenAI
from agent.budget import spend

client = OpenAI(
    base_url=os.getenv("SERVERSPACE_BASE_URL"),
    api_key=os.getenv("SERVERSPACE_API_KEY"),
)

# Точные ID моделей проверь в панели! Если "model not found" —
# подставь имена ровно как в их доке.
ROLES = {
    "planner": ["deepseek/deepseek-v4-flash", "gpt-5.4-mini"],
    "writer": ["deepseek/deepseek-v3.2", "deepseek/deepseek-v4-flash"],
    "critic": ["deepseek/deepseek-v4-flash", "gpt-5.4-mini"],
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
            return r.choices[0].message.content
        except Exception as e:
            print(f"[llm] {model} не вывез: {e}")
    raise RuntimeError("Все модели легли. Проверь ключ, base_url и интернет.")