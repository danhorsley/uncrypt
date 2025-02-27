import csv
import re

def parse_gutenberg_text(file_path):
    """Parse a Gutenberg text file to extract quotes and attributions."""
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    records = []
    current_major = None
    quote_lines = []
    
    for line in lines:
        line = line.strip()  # Remove leading/trailing whitespace
        if not line or "[Footnote:" in line:
            continue  # Skip empty lines and footnotes
        
        # Check if the line is a major attribution (all uppercase)
        if re.match(r'^(?=.*[A-Z])[A-Z0-9 \.\-]+$', line) and line!="PAGE":
            current_major = line
            continue
        
        # Check if the line is a minor attribution (starts with "_")
        if line.startswith("_"):
            if quote_lines:  # If we have collected a quote
                quote = " ".join(quote_lines)
                minor = line.strip("_").strip()  # Remove underscores and extra whitespace
                records.append({
                    "Major Attribution": current_major,
                    "Minor Attribution": minor,
                    "Quote": quote
                })
                quote_lines = []  # Reset quote collector
        else:
            # Assume this is part of a quote (not starting with "_")
            quote_lines.append(line)
    
    return records

def write_to_csv(records, csv_path):
    """Write the extracted records to a CSV file."""
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["Major Attribution", "Minor Attribution", "Quote"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record)

# Usage example
file_path = 'gutenberg.txt'  # Replace with your file path
csv_path = 'quotes.csv'
records = parse_gutenberg_text(file_path)
write_to_csv(records, csv_path)