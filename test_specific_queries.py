#!/usr/bin/env python
# coding: utf-8

import logging
import sys
from pathlib import Path

# Add the project directory to the path
project_dir = Path(__file__).parent
sys.path.append(str(project_dir))

# Import our modules
import config
from nlu_parser import parse_query
from recipe_matcher import find_matching_recipes
from data_loader import load_recipe_data, preprocess_ingredients
from data_cleaner import apply_cleaning_to_dataframe

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_specific_queries():
    """Test specific queries that were problematic."""
    # First, load the recipe data
    print("Loading recipe data...")
    recipes_df = load_recipe_data(limit=config.LIMIT_RECIPES)
    
    # Apply cleaning if the cleaned ingredients column doesn't exist
    if config.CLEANED_INGREDIENTS_COLUMN not in recipes_df.columns:
        recipes_df = apply_cleaning_to_dataframe(
            recipes_df, 
            config.RAW_INGREDIENTS_COLUMN, 
            config.CLEANED_INGREDIENTS_COLUMN
        )
    
    # Extract canonical ingredients
    canonical_ingredients = set()
    for ingredients_list in recipes_df[config.CLEANED_INGREDIENTS_COLUMN].dropna():
        if isinstance(ingredients_list, list):
            canonical_ingredients.update(ingredients_list)
    
    # Test queries
    test_queries = [
        "What can I make with chicken and rice?",
        "Show me recipes with beef and potatoes",
        "I want pasta recipes without onions",
        "Find vegetarian recipes",
        "I need a gluten-free dessert recipe",
        "Give me low-carb dinner ideas"
    ]
    
    for query in test_queries:
        print(f"\n\n=== Testing query: '{query}' ===")
        
        # Parse the query
        parsed = parse_query(query, canonical_ingredients)
        print(f"Parsed: {parsed}")
        
        # Find matching recipes
        matches = find_matching_recipes(
            include_ingredients=parsed['include_ingredients'],
            exclude_ingredients=parsed['exclude_ingredients'],
            dietary_preferences=parsed['dietary_preferences'],
            df_recipes=recipes_df,
            config=config,
            limit=5,
            recipe_category=parsed['recipe_category']
        )
        
        # Print results
        if matches.empty:
            print("No matching recipes found.")
        else:
            print(f"Found {len(matches)} matching recipes:")
            for i, (_, match) in enumerate(matches.iterrows(), 1):
                recipe_name = match[config.RECIPE_NAME_COLUMN]
                score = match['match_score']
                
                print(f"  {i}. {recipe_name}")
                print(f"     Match score: {score:.2f}")
                print(f"     Common ingredients: {', '.join(match['common_ingredients'])}")

def test_cooking_method_recognition():
    """Test recognition of cooking methods in queries."""
    import config
    import pandas as pd
    from nlu_parser import parse_query
    from data_loader import load_recipe_data
    from data_cleaner import apply_cleaning_to_dataframe
    
    # Load a sample of recipes
    recipes_df = load_recipe_data(config.DATASET_PATH, limit=100)
    
    # Apply cleaning if the cleaned ingredients column doesn't exist
    if config.CLEANED_INGREDIENTS_COLUMN not in recipes_df.columns:
        recipes_df = apply_cleaning_to_dataframe(
            recipes_df,
            config.RAW_INGREDIENTS_COLUMN,
            config.CLEANED_INGREDIENTS_COLUMN
        )
    
    # Extract canonical ingredients for testing
    canonical_ingredients = set()
    for ingredients_list in recipes_df[config.CLEANED_INGREDIENTS_COLUMN].dropna():
        canonical_ingredients.update(ingredients_list)
    
    # Test queries with different cooking methods
    test_queries = [
        "I want to make baked chicken",
        "Show me recipes for grilled fish",
        "I'd like to make a stir-fry with vegetables",
        "Find me some slow cooked beef recipes",
        "What can I make in my air fryer?",
        "I want to make soup in my pressure cooker",
        "Show me some quick pasta dishes I can make in 30 minutes",
        "I need a slow-cooked meal for dinner",
        "What's a good recipe for steamed vegetables?",
        "I'd like to make a microwave dessert"
    ]
    
    print("\n===== TESTING COOKING METHOD RECOGNITION =====")
    for query in test_queries:
        result = parse_query(query, canonical_ingredients)
        print(f"\nQuery: {query}")
        print(f"Cooking methods: {result['cooking_methods']}")
        print(f"Cooking time: {result['cooking_time']}")
        print(f"Ingredients: {result['include_ingredients']}")
        print(f"Category: {result['recipe_category']}")

def test_time_preference_recognition():
    """Test recognition of cooking time preferences in queries."""
    import config
    import pandas as pd
    from nlu_parser import parse_query
    from data_loader import load_recipe_data
    from data_cleaner import apply_cleaning_to_dataframe
    
    # Load a sample of recipes
    recipes_df = load_recipe_data(config.DATASET_PATH, limit=100)
    
    # Apply cleaning if the cleaned ingredients column doesn't exist
    if config.CLEANED_INGREDIENTS_COLUMN not in recipes_df.columns:
        recipes_df = apply_cleaning_to_dataframe(
            recipes_df,
            config.RAW_INGREDIENTS_COLUMN,
            config.CLEANED_INGREDIENTS_COLUMN
        )
    
    # Extract canonical ingredients for testing
    canonical_ingredients = set()
    for ingredients_list in recipes_df[config.CLEANED_INGREDIENTS_COLUMN].dropna():
        canonical_ingredients.update(ingredients_list)
    
    # Test queries with different time preferences
    test_queries = [
        "I need a quick dinner recipe",
        "Show me recipes I can make in under 30 minutes",
        "What are some easy 15 minute meals?",
        "I want a recipe that takes about an hour to make",
        "Find me slow cooker recipes for beef",
        "What can I cook overnight?",
        "I'd like to make something that takes all day to cook",
        "Show me some fast breakfast ideas",
        "What's a simple lunch I can make?",
        "Give me some recipes for a quick weeknight dinner"
    ]
    
    print("\n===== TESTING COOKING TIME RECOGNITION =====")
    for query in test_queries:
        result = parse_query(query, canonical_ingredients)
        print(f"\nQuery: {query}")
        print(f"Cooking time: {result['cooking_time']}")
        print(f"Cooking methods: {result['cooking_methods']}")
        print(f"Ingredients: {result['include_ingredients']}")
        print(f"Category: {result['recipe_category']}")

if __name__ == "__main__":
    test_specific_queries()
    test_cooking_method_recognition()
    test_time_preference_recognition() 