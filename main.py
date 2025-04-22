#!/usr/bin/env python
# coding: utf-8

import logging
import re
import os
import sys
import pandas as pd
import argparse
from time import time
from pathlib import Path

# Add the project directory to the path
# This ensures we can import from sibling modules
project_dir = Path(__file__).parent
sys.path.append(str(project_dir))

# Import our custom modules
import config
from nlu_parser import parse_query
from recipe_matcher import find_matching_recipes, get_detailed_recipe
from data_loader import load_recipe_data, preprocess_ingredients
from data_cleaner import apply_cleaning_to_dataframe

# Set up logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_and_prepare_data():
    """
    Load and prepare the recipe data for the chatbot.
    Returns recipes, canonical_ingredients and preprocessed_recipes.
    """
    start_time = time()
    
    # Load recipes with limit from config
    recipes = load_recipe_data(limit=config.LIMIT_RECIPES)
    
    if recipes is None or recipes.empty:
        logger.error("Failed to load recipe data. Exiting.")
        sys.exit(1)
    
    # Automatically clean ingredients if needed
    if config.CLEANED_INGREDIENTS_COLUMN not in recipes.columns:
        logger.info(f"'{config.CLEANED_INGREDIENTS_COLUMN}' column not found. Running ingredient cleaning...")
        recipes = apply_cleaning_to_dataframe(
            recipes,
            config.RAW_INGREDIENTS_COLUMN,
            config.CLEANED_INGREDIENTS_COLUMN
        )
        logger.info(f"'{config.CLEANED_INGREDIENTS_COLUMN}' column added.")
    
    logger.info(f"Loaded {len(recipes)} recipes in {time() - start_time:.2f} seconds")
    
    # Extract canonical ingredients from the dataset
    canonical_ingredients = set()
    for ingredients_list in recipes['ingredients'].dropna():
        for ingredient in ingredients_list:
            # Extract the ingredient name using our preprocessing function
            processed = preprocess_ingredients([ingredient])
            if processed:  # Only add non-empty ingredients
                canonical_ingredients.update(processed)
    
    logger.info(f"Extracted {len(canonical_ingredients)} unique canonical ingredients")
    
    # We return both the original recipes and the canonical ingredients list
    return recipes, canonical_ingredients

def format_response(response_type, data=None):
    """
    Format the response based on the response type.
    """
    if response_type == 'welcome':
        return (
            "👨‍🍳 Welcome to Recipe Bot! 👩‍🍳\n\n"
            "I can help you find recipes based on ingredients you have or want to use.\n"
            "You can also specify dietary preferences (vegetarian, vegan, gluten-free, etc.)\n"
            "and ingredients you want to exclude.\n\n"
            "For example, try:\n"
            "- 'Find recipes with chicken and rice'\n"
            "- 'I want vegetarian pasta dishes'\n"
            "- 'What can I make with potatoes but no meat?'\n"
            "- 'Show me gluten-free desserts'\n\n"
            "Type 'help' for more information or 'quit' to exit."
        )
    
    elif response_type == 'help':
        return (
            "📚 Recipe Bot Help 📚\n\n"
            "- Search for recipes by listing ingredients:\n"
            "  'Find recipes with eggs and cheese'\n\n"
            "- Exclude ingredients you don't want:\n"
            "  'I want pasta recipes without mushrooms'\n\n"
            "- Specify dietary preferences:\n"
            "  'Show me vegetarian dinner ideas'\n"
            "  (Supported: vegetarian, vegan, gluten-free, dairy-free, nut-free, low-carb)\n\n"
            "- Search by meal type or category:\n"
            "  'Find dessert recipes' or 'Show me breakfast ideas'\n"
            "  (Supported: breakfast, lunch, dinner, dessert, appetizer, soup, salad, etc.)\n\n"
            "- Combine search criteria:\n"
            "  'Show me gluten-free desserts with chocolate'\n\n"
            "- Get recipe details:\n"
            "  After seeing search results, type the recipe number\n"
            "  or 'Show me recipe #3'\n\n"
            "- Other commands:\n"
            "  'help' - Display this help message\n"
            "  'quit' - Exit the chatbot"
        )
    
    elif response_type == 'not_found':
        return (
            "😕 I couldn't find any matching recipes.\n\n"
            "Try with different ingredients or dietary preferences, or be more general in your request.\n"
            "For example: 'Find recipes with chicken' or 'Show me vegetarian meals'"
        )
    
    elif response_type == 'no_input':
        return "Please tell me what ingredients you'd like to use or what kind of recipe you're looking for."
    
    elif response_type == 'error':
        return "Sorry, I encountered an error processing your request. Please try again."
    
    elif response_type == 'goodbye':
        return "Thank you for using Recipe Bot! Happy cooking! 👨‍🍳👩‍🍳"
    
    elif response_type == 'recipe_list':
        if not data or 'recipes' not in data or not data['recipes']:
            return format_response('not_found')
        
        recipes = data['recipes']
        response = f"📋 Found {len(recipes)} recipes:\n\n"
        
        # Group recipes by category if multiple categories are present
        categories = {}
        for recipe in recipes:
            category = recipe.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append(recipe)
        
        # If no categories, or just one category, display a simple list
        if len(categories) <= 1:
            for i, recipe in enumerate(recipes, 1):
                # Format the recipe information
                name = recipe.get('name', 'Unnamed Recipe')
                
                # Add average time if available
                avg_time = recipe.get('average_time', None)
                time_str = f" (Time: {avg_time} min)" if avg_time else ""
                
                # Add rating if available
                rating = recipe.get('rating', None)
                rating_str = f" ⭐ {rating}" if rating else ""
                
                # List key ingredients (up to 5)
                ingredients = recipe.get('ingredients', [])
                ingr_str = ""
                if ingredients:
                    ingr_list = ingredients[:5]
                    if len(ingredients) > 5:
                        ingr_list[-1] = "... and more"
                    ingr_str = f"\n   Key ingredients: {', '.join(ingr_list)}"
                
                response += f"{i}. {name}{rating_str}{time_str}{ingr_str}\n\n"
        else:
            # If multiple categories, group recipes by category
            for category, cat_recipes in categories.items():
                response += f"--- {category.upper()} ---\n"
                for i, recipe in enumerate(cat_recipes, 1):
                    name = recipe.get('name', 'Unnamed Recipe')
                    
                    # Add rating if available
                    rating = recipe.get('rating', None)
                    rating_str = f" ⭐ {rating}" if rating else ""
                    
                    response += f"{i}. {name}{rating_str}\n"
                response += "\n"
        
        response += "To view the details of a recipe, enter its number or say 'Show me recipe #X'"
        return response
    
    elif response_type == 'recipe_detail':
        if not data or 'recipe' not in data:
            return "Sorry, I couldn't find details for that recipe."
        
        recipe = data['recipe']
        name = recipe.get('name', 'Unnamed Recipe')
        
        # Format the star rating
        rating = recipe.get('rating', None)
        rating_str = f"⭐ {rating}\n" if rating else ""
        
        # Format the time
        time_info = recipe.get('cook_time', None)
        time_str = f"⏲️ {time_info}\n" if time_info else ""
        
        # Add category if available
        category = recipe.get('category', None)
        category_str = f"🍽️ Category: {category}\n" if category else ""
        
        # Format the ingredients
        ingredients = recipe.get('ingredients', [])
        ingr_str = "🧾 Ingredients:\n"
        for ingr in ingredients:
            ingr_str += f"  • {ingr}\n"
        
        # Format the instructions
        instructions = recipe.get('instructions', [])
        instr_str = "\n📝 Instructions:\n"
        for i, step in enumerate(instructions, 1):
            instr_str += f"  {i}. {step}\n"
        
        # Add source information if available
        source = recipe.get('source', None)
        source_str = f"\n🔗 Source: {source}" if source else ""
        
        return f"🍽️ {name}\n\n{rating_str}{time_str}{category_str}\n{ingr_str}{instr_str}{source_str}"
    
    else:
        return "I'm not sure how to respond to that. Try asking for recipes with specific ingredients."

def process_user_input(user_input, recipes_df, canonical_ingredients, session_context):
    """
    Process user input and generate an appropriate response.
    
    Parameters:
    -----------
    user_input : str
        The user's input text
    recipes_df : pandas.DataFrame
        DataFrame containing the recipe data
    canonical_ingredients : set
        Set of canonical ingredient names
    session_context : dict
        Dictionary containing session context (e.g., last search results)
        
    Returns:
    --------
    tuple
        A tuple containing (response, updated_session_context)
    """
    try:
        # Default empty session context if None
        if session_context is None:
            session_context = {
                'last_search_results': None,
                'current_page': 0,
                'recipes_per_page': 5
            }
        
        # Parse the user input
        logger.info(f"Processing user input: '{user_input}'")
        parsed_input = parse_query(user_input, canonical_ingredients)
        
        # Check for None values in recipe_category (could happen if the key is missing)
        if 'recipe_category' not in parsed_input:
            parsed_input['recipe_category'] = None
            logger.warning("recipe_category not found in parsed input, setting to None")
        
        # Log the parsed input for debugging
        logger.info(f"Parsed query result: Intent={parsed_input['intent']}, " +
                   f"Include={parsed_input['include_ingredients']}, " +
                   f"Exclude={parsed_input['exclude_ingredients']}, " +
                   f"Dietary={parsed_input['dietary_preferences']}, " +
                   f"Category={parsed_input['recipe_category']}, " +
                   f"Index={parsed_input['recipe_index']}, " +
                   f"Name={parsed_input['recipe_name']}")
        
        # Handle different intents
        intent = parsed_input['intent']
        
        if intent == 'quit':
            return format_response('goodbye'), session_context
        
        elif intent == 'help':
            return format_response('help'), session_context
        
        elif intent == 'get_recipe_details':
            # Check if we have a specific recipe index
            recipe_index = parsed_input['recipe_index']
            recipe_name = parsed_input['recipe_name']
            
            # If we have an index and last search results, use it
            if recipe_index is not None and session_context.get('last_search_results') is not None:
                if 0 <= recipe_index < len(session_context['last_search_results']):
                    recipe_id = session_context['last_search_results'][recipe_index]
                    
                    # Use 'id' column for lookup if available
                    if 'id' in recipes_df.columns:
                        recipe_row = recipes_df[recipes_df['id'] == recipe_id]
                        if not recipe_row.empty:
                            recipe_details = get_detailed_recipe(recipe_row.iloc[0]['name'], recipes_df, config)
                            return format_response('recipe_detail', {'recipe': recipe_details}), session_context
                    else:
                        # Fallback to index lookup
                        if recipe_id in recipes_df.index:
                            recipe_details = get_detailed_recipe(recipes_df.loc[recipe_id]['name'], recipes_df, config)
                            return format_response('recipe_detail', {'recipe': recipe_details}), session_context
            
            # If we have a recipe name, try to find it
            elif recipe_name:
                recipe_details = get_detailed_recipe(recipe_name, recipes_df, config)
                if recipe_details:
                    return format_response('recipe_detail', {'recipe': recipe_details}), session_context
                else:
                    return f"I couldn't find a recipe called '{recipe_name}'. Please try again.", session_context
            
            # If we have neither index nor name, but a single-digit input, try it as an index
            elif user_input.strip().isdigit():
                recipe_index = int(user_input.strip()) - 1  # Convert to 0-based index
                if session_context.get('last_search_results') is not None:
                    if 0 <= recipe_index < len(session_context['last_search_results']):
                        recipe_id = session_context['last_search_results'][recipe_index]
                        
                        # Use 'id' column for lookup if available
                        if 'id' in recipes_df.columns:
                            recipe_row = recipes_df[recipes_df['id'] == recipe_id]
                            if not recipe_row.empty:
                                recipe_details = get_detailed_recipe(recipe_row.iloc[0]['name'], recipes_df, config)
                                return format_response('recipe_detail', {'recipe': recipe_details}), session_context
                        else:
                            # Fallback to index lookup
                            if recipe_id in recipes_df.index:
                                recipe_details = get_detailed_recipe(recipes_df.loc[recipe_id]['name'], recipes_df, config)
                                return format_response('recipe_detail', {'recipe': recipe_details}), session_context
            
            return "Please specify which recipe you'd like to see, either by number or name.", session_context
        
        elif intent == 'find_recipe':
            include_ingredients = parsed_input['include_ingredients']
            exclude_ingredients = parsed_input['exclude_ingredients']
            dietary_preferences = parsed_input['dietary_preferences']
            recipe_category = parsed_input['recipe_category']
            
            # Log search parameters
            logger.info(f"Searching for recipes with: include={include_ingredients}, " + 
                       f"exclude={exclude_ingredients}, dietary={dietary_preferences}, category={recipe_category}")
            
            # If no ingredients, no dietary preferences, and no category, prompt the user
            if not include_ingredients and not dietary_preferences and not recipe_category:
                return format_response('no_input'), session_context
            
            # Find matching recipes
            matching_df = find_matching_recipes(
                include_ingredients=include_ingredients,
                exclude_ingredients=exclude_ingredients,
                dietary_preferences=dietary_preferences,
                df_recipes=recipes_df,
                config=config,
                limit=10,
                recipe_category=recipe_category
            )
            
            # Log search results
            logger.info(f"Recipe search returned {len(matching_df) if not matching_df.empty else 0} results")
            
            # Store recipe IDs (prefer 'id' column if available)
            if not matching_df.empty and 'id' in matching_df.columns:
                recipe_ids = list(matching_df['id'])
            else:
                recipe_ids = list(matching_df.index) if not matching_df.empty else []
            session_context['last_search_results'] = recipe_ids
            
            if not matching_df.empty:
                # Add logging to check the type before conversion
                logger.info(f"Type of matching_df before to_dict: {type(matching_df)}")
                recipes_list = matching_df.to_dict(orient='records')
                return format_response('recipe_list', {'recipes': recipes_list}), session_context
            else:
                return format_response('not_found'), session_context
        
        else:
            return format_response('error'), session_context
    
    except Exception as e:
        logger.error(f"Error processing user input: {e}", exc_info=True)
        return format_response('error'), session_context

def chat_loop(recipes_df, canonical_ingredients):
    """
    Main chat loop for the recipe chatbot.
    
    Parameters:
    -----------
    recipes_df : pandas.DataFrame
        DataFrame containing the recipe data
    canonical_ingredients : set
        Set of canonical ingredient names
    """
    # Initialize session context
    session_context = {
        'last_search_results': None,
        'current_page': 0,
        'recipes_per_page': 5
    }
    
    # Print welcome message
    print(format_response('welcome'))
    
    # Main chat loop
    while True:
        try:
            # Get user input
            print("\n> ", end="")
            user_input = input().strip()
            
            # Process the input
            if not user_input:
                print(format_response('no_input'))
                continue
            
            # Lower case for case-insensitive comparison
            lower_input = user_input.lower()
            
            # Simple exit commands (bypass the parser for efficiency)
            if lower_input in ('quit', 'exit', 'bye', 'goodbye'):
                print(format_response('goodbye'))
                break
            
            # Process input
            response, session_context = process_user_input(
                user_input, recipes_df, canonical_ingredients, session_context
            )
            
            # Print the response
            print(response)
            
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print("\nExiting recipe bot...")
            break
        except Exception as e:
            logger.error(f"Error in chat loop: {e}", exc_info=True)
            print("Sorry, something went wrong. Please try again.")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Recipe Chatbot')
    
    parser.add_argument(
        '--no-limit', 
        action='store_true',
        help='Load all recipes instead of using the configured limit'
    )
    
    parser.add_argument(
        '--limit', 
        type=int,
        help='Override the configured recipe limit with a specific number'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run test queries instead of interactive mode'
    )
    
    return parser.parse_args()

def main():
    """Main function to start the recipe chatbot."""
    try:
        # Parse command line arguments
        args = parse_args()
        
        # Override LIMIT_RECIPES if specified
        if args.no_limit:
            config.LIMIT_RECIPES = None
            logger.info("Loading all recipes (no limit)")
        elif args.limit is not None:
            config.LIMIT_RECIPES = args.limit
            logger.info(f"Overriding recipe limit to {args.limit}")
        
        # Load and prepare data
        logger.info("Starting recipe chatbot...")
        recipes_df, canonical_ingredients = load_and_prepare_data()
        
        # Start the chat loop
        logger.info("Chat loop starting...")
        chat_loop(recipes_df, canonical_ingredients)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print("Sorry, an unexpected error occurred and the chatbot needs to close.")
        return 1
    
    return 0

def test_queries():
    """
    Function to manually test the recipe bot with various inputs.
    Useful for debugging and ensuring proper functionality.
    """
    print("Starting recipe bot testing...")
    
    # Set logging level for testing
    logging.getLogger().setLevel(logging.INFO)
    
    # Load and prepare data
    recipes_df, canonical_ingredients = load_and_prepare_data()
    
    # Create a session context
    session_context = {
        'last_search_results': None,
        'current_page': 0,
        'recipes_per_page': 5
    }
    
    # Define test queries
    test_cases = [
        "Show me vegetarian meals",
        "Find gluten-free desserts",
        "What can I make with chicken and rice",
        "I want dinner recipes without onions",
        "Show me recipe 3",  # This should work after a search
        "Give me some breakfast ideas",
        "Find low-carb dinner recipes"
    ]
    
    # Run tests
    for query in test_cases:
        print("\n" + "="*50)
        print(f"TESTING QUERY: '{query}'")
        print("="*50)
        
        try:
            import time
            start_time = time.time()
            
            # Process the query with a timeout
            response, session_context = process_user_input(query, recipes_df, canonical_ingredients, session_context)
            
            end_time = time.time()
            print(f"\nProcessing time: {end_time - start_time:.2f} seconds")
            
            print("\nRESPONSE:")
            print(response)
            
            # If this is the first query that should return recipes, test recipe selection
            if query == "Show me vegetarian meals":
                # Now test recipe details selection
                details_query = "3"
                print("\n" + "="*50)
                print(f"TESTING SELECTION: '{details_query}'")
                print("="*50)
                
                start_time = time.time()
                details_response, session_context = process_user_input(details_query, recipes_df, canonical_ingredients, session_context)
                end_time = time.time()
                
                print(f"\nProcessing time: {end_time - start_time:.2f} seconds")
                print("\nDETAILS RESPONSE:")
                print(details_response)
        
        except Exception as e:
            print(f"\nERROR processing query '{query}': {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\nTesting complete.")

if __name__ == "__main__":
    # Add debug flag
    import argparse
    parser = argparse.ArgumentParser(description='Recipe Chatbot')
    
    parser.add_argument(
        '--no-limit', 
        action='store_true',
        help='Load all recipes instead of using the configured limit'
    )
    
    parser.add_argument(
        '--limit', 
        type=int,
        help='Override the configured recipe limit with a specific number'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run test queries instead of interactive mode'
    )
    
    args = parser.parse_args()
    
    # Override LIMIT_RECIPES if specified
    if args.no_limit:
        config.LIMIT_RECIPES = None
        logger.info("Loading all recipes (no limit)")
    elif args.limit is not None:
        config.LIMIT_RECIPES = args.limit
        logger.info(f"Overriding recipe limit to {args.limit}")
    
    if args.test:
        # Run test mode
        test_queries()
    else:
        # Run normal mode
        sys.exit(main()) 