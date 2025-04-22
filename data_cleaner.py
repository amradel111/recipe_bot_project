"""
Data cleaning module for Recipe Bot.
This module contains functions to clean and process recipe ingredients data.
"""

import re
import pandas as pd
from collections import Counter
import config
import logging
import os

logger = logging.getLogger(__name__)

# If using NLTK
if config.USE_NLTK:
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.stem import WordNetLemmatizer
    from nltk.corpus import stopwords
    
    lemmatizer = WordNetLemmatizer()
    STOP_WORDS = set(stopwords.words('english'))

# Common cooking units of measurement to remove
UNITS = [
    'cup', 'cups', 'tablespoon', 'tablespoons', 'tbsp', 'teaspoon', 'teaspoons', 'tsp',
    'pound', 'pounds', 'lb', 'lbs', 'ounce', 'ounces', 'oz', 'gram', 'grams', 'g',
    'kilogram', 'kilograms', 'kg', 'ml', 'milliliter', 'milliliters', 'liter', 'liters',
    'l', 'quart', 'quarts', 'qt', 'pint', 'pints', 'pt', 'gallon', 'gallons', 'gal',
    'pinch', 'pinches', 'dash', 'dashes', 'bunch', 'bunches', 'clove', 'cloves',
    'slice', 'slices', 'piece', 'pieces', 'drop', 'drops', 'handful', 'handfuls',
    'stick', 'sticks', 'package', 'packages', 'pack', 'packs', 'can', 'cans',
    'jar', 'jars', 'bottle', 'bottles', 'container', 'containers', 'box', 'boxes',
    'inch', 'inches', 'in'
]

# Common preparation terms to remove
PREP_TERMS = [
    'diced', 'chopped', 'minced', 'sliced', 'grated', 'shredded', 'peeled', 'crushed',
    'mashed', 'boiled', 'steamed', 'roasted', 'baked', 'fried', 'sautéed', 'sauteed',
    'grilled', 'broiled', 'poached', 'cored', 'seeded', 'pitted', 'trimmed', 'washed',
    'cleaned', 'rinsed', 'dried', 'deveined', 'deboned', 'skinless', 'boneless',
    'thawed', 'frozen', 'melted', 'softened', 'room temperature', 'cold', 'hot',
    'warm', 'fresh', 'dried', 'ground', 'powdered', 'whole', 'halved', 'quartered',
    'cubed', 'julienned', 'torn', 'crumbled', 'cooked', 'raw', 'uncooked', 'beaten',
    'whisked', 'mixed'
]

# Common compound ingredients that should be kept together
COMPOUND_INGREDIENTS = [
    'olive oil', 'vegetable oil', 'canola oil', 'sesame oil', 'coconut oil', 'peanut oil',
    'all purpose flour', 'all-purpose flour', 'cake flour', 'bread flour', 'whole wheat flour',
    'baking powder', 'baking soda', 'cream cheese', 'sour cream', 'heavy cream', 'whipping cream',
    'tomato sauce', 'tomato paste', 'red wine', 'white wine', 'rice vinegar', 'balsamic vinegar',
    'maple syrup', 'vanilla extract', 'almond extract', 'chicken broth', 'beef broth', 'vegetable broth',
    'soy sauce', 'fish sauce', 'worcestershire sauce', 'hot sauce', 'lime juice', 'lemon juice',
    'orange juice', 'bell pepper', 'green onion', 'green bean', 'brown sugar', 'powdered sugar',
    'confectioners sugar', 'peanut butter', 'cream of tartar', 'whipped cream', 'coconut milk',
    'almond milk', 'buttermilk', 'sea salt', 'kosher salt', 'black pepper', 'red pepper'
]

# Common descriptors to avoid as main ingredients
DESCRIPTIVE_TERMS = [
    'fresh', 'dried', 'frozen', 'canned', 'chopped', 'minced', 'diced', 'sliced', 'grated',
    'peeled', 'pitted', 'seeded', 'large', 'small', 'medium', 'finely', 'coarsely',
    'thinly', 'roughly', 'freshly', 'ground', 'cold', 'hot', 'warm', 'softened', 'melted',
    'cubed', 'divided', 'unsalted', 'salted', 'skinless', 'boneless', 'organic', 'extra',
    'virgin', 'low-fat', 'fat-free', 'reduced', 'packed', 'heaping', 'level', 'sifted',
    'crushed', 'crumbled', 'rolled', 'steel-cut', 'instant', 'condensed', 'sweetened',
    'unsweetened', 'light', 'dark', 'toasted', 'roasted', 'smoked', 'raw'
]

# Basic ingredient categories to help weight important ingredients more than others
IMPORTANT_INGREDIENTS = [
    'chicken', 'beef', 'pork', 'lamb', 'turkey', 'fish', 'salmon', 'tuna', 'shrimp', 'tofu',
    'rice', 'pasta', 'noodle', 'bread', 'potato', 'bean', 'lentil', 'quinoa', 'egg',
    'flour', 'sugar', 'butter', 'oil', 'milk', 'cream', 'yogurt', 'cheese',
    'onion', 'garlic', 'tomato', 'carrot', 'celery', 'pepper', 'lettuce', 'spinach',
    'broccoli', 'cauliflower', 'corn', 'pea', 'mushroom', 'avocado', 'cucumber',
    'apple', 'banana', 'orange', 'lemon', 'lime', 'berry', 'strawberry', 'blueberry',
    'chocolate', 'vanilla', 'cinnamon', 'nutmeg', 'ginger', 'cumin', 'curry', 'basil',
    'oregano', 'thyme', 'rosemary', 'cilantro', 'parsley', 'mint', 'salt', 'pepper'
]

def clean_and_extract_ingredients(raw_ingredients_data):
    """
    Clean and extract ingredient names from raw ingredient data.
    
    Parameters:
    -----------
    raw_ingredients_data : str or list
        Raw ingredient data (could be a string or a list, depending on dataset).
        
    Returns:
    --------
    list
        List of cleaned, lemmatized ingredient names.
    """
    # Log the input data type for debugging
    logger.debug(f"Raw ingredients data type: {type(raw_ingredients_data)}")
    
    # Convert to list if it's a string or handle other types
    if isinstance(raw_ingredients_data, str):
        # Check if it looks like a JSON string and try to parse it
        if raw_ingredients_data.startswith('[') and raw_ingredients_data.endswith(']'):
            try:
                import json
                raw_ingredients_data = json.loads(raw_ingredients_data)
                logger.debug("Converted JSON string to list")
            except:
                # If parsing fails, treat as comma-separated
                raw_ingredients_data = [ingr.strip() for ingr in raw_ingredients_data.split(',')]
                logger.debug("Split string by commas")
        else:
            # Treat as comma-separated
            raw_ingredients_data = [ingr.strip() for ingr in raw_ingredients_data.split(',')]
            logger.debug("Split string by commas")
    elif not isinstance(raw_ingredients_data, list):
        # Convert to string if it's another type
        raw_ingredients_data = [str(raw_ingredients_data)]
        logger.debug(f"Converted {type(raw_ingredients_data)} to list with string")
    
    # Now raw_ingredients_data should be a list
    cleaned_ingredients = []
    
    for ingredient in raw_ingredients_data:
        # Convert to string if it's not already
        if not isinstance(ingredient, str):
            ingredient = str(ingredient)
            
        # Convert to lowercase
        ingredient = ingredient.lower()
        
        # Check for compound ingredients first
        compound_found = False
        for compound in COMPOUND_INGREDIENTS:
            if compound in ingredient:
                cleaned_ingredients.append(compound)
                compound_found = True
                break
                
        # If a compound ingredient was found, skip the rest of processing for this ingredient
        if compound_found:
            continue
        
        # Remove quantities (numbers, fractions, etc.)
        ingredient = re.sub(r'\d+\s*\/\s*\d+', '', ingredient)  # Remove fractions like 1/2
        ingredient = re.sub(r'\d+\s*\.\s*\d+', '', ingredient)  # Remove decimals like 0.5
        ingredient = re.sub(r'\d+', '', ingredient)  # Remove integers
        
        # Remove units of measurement
        for unit in UNITS:
            ingredient = re.sub(r'\b' + unit + r'\b', '', ingredient)
        
        # Remove preparation instructions
        for prep in PREP_TERMS:
            ingredient = re.sub(r'\b' + prep + r'\b', '', ingredient)
            
        # Remove additional parenthetical information
        ingredient = re.sub(r'\([^)]*\)', '', ingredient)
        
        # Remove extra spaces and punctuation
        ingredient = re.sub(r'[^\w\s]', ' ', ingredient)
        ingredient = re.sub(r'\s+', ' ', ingredient).strip()
        
        if ingredient:
            # Process with NLTK or spaCy
            if config.USE_NLTK:
                tokens = word_tokenize(ingredient)
                # Lemmatize tokens
                lemmas = [lemmatizer.lemmatize(token) for token in tokens 
                         if token.isalpha() and token not in STOP_WORDS]
                
                if lemmas:
                    # Filter out descriptive terms
                    core_lemmas = [lemma for lemma in lemmas if lemma not in DESCRIPTIVE_TERMS]
                    if not core_lemmas:
                        # If all terms were filtered out, use original lemmas but try to avoid descriptors
                        for lemma in lemmas:
                            if lemma not in DESCRIPTIVE_TERMS:
                                cleaned_ingredients.append(lemma)
                                break
                    else:
                        # Try to find an important ingredient first
                        important_found = False
                        for lemma in core_lemmas:
                            if lemma in IMPORTANT_INGREDIENTS:
                                cleaned_ingredients.append(lemma)
                                important_found = True
                                break
                        
                        # If no important ingredient was found, use the longest non-descriptive lemma
                        if not important_found and core_lemmas:
                            main_ingredient = max(core_lemmas, key=len)
                            cleaned_ingredients.append(main_ingredient)
            else:
                # Using spaCy
                # This part requires spaCy to be installed and a model loaded
                # Assuming config.nlp is a loaded spaCy model if USE_NLTK is False
                if hasattr(config, 'nlp') and config.nlp:
                    doc = config.nlp(ingredient)
                    tokens = [token.lemma_ for token in doc 
                             if token.is_alpha and not token.is_stop]
                    
                    if tokens:
                        # Filter out descriptive terms
                        core_tokens = [token for token in tokens if token not in DESCRIPTIVE_TERMS]
                        if not core_tokens:
                            # If all terms were filtered out, use original tokens but try to avoid descriptors
                            for token in tokens:
                                if token not in DESCRIPTIVE_TERMS:
                                    cleaned_ingredients.append(token)
                                    break
                        else:
                            # Try to find an important ingredient first
                            important_found = False
                            for token in core_tokens:
                                if token in IMPORTANT_INGREDIENTS:
                                    cleaned_ingredients.append(token)
                                    important_found = True
                                    break
                            
                            # If no important ingredient was found, use the longest non-descriptive token
                            if not important_found and core_tokens:
                                main_ingredient = max(core_tokens, key=len)
                                cleaned_ingredients.append(main_ingredient)
                else:
                    logger.warning("config.USE_NLTK is False, but spaCy model (config.nlp) not loaded. Skipping spaCy processing.")
                    # Fallback or simply skip if spaCy isn't configured
                    cleaned_ingredients.append(ingredient) # Add the minimally cleaned ingredient as fallback
    
    # Remove duplicates and return
    # Using dict.fromkeys preserves order while removing duplicates
    return list(dict.fromkeys(cleaned_ingredients))

def apply_cleaning_to_dataframe(df, raw_col_name, new_col_name):
    """
    Apply ingredient cleaning to all recipes in a DataFrame.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing recipe data.
    raw_col_name : str
        Name of the column containing raw ingredients.
    new_col_name : str
        Name for the new column to store cleaned ingredients.
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with an additional column for cleaned ingredients.
    """
    # Ensure the raw column exists
    if raw_col_name not in df.columns:
        logger.error(f"Raw ingredient column '{raw_col_name}' not found in DataFrame. Cannot apply cleaning.")
        return df # Return original df
    
    # Apply cleaning function to each row, handling potential errors
    logger.info(f"Applying cleaning to column '{raw_col_name}' to create '{new_col_name}'")
    def safe_clean(x):
        # Handle NaN, None, and ambiguous array/list types
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return []
        # If x is a numpy array, check if all values are nan
        if hasattr(x, 'dtype') and hasattr(x, 'all'):
            try:
                if pd.isna(x).all():
                    return []
            except Exception:
                pass
        return clean_and_extract_ingredients(x)
    df[new_col_name] = df[raw_col_name].apply(safe_clean)
    logger.info("Finished applying cleaning.")
    return df

def get_canonical_ingredients(df, cleaned_col_name):
    """
    Get a set of all unique canonical ingredients from the cleaned ingredient lists.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing cleaned ingredient lists.
    cleaned_col_name : str
        Name of the column containing cleaned ingredient lists.
        
    Returns:
    --------
    set
        Set of unique canonical ingredient lemmas.
    """
    # Ensure the cleaned column exists
    if cleaned_col_name not in df.columns:
        logger.error(f"Cleaned ingredient column '{cleaned_col_name}' not found. Cannot extract canonical ingredients.")
        return set()
        
    # Flatten the list of lists and convert to a set to get unique values
    all_ingredients = [ingredient for sublist in df[cleaned_col_name].dropna().tolist() for ingredient in sublist]
    
    # Count occurrences to find the most common ingredients
    ingredient_counts = Counter(all_ingredients)
    
    # Print some statistics
    logger.info(f"Found {len(ingredient_counts)} unique ingredients after cleaning.")
    logger.info("Top 20 most common cleaned ingredients:")
    for ingredient, count in ingredient_counts.most_common(20):
        logger.info(f"  {ingredient}: {count} occurrences")
    
    return set(all_ingredients)

def adapt_column_names(df):
    """
    Adapt column names from the sample file to match expected column names.
    This function is likely superseded by the logic in data_loader.py
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame to adapt columns for.
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with adapted column names.
    """
    logger.warning("adapt_column_names in data_cleaner.py might be redundant due to logic in data_loader.py")
    # Define expected columns (these should align with data_loader needs)
    expected_cols = {
        'name': ['title', 'recipe_name', 'name'],
        'ingredients': ['ingredients', 'ingredient_list', 'ingredients_list', 'raw_ingredients'],
        'instructions': ['instructions', 'directions', 'steps']
    }
    
    rename_map = {}
    for standard_name, possible_names in expected_cols.items():
        actual_col = next((col for col in possible_names if col in df.columns), None)
        if actual_col and actual_col != standard_name:
            rename_map[actual_col] = standard_name
            logger.info(f"Mapping column '{actual_col}' to standard name '{standard_name}'")
            
    if rename_map:
        df = df.rename(columns=rename_map)
    
    return df

if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Add project root to sys.path to allow importing config and load_data
    project_dir = Path(__file__).resolve().parents[1] # Should point to D:\chatbot-project
    sys.path.insert(0, str(project_dir))

    # Now import config and load_data from the correct location
    from recipe_bot_project import config
    from recipe_bot_project.data_loader import load_recipe_data # Import specific function
    
    # Configure logging for testing
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # --- Use standard columns defined in config --- 
    # These names are now globally defined in config.py
    # STANDARD_RECIPE_NAME_COL = "name" # Now use config.RECIPE_NAME_COLUMN
    # STANDARD_RAW_INGREDIENTS_COL = "ingredients" # Now use config.RAW_INGREDIENTS_COLUMN
    # STANDARD_CLEANED_INGREDIENTS_COL = "cleaned_ingredients" # Now use config.CLEANED_INGREDIENTS_COLUMN

    try:
        logger.info(f"Loading recipe dataset from: {config.DATASET_PATH}")
        
        # Check if the dataset file exists
        if not os.path.exists(config.DATASET_PATH):
            logger.error(f"ERROR: Dataset file not found at: {config.DATASET_PATH}")
            logger.error("Please update the DATASET_PATH in config.py to point to the correct dataset file.")
            exit(1)
            
        # Load the dataset using the function from data_loader
        df_recipes = load_recipe_data(limit=config.LIMIT_RECIPES)
        if df_recipes is None:
            logger.error("Failed to load data using load_recipe_data. Exiting.")
            exit(1)
        
        logger.info(f"Successfully loaded {len(df_recipes)} recipes via load_recipe_data")
        logger.info(f"Columns after loading: {df_recipes.columns.tolist()}")

        # Validate required columns *after* loading (should be standardized now)
        if config.RECIPE_NAME_COLUMN not in df_recipes.columns or config.RAW_INGREDIENTS_COLUMN not in df_recipes.columns:
             logger.error(f"Missing required standardized columns ('{config.RECIPE_NAME_COLUMN}', '{config.RAW_INGREDIENTS_COLUMN}') after loading. Columns found: {df_recipes.columns.tolist()}")
             exit(1)

        # Apply cleaning using the standardized 'ingredients' column
        logger.info("\nCleaning ingredient data...")
        df_cleaned = apply_cleaning_to_dataframe(
            df_recipes, 
            config.RAW_INGREDIENTS_COLUMN, 
            config.CLEANED_INGREDIENTS_COLUMN
        )
        
        # Get canonical ingredients from the new 'cleaned_ingredients' column
        logger.info("\nExtracting canonical ingredients...")
        canonical_ingredients = get_canonical_ingredients(df_cleaned, config.CLEANED_INGREDIENTS_COLUMN)
        
        # Show a sample of cleaned data
        logger.info("\nSample of cleaned data:")
        # Display original ingredients and cleaned ingredients side-by-side
        sample_cols = [config.RECIPE_NAME_COLUMN, config.RAW_INGREDIENTS_COLUMN, config.CLEANED_INGREDIENTS_COLUMN]
        sample_data = df_cleaned[sample_cols].head()
        print(sample_data.to_string())
        
        logger.info("\nData cleaning test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during data cleaning test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc()) 