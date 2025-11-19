"""
AI Service - Handles all AI API calls
Uses Google Gemini API (can be switched to OpenAI)
"""

import os
import json
import httpx
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()


def call_gemini_api(prompt: str, temperature: float = 0.3) -> str:
    """Call Google Gemini API"""
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise Exception('GOOGLE_API_KEY not found in .env file')
    
    models = ['gemini-2.0-flash-exp', 'gemini-1.5-flash', 'gemini-1.5-pro']
    
    with httpx.Client(timeout=30.0) as client:
        for model in models:
            try:
                response = client.post(
                    f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}',
                    json={
                        'contents': [{'parts': [{'text': prompt}]}],
                        'generationConfig': {
                            'temperature': temperature,
                            'topK': 40,
                            'topP': 0.95,
                            'maxOutputTokens': 8000,
                        }
                    },
                    headers={'Content-Type': 'application/json'}
                )
                
                result = response.json()
                text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '').strip()
                
                if text:
                    return text
            except Exception as e:
                if model == models[-1]:
                    raise Exception(f'All Gemini models failed: {e}')
                continue
    
    raise Exception('Failed to get response from Gemini API')


def identify_form_fields(html: str, profile_data: Dict) -> List[Dict]:
    """
    Step 1: Use AI to identify form fields and create selectors
    """
    print('🤖 Step 1: Asking AI to identify form fields...')
    
    prompt = f"""You are a form automation expert. Analyze this HTML and identify ALL form input fields.

HTML:
{html[:15000]}  

For EACH input field (text, email, tel, select, textarea, radio, checkbox, file), return a JSON array with this structure:

[
  {{
    "label": "First Name",
    "fieldType": "text|email|tel|select|textarea|radio|checkbox|file",
    "selector": "CSS selector or XPath to find this element",
    "xpath": "XPath to find this element",
    "name": "field name attribute",
    "id": "field id attribute",
    "required": true|false,
    "options": ["option1", "option2"] (for select/radio/checkbox, otherwise null),
    "placeholder": "placeholder text if any"
  }}
]

IMPORTANT:
- Return ONLY valid JSON array, no markdown or explanations
- Include ALL form fields you can find
- Make selectors as specific as possible
- For select/radio/checkbox, list all available options
- If a field has multiple ways to select it (id, name, class), provide the most reliable selector

Return the JSON array now:"""

    response = call_gemini_api(prompt, temperature=0.1)
    
    # Extract JSON from response
    json_match = re.search(r'\[.*\]', response, re.DOTALL)
    if json_match:
        try:
            fields = json.loads(json_match.group())
            print(f'✅ AI identified {len(fields)} form fields')
            return fields
        except json.JSONDecodeError as e:
            print(f'❌ Failed to parse JSON: {e}')
            print(f'Response was: {response[:500]}')
            return []
    
    print('❌ No JSON found in AI response')
    return []


def map_fields_to_profile(fields: List[Dict], profile_data: Dict) -> Dict[str, Any]:
    """
    Step 2: Map profile data to identified fields
    """
    print('🤖 Step 2: Mapping profile data to fields...')
    
    fields_json = json.dumps(fields, indent=2)
    profile_json = json.dumps(profile_data, indent=2)
    
    prompt = f"""You are mapping user profile data to form fields.

FORM FIELDS:
{fields_json}

USER PROFILE DATA:
{profile_json}

For each field, determine the best value from the profile data. Return JSON object mapping field labels to values:

{{
  "First Name": "John",
  "Email": "john@example.com",
  "Phone": "5551234567",
  ...
}}

RULES:
- For phone numbers, remove country code (+1, etc) if the field doesn't expect it
- For boolean fields (Yes/No), convert true/false to "Yes"/"No"
- For select/radio/checkbox fields, choose the value that best matches from available options
- For degree fields: "Bachelor of Science" should map to "Bachelor's Degree" if that's the closest option
- For work authorization: if user has authorization, select "Yes" or "Authorized" option
- If no matching profile data exists, use null
- Return ONLY valid JSON, no markdown or explanations

Return the JSON mapping now:"""

    response = call_gemini_api(prompt, temperature=0.2)
    
    # Extract JSON
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        try:
            mapping = json.loads(json_match.group())
            print(f'✅ Mapped {len(mapping)} fields to profile data')
            return mapping
        except json.JSONDecodeError as e:
            print(f'❌ Failed to parse mapping JSON: {e}')
            return {}
    
    return {}


def fill_remaining_fields(html: str, filled_fields: List[str], profile_data: Dict) -> Dict[str, str]:
    """
    Step 3: For fields not filled yet, use AI to determine best answers
    """
    print('🤖 Step 3: Using AI to fill remaining fields...')
    
    prompt = f"""You are filling out a job application form. Some fields are already filled, but some remain empty.

CURRENT HTML (showing current state):
{html[:10000]}

FIELDS ALREADY FILLED:
{json.dumps(filled_fields, indent=2)}

USER PROFILE:
{json.dumps(profile_data, indent=2)}

Identify any UNFILLED form fields and provide the best answer for each based on:
1. The user's profile data
2. Common sense and professional standards
3. The context of the question

Return JSON object with field labels and recommended values:
{{
  "Why do you want to work here?": "I am excited about...",
  "How did you hear about us?": "Online job board",
  "Are you legally authorized to work?": "Yes",
  ...
}}

RULES:
- For "Why this company" questions, use whyThisCompany from profile or generate professional answer
- For "How did you hear" questions, use "Online job board" or similar
- For Yes/No questions about eligibility, default to "Yes" unless profile says otherwise
- For diversity questions, use "Prefer not to say" if not in profile
- Return ONLY valid JSON, no markdown

Return the JSON now:"""

    response = call_gemini_api(prompt, temperature=0.5)
    
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        try:
            remaining = json.loads(json_match.group())
            print(f'✅ AI provided answers for {len(remaining)} remaining fields')
            return remaining
        except:
            return {}
    
    return {}


import re

