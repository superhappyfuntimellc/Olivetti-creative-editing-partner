import json

def generate_json(*, model: str, instructions: str, payload: str, max_output_tokens: int = 700) -> dict:
    resp = client.responses.create(
        model=model,
        instructions=instructions,
        input=payload,
        max_output_tokens=max_output_tokens,
    )
    text = (resp.output_text or "").strip()
    # best-effort JSON parse
    try:
        return json.loads(text)
    except Exception:
        # fallback: try to locate first/last braces
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start:end+1])
        raise
