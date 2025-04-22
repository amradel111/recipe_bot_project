"""
Test script for the enhanced NLU functionality in Recipe Bot.
This script demonstrates how the improved NLU works with the cleaned ingredients.
"""

import logging
import sys
import pandas as pd
import config
from data_cleaner import apply_cleaning_to_dataframe, get_canonical_ingredients
from nlu_parser import parse_user_input
from load_data import load_recipe_data

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def load_test_data():
    """Load a small subset of recipe data for testing."""
    try:
        # Load a small subset of the recipes
        logger.info(f"Loading recipe dataset from: {config.RECIPE_DATASET_PATH}")
        df_recipes = load_recipe_data(config.RECIPE_DATASET_PATH, limit=100)
        logger.info(f"Successfully loaded {len(df_recipes)} recipes")
        
        # Apply cleaning to get canonical ingredients
        logger.info("Cleaning ingredient data...")
        df_recipes = apply_cleaning_to_dataframe(
            df_recipes, 
            config.RAW_INGREDIENTS_COLUMN, 
            config.CLEANED_INGREDIENTS_COLUMN
        )
        
        # Get canonical ingredients list
        logger.info("Extracting canonical ingredients...")
        canonical_ingredients = get_canonical_ingredients(df_recipes, config.CLEANED_INGREDIENTS_COLUMN)
        logger.info(f"Extracted {len(canonical_ingredients)} canonical ingredients")
        
        return canonical_ingredients
        
    except Exception as e:
        logger.error(f"Error loading test data: {str(e)}")
        return set()

def test_queries(canonical_ingredients):
    """Test various query types with the enhanced NLU."""
    
    test_inputs = [
        # Basic ingredient queries
        "What can I make with chicken, onions, and potatoes?",
        "I have eggs, milk, and flour",
        
        # Queries with negation/exclusion
        "Find recipes with chicken but without garlic",
        "I want pasta recipes but no cheese",
        
        # Dietary preference queries
        "I need a vegetarian recipe with mushrooms",
        "Show me gluten-free desserts",
        "Quick dinner ideas with chicken",
        "Vegan recipes with avocado",
        
        # Multiple dietary preferences
        "I want quick vegetarian recipes",
        
        # Help and quit intents
        "How do I use this chatbot?",
        "exit",
        
        # Recipe selection
        "2",
        "Show me recipe number 3"
    ]
    
    logger.info("\nTesting enhanced NLU with sample queries:")
    for test_input in test_inputs:
        intent_data, entities = parse_user_input(test_input, canonical_ingredients)
        
        print(f"\nQuery: \"{test_input}\"")
        print(f"  Primary Intent: {intent_data['primary']}")
        
        if intent_data['dietary_preferences']:
            print(f"  Dietary Preferences: {intent_data['dietary_preferences']}")
            
        if intent_data['description']:
            print(f"  Description: {intent_data['description']}")
            
        if entities['include']:
            print(f"  Include Ingredients: {entities['include']}")
            
        if entities['exclude']:
            print(f"  Exclude Ingredients: {entities['exclude']}")

if __name__ == "__main__":
    print("Testing Enhanced NLU with Ingredient Cleaning")
    print("=" * 50)
    
    canonical_ingredients = load_test_data()
    
    if canonical_ingredients:
        test_queries(canonical_ingredients)
    else:
        logger.error("Failed to load canonical ingredients. Exiting.")
        sys.exit(1) 