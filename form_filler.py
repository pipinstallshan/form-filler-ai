import time
import re
from pathlib import Path
from typing import Dict, Any, List
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import httpx


def find_element_by_any_selector(driver, field: Dict):
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
    
    label = field.get('label', '')
    if label:
        try:
            xpath = f"//label[contains(text(), '{label}')]/following::input[1] | //label[contains(text(), '{label}')]//input"
            elements = driver.find_elements(By.XPATH, xpath)
            if elements:
                return elements[0]
        except:
            pass
        
        return None

def fill_text_field(element, value: str):
    element.clear()
    time.sleep(0.1)
    
    element.click()
    time.sleep(0.1)
    
    for char in str(value):
        element.send_keys(char)
        time.sleep(0.05)

def fill_select_field(element, value: str, options: list):
    try:
        select = Select(element)
        try:
            select.select_by_visible_text(value)
            time.sleep(0.2)
            element.send_keys(Keys.ESCAPE)
            time.sleep(0.2)
            return True
        except:
            pass
        
        value_lower = value.lower()
        for option in select.options:
            option_text = option.text.lower()
            if value_lower in option_text or option_text in value_lower:
                option.click()
                time.sleep(0.2)
                element.send_keys(Keys.ESCAPE)
                time.sleep(0.2)
                return True
        
        for option in select.options:
            if option.text.strip() and option.text.lower() not in ['select', 'choose', 'please select']:
                option.click()
                time.sleep(0.2)
                element.send_keys(Keys.ESCAPE)
                time.sleep(0.2)
                return True
        
        return False
    except Exception as e:
        print(f'    ❌ Select error: {e}')
        return False

def fill_checkbox_group_option(driver, field: Dict, value: Any, options: list):
    pass

def fill_autocomplete_dropdown(driver, element, value: str, options: list):
    try:
        tag_name = element.tag_name.lower()
        is_native_select = tag_name == 'select'
        
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", element)
        time.sleep(0.3)
        
        if is_native_select:
            try:
                element.click()
                time.sleep(0.4)
                
                value_str = str(value).strip()
                value_lower = value_str.lower()
                
                select = Select(element)
                
                for option in select.options:
                    option_text = option.text.strip().lower()
                    if value_lower == option_text or (value_lower in option_text and len(value_lower) > 3):
                        search_term = value_str[:15]
                        for char in search_term:
                            try:
                                element.send_keys(char)
                                time.sleep(0.08)
                            except:
                                break
                        
                        time.sleep(0.5)
                        
                        try:
                            option.click()
                        except:
                            driver.execute_script("arguments[0].selected = true; arguments[0].dispatchEvent(new Event('change', {bubbles: true}));", option)
                        
                        time.sleep(0.3)
                        element.send_keys(Keys.ESCAPE)
                        time.sleep(0.2)
                        return True
                
                search_term = value_str[:15]
                for char in search_term:
                    try:
                        element.send_keys(char)
                        time.sleep(0.1)
                    except:
                        break
                
                time.sleep(0.6)
                
                for option in select.options:
                    option_text = option.text.strip().lower()
                    if value_lower in option_text or option_text in value_lower:
                        try:
                            option.click()
                            time.sleep(0.3)
                            element.send_keys(Keys.ESCAPE)
                            time.sleep(0.2)
                            return True
                        except:
                            continue
                
                try:
                    element.send_keys(Keys.ESCAPE)
                except:
                    pass
                return False
                    
            except Exception as e:
                print(f'    ⚠️  Native select handling failed: {e}')
                try:
                    element.send_keys(Keys.ESCAPE)
                except:
                    pass
                return False
        
        try:
            element.clear()
        except:
            pass
        
        time.sleep(0.2)
        
        try:
            element.click()
        except:
            try:
                driver.execute_script("arguments[0].click();", element)
            except:
                ActionChains(driver).move_to_element(element).click().perform()
        
        time.sleep(0.5)
        
        search_term = str(value).strip()[:30]
        
        for i, char in enumerate(search_term):
            try:
                element.send_keys(char)
                time.sleep(0.1)
            except:
                break
        
        time.sleep(1.2)
        
        option_selectors = [
            '//div[@role="option"]',
            '//li[@role="option"]',
            '//div[contains(@class, "option")]',
            '//li[contains(@class, "option")]',
            '//div[contains(@id, "option")]',
            '//li[contains(@id, "option")]',
            '//*[@role="option"]'
        ]
        
        first_option = None
        
        for selector in option_selectors:
            try:
                option_elements = driver.find_elements(By.XPATH, selector)
                visible_options = [opt for opt in option_elements if opt.is_displayed() and opt.text.strip()]
                
                if visible_options:
                    first_option = visible_options[0]
                    break
            except:
                continue
        
        if first_option:
            try:
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", first_option)
                time.sleep(0.3)
                
                try:
                    first_option.click()
                except:
                    try:
                        driver.execute_script("arguments[0].click();", first_option)
                    except:
                        ActionChains(driver).move_to_element(first_option).click().perform()
                
                time.sleep(0.5)
                
                try:
                    element.send_keys(Keys.ESCAPE)
                    time.sleep(0.2)
                except:
                    pass
                
                return True
            except Exception as e:
                print(f'    ⚠️  Could not click first option: {e}')
        
        try:
            element.send_keys(Keys.ESCAPE)
        except:
            pass
        
        time.sleep(0.2)
        return False
        
    except Exception as e:
        print(f'    ❌ Dropdown error: {e}')
        import traceback
        traceback.print_exc()
        try:
            element.send_keys(Keys.ESCAPE)
        except:
            pass
        return False

def download_file(url: str, filename: str) -> str:
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
        
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
        time.sleep(0.3)
        
        is_autocomplete = field.get('isAutocomplete', False) or field_type == 'autocomplete'
        role = element.get_attribute('role') or ''
        has_popup = element.get_attribute('aria-haspopup') == 'listbox' or role == 'combobox'
        
        if field_type in ['text', 'email', 'tel', 'textarea', 'phone']:
            time.sleep(0.2)
            
            if field_type == 'tel':
                value = re.sub(r'^\+\d{1,3}[-\s]?', '', str(value))
            
            fill_text_field(element, value)
            print(f'    ✅ Filled text field')
            
        elif field_type == 'select' or field_type == 'autocomplete' or (field_type == 'text' and (is_autocomplete or has_popup)):
            options = field.get('options', [])
            
            if fill_autocomplete_dropdown(driver, element, str(value), options):
                print(f'    ✅ Selected dropdown: {value}')
            else:
                print(f'    ⚠️  Could not select dropdown value')
            
        elif field_type == 'radio':
            name = field.get('name')
            if name:
                radios = driver.find_elements(By.NAME, name)
                for radio in radios:
                    radio_value = radio.get_attribute('value')
                    if str(value).lower() in str(radio_value).lower():
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", radio)
                        time.sleep(0.2)
                        radio.click()
                        print(f'    ✅ Selected radio')
                        break
            
        elif field_type == 'checkbox':
            if value is True or str(value).lower() in ['yes', 'true', '1', 'acknowledge']:
                if not element.is_selected():
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", element)
                    time.sleep(0.2)
                    element.click()
                    print(f'    ✅ Checked')
        
        elif field_type == 'checkbox-group':
            field_name = field.get('name', '')
            options = field.get('options', [])
            
            values_to_check = []
            if isinstance(value, list):
                values_to_check = [str(v).strip() for v in value]
            else:
                values_to_check = [str(value).strip()]
            
            if not field_name:
                print(f'    ⚠️  No field name for checkbox group')
                return False
            
            try:
                script = """
                var fieldName = arguments[0];
                var valuesToCheck = arguments[1];
                var clicked = 0;
                
                var checkboxes = document.querySelectorAll('input[name="' + fieldName + '"][type="checkbox"]');
                
                for (var i = 0; i < checkboxes.length; i++) {
                    var checkbox = checkboxes[i];
                    var checkboxValue = (checkbox.value || '').toLowerCase().trim();
                    var checkboxId = checkbox.id || '';
                    var labelText = '';
                    
                    if (checkboxId) {
                        var label = document.querySelector('label[for="' + checkboxId + '"]');
                        if (label) {
                            labelText = (label.textContent || label.innerText || '').toLowerCase().trim();
                        }
                    }
                    
                    if (!labelText) {
                        var parent = checkbox.parentElement;
                        if (parent) {
                            labelText = (parent.textContent || parent.innerText || '').toLowerCase().trim();
                        }
                    }
                    
                    for (var j = 0; j < valuesToCheck.length; j++) {
                        var valueToCheck = (valuesToCheck[j] || '').toLowerCase().trim();
                        
                        if (!valueToCheck) continue;
                        
                        if (checkboxValue === valueToCheck || 
                            (labelText && labelText.indexOf(valueToCheck) !== -1) || 
                            (valueToCheck.indexOf(checkboxValue) !== -1) ||
                            (checkboxValue && checkboxValue.indexOf(valueToCheck) !== -1)) {
                            
                            if (!checkbox.checked) {
                                checkbox.scrollIntoView({behavior: 'auto', block: 'center'});
                                checkbox.click();
                                clicked++;
                            }
                            break;
                        }
                    }
                }
                
                return clicked;
                """
                
                clicked_count = driver.execute_script(script, field_name, values_to_check)
                time.sleep(0.3)
                
                if clicked_count is None:
                    clicked_count = 0
                else:
                    clicked_count = int(clicked_count)
                
                if clicked_count > 0:
                    print(f'    ✅ Checked {clicked_count} option(s) in checkbox group')
                    return True
                else:
                    print(f'    ⚠️  Could not find matching checkbox(es)')
                    return False
                    
            except Exception as e:
                print(f'    ❌ Error filling checkbox group: {e}')
                import traceback
                traceback.print_exc()
                return False
            
        elif field_type == 'file':
            if isinstance(value, str) and value.startswith('http'):
                file_path = download_file(value, 'resume.pdf')
                element.send_keys(file_path)
                time.sleep(3)
                print(f'    ✅ Uploaded file')
            elif isinstance(value, str) and Path(value).exists():
                element.send_keys(str(Path(value).absolute()))
                time.sleep(3)
                print(f'    ✅ Uploaded file')
        
        time.sleep(0.2)
        return True
        
    except Exception as e:
        print(f'    ❌ Error: {e}')
        return False

def fill_form(driver, fields: List[Dict], field_values: Dict[str, Any]):
    driver.refresh()
    time.sleep(2)
    
    print(f'\n📝 Filling {len(fields)} form fields...\n')
    filled_count = 0
    for field in fields:
        label = field.get('label', '')
        value = field_values.get(label)
        
        if value is not None and value != '':
            if fill_field(driver, field, value):
                filled_count += 1
    
    print(f'\n✅ Successfully filled {filled_count}/{len(fields)} fields')
    return filled_count