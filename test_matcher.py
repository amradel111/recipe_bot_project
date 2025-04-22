"""
Test script for the enhanced recipe matching functionality.
This demonstrates how the matcher handles dietary preferences and excluded ingredients.
"""

import logging
import sys
import pandas as pd
import config
from data_cleaner import apply_cleaning_to_dataframe, get_canonical_ingredients
from nlu_parser import parse_user_input
from recipe_matcher import find_matching_recipes
from load_data import load_recipe_data

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def load_test_data():
    """Load recipe data for testing."""
    try:
        # Load recipes
        logger.info(f"Loading recipe dataset from: {config.RECIPE_DATASET_PATH}")
        df_recipes = load_recipe_data(config.RECIPE_DATASET_PATH, limit=300)  # Using more recipes for better testing
        logger.info(f"Successfully loaded {len(df_recipes)} recipes")
        
        # Apply cleaning
        logger.info("Cleaning ingredient data...")
        df_recipes = apply_cleaning_to_dataframe(
            df_recipes, 
            config.RAW_INGREDIENTS_COLUMN, 
            config.CLEANED_INGREDIENTS_COLUMN
        )
        
        # Get canonical ingredients
        logger.info("Extracting canonical ingredients...")
        canonical_ingredients = get_canonical_ingredients(df_recipes, config.CLEANED_INGREDIENTS_COLUMN)
        logger.info(f"Extracted {len(canonical_ingredients)} canonical ingredients")
        
        return df_recipes, canonical_ingredients
        
    except Exception as e:
        logger.error(f"Error loading test data: {str(e)}")
        return None, set()

def test_recipe_matcher(df_recipes, canonical_ingredients):
    """Test recipe matcher with various queries."""
    
    test_cases = [
        # Basic ingredient matching
        {
            "query": "What can I make with chicken, garlic, and olive oil?",
            "description": "Basic ingredient matching"
        },
        # Ingredient exclusion
        {
            "query": "I want recipes with pasta but no cheese",
            "description": "Ingredient exclusion"
        },
        # Vegetarian recipes
        {
            "query": "Give me vegetarian recipes with mushrooms",
            "description": "Vegetarian preference"
        },
        # Gluten-free desserts
        {
            "query": "Show me gluten-free desserts",
            "description": "Gluten-free preference"
        },
        # Quick dinner
        {
            "query": "Quick dinner recipes with chicken",
            "description": "Quick meal preference"
        },
        # Multiple dietary preferences
        {
            "query": "I need vegan gluten-free recipes",
            "description": "Multiple dietary preferences"
        }
    ]
    
    for test_case in test_cases:
        query = test_case["query"]
        description = test_case["description"]
        
        print(f"\n{'=' * 60}")
        print(f"TEST CASE: {description}")
        print(f"QUERY: \"{query}\"")
        print(f"{'=' * 60}")
        
        # Parse the query
        intent_data, entities = parse_user_input(query, canonical_ingredients)
        
        print(f"Detected intent: {intent_data['primary']}")
        if intent_data['dietary_preferences']:
            print(f"Dietary preferences: {intent_data['dietary_preferences']}")
        print(f"Include ingredients: {entities['include']}")
        print(f"Exclude ingredients: {entities['exclude']}")
        
        # Find matching recipes
        matches = find_matching_recipes(
            include_ingredients=entities['include'],
            exclude_ingredients=entities['exclude'],
            dietary_preferences=intent_data['dietary_preferences'],
            df_recipes=df_recipes,
            config=config,
            limit=3  # Only show top 3 for brevity
        )
        
        # Display results
        if matches:
            print(f"\nFound {len(matches)} matching recipes:")
            for i, match in enumerate(matches, 1):
                recipe_name = match['recipe_name']
                score = match['match_score']
                
                print(f"\n{i}. {recipe_name}")
                print(f"   Score: {score['score']:.2f}")
                print(f"   Matched ingredients: {', '.join(score['common_ingredients'])}")
                if score['excluded_found']:
                    print(f"   Excluded ingredients found: {', '.join(score['excluded_found'])}")
        else:
            print("\nNo matching recipes found.")

if __name__ == "__main__":
    print("Testing Enhanced Recipe Matching")
    print("=" * 50)
    
    df_recipes, canonical_ingredients = load_test_data()
    
    if df_recipes is not None and canonical_ingredients:
        test_recipe_matcher(df_recipes, canonical_ingredients)
    else:
        logger.error("Failed to load test data. Exiting.")
        sys.exit(1) 