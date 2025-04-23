"""
Recipe matching module for Recipe Bot.
This module contains functions to match user ingredients with recipes.
"""

import pandas as pd
import numpy as np
import logging
import config
import re
from collections import Counter
from fuzzywuzzy import fuzz

# Set up logging
logger = logging.getLogger(__name__)

# Dietary indicators - keywords that might indicate a recipe matches a dietary preference
DIETARY_INDICATORS = {
    'vegetarian': [
        'vegetarian', 'veggie', 'meatless', 'plant-based',
        # Ingredients that indicate meat
        'chicken', 'beef', 'pork', 'lamb', 'turkey', 'bacon', 'ham', 'sausage',
        'fish', 'salmon', 'tuna', 'shrimp', 'meat', 'veal'
    ],
    'vegan': [
        'vegan', 'plant-based',
        # Ingredients that indicate animal products
        'milk', 'cheese', 'cream', 'butter', 'egg', 'honey', 'yogurt', 'chicken',
        'beef', 'pork', 'fish', 'meat', 'gelatin'
    ],
    'gluten_free': [
        'gluten-free', 'gluten free', 'no gluten',
        # Ingredients that contain gluten
        'flour', 'wheat', 'barley', 'rye', 'pasta', 'bread', 'soy sauce', 'couscous'
    ],
    'dairy_free': [
        'dairy-free', 'dairy free', 'non-dairy',
        # Dairy ingredients
        'milk', 'cheese', 'cream', 'butter', 'yogurt', 'ice cream'
    ],
    'low_carb': [
        'low carb', 'keto', 'low-carb',
        # High carb ingredients
        'sugar', 'pasta', 'rice', 'potato', 'bread', 'flour', 'corn'
    ]
}

def calculate_match_score(user_ingredients, recipe_ingredients, exclude_ingredients=None):
    """
    Calculate a match score between user ingredients and recipe ingredients.
    
    Parameters:
    -----------
    user_ingredients : list
        List of ingredients specified by the user
    recipe_ingredients : list
        List of ingredients in the recipe
    exclude_ingredients : list, optional
        List of ingredients to exclude
        
    Returns:
    --------
    dict
        Match score information with keys:
        - common_ingredients: list of ingredients found in both
        - match_count: number of common ingredients
        - match_ratio: ratio of common ingredients to user_ingredients
        - coverage_ratio: ratio of common ingredients to recipe_ingredients
        - score: overall match score
    """
    if not user_ingredients or not recipe_ingredients:
        return {
            'common_ingredients': [],
            'match_count': 0,
            'match_ratio': 0,
            'coverage_ratio': 0,
            'score': 0
        }
    
    # Ensure working with lists
    if not isinstance(user_ingredients, list):
        user_ingredients = [user_ingredients]
    if not isinstance(recipe_ingredients, list):
        recipe_ingredients = [recipe_ingredients]
    if exclude_ingredients and not isinstance(exclude_ingredients, list):
        exclude_ingredients = [exclude_ingredients]
    
    # Clean up ingredients
    user_ingredients = [str(ing).lower() for ing in user_ingredients if ing]
    recipe_ingredients_lower = [str(ing).lower() for ing in recipe_ingredients if ing]
    
    # Create a single string of all recipe ingredients for better substring matching
    recipe_text = " ".join(recipe_ingredients_lower)
    
    # Find common ingredients
    common_ingredients = []
    for user_ing in user_ingredients:
        found = False
        
        # Check exact matches first (1. exact match, 2. substring in recipe)
        if user_ing in recipe_ingredients_lower:
            common_ingredients.append(user_ing)
            found = True
        # Check if ingredient is mentioned in any recipe ingredient
        elif user_ing in recipe_text:
            common_ingredients.append(user_ing)
            found = True
        # Fallback to checking each recipe ingredient for substring match
        else:
            for recipe_ing in recipe_ingredients_lower:
                # Check if user ingredient is contained within recipe ingredient
                if user_ing in recipe_ing:
                    common_ingredients.append(recipe_ing)
                    found = True
                    break
                # For shorter ingredients, check if recipe ingredient contains them
                elif len(user_ing) <= 4 and user_ing in recipe_ing:
                    common_ingredients.append(recipe_ing)
                    found = True
                    break
        
        # If still not found, try fuzzy matching as last resort
        if not found:
            best_match = None
            best_score = 0
            
            for recipe_ing in recipe_ingredients_lower:
                # Try fuzzy ratio for more complex matches
                similarity = fuzz.ratio(user_ing, recipe_ing)
                
                if similarity > 85 and similarity > best_score:  # Stricter threshold (85% vs 80%)
                    best_match = recipe_ing
                    best_score = similarity
            
            if best_match and best_match not in common_ingredients:
                common_ingredients.append(best_match)
    
    # Calculate basic metrics
    match_count = len(common_ingredients)
    match_ratio = match_count / len(user_ingredients) if user_ingredients else 0
    coverage_ratio = match_count / len(recipe_ingredients_lower) if recipe_ingredients_lower else 0
    
    # Calculate a weighted score (prioritize match_ratio over coverage)
    # Increase the weight on match_ratio to prioritize recipes with all requested ingredients
    score = (0.8 * match_ratio) + (0.2 * coverage_ratio)
    
    # Apply penalty for excluded ingredients if provided
    if exclude_ingredients and recipe_ingredients_lower:
        excluded_found = []
        
        for exclude_ing in exclude_ingredients:
            exclude_ing = exclude_ing.lower()
            
            # Check if excluded ingredient appears in recipe text
            if exclude_ing in recipe_text:
                excluded_found.append(exclude_ing)
                continue
            
            # Check against each recipe ingredient
            for recipe_ing in recipe_ingredients_lower:
                # Check for substring match
                if exclude_ing in recipe_ing or recipe_ing in exclude_ing:
                    excluded_found.append(recipe_ing)
                    break
        
        # Apply stricter penalty for excluded ingredients
        excluded_count = len(excluded_found)
        if excluded_count > 0:
            # Significant penalty for each excluded ingredient
            exclusion_penalty = min(1.0, 0.7 * excluded_count)  # Increased from 0.5 to 0.7
            score = max(0, score - exclusion_penalty)
    
    return {
        'common_ingredients': common_ingredients,
        'match_count': match_count,
        'match_ratio': match_ratio,
        'coverage_ratio': coverage_ratio,
        'score': score
    }

def check_dietary_preferences(recipe_ingredients, dietary_preferences):
    """
    Check if a recipe meets the specified dietary preferences.
    
    Parameters:
    -----------
    recipe_ingredients : list
        List of ingredients in the recipe
    dietary_preferences : list
        List of dietary preferences (e.g., 'vegetarian', 'vegan', 'gluten-free')
        
    Returns:
    --------
    bool
        True if the recipe meets all dietary preferences, False otherwise
    """
    if not dietary_preferences:
        return True  # No preferences specified, so all recipes are valid
    
    # Convert recipe ingredients to lowercase for case-insensitive matching
    recipe_ingredients_lower = [ing.lower() for ing in recipe_ingredients]
    recipe_text = ' '.join(recipe_ingredients_lower)
    
    # Define ingredient lists for each dietary preference
    non_vegetarian_ingredients = [
        'meat', 'beef', 'chicken', 'pork', 'lamb', 'veal', 'turkey', 'duck', 'goose',
        'bacon', 'ham', 'sausage', 'prosciutto', 'pepperoni', 'salami', 'chorizo',
        'fish', 'salmon', 'tuna', 'shrimp', 'lobster', 'crab', 'clam', 'mussel', 'oyster', 
        'squid', 'octopus', 'anchovies', 'sardines', 'cod', 'tilapia', 'catfish',
        'gelatin'
    ]
    
    non_vegan_ingredients = non_vegetarian_ingredients + [
        'milk', 'cream', 'butter', 'cheese', 'yogurt', 'ice cream', 'dairy',
        'egg', 'eggs', 'honey', 'mayonnaise', 'whey', 'casein', 'lactose'
    ]
    
    gluten_ingredients = [
        'wheat', 'rye', 'barley', 'triticale', 'semolina', 'spelt', 'farina',
        'farro', 'graham flour', 'matzo', 'panko', 'bulgur', 'couscous',
        'pasta', 'noodles', 'bread', 'flour', 'soy sauce'
    ]
    
    dairy_ingredients = [
        'milk', 'cream', 'butter', 'cheese', 'yogurt', 'ice cream', 'dairy',
        'whey', 'casein', 'lactose', 'ghee', 'buttermilk', 'half-and-half',
        'sour cream', 'creme fraiche', 'custard', 'pudding'
    ]
    
    nut_ingredients = [
        'almond', 'almonds', 'walnut', 'walnuts', 'pecan', 'pecans', 'peanut', 'peanuts',
        'cashew', 'cashews', 'pistachio', 'pistachios', 'hazelnut', 'hazelnuts',
        'macadamia', 'brazil nut', 'pine nut', 'chestnut', 'nut', 'nuts', 'nut butter',
        'peanut butter', 'almond butter', 'nutella'
    ]
    
    # Normalize preferences
    normalized_preferences = []
    for pref in dietary_preferences:
        pref_lower = pref.lower()
        if pref_lower in ['vegetarian', 'veg', 'veggie', 'vegetable', 'no meat']:
            normalized_preferences.append('vegetarian')
        elif pref_lower in ['vegan', 'plant-based', 'plant based', 'no animal', 'no animal products']:
            normalized_preferences.append('vegan')
        elif pref_lower in ['gluten-free', 'gluten free', 'gluten_free', 'no gluten']:
            normalized_preferences.append('gluten-free')
        elif pref_lower in ['dairy-free', 'dairy free', 'no dairy', 'lactose-free']:
            normalized_preferences.append('dairy-free')
        elif pref_lower in ['nut-free', 'nut free', 'no nuts', 'peanut-free']:
            normalized_preferences.append('nut-free')
        else:
            normalized_preferences.append(pref_lower)
    
    # Log the normalized preferences
    logger.debug(f"Checking dietary preferences: {normalized_preferences}")
    
    # Check each dietary preference
    for preference in normalized_preferences:
        if preference == 'vegetarian':
            # Check if any non-vegetarian ingredient is in the recipe
            for ingredient in non_vegetarian_ingredients:
                if any(re.search(r'\b' + re.escape(ingredient) + r'\b', ing) for ing in recipe_ingredients_lower):
                    logger.debug(f"Recipe contains non-vegetarian ingredient: {ingredient}")
                    return False
                
        elif preference == 'vegan':
            # Check if any non-vegan ingredient is in the recipe
            for ingredient in non_vegan_ingredients:
                if any(re.search(r'\b' + re.escape(ingredient) + r'\b', ing) for ing in recipe_ingredients_lower):
                    logger.debug(f"Recipe contains non-vegan ingredient: {ingredient}")
                    return False
                    
        elif preference == 'gluten-free':
            # Check if any gluten ingredient is in the recipe
            for ingredient in gluten_ingredients:
                if any(re.search(r'\b' + re.escape(ingredient) + r'\b', ing) for ing in recipe_ingredients_lower):
                    logger.debug(f"Recipe contains gluten ingredient: {ingredient}")
                    return False
                    
        elif preference == 'dairy-free':
            # Check if any dairy ingredient is in the recipe
            for ingredient in dairy_ingredients:
                if any(re.search(r'\b' + re.escape(ingredient) + r'\b', ing) for ing in recipe_ingredients_lower):
                    logger.debug(f"Recipe contains dairy ingredient: {ingredient}")
                    return False
                    
        elif preference == 'nut-free':
            # Check if any nut ingredient is in the recipe
            for ingredient in nut_ingredients:
                if any(re.search(r'\b' + re.escape(ingredient) + r'\b', ing) for ing in recipe_ingredients_lower):
                    logger.debug(f"Recipe contains nut ingredient: {ingredient}")
                    return False
    
    # If we get here, all preferences were satisfied
    return True

def find_matching_recipes(include_ingredients, exclude_ingredients, dietary_preferences, df_recipes, config, limit=5, recipe_category=None):
    """
    Find recipes that match the specified ingredients and dietary preferences.
    
    Parameters:
    -----------
    include_ingredients : list
        List of ingredients to include
    exclude_ingredients : list
        List of ingredients to exclude
    dietary_preferences : list
        List of dietary preferences
    df_recipes : pandas.DataFrame
        DataFrame containing recipe data
    config : module
        Configuration module
    limit : int, optional
        Maximum number of recipes to return
    recipe_category : str, optional
        Category of recipes to search for
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame containing matching recipes, sorted by match score
    """
    logger.info(f"Finding recipes with ingredients: {include_ingredients}")
    logger.info(f"Excluding ingredients: {exclude_ingredients}")
    logger.info(f"Dietary preferences: {dietary_preferences}")
    logger.info(f"Recipe category: {recipe_category}")
    
    # Clean up inputs to ensure they're valid
    if include_ingredients and not isinstance(include_ingredients, list):
        include_ingredients = [include_ingredients]
    
    if exclude_ingredients and not isinstance(exclude_ingredients, list):
        exclude_ingredients = [exclude_ingredients]
    
    # Clean up ingredient inputs - remove non-ingredient strings
    include_ingredients = [ing for ing in include_ingredients if ing and len(ing) < 50]
    exclude_ingredients = [ing for ing in exclude_ingredients if ing and len(ing) < 50]
    
    # No ingredients, category or preferences - return empty result
    if (not include_ingredients and not dietary_preferences and not recipe_category) or df_recipes.empty:
        logger.warning("No ingredients, category or dietary preferences specified, or empty recipe dataframe")
        return pd.DataFrame()
    
    # Extract necessary columns
    ingredients_col = config.CLEANED_INGREDIENTS_COLUMN
    name_col = config.RECIPE_NAME_COLUMN
    
    # Add a match score column to the DataFrame
    df_with_scores = df_recipes.copy()
    
    # Check if the dataframe has the required columns
    if ingredients_col not in df_with_scores.columns:
        logger.error(f"Column '{ingredients_col}' not found in recipe dataframe")
        return pd.DataFrame()
    
    if name_col not in df_with_scores.columns:
        logger.error(f"Column '{name_col}' not found in recipe dataframe")
        return pd.DataFrame()
    
    # Apply category filter if specified
    if recipe_category:
        logger.info(f"Filtering by category: {recipe_category}")
        
        # Handle special categories and qualifiers
        special_categories = {
            'quick': ['quick', 'fast', 'rapid', 'ready in', 'minutes', '30 min', '15 min'],
            'easy': ['easy', 'simple', 'basic', 'beginner', 'effortless'],
            'fancy': ['fancy', 'gourmet', 'elegant', 'sophisticated', 'impressive', 'special'],
            'party': ['party', 'gathering', 'entertaining', 'celebrate', 'celebration', 'guests'],
            'dinner party': ['dinner party', 'entertaining', 'guests', 'gathering', 'formal dinner'],
            'spicy': ['spicy', 'spice', 'hot', 'chili', 'pepper', 'jalapeño', 'cayenne'],
            'bbq': ['bbq', 'barbecue', 'grill', 'grilled', 'cookout', 'outdoor cooking'],
            'healthy': ['healthy', 'nutritious', 'light', 'low-fat', 'low-calorie', 'fitness', 'diet']
        }
        
        # Check if we're dealing with a special category
        special_category = None
        for special, terms in special_categories.items():
            if recipe_category == special or recipe_category.startswith(f"{special} "):
                special_category = special
                logger.info(f"Identified special category: {special_category}")
                break
        
        # Create appropriate search terms based on the special category
        if special_category:
            # Get search terms for the special category
            search_terms = special_categories[special_category]
            
            # If there's a combined category (e.g., "quick breakfast"), add the second part
            if ' ' in recipe_category:
                primary_category = recipe_category.split(' ', 1)[1]
                logger.info(f"Combined category with primary: {primary_category}")
                
                # Create a separate mask for the primary category
                primary_mask = None
                
                # First, try to find a dedicated category column
                category_col = None
                potential_category_cols = ['category', 'categories', 'type', 'dish_type', 'meal_type', 'recipe_type']
                for col in potential_category_cols:
                    if col in df_with_scores.columns:
                        category_col = col
                        break
                
                # Apply primary category filter
                if category_col:
                    primary_mask = df_with_scores[category_col].str.lower().str.contains(primary_category.lower(), na=False)
                else:
                    # Search in recipe name
                    primary_mask = df_with_scores[name_col].str.lower().str.contains(primary_category.lower(), na=False)
                    
                    # Search in instruction text and other fields
                    if config.INSTRUCTIONS_COLUMN in df_with_scores.columns:
                        instr_mask = df_with_scores[config.INSTRUCTIONS_COLUMN].str.lower().str.contains(primary_category.lower(), na=False)
                        primary_mask = primary_mask | instr_mask
            
            # Initialize mask for special category
            special_mask = pd.Series(False, index=df_with_scores.index)
            
            # Apply masks for each search term in special category
            for term in search_terms:
                term_mask = False
                
                # Check in recipe name
                name_contains = df_with_scores[name_col].str.lower().str.contains(term, na=False)
                term_mask = term_mask | name_contains
                
                # Check in instructions
                if config.INSTRUCTIONS_COLUMN in df_with_scores.columns:
                    instr_contains = df_with_scores[config.INSTRUCTIONS_COLUMN].str.lower().str.contains(term, na=False)
                    term_mask = term_mask | instr_contains
                
                # Check in description if available
                if 'description' in df_with_scores.columns:
                    desc_contains = df_with_scores['description'].str.lower().str.contains(term, na=False)
                    term_mask = term_mask | desc_contains
                
                # Check in other potential columns
                for col in ['tags', 'keywords', 'notes']:
                    if col in df_with_scores.columns:
                        try:
                            if df_with_scores[col].dtype == 'object':
                                if isinstance(df_with_scores[col].iloc[0], list):
                                    # Handle list type columns
                                    col_contains = df_with_scores[col].apply(
                                        lambda x: any(term.lower() in str(tag).lower() for tag in x) if isinstance(x, list) else False
                                    )
                                else:
                                    # Handle string type columns
                                    col_contains = df_with_scores[col].str.lower().str.contains(term, na=False)
                                term_mask = term_mask | col_contains
                        except Exception as e:
                            logger.warning(f"Error searching in {col} column: {e}")
                
                # Add this term's mask to the special category mask
                special_mask = special_mask | term_mask
            
            # Combine masks if we have a primary category too
            if ' ' in recipe_category and primary_mask is not None:
                special_mask = special_mask & primary_mask
            
            # Apply the special category mask
            df_with_scores = df_with_scores[special_mask]
            logger.info(f"After special category filtering, found {len(df_with_scores)} recipes")
            
        else:
            # First, try to find a dedicated category column
            category_col = None
            potential_category_cols = ['category', 'categories', 'type', 'dish_type', 'meal_type', 'recipe_type']
            for col in potential_category_cols:
                if col in df_with_scores.columns:
                    category_col = col
                    break
            
            # If we have a dedicated category column, use it
            if category_col:
                logger.info(f"Using {category_col} column for category filtering")
                # Convert to lowercase for case-insensitive comparison
                df_with_scores = df_with_scores[df_with_scores[category_col].str.lower().str.contains(recipe_category.lower(), na=False)]
            else:
                # Otherwise, search in multiple columns and in the recipe name
                logger.info("No specific category column found, searching across multiple fields")
                
                # Start with recipe name
                category_mask = df_with_scores[name_col].str.lower().str.contains(recipe_category.lower(), na=False)
                
                # Also search in tags if available
                if 'tags' in df_with_scores.columns:
                    try:
                        if df_with_scores['tags'].dtype == 'object':
                            tags_mask = df_with_scores['tags'].apply(
                                lambda x: any(recipe_category.lower() in tag.lower() for tag in x) if isinstance(x, list) else False
                            )
                            category_mask = category_mask | tags_mask
                    except Exception as e:
                        logger.warning(f"Error searching in tags column: {e}")
                
                # Search in keywords if available
                if 'keywords' in df_with_scores.columns:
                    try:
                        keywords_mask = df_with_scores['keywords'].str.lower().str.contains(recipe_category.lower(), na=False)
                        category_mask = category_mask | keywords_mask
                    except Exception as e:
                        logger.warning(f"Error searching in keywords column: {e}")
                
                # Search in description if available
                if 'description' in df_with_scores.columns:
                    try:
                        desc_mask = df_with_scores['description'].str.lower().str.contains(recipe_category.lower(), na=False)
                        category_mask = category_mask | desc_mask
                    except Exception as e:
                        logger.warning(f"Error searching in description column: {e}")
                        
                # Search in instruction text if available (some recipes mention the meal type there)
                if config.INSTRUCTIONS_COLUMN in df_with_scores.columns:
                    try:
                        instr_mask = df_with_scores[config.INSTRUCTIONS_COLUMN].str.lower().str.contains(recipe_category.lower(), na=False)
                        category_mask = category_mask | instr_mask
                    except Exception as e:
                        logger.warning(f"Error searching in instructions column: {e}")
                
                # Apply the combined mask
                df_with_scores = df_with_scores[category_mask]
                
                logger.info(f"After category filtering, found {len(df_with_scores)} recipes")
    
    # If no recipes left after category filtering, return empty DataFrame
    if df_with_scores.empty:
        logger.info("No recipes found after category filtering")
        return pd.DataFrame()
        
    # Calculate match scores based on ingredients
    if include_ingredients:
        # Enhanced matching to better handle common ingredients
        # First, clean ingredients to handle standardization
        cleaned_include = []
        common_mapping = {
            'chicken': ['chicken', 'chicken breast', 'chicken thigh', 'chicken leg', 'chicken wing', 'chicken stock', 'chicken broth'],
            'rice': ['rice', 'jasmine rice', 'long grain rice', 'short grain rice', 'white rice', 'brown rice', 'basmati rice'],
            'potato': ['potato', 'potatoes', 'russet potato', 'yukon gold', 'sweet potato'],
            'beef': ['beef', 'ground beef', 'beef steak', 'beef chuck', 'beef brisket'],
            'pasta': ['pasta', 'spaghetti', 'linguine', 'penne', 'fettuccine', 'noodles']
        }
        
        # Expand common ingredients to include variations
        for ing in include_ingredients:
            ing_lower = ing.lower()
            if ing_lower in common_mapping:
                cleaned_include.extend(common_mapping[ing_lower])
            else:
                cleaned_include.append(ing_lower)
        
        # Deduplicate cleaned ingredients
        cleaned_include = list(set(cleaned_include))
        logger.info(f"Expanded include ingredients: {cleaned_include}")
        
        match_results = df_with_scores[ingredients_col].apply(
            lambda recipe_ingredients: calculate_match_score(
                cleaned_include, recipe_ingredients, exclude_ingredients
            ) if isinstance(recipe_ingredients, list) else {}
        )
        df_with_scores['match_score'] = match_results.apply(lambda x: x.get('score', 0))
        df_with_scores['common_ingredients'] = match_results.apply(lambda x: x.get('common_ingredients', []))
        df_with_scores['match_count'] = match_results.apply(lambda x: x.get('match_count', 0))
        df_with_scores['match_ratio'] = match_results.apply(lambda x: x.get('match_ratio', 0))
        df_with_scores['coverage_ratio'] = match_results.apply(lambda x: x.get('coverage_ratio', 0))
    else:
        # If no ingredients provided, set a default match score
        df_with_scores['match_score'] = 1.0
        df_with_scores['common_ingredients'] = df_with_scores.apply(lambda _: [], axis=1)
        df_with_scores['match_count'] = 0
        df_with_scores['match_ratio'] = 0
        df_with_scores['coverage_ratio'] = 0
    
    # Apply dietary preference filter
    if dietary_preferences:
        logger.info(f"Applying dietary preference filter: {dietary_preferences}")
        
        # Filter recipes based on dietary preferences
        df_with_scores['meets_preferences'] = df_with_scores[ingredients_col].apply(
            lambda recipe_ingredients: check_dietary_preferences(
                recipe_ingredients, dietary_preferences
            ) if isinstance(recipe_ingredients, list) else False
        )
        
        # Log the count of recipes meeting preferences
        meets_prefs_count = df_with_scores['meets_preferences'].sum()
        logger.info(f"Found {meets_prefs_count} recipes meeting dietary preferences")
        
        # Keep only recipes that meet dietary preferences
        df_with_scores = df_with_scores[df_with_scores['meets_preferences']]
    
    # If no recipes left after all filtering, return empty DataFrame
    if df_with_scores.empty:
        logger.info("No recipes found after all filtering")
        return pd.DataFrame()
    
    # Extra filtering to ensure ALL requested ingredients are present
    if include_ingredients and len(include_ingredients) > 1:
        logger.info("Filtering to ensure all requested ingredients are included")
        
        # Check match count against requested ingredient count
        user_ing_count = len(set(include_ingredients))
        
        # Only keep recipes that contain all requested ingredients
        # We use match_count >= user_ing_count * 0.9 to allow for some flexibility in matching
        df_with_scores = df_with_scores[df_with_scores['match_count'] >= user_ing_count * 0.9]
        
        # Log the count of recipes after ingredient filtering
        logger.info(f"After ensuring all ingredients present: {len(df_with_scores)} recipes")
        
        # If no recipes after strict filtering, fall back to the original list but mark it
        if df_with_scores.empty:
            logger.info("No recipes with ALL ingredients, falling back to partial matches")
            # We can return to the original approach in this case
            df_with_scores = df_recipes.copy()
            df_with_scores = df_with_scores.sort_values('match_score', ascending=False)
    
    # Sort by match score in descending order
    df_with_scores = df_with_scores.sort_values('match_score', ascending=False)
    
    # Apply minimum score threshold if there are user ingredients
    if include_ingredients:
        min_score_threshold = 0.1  # Minimum score to consider a recipe
        df_with_scores = df_with_scores[df_with_scores['match_score'] >= min_score_threshold]
    
    # Log the final count of recipes
    logger.info(f"Returning {len(df_with_scores.head(limit))} matching recipes")
    
    # Return top matching recipes with their full data
    return df_with_scores.head(limit)

def get_detailed_recipe(recipe_name, df_recipes, config):
    """
    Get detailed information about a specific recipe.
    
    Parameters:
    -----------
    recipe_name : str
        Name of the recipe to find
    df_recipes : pandas.DataFrame
        DataFrame containing recipe data
    config : module
        Configuration module
        
    Returns:
    --------
    dict or None
        Dictionary with recipe details or None if not found
    """
    # Get the recipe name column
    name_col = config.RECIPE_NAME_COLUMN
    
    # Check if the name column exists
    if name_col not in df_recipes.columns:
        logger.error(f"Column '{name_col}' not found in recipe dataframe")
        return None
    
    # Try exact matching first
    recipe_match = df_recipes[df_recipes[name_col] == recipe_name]
    
    # If no exact match, try fuzzy matching
    if recipe_match.empty:
        # Try partial string matching
        recipe_match = df_recipes[df_recipes[name_col].str.contains(recipe_name, case=False, regex=False)]
        
        # If still no match, try more aggressive fuzzy matching
        if recipe_match.empty:
            best_match = None
            best_score = 0
            
            for _, row in df_recipes.iterrows():
                curr_name = row[name_col]
                score = fuzz.ratio(recipe_name.lower(), curr_name.lower())
                
                if score > 70 and score > best_score:  # 70% threshold
                    best_match = row
                    best_score = score
            
            if best_match is not None:
                recipe_match = pd.DataFrame([best_match])
    
    # Return None if no match found
    if recipe_match.empty:
        return None
    
    # Get the first matching recipe (in case there are multiple)
    recipe = recipe_match.iloc[0]
    
    # Extract recipe details
    recipe_details = {
        'name': recipe[name_col],
        'ingredients': recipe[config.CLEANED_INGREDIENTS_COLUMN] if config.CLEANED_INGREDIENTS_COLUMN in recipe else [],
        'raw_ingredients': recipe[config.RAW_INGREDIENTS_COLUMN] if config.RAW_INGREDIENTS_COLUMN in recipe else [],
    }
    
    # Add instructions if available
    if config.INSTRUCTIONS_COLUMN in recipe and pd.notna(recipe[config.INSTRUCTIONS_COLUMN]):
        recipe_details['instructions'] = recipe[config.INSTRUCTIONS_COLUMN]
    
    # Add other metadata if available
    additional_fields = ['cook_time', 'prep_time', 'total_time', 'servings', 'calories', 'cuisine', 'url']
    for field in additional_fields:
        if field in recipe and pd.notna(recipe[field]):
            recipe_details[field] = recipe[field]
    
    return recipe_details

if __name__ == "__main__":
    # Test the recipe matching
    from data_loader import load_recipe_data
    from data_cleaner import apply_cleaning_to_dataframe
    
    try:
        print(f"LIMIT_RECIPES type: {type(config.LIMIT_RECIPES)}, value: {config.LIMIT_RECIPES}")
        # Load and clean the data
        df_recipes = load_recipe_data(limit=config.LIMIT_RECIPES)
        
        # Apply cleaning if the cleaned ingredients column doesn't exist
        if config.CLEANED_INGREDIENTS_COLUMN not in df_recipes.columns:
            df_recipes = apply_cleaning_to_dataframe(
                df_recipes,
                config.RAW_INGREDIENTS_COLUMN,
                config.CLEANED_INGREDIENTS_COLUMN
            )
        
        # Create sample user ingredients
        user_ingredients = ['chicken', 'potato', 'onion']
        
        print(f"Testing recipe matcher with ingredients: {', '.join(user_ingredients)}\n")
        
        # Find matching recipes
        matches = find_matching_recipes(user_ingredients, [], [], df_recipes, config)
        
        if matches.empty:
            print("No matching recipes found.")
        else:
            print(f"Found {len(matches)} matching recipes:\n")
            for i, (_, match) in enumerate(matches.iterrows(), 1):
                recipe_name = match[config.RECIPE_NAME_COLUMN]
                score = match['match_score']
                
                print(f"{i}. {recipe_name}")
                print(f"   Common ingredients: {', '.join(match['common_ingredients'])}")
                print(f"   Match count: {match['match_count']}")
                print(f"   Match ratio: {match['match_ratio']:.2f}")
                print(f"   Coverage ratio: {match['coverage_ratio']:.2f}")
                print(f"   Overall score: {match['match_score']:.2f}")
                print()
                
                # Get and print detailed recipe for the first match
                if i == 1:
                    details = get_detailed_recipe(recipe_name, df_recipes, config)
                    print("Detailed recipe information:")
                    print(f"Name: {details['name']}")
                    print(f"Ingredients: {details['ingredients']}")
                    if 'instructions' in details:
                        print(f"Instructions: {details['instructions'][:100]}...")
                    if 'cuisine' in details:
                        print(f"Cuisine: {details['cuisine']}")
                    print()
    except Exception as e:
        print(f"Error during recipe matching: {str(e)}") 