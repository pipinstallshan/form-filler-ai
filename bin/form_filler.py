"""
Form Filler - Fills forms using AI-generated field mappings
"""

import time
import re
from pathlib import Path
from typing import Dict, Any, List
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
import httpx


def find_element_by_any_selector(driver, field: Dict):
    """Try multiple strategies to find an element"""
    selectors = [
        (By.ID, field.get('id')),
        (By.NAME, field.get('name')),
        (By.CSS_SELECTOR, field.get('selector')),
        (By.XPATH, field.get('xpath'))
    ]
    
    for by, value in selectors:
        if value:
            try:
                elements = driver.find_elements(by, value)
                if elements:
                    return elements[0]
            except:
                continue
    
    # Try finding by label text
    label = field.get('label', '')
    if label:
        try:
            # Find label containing text, then find associated input
            xpath = f"//label[contains(text(), '{label}')]/following::input[1] | //label[contains(text(), '{label}')]//input"
            elements = driver.find_elements(By.XPATH, xpath)
            if elements:
                return elements[0]
        except:
            pass
        
        return None


def fill_text_field(element, value: str):
    """Fill text input with typing simulation"""
    element.clear()
    time.sleep(0.1)
    
    # Type with small delays for realism
    for char in str(value):
        element.send_keys(char)
        time.sleep(0.05)


def fill_select_field(element, value: str, options: list):
    """Fill select dropdown"""
    try:
        select = Select(element)
        
        # Try exact match
        try:
            select.select_by_visible_text(value)
            return True
        except:
            pass
        
        # Try case-insensitive partial match
        value_lower = value.lower()
        for option in select.options:
            option_text = option.text.lower()
            if value_lower in option_text or option_text in value_lower:
                option.click()
                return True
        
        # If nothing matched, select first non-empty option
        for option in select.options:
            if option.text.strip() and option.text.lower() not in ['select', 'choose', 'please select']:
                option.click()
                return True
        
        return False
    except Exception as e:
        print(f'    ❌ Select error: {e}')
        return False


def download_file(url: str, filename: str) -> str:
    """Download file from URL"""
    temp_dir = Path.cwd() / 'temp'
    temp_dir.mkdir(exist_ok=True)
    
    if '.' not in filename:
        filename = filename + '.pdf'
    
    temp_path = temp_dir / filename
    
    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, follow_redirects=True)
        response.raise_for_status()
        temp_path.write_bytes(response.content)
    
    return str(temp_path.absolute())


def fill_field(driver, field: Dict, value: Any):
    """Fill a single form field"""
    label = field.get('label', 'Unknown')
    field_type = field.get('fieldType', 'text')
    
    if value is None or value == '':
        print(f'  ⏭️  Skipping: {label} (no value)')
        return False
    
    print(f'  📝 Filling: {label} = {value}')
    
    try:
        element = find_element_by_any_selector(driver, field)
        if not element:
            print(f'    ❌ Element not found')
            return False
        
        # Scroll into view
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
        time.sleep(0.3)
        
        # Fill based on field type
        if field_type in ['text', 'email', 'tel', 'textarea']:
            # Clean phone numbers
            if field_type == 'tel':
                value = re.sub(r'^\+\d{1,3}[-\s]?', '', str(value))
            
            fill_text_field(element, value)
            print(f'    ✅ Filled text field')
            
        elif field_type == 'select':
            options = field.get('options', [])
            if fill_select_field(element, str(value), options):
                print(f'    ✅ Selected: {value}')
            else:
                print(f'    ⚠️  Could not select value')
            
        elif field_type == 'radio':
            # Find radio button with matching value or label
            name = field.get('name')
            if name:
                radios = driver.find_elements(By.NAME, name)
                for radio in radios:
                    radio_value = radio.get_attribute('value')
                    if str(value).lower() in str(radio_value).lower():
                        radio.click()
                        print(f'    ✅ Selected radio')
                        break
            
        elif field_type == 'checkbox':
            if str(value).lower() in ['yes', 'true', '1']:
                if not element.is_selected():
                    element.click()
                    print(f'    ✅ Checked')
            
        elif field_type == 'file':
            if isinstance(value, str) and value.startswith('http'):
                file_path = download_file(value, 'resume.pdf')
                element.send_keys(file_path)
                print(f'    ✅ Uploaded file')
            elif isinstance(value, str) and Path(value).exists():
                element.send_keys(str(Path(value).absolute()))
                print(f'    ✅ Uploaded file')
        
        time.sleep(0.2)
        return True
        
    except Exception as e:
        print(f'    ❌ Error: {e}')
        return False


def fill_form(driver, fields: List[Dict], field_values: Dict[str, Any]):
    """Fill all form fields"""
    print(f'\n📝 Filling {len(fields)} form fields...\n')
    
    filled_count = 0
    
    for field in fields:
        label = field.get('label', '')
        value = field_values.get(label)
        
        if value:
            if fill_field(driver, field, value):
                filled_count += 1
    
    print(f'\n✅ Successfully filled {filled_count}/{len(fields)} fields')
    return filled_count
