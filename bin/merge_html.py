from bs4 import BeautifulSoup
import hashlib

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

if __name__ == "__main__":
    input_file = 'ppv2_result.html'
    output_file = 'ppv2_result_merged.html'
    merge_html_file(input_file, output_file)