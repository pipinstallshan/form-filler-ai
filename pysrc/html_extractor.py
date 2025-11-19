import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import Select


def take_element_screenshot(driver, element, screenshot_path: str, field_type: str = 'text') -> bool:
    try:
        driver.save_screenshot(screenshot_path)
        
        if Path(screenshot_path).exists() and Path(screenshot_path).stat().st_size > 0:
            return True
        else:
            print(f'    ⚠️  Screenshot file was not created or is empty')
            return False
    except Exception as e:
        print(f'    ⚠️  Screenshot failed: {e}')
        return False


def extract_field_html(driver, element, field_type: str) -> str:
    try:
        ancestor = driver.execute_script("""
            var el = arguments[0];
            var fieldType = arguments[1];
            
            if (fieldType === 'checkbox' || fieldType === 'radio') {
                var name = el.name;
                if (name) {
                    var allInputs = document.querySelectorAll('input[name="' + name + '"]');
                    if (allInputs.length > 1) {
                        var firstInput = allInputs[0];
                        var group = firstInput.closest('fieldset, div.checkbox, div.checkbox-group, div.radio-group, div[class*="checkbox"], div[class*="radio"]');
                        if (group) return group.outerHTML;
                        
                        var parent = firstInput.parentElement;
                        while (parent && parent.tagName !== 'BODY') {
                            if (parent.tagName === 'FIELDSET' || 
                                (parent.classList && (parent.classList.contains('checkbox') || parent.classList.contains('radio') || parent.classList.contains('checkbox-group') || parent.classList.contains('radio-group'))) ||
                                (parent.getAttribute('class') && (parent.getAttribute('class').includes('checkbox') || parent.getAttribute('class').includes('radio')))) {
                                return parent.outerHTML;
                            }
                            parent = parent.parentElement;
                        }
                    }
                }
            }
            
            var current = el;
            var steps = 0;
            var targetSteps = 4;
            
            while (current && current.parentElement && current.parentElement.tagName !== 'BODY' && current.parentElement.tagName !== 'HTML' && steps < targetSteps) {
                current = current.parentElement;
                steps++;
            }
            
            if (current && current.tagName !== 'BODY' && current.tagName !== 'HTML') {
                return current.outerHTML;
            }
            
            return el.outerHTML;
        """, element, field_type)
        
        return ancestor or element.get_attribute('outerHTML')
    except Exception as e:
        print(f'    ⚠️  Error extracting HTML: {e}')
        return element.get_attribute('outerHTML')


def handle_text_input(driver, element, screenshot_path: str) -> bool:
    print('    📝 Text input field')
    try:
        element.click()
        time.sleep(0.3)
        
        result = take_element_screenshot(driver, element, screenshot_path, 'text')
        
        time.sleep(0.2)
        
        try:
            element.send_keys(Keys.ESCAPE)
        except:
            pass
        
        time.sleep(0.2)
        
        return result
    except Exception as e:
        print(f'    ❌ Error: {e}')
        return False


def handle_email_input(driver, element, screenshot_path: str) -> bool:
    print('    📧 Email input field')
    try:
        element.click()
        time.sleep(0.3)
        return take_element_screenshot(driver, element, screenshot_path, 'email')
    except Exception as e:
        print(f'    ❌ Error: {e}')
        return False


def handle_tel_input(driver, element, screenshot_path: str) -> bool:
    print('    📞 Phone input field')
    try:
        element.click()
        time.sleep(0.3)
        return take_element_screenshot(driver, element, screenshot_path, 'tel')
    except Exception as e:
        print(f'    ❌ Error: {e}')
        return False


def handle_textarea(driver, element, screenshot_path: str) -> bool:
    print('    📄 Textarea field')
    try:
        element.click()
        time.sleep(0.3)
        return take_element_screenshot(driver, element, screenshot_path, 'textarea')
    except Exception as e:
        print(f'    ❌ Error: {e}')
        return False


def handle_select_dropdown(driver, element, screenshot_path: str) -> bool:
    print('    🔽 Select dropdown field')
    try:
        element.click()
        time.sleep(1.5)
        
        wait = WebDriverWait(driver, 5)
        try:
            wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, 'option')) > 0 or 
                                 len(d.find_elements(By.CSS_SELECTOR, '[role="option"]')) > 0)
        except:
            pass
        
        time.sleep(1.5)
        
        try:
            select = Select(element)
            if len(select.options) > 0:
                first_option = select.options[0]
                driver.execute_script("arguments[0].scrollIntoView();", first_option)
                time.sleep(0.5)
        except:
            pass
        
        result = take_element_screenshot(driver, element, screenshot_path, 'select')
        
        time.sleep(0.2)
        
        try:
            element.send_keys(Keys.ESCAPE)
        except:
            pass
        
        time.sleep(0.2)
        
        return result
    except Exception as e:
        print(f'    ❌ Error: {e}')
        return False


def handle_autocomplete_dropdown(driver, element, screenshot_path: str) -> bool:
    print('    🔍 Autocomplete field')
    try:
        element.click()
        time.sleep(1)
        
        element.send_keys('a')
        time.sleep(1.5)
        
        wait = WebDriverWait(driver, 5)
        try:
            wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, '[role="option"], [role="listbox"], .dropdown-menu, [class*="option"]')) > 0)
        except:
            pass
        
        time.sleep(1)
        
        result = take_element_screenshot(driver, element, screenshot_path, 'autocomplete')
        
        time.sleep(0.5)
        
        try:
            element.send_keys(Keys.ESCAPE)
        except:
            pass
        
        time.sleep(0.5)
        
        element.clear()
        time.sleep(0.2)
        
        return result
    except Exception as e:
        print(f'    ❌ Error: {e}')
        return False


def handle_radio_group(driver, element, screenshot_path: str) -> bool:
    print('    🔘 Radio button field')
    try:
        element.click()
        time.sleep(0.3)
        return take_element_screenshot(driver, element, screenshot_path, 'radio')
    except Exception as e:
        print(f'    ❌ Error: {e}')
        return False


def handle_checkbox(driver, element, screenshot_path: str) -> bool:
    print('    ☑️  Checkbox field')
    try:
        element.click()
        time.sleep(0.3)
        return take_element_screenshot(driver, element, screenshot_path, 'checkbox')
    except Exception as e:
        print(f'    ❌ Error: {e}')
        return False


def handle_file_input(driver, element, screenshot_path: str) -> bool:
    print('    📎 File input field')
    try:
        driver.execute_script("""
            var el = arguments[0];
            if (el.style.display === 'none' || el.style.visibility === 'hidden') {
                el.style.position = 'absolute';
                el.style.visibility = 'visible';
                el.style.opacity = '1';
            }
        """, element)
        time.sleep(0.3)
        return take_element_screenshot(driver, element, screenshot_path, 'file')
    except Exception as e:
        print(f'    ❌ Error: {e}')
        return False


def find_all_form_fields(driver) -> list:
    fields = []
    processed_names = set()
    
    inputs = driver.find_elements(By.TAG_NAME, 'input')
    for inp in inputs:
        inp_type = inp.get_attribute('type') or 'text'
        if inp_type == 'hidden':
            continue
        
        aria_hidden = inp.get_attribute('aria-hidden')
        tabindex = inp.get_attribute('tabindex')
        
        if aria_hidden == 'true' or tabindex == '-1':
            continue
        
        try:
            display = inp.value_of_css_property('display')
            visibility = inp.value_of_css_property('visibility')
            if display == 'none' or visibility == 'hidden':
                continue
        except:
            pass
        
        name = inp.get_attribute('name')
        
        if inp_type == 'checkbox' and name:
            if name in processed_names:
                continue
            checkboxes = driver.find_elements(By.NAME, name)
            if len(checkboxes) > 1:
                processed_names.add(name)
                fields.append({
                    'element': checkboxes[0],
                    'type': 'checkbox',
                    'tag': 'input',
                    'is_group': True
                })
                continue
        
        if inp_type == 'radio' and name:
            if name in processed_names:
                continue
            radios = driver.find_elements(By.NAME, name)
            if len(radios) > 1:
                processed_names.add(name)
                fields.append({
                    'element': radios[0],
                    'type': 'radio',
                    'tag': 'input',
                    'is_group': True
                })
                continue
        
        fields.append({
            'element': inp,
            'type': inp_type,
            'tag': 'input'
        })
    
    selects = driver.find_elements(By.TAG_NAME, 'select')
    for sel in selects:
        fields.append({
            'element': sel,
            'type': 'select',
            'tag': 'select'
        })
    
    textareas = driver.find_elements(By.TAG_NAME, 'textarea')
    for ta in textareas:
        fields.append({
            'element': ta,
            'type': 'textarea',
            'tag': 'textarea'
        })
    
    autocompletes = driver.find_elements(By.CSS_SELECTOR, '[role="combobox"], [role="listbox"], [aria-haspopup="listbox"]')
    for ac in autocompletes:
        tag = ac.tag_name.lower()
        if tag not in ['input', 'select']:
            fields.append({
                'element': ac,
                'type': 'autocomplete',
                'tag': tag
            })
    
    return fields


def extract_screenshots_from_page(driver, url: str, screenshot_folder: str = 'screenshots') -> int:
    print('🚀 Starting Screenshot Extraction...\n')
    print(f'📍 Navigating to: {url}\n')
    
    driver.get(url)
    time.sleep(3)
    
    print('🔍 Finding all form fields...\n')
    fields = find_all_form_fields(driver)
    print(f'✅ Found {len(fields)} form fields\n')
    
    screenshot_dir = Path(screenshot_folder)
    screenshot_dir.mkdir(exist_ok=True)
    
    print('=' * 60)
    print('📸 Taking screenshots of each field...\n')
    
    screenshot_count = 0
    processed_elements = set()
    
    for i, field_info in enumerate(fields, 1):
        element = field_info['element']
        field_type = field_info['type']
        tag = field_info['tag']
        
        try:
            element_id = element.id or element.get_attribute('name') or element.get_attribute('id') or f"{tag}_{i}"
            if element_id in processed_elements:
                continue
            processed_elements.add(element_id)
        except:
            element_id = f"{tag}_{i}"
        
        screenshot_filename = f"field_{i:03d}_{field_type}_{element_id}.png"
        screenshot_path = screenshot_dir / screenshot_filename
        
        print(f'[{i}/{len(fields)}] Processing {field_type} field: {element_id}')
        
        try:
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(0.3)
            
            success = False
            if field_type == 'text':
                success = handle_text_input(driver, element, str(screenshot_path))
            elif field_type == 'email':
                success = handle_email_input(driver, element, str(screenshot_path))
            elif field_type == 'tel':
                success = handle_tel_input(driver, element, str(screenshot_path))
            elif field_type == 'textarea':
                success = handle_textarea(driver, element, str(screenshot_path))
            elif field_type == 'select':
                success = handle_select_dropdown(driver, element, str(screenshot_path))
            elif field_type == 'autocomplete' or (tag == 'input' and element.get_attribute('role') == 'combobox'):
                success = handle_autocomplete_dropdown(driver, element, str(screenshot_path))
            elif field_type == 'radio':
                success = handle_radio_group(driver, element, str(screenshot_path))
            elif field_type == 'checkbox':
                success = handle_checkbox(driver, element, str(screenshot_path))
            elif field_type == 'file':
                success = handle_file_input(driver, element, str(screenshot_path))
            else:
                success = handle_text_input(driver, element, str(screenshot_path))
            
            if success:
                screenshot_count += 1
                print(f'    ✅ Screenshot saved: {screenshot_filename}')
            else:
                if Path(screenshot_path).exists():
                    screenshot_count += 1
                    print(f'    ✅ Screenshot file exists (counted despite error): {screenshot_filename}')
                else:
                    print(f'    ⚠️  Screenshot failed')
            
        except Exception as e:
            print(f'    ❌ Error processing field: {e}')
            if Path(screenshot_path).exists():
                screenshot_count += 1
                print(f'    ✅ Screenshot file exists (counted despite exception): {screenshot_filename}')
        
        print()
    
    print('=' * 60)
    print(f'✅ Screenshot extraction complete!')
    print(f'📁 Screenshots saved to: {screenshot_dir.absolute()}')
    print(f'📦 Total screenshots: {screenshot_count}/{len(fields)}')
    
    return screenshot_count


def main():
    from selenium.webdriver.chrome.options import Options
    
    chrome_options = Options()
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        url = 'https://job-boards.greenhouse.io/twilio/jobs/7394811'
        count = extract_screenshots_from_page(driver, url, 'screenshots')
        print(f'\n✅ Extraction complete! {count} screenshots saved.')
    except Exception as e:
        print(f'\n❌ Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        input('\nPress Enter to close browser...')
        driver.quit()


if __name__ == '__main__':
    main()