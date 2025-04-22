"""
Simple script to display a sample of the recipe dataset.
"""

import pandas as pd
import config
from load_data import load_recipe_data
import json

def main():
    print(f"Loading sample from dataset: {config.RECIPE_DATASET_PATH}")
    
    # Load a small sample of recipes
    df = load_recipe_data(config.RECIPE_DATASET_PATH, limit=3)
    
    print("\nDataset Columns:")
    print(df.columns.tolist())
    
    print("\nSample Recipe 1:")
    sample = df.iloc[0]
    
    print(f"Title: {sample[config.RECIPE_NAME_COLUMN]}")
    
    print("\nIngredients:")
    ingredients = sample[config.RAW_INGREDIENTS_COLUMN]
    if isinstance(ingredients, str):
        try:
            # Try parsing as JSON
            ingredients_list = json.loads(ingredients)
            for ingredient in ingredients_list:
                print(f"- {ingredient}")
        except:
            print(ingredients)
    elif isinstance(ingredients, list):
        for ingredient in ingredients:
            print(f"- {ingredient}")
    else:
        print(ingredients)
    
    print("\nInstructions:")
    instructions = sample[config.INSTRUCTIONS_COLUMN]
    if isinstance(instructions, str):
        print(instructions[:200] + "..." if len(instructions) > 200 else instructions)
    else:
        print(instructions)
    
    print("\nRecipe ID:")
    print(sample['recipe_id'])
    
    print("\nComplete First Row Data (Raw):")
    for col in df.columns:
        print(f"\n{col}:")
        print(sample[col])

if __name__ == "__main__":
    main() 