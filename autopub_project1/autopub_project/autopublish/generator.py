import os
import openai
import cohere
from typing import List, Dict

# ---------- Load API Keys ---------- #
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
USE_COHERE = os.getenv("USE_COHERE", "false").lower() in ("1", "true", "yes")

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

co = None
if COHERE_API_KEY:
    co = cohere.Client(COHERE_API_KEY)


# ---------- Prompt Builder ---------- #
def build_prompt(
    keyword: str,
    serp_results: List[Dict],
    competitor_content: str,
    word_count: int = 900,
) -> str:
    competitor_snippets = "\n\n".join(
        [
            f"- {r.get('title','')} ({r.get('link','')})\n  snippet: {r.get('snippet','')}"
            for r in serp_results
        ]
    )
    return f"""
You are an SEO expert. Generate a detailed blog post about: "{keyword}".

Return the result as JSON with these fields ONLY:
{{
  "meta_title": "string (<=60 chars, must contain keyword)",
  "meta_description": "string (<=160 chars, must contain keyword)",
  "title": "string (H1 blog post title, must contain keyword)",
  "body_markdown": "Full blog post body in MARKDOWN (without meta title, description, or table of contents). Use H2/H3, keyword density 2–3%, short paragraphs, bullet lists, and a clear conclusion with a call-to-action."
}}

Requirements:
- Target keyword: "{keyword}" (use in H1, at least one H2, first 100 words, and naturally 2–3% density).
- Do NOT include table of contents, suggested slug, or meta fields inside the body.
- Suggested word count: {word_count}.

Competitor SERP snippets:
{competitor_snippets}

Additional competitor page content (summarized, do not copy directly):
{competitor_content}
""".strip()


# ---------- OpenAI ---------- #
def generate_content_openai(prompt: str, max_tokens: int = 1800, temperature: float = 0.7) -> str:
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp["choices"][0]["message"]["content"].strip()


# ---------- Cohere ---------- #
def generate_content_cohere(prompt: str, temperature: float = 0.7) -> str:
    try:
        if not COHERE_API_KEY:
            return "Error: Cohere API key not found."

        response = co.chat(
            model="command-r-plus-08-2024",
            message=prompt,
            temperature=temperature,
        )
        return response.text.strip() if hasattr(response, "text") else "Error: No content generated"
    except Exception as e:
        return f"Error: {str(e)}"


# ---------- Main entry point ---------- #
def generate_article(
    keyword: str, serp_results: List[Dict], competitor_content: str, word_count: int = 900
) -> str:
    """Main entry point for content generation (chooses OpenAI or Cohere)."""
    prompt = build_prompt(keyword, serp_results, competitor_content, word_count)

    if USE_COHERE and co:
        return generate_content_cohere(prompt)
    elif OPENAI_API_KEY:
        return generate_content_openai(prompt)
    else:
        return "Error: No content generation API configured. Set OPENAI_API_KEY or COHERE_API_KEY."
