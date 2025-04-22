import logging
import pandas as pd
import json
import re
from pathlib import Path
import config
from time import time
import chardet # Import chardet

logger = logging.getLogger(__name__)

def detect_encoding(filepath):
    """Detect the encoding of a file."""
    try:
        with open(filepath, 'rb') as f:
            raw_data = f.read(10000)  # Read enough bytes to make a guess
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            confidence = result['confidence']
            logger.info(f"Detected encoding: {encoding} with confidence {confidence}")
            return encoding if confidence > 0.7 else 'utf-8' # Use detected if confidence is high
    except Exception as e:
        logger.warning(f"Could not detect encoding for {filepath}: {e}. Defaulting to utf-8.")
        return 'utf-8'

def load_recipe_data(limit=None):
    """
    Load recipe data from the dataset file, handling different JSON structures.
    
    Parameters:
    -----------
    limit : int, optional
        Limit the number of recipes to load. Default is None (load all).
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame containing recipe data
    """
    # Defensive: ensure limit is int if not None
    if limit is not None:
        try:
            limit = int(limit)
        except Exception:
            logger.warning(f"Could not convert limit '{limit}' to int. Setting limit to None.")
            limit = None
    
    try:
        start_time = time()
        dataset_path = Path(config.DATASET_PATH)
        
        if not dataset_path.exists():
            logger.error(f"Dataset file not found: {dataset_path}")
            return None
        
        logger.info(f"Loading recipe data from {dataset_path}")
        
        # Determine file type and encoding
        file_extension = dataset_path.suffix.lower()
        encoding = detect_encoding(dataset_path)
        
        if file_extension == '.csv':
            df = pd.read_csv(dataset_path, encoding=encoding)
        elif file_extension == '.json':
            logger.info(f"Loading JSON with encoding: {encoding}")
            with open(dataset_path, 'r', encoding=encoding) as f:
                # Peek at the first non-whitespace character
                first_char = ''
                while not first_char:
                    c = f.read(1)
                    if not c:
                        raise ValueError("JSON file appears to be empty.")
                    if not c.isspace():
                        first_char = c
                f.seek(0) # Reset file pointer

                if first_char == '[':
                    logger.info("Detected JSON Array format.")
                    # Load as list of objects
                    data = json.load(f)
                    df = pd.DataFrame(data)
                elif first_char == '{':
                    logger.info("Detected JSON Object format. Converting to list.")
                    # Load as object, then convert
                    data_dict = json.load(f)
                    recipes_list = []
                    for key, value in data_dict.items():
                        if isinstance(value, dict):
                            # Add the key as an 'id' field if not present
                            if 'id' not in value:
                                value['id'] = key 
                            recipes_list.append(value)
                        else:
                             logger.warning(f"Skipping non-dictionary value for key '{key}' in JSON object.")
                    df = pd.DataFrame(recipes_list)
                else:
                     raise ValueError(f"Unsupported JSON format: Does not start with [ or {{. Starts with: '{first_char}'")

        elif file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(dataset_path)
        else:
            logger.error(f"Unsupported file format: {file_extension}")
            return None
        
        # Apply limit if specified
        if limit is not None and limit > 0 and len(df) > limit:
            df = df.head(limit)
            logger.info(f"Limited dataset to {limit} recipes")
        
        # --- Column Mapping --- 
        logger.info("Checking and mapping columns...")
        # Define potential names for the core fields
        name_candidates = ['title', 'recipe_name', 'name']
        ingredients_candidates = ['ingredients', 'ingredient_list', 'ingredients_list', 'raw_ingredients']
        instructions_candidates = ['instructions', 'directions', 'steps']

        # Find the actual columns used in the DataFrame
        actual_name_col = next((col for col in name_candidates if col in df.columns), None)
        actual_ingredients_col = next((col for col in ingredients_candidates if col in df.columns), None)
        actual_instructions_col = next((col for col in instructions_candidates if col in df.columns), None)

        # Check if essential columns were found
        if not actual_name_col:
            logger.error(f"Could not find a suitable column for recipe name. Looked for: {name_candidates}. Found: {df.columns.tolist()}")
            return None
        if not actual_ingredients_col:
            logger.error(f"Could not find a suitable column for ingredients. Looked for: {ingredients_candidates}. Found: {df.columns.tolist()}")
            return None

        logger.info(f"Using '{actual_name_col}' for recipe name.")
        logger.info(f"Using '{actual_ingredients_col}' for ingredients.")
        if actual_instructions_col:
            logger.info(f"Using '{actual_instructions_col}' for instructions.")
        else:
            logger.warning("No instructions column found.")

        # --- Create Standardized DataFrame ---
        # Select and rename columns to standard names
        standard_df_data = {}
        standard_df_data['name'] = df[actual_name_col]
        standard_df_data['ingredients'] = df[actual_ingredients_col]
        if actual_instructions_col:
            standard_df_data['instructions'] = df[actual_instructions_col]
        else:
            standard_df_data['instructions'] = None # Ensure column exists even if empty
        
        # Add 'id' column - try to preserve original key if possible
        if 'id' in df.columns:
            standard_df_data['id'] = df['id']
        elif not isinstance(df.index, pd.RangeIndex):
             standard_df_data['id'] = df.index # Use index if it holds original keys
        else:
             standard_df_data['id'] = df.index # Fallback to range index

        df = pd.DataFrame(standard_df_data) # Replace original df with the standardized one
        logger.info(f"Standardized DataFrame columns: {df.columns.tolist()}")

        # --- Ingredient Processing --- 
        # Ensure 'ingredients' column is list type
        if 'ingredients' in df.columns:
            # Handle potential string representations of lists
            def parse_ingredient_list(x):
                if isinstance(x, str):
                    try:
                        # Try parsing as JSON list
                        parsed = json.loads(x)
                        if isinstance(parsed, list):
                            return parsed
                    except json.JSONDecodeError:
                        # If not JSON, split common delimiters
                        if ',' in x:
                            return [i.strip() for i in x.split(',')]
                        if '\n' in x:
                            return [i.strip() for i in x.split('\n')]
                        return [x] # Treat as single ingredient list
                elif isinstance(x, list):
                    return x
                else:
                    return [] # Return empty list for NaNs or other types
            
            df['ingredients'] = df['ingredients'].apply(parse_ingredient_list)
            logger.info("Standardized ingredients column to list format.")
            
            # Clean up ingredient text within the lists
            df['ingredients'] = df['ingredients'].apply(lambda ingredients: [clean_ingredient_text(i) for i in ingredients if i]) # Ensure i is not empty
            logger.info("Cleaned ingredient text.")
        else:
            logger.error("Critical error: 'ingredients' column could not be created or found.")
            return None

        logger.info(f"Successfully loaded and processed {len(df)} recipes in {time() - start_time:.2f} seconds")
        return df
    
    except Exception as e:
        logger.error(f"Error loading recipe data: {e}", exc_info=True)
        return None

def clean_ingredient_text(ingredient):
    """
    Clean up ingredient text by removing extra whitespace, punctuation, etc.
    
    Parameters:
    -----------
    ingredient : str
        Raw ingredient text
    
    Returns:
    --------
    str
        Cleaned ingredient text
    """
    if not isinstance(ingredient, str):
        return ""
    
    # Convert to lowercase
    text = ingredient.lower()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove quantities and units (optional)
    if config.REMOVE_QUANTITIES:
        # Remove common measurement units and quantities
        text = re.sub(r'\b\d+(\.\d+)?\s*(g|kg|oz|lb|cups?|tbsp|tsp|ml|l)\b', '', text)
        # Remove fractions like 1/2, 1/4, etc.
        text = re.sub(r'\b\d+/\d+\b', '', text)
        
    # Remove punctuation except hyphens in compound words
    text = re.sub(r'[^\w\s-]', '', text)
    
    return text.strip()

def preprocess_ingredients(ingredients_list):
    """
    Preprocess a list of ingredients to extract the core ingredient names.
    
    Parameters:
    -----------
    ingredients_list : list
        List of ingredient strings
    
    Returns:
    --------
    list
        List of preprocessed ingredient names
    """
    if not ingredients_list:
        return []
    
    processed = []
    
    for ingredient in ingredients_list:
        if not isinstance(ingredient, str) or not ingredient.strip():
            continue
        
        # Clean the text
        clean_text = clean_ingredient_text(ingredient)
        if not clean_text:
            continue
        
        # Remove preparation instructions
        # e.g., "onions, chopped" -> "onions"
        core_ingredient = re.sub(r',.*$', '', clean_text)
        core_ingredient = re.split(r'\s+(?:diced|chopped|sliced|minced|grated|peeled|crushed|ground|beaten|sifted|washed|rinsed)', core_ingredient)[0].strip()
        
        # Only add ingredients with meaningful content
        if core_ingredient and len(core_ingredient) > 1:
            processed.append(core_ingredient)
    
    return processed

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Test the loader
    recipes = load_recipe_data(limit=10)
    
    if recipes is not None:
        print(f"Loaded {len(recipes)} recipes")
        print(f"Columns: {recipes.columns.tolist()}")
        print("\nSample recipe:")
        # Ensure 'name' and 'ingredients' columns exist before printing
        if 'name' in recipes.columns and 'ingredients' in recipes.columns:
            print(recipes[['id','name', 'ingredients']].iloc[0])
        else:
            print("Could not display sample, missing 'name' or 'ingredients' column.")
    else:
        print("Failed to load recipes.") 