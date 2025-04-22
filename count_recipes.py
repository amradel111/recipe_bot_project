import json
import os
import sys
from pathlib import Path

# Add project root to sys.path to allow importing config
project_dir = Path(__file__).resolve().parents[1] # Should point to D:\chatbot-project
sys.path.insert(0, str(project_dir))

# Now import config from the recipe_bot_project package
from recipe_bot_project import config


# Load the JSON data
json_path = config.DATASET_PATH

print(f"Counting recipes in {json_path}...")

try:
    # Check if file exists
    if not os.path.exists(json_path):
        print(f"Error: Dataset file not found at {json_path}")
        sys.exit(1)
    
    # Process file in a memory-efficient way
    counter = 0
    with open(json_path, 'r', encoding='utf-8') as f:
        # Count opening braces after colons to estimate recipe count
        # This is a rough approximation that will work for our dictionary format
        in_quotes = False
        escape_next = False
        
        # Track recipe separators (commas outside of quotes at the top level)
        brace_level = 0
        
        for char in f.read():
            # Handle escape sequences
            if char == '\\':
                escape_next = True
                continue
            
            if escape_next:
                escape_next = False
                continue
                
            # Handle quotes
            if char == '"' and not escape_next:
                in_quotes = not in_quotes
                continue
                
            # Only count outside of quotes
            if not in_quotes:
                if char == '{':
                    brace_level += 1
                    if brace_level == 2:  # We're inside a recipe object
                        counter += 1
                        
                        # Print progress
                        if counter % 1000 == 0:
                            print(f"Counted {counter} recipes so far...")
                elif char == '}':
                    brace_level -= 1
    
    print(f"Total recipes in the dataset: {counter}")
    
except Exception as e:
    print(f"Error: {str(e)}")
    sys.exit(1) 