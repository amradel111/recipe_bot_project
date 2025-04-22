"""
Response generation module for Recipe Bot.
This module contains functions to generate text responses for the chatbot.
"""

import random
import logging

# Set up logging
logger = logging.getLogger(__name__)

def generate_welcome_response():
    """
    Generate a welcome message for the chatbot.
    
    Returns:
    --------
    str
        Welcome message.
    """
    return """
Welcome to Recipe Bot!
----------------------
I can help you find recipes based on ingredients you have.

Tell me what ingredients you have, and I'll suggest recipes you can make.
For example, you can ask: "What can I make with eggs, flour, and sugar?"

Type "help" for more information or "quit" to exit.
"""

def generate_help_response():
    """
    Generate a help message for the chatbot.
    
    Returns:
    --------
    str
        Help message.
    """
    return """
Recipe Bot Help:
---------------
Here's how to use Recipe Bot:

1. Find recipes by ingredients:
   Example: "What can I make with chicken, rice, and tomatoes?"

2. Exclude ingredients:
   Example: "Find recipes with potatoes but without cheese"

3. Ask for specific dietary preferences:
   Example: "Vegetarian recipes with mushrooms"
   Example: "Quick dinner ideas with chicken"
   Example: "Gluten-free desserts"

4. View recipe details:
   After seeing recipe matches, enter the number or name of a recipe.

5. Exit the chatbot:
   Type "quit" or "exit"
"""

def generate_no_matches_response(entities):
    """
    Generate a response for when no recipe matches are found.
    
    Parameters:
    -----------
    entities : dict
        Dictionary containing 'include' and 'exclude' lists.
        
    Returns:
    --------
    str
        No matches response.
    """
    include = entities.get('include', [])
    exclude = entities.get('exclude', [])
    
    if not include and not exclude:
        return "I couldn't find any recipes for that. Please try specifying some ingredients."
    
    if include and exclude:
        return f"I couldn't find any recipes with {', '.join(include)} that don't contain {', '.join(exclude)}. Try removing some restrictions or using different ingredients."
    
    if include:
        return f"I couldn't find any recipes with {', '.join(include)}. Try using different ingredients or fewer restrictions."
    
    if exclude:
        return f"I couldn't find any recipes without {', '.join(exclude)}. Try being more specific about what ingredients you want to use."

def generate_recipe_matches_response(matches, entities):
    """
    Generate a response for recipe matches.
    
    Parameters:
    -----------
    matches : list
        List of recipe match dictionaries.
    entities : dict
        Dictionary containing 'include' and 'exclude' lists.
        
    Returns:
    --------
    str
        Recipe matches response.
    """
    include = entities.get('include', [])
    exclude = entities.get('exclude', [])
    
    # Create introduction based on ingredients
    if include and exclude:
        intro = f"I found {len(matches)} recipes with {', '.join(include)} and without {', '.join(exclude)}:"
    elif include:
        intro = f"I found {len(matches)} recipes with {', '.join(include)}:"
    elif exclude:
        intro = f"I found {len(matches)} recipes without {', '.join(exclude)}:"
    else:
        intro = f"I found {len(matches)} recipes that might work for you:"
    
    # Build the list of recipes
    recipe_list = []
    for i, match in enumerate(matches, 1):
        recipe_name = match['recipe_name']
        score = match['match_score']
        
        # Format common ingredients
        common = ', '.join(score['common_ingredients']) if score['common_ingredients'] else "none"
        
        # Add recipe to the list
        recipe_list.append(f"{i}. {recipe_name} (matched ingredients: {common})")
    
    # Combine intro and recipe list
    result = intro + "\n\n" + "\n".join(recipe_list)
    
    # Add prompt for selection
    result += "\n\nEnter a number to see the detailed recipe."
    
    return result

def generate_recipe_detail_response(recipe_details):
    """
    Generate a response with detailed recipe information.
    
    Parameters:
    -----------
    recipe_details : dict
        Dictionary with recipe details.
        
    Returns:
    --------
    str
        Recipe detail response.
    """
    # Build the response
    response = f"Here's the recipe for {recipe_details['name']}:\n\n"
    
    # Add ingredients
    if isinstance(recipe_details['ingredients'], list):
        response += "Ingredients:\n" + "\n".join([f"- {ingredient}" for ingredient in recipe_details['ingredients']])
    else:
        response += f"Ingredients: {recipe_details['ingredients']}\n"
    
    # Add instructions if available
    if 'instructions' in recipe_details:
        response += f"\n\nInstructions: {recipe_details['instructions']}"
    
    # Add cuisine if available
    if 'cuisine' in recipe_details:
        response += f"\n\nCuisine: {recipe_details['cuisine']}"
    
    return response

def generate_response(intent_data, matches=None, entities=None):
    """
    Generate a response based on intent and entities.
    
    Parameters:
    -----------
    intent_data : dict
        Dictionary with intent information.
    matches : list, optional
        List of recipe matches (default: None).
    entities : dict, optional
        Dictionary containing 'include' and 'exclude' lists (default: None).
        
    Returns:
    --------
    str
        Generated response.
    """
    # Default values
    matches = matches or []
    entities = entities or {'include': [], 'exclude': []}
    
    primary_intent = intent_data.get('primary', 'find_recipe')
    
    # Generate different responses based on intent
    if primary_intent == 'quit':
        return random.choice([
            "Goodbye! Come back when you're hungry again.",
            "See you later. Happy cooking!",
            "Bye! Hope I helped you find something tasty.",
            "Until next time! Enjoy your meal."
        ])
    
    elif primary_intent == 'help':
        return generate_help_response()
    
    elif primary_intent == 'find_recipe':
        # Handle dietary preferences in response
        diet_prefixes = {
            'vegetarian': "vegetarian",
            'vegan': "vegan",
            'gluten_free': "gluten-free",
            'dairy_free': "dairy-free",
            'low_carb': "low-carb",
            'quick': "quick"
        }
        
        dietary_preferences = intent_data.get('dietary_preferences', [])
        diet_prefix = ""
        
        if dietary_preferences:
            diet_terms = [diet_prefixes.get(pref, pref) for pref in dietary_preferences]
            diet_prefix = f"I'm looking for {', '.join(diet_terms)} recipes. "
        
        # Check if we have matches
        if not matches:
            return diet_prefix + generate_no_matches_response(entities)
        else:
            return diet_prefix + generate_recipe_matches_response(matches, entities)
    
    # Default response if no specific intent is matched
    return "I'm not sure what you're asking. You can try asking for recipes with specific ingredients, or type 'help' for more information."

if __name__ == "__main__":
    # Test the response generator
    
    print("Testing response generator with sample inputs:\n")
    
    # Test help intent
    print("Help Intent Response:")
    print(generate_response({'primary': 'help'}))
    print("\n" + "-"*50 + "\n")
    
    # Test quit intent
    print("Quit Intent Response:")
    print(generate_response({'primary': 'quit'}))
    print("\n" + "-"*50 + "\n")
    
    # Test find_recipe intent with no ingredients
    print("Find Recipe Intent (No Ingredients) Response:")
    print(generate_response({'primary': 'find_recipe'}, [], []))
    print("\n" + "-"*50 + "\n")
    
    # Test find_recipe intent with ingredients but no matches
    print("Find Recipe Intent (No Matches) Response:")
    print(generate_response({'primary': 'find_recipe'}, [], {'include': ['exotic_ingredient', 'rare_spice'], 'exclude': []}))
    print("\n" + "-"*50 + "\n")
    
    # Test find_recipe intent with ingredients and matches
    sample_matches = [
        {
            'recipe_name': 'Chicken and Rice Casserole',
            'match_score': {
                'common_ingredients': ['chicken', 'rice', 'onion'],
                'match_count': 3,
                'match_ratio': 0.75,
                'coverage_ratio': 0.5,
                'score': 0.675
            }
        },
        {
            'recipe_name': 'Chicken Soup',
            'match_score': {
                'common_ingredients': ['chicken', 'onion'],
                'match_count': 2,
                'match_ratio': 0.5,
                'coverage_ratio': 0.33,
                'score': 0.449
            }
        }
    ]
    
    print("Find Recipe Intent (With Matches) Response:")
    print(generate_response({'primary': 'find_recipe'}, sample_matches, {'include': ['chicken', 'rice', 'onion', 'carrot'], 'exclude': []}))
    print("\n" + "-"*50 + "\n")
    
    # Test recipe detail response
    sample_recipe_details = {
        'name': 'Chicken and Rice Casserole',
        'ingredients': ['1 lb chicken breast', '2 cups rice', '1 onion, diced', '2 cups chicken broth'],
        'instructions': 'Preheat oven to 375°F. In a casserole dish, combine chicken, rice, and onion. Pour broth over the top. Bake for 45 minutes.',
        'cuisine': 'American'
    }
    
    print("Recipe Detail Response:")
    print(generate_recipe_detail_response(sample_recipe_details)) 