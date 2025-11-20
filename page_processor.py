import re
import time
import hashlib
from typing import List
from pathlib import Path
from bs4 import BeautifulSoup
from selenium import webdriver
from bs4 import BeautifulSoup, Tag
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def has_meaningful_content(tag):
    if tag.name == 'input':
        return tag.get('value', '').strip() != ''
    elif tag.name == 'textarea':
        return tag.text.strip() != ''
    elif tag.name == 'select':
        options = tag.find_all('option')
        return any(opt.get('value', '').strip() not in ('', 'placeholder') for opt in options)
    else:
        return tag.decode_contents().strip() != ''

def dedupe_html(soup):
    seen = {}
    for tag in soup.find_all(True, recursive=True):
        if not hasattr(tag, 'name') or tag.name is None:
            continue

        classes = tag.get('class', [])
        if classes is None:
            classes = []

        content_hash = hashlib.md5(tag.decode_contents().encode('utf-8')).hexdigest()
        key = (tag.name, tuple(classes), tag.get('id'), content_hash)

        if key not in seen:
            seen[key] = tag
        else:
            existing_tag = seen[key]
            if not has_meaningful_content(existing_tag) and has_meaningful_content(tag):
                existing_tag.replace_with(tag)
                seen[key] = tag
            else:
                tag.decompose()
    return soup

def merge_html_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    merged_soup = dedupe_html(soup)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(str(merged_soup))

def wait_for_page_load(driver: WebDriver, timeout: int = 10) -> None:
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        time.sleep(2)
    except TimeoutException:
        pass

def get_full_html(driver: WebDriver) -> str:
    return driver.page_source

def get_element_unique_id(element) -> str:
    try:
        eid = element.get_attribute('id')
        if eid:
            return f"id:{eid}"
        ename = element.get_attribute('name')
        if ename:
            return f"name:{ename}"
        for attr in ['data-testid', 'data-id', 'data-name']:
            val = element.get_attribute(attr)
            if val:
                return f"{attr}:{val}"
        loc = element.location
        size = element.size
        tag = element.tag_name
        return f"tag:{tag}_loc:{loc['x']},{loc['y']}_size:{size['width']},{size['height']}"
    except:
        return f"unknown_{id(element)}"

def find_all_dropdowns(driver: WebDriver) -> List[dict]:
    dropdowns = []
    seen_ids = set()
    selects = driver.find_elements(By.TAG_NAME, 'select')
    for s in selects:
        try:
            if s.is_displayed() and s.is_enabled():
                uid = get_element_unique_id(s)
                if uid not in seen_ids:
                    seen_ids.add(uid)
                    dropdowns.append({'element': s, 'type': 'select', 'name': uid})
        except: continue
    custom = driver.find_elements(By.CSS_SELECTOR, '[role="combobox"], [aria-haspopup="listbox"], [role="listbox"]')
    for c in custom:
        try:
            if c.is_displayed() and c.is_enabled():
                uid = get_element_unique_id(c)
                if uid not in seen_ids:
                    seen_ids.add(uid)
                    dropdowns.append({'element': c, 'type': 'custom', 'name': uid})
        except: continue
    search_fields = driver.find_elements(By.CSS_SELECTOR,
        'input[type="search"], input[autocomplete], input[list], input[class*="search"], input[class*="autocomplete"], input[class*="combobox"]')
    for f in search_fields:
        try:
            if f.is_displayed() and f.is_enabled():
                uid = get_element_unique_id(f)
                if uid not in seen_ids:
                    seen_ids.add(uid)
                    dropdowns.append({'element': f, 'type': 'search', 'name': uid})
        except: continue
    return dropdowns

def click_dropdown(driver: WebDriver, dropdown_info: dict) -> bool:
    el = dropdown_info['element']
    try:
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", el)
        time.sleep(0.2)
        try:
            el.click()
            if dropdown_info['type'] == 'search':
                el.send_keys('a')
                time.sleep(0.5)
                el.clear()
            return True
        except:
            driver.execute_script("arguments[0].click();", el)
            if dropdown_info['type'] == 'search':
                driver.execute_script("arguments[0].value='a'; arguments[0].dispatchEvent(new Event('input'));", el)
                time.sleep(0.5)
                driver.execute_script("arguments[0].value='';", el)
            return True
    except:
        return False

def expand_all_dropdowns(driver: WebDriver) -> (List[str], List[str]):
    dropdowns = find_all_dropdowns(driver)
    html_snapshots = []
    dropdown_names = []
    html_snapshots.append(get_full_html(driver))
    dropdown_names.append("Base HTML")
    processed = set()
    for dd in dropdowns:
        uid = dd['name']
        if uid in processed:
            continue
        processed.add(uid)
        if click_dropdown(driver, dd):
            time.sleep(1.7)
            html_snapshots.append(get_full_html(driver))
            dropdown_names.append(uid)
            try:
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(0.5)
            except:
                pass
    return html_snapshots, dropdown_names

def save_all_dropdowns_in_one_html(html_snapshots: list, dropdown_names: list, output_path: str = "all_dropdowns.html"):
    base_soup = BeautifulSoup("<html><head><meta charset='utf-8'></head><body></body></html>", "html.parser")
    body = base_soup.find('body')
    for idx, html in enumerate(html_snapshots):
        name = dropdown_names[idx] if idx < len(dropdown_names) else f"Dropdown_{idx+1}"
        section_tag = base_soup.new_tag("section")
        section_tag.string = name
        body.append(section_tag)
        snapshot_soup = BeautifulSoup(html, 'html.parser')
        snapshot_body = snapshot_soup.find('body') or snapshot_soup
        for tag_name in ['script', 'style', 'noscript', 'iframe', 'img', 'meta', 'link', 'head', 'path', 'svg']:
            for tag in snapshot_body.find_all(tag_name):
                tag.decompose()
        for tag in snapshot_body.find_all(True):
            for attr in list(tag.attrs):
                if attr not in ['id','name','type','value','for','aria-label','aria-labelledby','aria-required','role','placeholder','style']:
                    del tag[attr]
        body.append(snapshot_body)
    return base_soup

def process_page(driver: WebDriver, url: str, output_path: str = "all_dropdowns.html"):
    driver.get(url)
    wait_for_page_load(driver)
    html_snapshots, dropdown_names = expand_all_dropdowns(driver)
    soup = save_all_dropdowns_in_one_html(html_snapshots, dropdown_names, output_path)
    merged_soup = dedupe_html(soup)
    with open('pp_result.html', 'w', encoding='utf-8') as f:
        f.write(str(merged_soup))
    print(len(str(merged_soup)))