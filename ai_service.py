import os
import json
import re
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def get_gemini_model():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("Missing GEMINI_API_KEY or GOOGLE_API_KEY in .env file")
    
    genai.configure(api_key=api_key)
    
    models_to_try = ['gemini-2.5-flash']
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            return model
        except:
            continue
    
    return genai.GenerativeModel('gemini-1.5-flash')

def parse_html_structure(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, 'html.parser')
    
    base_html = None
    sections = {}
    
    body = soup.find('body')
    if not body:
        return {'base_html': html, 'sections': {}}
    
    current_section = None
    base_parts = []
    
    for element in body.descendants:
        if isinstance(element, str):
            continue
        
        if element.name == 'section':
            section_text = element.get_text(strip=True)
            if section_text and 'id:' in section_text:
                current_section = section_text.replace('id:', '').strip()
                sections[current_section] = {'html': '', 'options': []}
                continue
        
        if current_section:
            if element.name == 'body':
                parent = element.parent
                if parent and parent.name == 'body':
                    section_soup = BeautifulSoup(str(element), 'html.parser')
                    sections[current_section]['html'] = str(element)
                    
                    options = []
                    for option_elem in section_soup.find_all(True):
                        role = option_elem.get('role', '')
                        if role == 'option':
                            option_text = option_elem.get_text(strip=True)
                            if option_text and len(option_text) < 200:
                                options.append(option_text)
                    
                    sections[current_section]['options'] = list(set(options))
                    current_section = None
                    continue
        else:
            if element.name == 'body' and not base_html:
                parent = element.parent
                if parent and parent.name == 'body':
                    base_html = str(element)
    
    if base_html is None:
        bodies = body.find_all('body', recursive=False)
        if bodies:
            base_html = str(bodies[0])
        else:
            base_html = str(body)
    
    return {'base_html': base_html, 'sections': sections}

def identify_form_fields(html: str, profile_dict: Dict[str, Any], use_cache: bool = False) -> List[Dict[str, Any]]:  
    print('🔍 Identifying form fields using AI...')
    
    structure = parse_html_structure(html)
    base_html = structure['base_html']
    sections = structure['sections']
    
    section_info = ""
    for section_id, section_data in sections.items():
        if section_data['options']:
            section_info += f"\nSection: {section_id}\n"
            section_info += f"Available options: {', '.join(section_data['options'])}"
    
    profile_context = json.dumps(profile_dict, indent=2)
    
    prompt = f"""Analyze this HTML form structure and identify all form fields.

    BASE HTML (contains the form structure):
    {base_html}

    SECTIONS (contain expanded dropdown options):
    {section_info if section_info else "No sections with options found."}

    PROFILE DATA (for contextual answers):
    {profile_context}

    For each form field, extract:
    1. Selector (prioritize: ID > name > CSS selector > xpath)
    2. Field type (text, email, tel, number, select, radio, checkbox, checkbox-group, file, autocomplete)
    3. Label
    4. Required status
    5. If dropdown/select: find related section and extract options
    6. Placeholder (if exists)
    7. If checkbox-group: extract all checkbox options
    8. Field category: direct-mapping, generic-referral, acknowledgment, consent, or custom

    FIELD CATEGORIES:
    - direct-mapping: firstName, lastName, email, phone, address, etc. - map directly to profile data
    - generic-referral: "How did you hear about us?", "Where did you find this job?", referral source questions
    - acknowledgment: Privacy policy, AI policy, terms acknowledgment checkboxes
    - consent: Demographic data consent, processing consent checkboxes
    - custom: Other fields that need AI-generated answers

    GENERIC FIELD HANDLING:
    1. Referral source fields ("How did you hear about us?"):
    - If profile has linkedinUrl: suggest "LinkedIn"
    - If profile has portfolioUrl/website: suggest "Careers Website"
    - Otherwise suggest "Careers Website" or "LinkedIn" or any other option

    2. Acknowledgment checkboxes (privacy policy, AI policy, terms):
    - If required: suggest "Acknowledge" or check the checkbox
    - Always acknowledge if required field

    3. Consent checkboxes (demographic data processing):
    - If required: suggest acknowledging
    - Mark as consent field type

    4. Checkbox groups ("select all that apply"):
    - Identify all options
    - For referral sources: select appropriate option(s) based on profile
    - Mark as checkbox-group type

    IMPORTANT:
    - Extract selectors from BASE HTML only
    - If a field has dropdown options, look for the related section (sections marked with id:field_id)
    - Some sections may be empty or have errors - handle gracefully
    - For generic fields, include suggestedValue based on profile context
    - For checkbox groups, include all options in the options array
    - Return JSON array of fields with this structure only:
    [
    {{
        "selector": "#field_id or [name='field_name']",
        "id": "field_id",
        "name": "field_name",
        "fieldType": "text|email|tel|select|radio|checkbox|checkbox-group|file|autocomplete",
        "label": "Field Label",
        "required": true|false,
        "placeholder": "placeholder text",
        "options": ["option1", "option2"],
        "category": "direct-mapping|generic-referral|acknowledgment|consent|custom",
        "suggestedValue": "suggested answer" // only for generic/custom fields
    }}
    ]

    Return ONLY valid JSON, no markdown, no explanations."""

    try:
        model = get_gemini_model()
        response = model.generate_content(prompt)
        
        response_text = response.text.strip()
        
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        fields = json.loads(response_text)
        for field in fields:
            field_id = field.get('id', '')
            field_name = field.get('name', '')
            field_category = field.get('category', 'custom')
            
            if field_id and field_id in sections:
                section_options = sections[field_id]['options']
                if section_options:
                    field['options'] = section_options
            
            if not field.get('options') and field.get('fieldType') == 'checkbox-group':
                if field.get('label', '').lower().find('click all that apply') != -1:
                    field['category'] = 'generic-referral'
        
        print(f'✅ Identified {len(fields)} form fields')
        mapped_count = sum(1 for f in fields if f.get('options'))
        if mapped_count > 0:
            print(f'   📋 {mapped_count} field(s) have dropdown options from sections')
        
        return fields
        
    except Exception as e:
        print(f'❌ Error identifying fields: {e}')
        import traceback
        traceback.print_exc()
        return []

def match_profile_to_dropdown_options(profile_value: str, options: List[str], field_label: str = "") -> Optional[str]:
    if not profile_value or not options:
        return None
    
    profile_value_clean = str(profile_value).strip().lower()
    field_label_lower = str(field_label).lower()
    
    if 'gender' in field_label_lower or 'sex' in field_label_lower:
        for option in options:
            option_clean = str(option).strip().lower()
            if profile_value_clean == option_clean:
                return option
        return None
    
    for option in options:
        option_clean = str(option).strip().lower()
        
        if profile_value_clean == option_clean:
            return option
        
        if profile_value_clean in option_clean or option_clean in profile_value_clean:
            return option
    
    try:
        model = get_gemini_model()
        
        prompt = f"""Match this profile value to the best dropdown option.

        Profile Value: "{profile_value}"
        Field Label: "{field_label}"
        Available Options:
        {chr(10).join([f"{i+1}. {opt}" for i, opt in enumerate(options)])}

        Examples:
        - "Bachelor of Science" should match "Bachelor's Degree"
        - "BS" should match "Bachelor's Degree"  
        - "United States" should match "United States"
        - "USA" should match "United States"

        Return ONLY the exact option text that best matches, nothing else."""

        response = model.generate_content(prompt)
        matched = response.text.strip()
        
        if matched in options:
            return matched
        
        matched_lower = matched.lower()
        for option in options:
            if option.lower() == matched_lower or matched_lower in option.lower() or option.lower() in matched_lower:
                return option
        
        if len(options) > 0:
            return options[0]
        
        return None
        
    except Exception as e:
        if options:
            return options[0]
        return None

def generate_referral_answer(field: Dict[str, Any], profile_dict: Dict[str, Any], options: List[str]) -> Optional[str]:
    label = (field.get('label') or '').lower()
    
    if 'hear' in label or 'referral' in label or 'find' in label or 'where' in label:
        if profile_dict.get('linkedinUrl'):
            for option in options:
                if 'linkedin' in option.lower():
                    return option
        
        if profile_dict.get('portfolioUrl') or profile_dict.get('websiteUrl'):
            for option in options:
                if any(term in option.lower() for term in ['career', 'website', 'company website']):
                    return option
        
        for option in options:
            option_lower = option.lower()
            if any(term in option_lower for term in ['career', 'website', 'company']):
                return option
        
        if options:
            return options[0]
    
    return None

def map_fields_to_profile(fields: List[Dict[str, Any]], profile_dict: Dict[str, Any]) -> Dict[str, Any]:
    print('🎯 Mapping profile data to fields...')
    
    field_values = {}
    field_mapping = {
        'firstName': 'firstName',
        'lastName': 'lastName',
        'email': 'email',
        'phone': 'phone',
        'address': 'address',
        'city': 'city',
        'state': 'state',
        'zipCode': 'zipCode',
        'country': 'country',
        'currentCompany': 'currentCompany',
        'currentJobTitle': 'currentJobTitle',
        'yearsOfExperience': 'yearsOfExperience',
        'linkedinUrl': 'linkedinUrl',
        'githubUrl': 'githubUrl',
        'portfolioUrl': 'portfolioUrl',
        'highestDegree': 'highestDegree',
        'university': 'university',
        'graduationYear': 'graduationYear',
        'fieldOfStudy': 'fieldOfStudy',
        'gpa': 'gpa',
        'expectedSalary': 'expectedSalary',
        'workAuthorization': 'workAuthorization',
        'requiresSponsorship': 'requiresSponsorship',
        'willingToRelocate': 'willingToRelocate',
        'availableStartDate': 'availableStartDate',
        'technicalSkills': 'technicalSkills',
        'resumeUrl': 'resumeUrl',
        'coverLetterUrl': 'coverLetterUrl',
        'whyThisCompany': 'whyThisCompany',
        'gender': 'gender',
        'veteranStatus': 'veteranStatus',
        'disabilityStatus': 'disabilityStatus',
        'race': 'race'
    }
    
    label_mapping = {
        r'first[\s_-]?name|fname|first$': 'firstName',
        r'last[\s_-]?name|lname|last$|surname': 'lastName',
        r'^email$|e-?mail': 'email',
        r'^phone$|telephone|mobile|tel': 'phone',
        r'^address$|street[\s_-]?address': 'address',
        r'^city$|town': 'city',
        r'^state$|province|region': 'state',
        r'zip|postal[\s_-]?code|postcode': 'zipCode',
        r'^country$|nation': 'country',
        r'current[\s_-]?company|current[\s_-]?employer|^company$|^employer$': 'currentCompany',
        r'current[\s_-]?job[\s_-]?title|^job[\s_-]?title$|^title$|^position$|^role$': 'currentJobTitle',
        r'years?[\s_-]?(of[\s_-]?)?experience|experience[\s_-]?years?': 'yearsOfExperience',
        r'linkedin|linked[\s_-]?in': 'linkedinUrl',
        r'github|git[\s_-]?hub': 'githubUrl',
        r'portfolio|personal[\s_-]?website|^website$': 'portfolioUrl',
        r'^degree$|education[\s_-]?level|highest[\s_-]?degree|qualification': 'highestDegree',
        r'university|college|school|institution': 'university',
        r'graduation[\s_-]?year|year[\s_-]?(of[\s_-]?)?graduation': 'graduationYear',
        r'field[\s_-]?of[\s_-]?study|major|specialization': 'fieldOfStudy',
        r'gpa|grade[\s_-]?point': 'gpa',
        r'expected[\s_-]?salary|desired[\s_-]?salary': 'expectedSalary',
        r'work[\s_-]?authorization|legally[\s_-]?authorized': 'workAuthorization',
        r'require.*sponsor|visa[\s_-]?sponsor|need.*sponsor': 'requiresSponsorship',
        r'willing[\s_-]?to[\s_-]?relocate|able[\s_-]?to[\s_-]?relocate': 'willingToRelocate',
        r'available|start[\s_-]?date|notice[\s_-]?period|joining[\s_-]?date': 'availableStartDate',
        r'technical[\s_-]?skills|skills|technologies': 'technicalSkills',
        r'resume|cv|resume/cv': 'resumeUrl',
        r'cover[\s_-]?letter': 'coverLetterUrl',
        r'why|interest|motivated|excited': 'whyThisCompany',
        r'gender|\bsex\b': 'gender',
        r'veteran|military': 'veteranStatus',
        r'disability|disabled': 'disabilityStatus',
        r'race|racial|ethnicity|ethnic': 'race'
    }
    
    for field in fields:
        label = (field.get('label') or '').lower()
        field_id = (field.get('id') or '').lower()
        field_name = (field.get('name') or '').lower()
        field_type = field.get('fieldType', '')
        field_category = field.get('category', 'custom')
        options = field.get('options', [])
        suggested_value = field.get('suggestedValue')
        
        field_label = field.get('label') or field.get('name') or field.get('id') or 'unknown'
        
        if field_category == 'acknowledgment':
            if field_type in ['checkbox', 'checkbox-group']:
                if field.get('required', False):
                    field_values[field_label] = True
                    print(f'  ✅ {field_label}: Acknowledged (required)')
                continue
        
        if field_category == 'consent':
            if field_type in ['checkbox', 'checkbox-group']:
                if field.get('required', False):
                    field_values[field_label] = True
                    print(f'  ✅ {field_label}: Consent given (required)')
                continue
        
        if field_category == 'generic-referral':
            if suggested_value:
                field_values[field_label] = suggested_value
                print(f'  ✅ {field_label}: {suggested_value} (AI suggested)')
            else:
                referral_value = generate_referral_answer(field, profile_dict, options)
                if referral_value:
                    field_values[field_label] = referral_value
                    print(f'  ✅ {field_label}: {referral_value} (contextual)')
            continue
        
        if suggested_value is not None and suggested_value != '':
            if options and field_type in ['select', 'autocomplete']:
                matched_value = match_profile_to_dropdown_options(
                    str(suggested_value), options, field.get('label', '')
                )
                if matched_value:
                    field_values[field_label] = matched_value
                    print(f'  ✅ {field_label}: {suggested_value} → {matched_value} (AI suggested, matched)')
                else:
                    field_values[field_label] = suggested_value
                    print(f'  ✅ {field_label}: {suggested_value} (AI suggested)')
            else:
                field_values[field_label] = suggested_value
                print(f'  ✅ {field_label}: {suggested_value} (AI suggested)')
            continue
        
        profile_key = None
        field_identifier = f"{label} {field_id} {field_name}".lower()
        
        for pattern, key in label_mapping.items():
            if re.search(pattern, field_identifier):
                profile_key = key
                break
        
        if profile_key and profile_key in profile_dict:
            value = profile_dict[profile_key]
            
            if value is None or value == '':
                continue
            
            if options and field_type in ['select', 'autocomplete']:
                matched_value = match_profile_to_dropdown_options(
                    str(value), options, field.get('label', '')
                )
                if matched_value:
                    field_values[field_label] = matched_value
                    print(f'  ✅ {field_label}: "{value}" → "{matched_value}"')
                else:
                    if options:
                        field_values[field_label] = value
                        print(f'  ⚠️  {field_label}: "{value}" (no match found in {len(options)} options)')
            else:
                if profile_key == 'requiresSponsorship':
                    value = 'Yes' if value else 'No'
                elif profile_key == 'willingToRelocate':
                    value = 'Yes' if value else 'No'
                
                field_values[field_label] = value
                print(f'  ✅ {field_label}: {value}')
    
    print(f'✅ Mapped {len(field_values)} field(s)')
    return field_values