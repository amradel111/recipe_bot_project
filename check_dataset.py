import json
import pandas as pd
import os
import chardet
import config  # Import the config module

# Define the path to the dataset using the config file
dataset_path = config.DATASET_PATH

# Check if the file exists
print(f"Checking if file exists at: {dataset_path}")
print(f"File exists: {os.path.exists(dataset_path)}")
print(f"File size: {os.path.getsize(dataset_path) / (1024*1024):.2f} MB")

# Try to detect file encoding
print("\nDetecting file encoding...")
encoding = 'utf-8'  # Default encoding
try:
    with open(dataset_path, 'rb') as f:
        raw_data = f.read(10000)  # Read the first 10,000 bytes
        result = chardet.detect(raw_data)
        detected_encoding = result['encoding']
        if detected_encoding:
            encoding = detected_encoding
            print(f"Detected encoding: {encoding} (confidence: {result['confidence']})")
        else:
            print("Could not detect encoding, defaulting to UTF-8")
except Exception as e:
    print(f"Error detecting encoding: {e}")
    print("Defaulting to UTF-8 encoding")

# Try to read the first few lines and parse the first recipe structure
print("\nReading the beginning of the file to find the first recipe structure...")
keys_found = None
try:
    with open(dataset_path, 'r', encoding=encoding) as f:
        # Find the first opening brace/bracket
        first_char = ''
        while not first_char:
            first_char = f.read(1)
            if not first_char: # End of file
                raise ValueError("File appears to be empty or doesn't start with JSON.")
            first_char = first_char.strip()

        if first_char == '[':
            print("Detected JSON Array structure.")
            start_token = '{'
            end_token = '}'
            is_list = True
        elif first_char == '{':
            print("Detected JSON Object structure.")
            start_token = '"' # Keys start with quotes in JSON objects
            end_token = ':' # Key ends before the colon
            is_list = False
            # Need to read more to find the first value brace
            f.seek(0) # Go back to start
            buffer = f.read(20000)
            first_key_start = buffer.find('"')
            first_key_end = buffer.find('"', first_key_start + 1)
            first_colon = buffer.find(':', first_key_end)
            first_value_brace = buffer.find('{', first_colon)
            if first_value_brace == -1:
                 raise ValueError("Could not find opening brace '{' for the first value in JSON object.")
            f.seek(first_value_brace) # Position stream at start of first value object
            start_token = '{'
            end_token = '}'
        else:
            raise ValueError(f"File does not start with JSON array '[' or object '{{'. Found: '{first_char}'")

        # Reset stream position to start of first actual data object
        f.seek(f.tell() - 1) # Go back one character to include the starting brace/bracket
        
        # Find the start of the first data object
        buffer = f.read(20000) # Read a larger buffer
        start_index = buffer.find(start_token)
        if start_index == -1:
            raise ValueError(f"Could not find the start token '{start_token}' in the first 20KB.")

        # Find the corresponding end token for the first object/key-value pair
        brace_level = 0
        end_index = -1
        in_string = False
        escaped = False

        for i, char in enumerate(buffer[start_index:]):
            if char == '"' and not escaped:
                in_string = not in_string
            elif char == '\\' and not escaped:
                escaped = True
                continue
            elif not in_string:
                if char == '{' or (not is_list and char == start_token):
                    brace_level += 1
                elif char == '}' or (not is_list and char == end_token and brace_level == 1): # Found end of key
                    brace_level -= 1
                    if brace_level == 0:
                        end_index = start_index + i
                        break
                elif is_list and char == '}': # End of object in list
                     brace_level -=1
                     if brace_level == 0:
                         end_index = start_index + i
                         break
            escaped = False

        if end_index == -1:
            raise ValueError(f"Could not find the end token for the first element within the buffer (token:'{end_token}').")

        # Extract the first element string
        first_element_str = buffer[start_index : end_index + (1 if is_list else 0)] # Include closing brace for list item
        if not is_list: # If it's an object, we only read the key. Need to read the value
            # Re-read from start of value
             f.seek(first_value_brace)
             buffer = f.read(20000)
             start_index = buffer.find('{')
             # Repeat finding the end brace for the value object
             brace_level = 0
             end_index = -1
             in_string = False
             escaped = False
             for i, char in enumerate(buffer[start_index:]):
                 if char == '"' and not escaped:
                     in_string = not in_string
                 elif char == '\\' and not escaped:
                     escaped = True
                     continue
                 elif not in_string:
                     if char == '{':
                         brace_level += 1
                     elif char == '}':
                         brace_level -= 1
                         if brace_level == 0:
                             end_index = start_index + i
                             break
                 escaped = False
             if end_index == -1:
                 raise ValueError("Could not find end brace for first value object")
             first_element_str = buffer[start_index: end_index + 1]


        # Parse just the first element
        first_data = json.loads(first_element_str)
        keys_found = list(first_data.keys())

        print("\nSuccessfully parsed the first data element structure.")
        print(f"Keys found in the first element: {keys_found}")

except FileNotFoundError:
    print(f"Error: File not found at {dataset_path}")
except UnicodeDecodeError as e:
    print(f"Error: Could not decode the file with {encoding}. The detected encoding might be wrong ({e}).")
except json.JSONDecodeError as e:
    print(f"Error decoding JSON from the first part of the file: {e}")
    print(f"String being parsed: {first_element_str[:200]}...") # Print part of the string that failed
    print("The file might be corrupted or not in the expected JSON format near the beginning.")
except ValueError as e:
    print(f"Error processing the file structure: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")


# Compare with expected columns from data_loader perspective
if keys_found:
    print("\nComparing found keys with expected columns ('title', 'ingredients') mapped in data_loader...")
    # Keys data_loader expects or can map
    expected_keys = {'name', 'ingredients', 'title', 'recipe_name', 'ingredient_list', 'ingredients_list', 'raw_ingredients'}
    
    # Check if at least one name key and one ingredients key is present
    name_key_present = any(k in keys_found for k in ['name', 'title', 'recipe_name'])
    ingredients_key_present = any(k in keys_found for k in ['ingredients', 'ingredient_list', 'ingredients_list', 'raw_ingredients'])
    
    if name_key_present and ingredients_key_present:
        print("Found compatible keys for 'name' and 'ingredients' based on data_loader mapping.")
        if 'title' in keys_found:
            print("  - Using 'title' for recipe name.")
        elif 'recipe_name' in keys_found:
             print("  - Using 'recipe_name' for recipe name.")
        elif 'name' in keys_found:
             print("  - Using 'name' for recipe name.")
             
        if 'ingredients' in keys_found:
            print("  - Using 'ingredients' for ingredients.")
        elif 'ingredient_list' in keys_found:
            print("  - Using 'ingredient_list' for ingredients.")
        elif 'ingredients_list' in keys_found:
            print("  - Using 'ingredients_list' for ingredients.")
        elif 'raw_ingredients' in keys_found:
            print("  - Using 'raw_ingredients' for ingredients.")
    else:
        print("Warning: Could not find compatible keys for both 'name' and 'ingredients' based on data_loader mapping.")
        if not name_key_present:
            print("  - Missing a key like 'name', 'title', or 'recipe_name'.")
        if not ingredients_key_present:
             print("  - Missing a key like 'ingredients', 'ingredient_list', 'ingredients_list', or 'raw_ingredients'.")
        print("The data_loader will likely fail or require adjustments.")

print("\nDone.") 