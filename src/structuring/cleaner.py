"""
File description: Core logic for cleaning and repairing LLM-generated JSON content
Purpose: Provides reusable functions to fix common structural errors and truncation in LLM outputs.
"""
import re
import json

def repair_json(json_str):
    
    # Attempts to repair common JSON malformations and handles truncation by iteratively backtracking until a valid JSON state is found.
    
    # 1. Base fixes for adjacent blocks and trailing commas
    json_str = re.sub(r'\}\s*\{', '},{', json_str)
    json_str = re.sub(r'\]\s*\[', '],[', json_str)
    json_str = re.sub(r',\s*([\}\]])', r'\1', json_str)

    def try_close_json(s):
        # Helper to close all open brackets and strings in a string
        stack = []
        is_string = False
        escape = False
        for char in s:
            if is_string:
                if escape:
                    escape = False
                elif char == '\\':
                    escape = True
                elif char == '"':
                    is_string = False
                    stack.pop()
            else:
                if char == '"':
                    is_string = True
                    stack.append('"')
                elif char == '{':
                    stack.append('{')
                elif char == '[':
                    stack.append('[')
                elif char == '}':
                    if stack and stack[-1] == '{':
                        stack.pop()
                elif char == ']':
                    if stack and stack[-1] == '[':
                        stack.pop()
        
        res = s
        if stack:
            # If we ended inside a string, close the string
            if is_string:
                res += '"'
                stack.pop()
            # Close remaining structures in reverse order
            while stack:
                opener = stack.pop()
                res += '}' if opener == '{' else ']'
        return res

    # 2. Iterative backtracking to handle mid-key or mid-value truncation
    current_attempt = json_str
    last_error = None
    
    # We attempt up to 500 characters of backtracking (safety limit)
    attempts = 0
    while len(current_attempt) > 0 and attempts < 1000:
        attempts += 1
        candidate = try_close_json(current_attempt)
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError as e:
            last_error = e
            # Logic: Remove the last character and try again.
            # Optimization: Peel back to the last "structural" character (comma, brace, bracket, colon, or quote)
            match = re.search(r'(.*)[,:{}\[\]"]', current_attempt, re.DOTALL)
            if match:
                # Remove one character to force progress past the current marker
                current_attempt = match.group(1).rstrip()
                if not current_attempt:
                    break
            else:
                current_attempt = current_attempt[:-1].rstrip()

    return json_str # Final fallback

def clean_text_content(text):
   
    # Normalizes a string into valid JSON by removing reasoning tags, markdown fences, and fixing common structural errors.
    
    if not text:
        return ""

    # 1. Strip reasoning tags
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

    # 2. Extract content from markdown code fences
    fence_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text, re.IGNORECASE)
    if fence_match:
        text = fence_match.group(1).strip()
    
    # 3. Handle common prefix text
    text = re.sub(r'^(?:json|output|result|data):\s*', '', text, flags=re.IGNORECASE | re.MULTILINE)

    # 4. Find the first JSON-like start
    start_idx_brace = text.find('{')
    start_idx_bracket = text.find('[')
    
    start_idx = -1
    if start_idx_brace != -1 and start_idx_bracket != -1:
        start_idx = min(start_idx_brace, start_idx_bracket)
    else:
        start_idx = max(start_idx_brace, start_idx_bracket)
        
    if start_idx == -1:
        return text

    # Extract from start_idx to the end, then repair
    candidate = text[start_idx:].strip()

    # 5. Apply repairs (handles truncation, missing commas, etc.)
    candidate = repair_json(candidate)

    # 6. Final attempt to wrap loose object sequences
    if candidate.startswith('{') and not candidate.startswith('{"intent": "parse_error"'):
        try:
            json.loads(candidate)
        except json.JSONDecodeError:
            wrapped = '[' + candidate.rstrip(', \n\r') + ']'
            try:
                json.loads(wrapped)
                return wrapped
            except:
                pass
    
    return candidate
