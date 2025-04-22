"""
Simple script to display sample recipe data.
"""

import pandas as pd
import config
from load_data import load_recipe_data

def display_recipe_sample():
    print("Loading recipes...")
    df = load_recipe_data(config.RECIPE_DATASET_PATH, limit=3)
    
    print(f"\nNumber of recipes loaded: {len(df)}")
    print(f"Dataset columns: {df.columns.tolist()}")
    
    for i in range(min(3, len(df))):
        recipe = df.iloc[i]
        print("\n" + "=" * 40)
        print(f"RECIPE #{i+1}: {recipe['title']}")
        print("=" * 40)
        
        # Print ingredients
        print("\nINGREDIENTS:")
        try:
            for ingredient in recipe['ingredients']:
                print(f"- {ingredient}")
        except:
            print(recipe['ingredients'])
            
        # Print a portion of the instructions
        print("\nINSTRUCTIONS:")
        instructions = recipe['instructions']
        if isinstance(instructions, str) and len(instructions) > 100:
            print(instructions[:100] + "...")
        else:
            print(instructions)
            
        # Print other fields
        print(f"\nRECIPE ID: {recipe['recipe_id']}")
        if 'picture_link' in recipe:
            print(f"PICTURE: {recipe['picture_link']}")

if __name__ == "__main__":
    display_recipe_sample() 