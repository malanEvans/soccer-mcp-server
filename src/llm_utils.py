import json
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader
from openai import AsyncOpenAI

TEMP_MODEL_ID = "meta-llama/Meta-Llama-3.1-70B-Instruct"


async def invoke_llm(
    nebius_api_key: str, prompt_id: str, prompt_args: Dict[str, Any]
) -> Any:
    client = AsyncOpenAI(
        base_url="https://api.studio.nebius.com/v1/",
        api_key=nebius_api_key,
    )

    env = Environment(
        loader=FileSystemLoader(Path(__file__).parents[1] / "prompts"),
    )

    prompt = env.get_template(prompt_id)
    prompt_text = prompt.render(**prompt_args)

    try:
        response = await client.chat.completions.create(
            model=TEMP_MODEL_ID,
            messages=[
                {"role": "user", "content": prompt_text},
                {"role": "assistant", "content": "```json"},
            ],
            temperature=0.0,
            top_p=0.0001,
            max_tokens=256,
        )

        content = response.choices[0].message.content or ""
        content = content.removesuffix("```").strip()

        if not content:
            raise ValueError("Empty response from LLM")

        print(f"LLM response: {content}")

        return json.loads(content)

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse LLM response as JSON: {content}") from e
    finally:
        await client.close()
