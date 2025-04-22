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

if __name__ == "__main__":
    test_specific_queries() 