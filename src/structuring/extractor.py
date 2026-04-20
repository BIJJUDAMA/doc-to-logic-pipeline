"""
File description: LLM-based intent extraction logic
Purpose: Interfaces with LLM providers (OpenAI or Gemini) to parse structural intents from text chunks
How it works: Loads a prompt template, sets up clients based on API keys, and requests model completions to extract intent data as JSON
"""
import os
import json
import time
import google.generativeai as genai
import openai
from src.structuring.config import GEMINI_API_KEY, MODEL_NAME, OPENAI_API_KEY, OPENAI_MODEL, MAX_TOKENS


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
            return data.get("structuring", {}).get("prompt", "")
    except Exception as e:
        print(f"Error loading prompt: {e}")
        return ""

PROMPT = load_prompt()

def extract_intents(text):
    # Invokes the configured LLM API to extract intents from the input text
    try:
        if OPENAI_API_KEY:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": PROMPT},
                    {"role": "user", "content": text}
                ],
                max_tokens=MAX_TOKENS
            )
            resp_text = response.choices[0].message.content

        else:
            time.sleep(1)
            response = model.generate_content(
                PROMPT + text,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=MAX_TOKENS
                )
            )
            resp_text = response.text.strip()
        
        print(f"--- LLM Response ---:\n{resp_text}\n--------------------")
        

        # Clean the Markdown output for JSON parsing
        if resp_text.startswith("```json"):
            resp_text = resp_text.split("```json")[1].split("```")[0].strip()
        elif resp_text.startswith("```"):
            resp_text = resp_text.split("```")[1].split("```")[0].strip()
            
        return json.loads(resp_text)
    except Exception as e:
        print(f"Error during intent extraction: {e}")

        # Fallback object creation on failed extraction
        raw_resp = ""
        try:
            raw_resp = response.text
        except:
            raw_resp = str(e)
        return {"intent": "parse_error", "raw": raw_resp}
