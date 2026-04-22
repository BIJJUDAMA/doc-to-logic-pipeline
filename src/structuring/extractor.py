"""
File description: LLM-based intent extraction logic
Purpose: Interfaces with LLM providers (OpenAI or Gemini) to parse structural intents from text chunks
How it works: Loads a prompt template, sets up clients based on API keys, and requests model completions to extract intent data as JSON
"""
import os
import json
import time
import re
import google.generativeai as genai
import openai
from src.structuring.config import GEMINI_API_KEY, MODEL_NAME, OPENAI_API_KEY, OPENAI_MODEL, MAX_TOKENS, ENABLE_REASONING, INTENT_EXTRACTION_MODE
from .cleaner import clean_text_content


# Set up the LLM client (OpenAI or Gemini) based on environment availability
if OPENAI_API_KEY:
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENAI_API_KEY
    )
    MODEL_NAME = OPENAI_MODEL or "mistralai/mistral-7b-instruct" 
elif GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)

def load_prompt():
    # Reads the structuring instructions from the local JSON file
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts.json")
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            mode_key = "intent_extraction" if INTENT_EXTRACTION_MODE else "zero_schema"
            return data.get(mode_key, {})
    except Exception as e:
        print(f"Error loading prompt: {e}")
        return {}

PROMPT_DATA = load_prompt()

def extract_intents(text, prompt_idx=None):
    # Select the correct prompt version (prompt_1, prompt_2, etc.)
    # If prompt_idx is None, default to prompt_1
    idx = 1 if prompt_idx is None else prompt_idx + 1
    prompt_key = f"prompt_{idx}"
    
    # Fallback to prompt_1 if the specific prompt_n key doesn't exist
    current_prompt = PROMPT_DATA.get(prompt_key, PROMPT_DATA.get("prompt_1", ""))

    # Invokes the configured LLM API to extract intents from the input text
    try:
        if OPENAI_API_KEY:
            # We use extra_body to pass OpenRouter-specific parameters like 'reasoning'
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": current_prompt},
                    {"role": "user", "content": text}
                ],
                max_tokens=MAX_TOKENS,
                extra_body={"reasoning": {"enabled": True}} if ENABLE_REASONING else {}
            )
            resp_text = response.choices[0].message.content

        else:
            time.sleep(1)
            response = model.generate_content(
                current_prompt + "\n\nTEXT TO ANALYZE:\n" + text,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=MAX_TOKENS
                )
            )
            resp_text = response.text.strip()
        
        print(f"--- LLM Response ---:\n{resp_text}\n--------------------")
        
        # 1. Safely strip out reasoning <think>...</think> tags if the model returned them inline
        resp_text = re.sub(r'<think>.*?</think>', '', resp_text, flags=re.DOTALL).strip()

        if not INTENT_EXTRACTION_MODE:
            resp_text = clean_text_content(resp_text)
        else:
            # 2. Strict Mode: Strip markdown code fences
            fence_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', resp_text)
            if fence_match:
                resp_text = fence_match.group(1).strip()
            else:
                # 3. Fallback: find the first JSON object or array in the raw response
                json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', resp_text)
                if json_match:
                    resp_text = json_match.group(1).strip()

        return json.loads(resp_text)
    except Exception as e:
        print(f"Error during intent extraction: {e}")

        # Fallback object creation on failed extraction
        raw_resp = ""
        try:
            raw_resp = resp_text if 'resp_text' in dir() else response.text
        except:
            raw_resp = str(e)
        print(f"Parse failed. Raw response was:\n{raw_resp}")
        return {"intent": "parse_error", "raw": raw_resp}
