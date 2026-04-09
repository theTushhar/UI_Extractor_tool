import json
import argparse
from lxml import html
from lxml.cssselect import CSSSelector

def verify_single_locator(root, tree, strategy, value, ground_truth_xpath):
    matches = []
    try:
        if strategy.startswith("xpath:"):
            matches = root.xpath(value)
        else:
            selector = CSSSelector(value)
            matches = selector(root)
    except Exception as e:
        return "error", 0, False

    match_count = len(matches)
    is_correct_element = False
    
    if match_count == 0:
        return "broken", 0, False
    
    # Check if ground truth element is in matches
    for match in matches:
        if tree.getpath(match) == ground_truth_xpath:
            is_correct_element = True
            break
            
    if match_count == 1:
        if is_correct_element:
            return "correct", 1, True
        else:
            return "misidentified", 1, False
    else:
        return "duplicate", match_count, is_correct_element

def main():
    parser = argparse.ArgumentParser(description="Verify UI locators against HTML content.")
    parser.add_argument("--data", required=True, help="Path to the JSON data file (containing html and elements).")
    parser.add_argument("--html-file", help="Path to an external HTML file (optional, overrides JSON html).")
    
    args = parser.parse_args()
    
    with open(args.data, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    html_content = data.get("html")
    if args.html_file:
        with open(args.html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
    if not html_content:
        print("Error: No HTML content found in JSON or external file.")
        return

    root = html.fromstring(html_content)
    tree = root.getroottree()
    
    elements = data.get("elements", [])
    if not elements:
        # Check if it's the newer format with page inventory
        elements = data.get("inventory", {}).get("elements", [])
    
    print(f"\nVerifying {len(elements)} elements...\n")
    print(f"{'Status':<15} | {'Count':<5} | {'Strategy':<20} | {'Value'}")
    print("-" * 80)
    
    summary = {"correct": 0, "broken": 0, "duplicate": 0, "misidentified": 0, "error": 0}
    
    for el in elements:
        name = el.get("element_name", "Unnamed")
        gt_xpath = el.get("absolute_xpath")
        
        if not gt_xpath:
            print(f"! Skipping {name}: No absolute_xpath found.")
            continue
            
        locators = el.get("locators", [])
        # Also check recommended_locator
        rec = el.get("recommended_locator")
        if rec:
            locators = [rec] + locators

        for loc in locators:
            strategy = loc.get("strategy")
            value = loc.get("value")
            
            status, count, is_correct = verify_single_locator(root, tree, strategy, value, gt_xpath)
            summary[status] += 1
            
            color = ""
            if status == "correct": color = "\033[92m" # Green
            elif status == "broken": color = "\033[91m" # Red
            elif status == "duplicate": color = "\033[93m" # Yellow
            
            reset = "\033[0m"
            
            print(f"{color}{status.upper():<15}{reset} | {count:<5} | {strategy:<20} | {value}")

    print("\n" + "="*30)
    print("Verification Summary")
    print("="*30)
    for k, v in summary.items():
        print(f"{k.capitalize():<15}: {v}")
    print("="*30)

if __name__ == "__main__":
    main()
