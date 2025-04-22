#!/usr/bin/env python
# coding: utf-8

import logging
import sys
from pathlib import Path

# Add the project directory to the path
project_dir = Path(__file__).parent
sys.path.append(str(project_dir))

# Import our modules
from nlu_parser import extract_common_ingredients, parse_query
import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_ingredient_extraction():
    """Test the ingredient extraction function with various queries."""
    test_queries = [
        "What can I make with chicken and rice?",
        "Find recipes with beef",
        "I want pasta recipes without onions",
        "Show me gluten-free desserts",
        "Find recipes using potatoes and carrots",
        "What can I cook with chicken but no garlic?",
        "Rice and beans recipe",
        "Easy chicken soup recipes"
    ]
    
    print("\n=== Testing direct ingredient extraction ===")
    for query in test_queries:
        include, exclude = extract_common_ingredients(query)
        print(f"\nQuery: '{query}'")
        print(f"Include: {include}")
        print(f"Exclude: {exclude}")
    
    print("\n=== Testing full query parsing ===")
    for query in test_queries:
        parse_result = parse_query(query)
        print(f"\nQuery: '{query}'")
        print(f"Intent: {parse_result['intent']}")
        print(f"Include ingredients: {parse_result['include_ingredients']}")
        print(f"Exclude ingredients: {parse_result['exclude_ingredients']}")
        print(f"Dietary preferences: {parse_result['dietary_preferences']}")
        print(f"Recipe category: {parse_result['recipe_category']}")

if __name__ == "__main__":
    test_ingredient_extraction() 