import logging
from recipe_matcher import find_matching_recipes
from nlu_parser import parse_user_query
import pandas as pd

class RecipeBot:
    def __init__(self, df_recipes, canonical_ingredients, config):
        """
        Initialize the recipe bot with necessary data and configuration.
        
        Parameters:
        -----------
        df_recipes : pandas.DataFrame
            DataFrame containing recipes data.
        canonical_ingredients : list
            List of canonical ingredient names.
        config : module
            Configuration module with settings.
        """
        self.df_recipes = df_recipes
        self.canonical_ingredients = canonical_ingredients
        self.config = config
        self.conversation_history = []
        logging.info(f"RecipeBot initialized with {len(df_recipes)} recipes and {len(canonical_ingredients)} ingredients")
    
    def process_query(self, query):
        """
        Process a user query and return a response.
        
        Parameters:
        -----------
        query : str
            The user's query text.
            
        Returns:
        --------
        str
            Response text to the user.
        """
        # Add query to conversation history
        self.conversation_history.append({"role": "user", "content": query})
        
        # Parse the query using the NLU parser
        parsed_data = parse_user_query(query, self.canonical_ingredients)
        logging.info(f"Parsed query: {parsed_data}")
        
        # Generate response based on the intent
        response = self._generate_response(parsed_data)
        
        # Add response to conversation history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response
    
    def _generate_response(self, parsed_data):
        """
        Generate a response based on the parsed query data.
        
        Parameters:
        -----------
        parsed_data : dict
            Dictionary containing the parsed query data.
            
        Returns:
        --------
        str
            Response text.
        """
        intent = parsed_data.get('intent', 'unknown')
        
        if intent == 'unknown':
            return "I'm not sure what you're asking. You can ask me for recipe suggestions based on ingredients you have or dietary preferences."
        
        elif intent == 'help':
            return """I'm a recipe suggestion bot. Here's how I can help:
- Ask for recipes with specific ingredients (e.g., "Find me recipes with chicken and rice")
- Exclude ingredients you don't want (e.g., "Pasta recipes without mushrooms")
- Specify dietary preferences (e.g., "Vegetarian dinner ideas" or "Gluten-free desserts")
- Get quick meal ideas (e.g., "Quick dinner recipes with beef")"""
        
        elif intent == 'find_recipe':
            include_ingredients = parsed_data.get('include_ingredients', [])
            exclude_ingredients = parsed_data.get('exclude_ingredients', [])
            dietary_preferences = parsed_data.get('dietary_preferences', [])
            
            # If no ingredients or preferences specified, ask for more information
            if not include_ingredients and not dietary_preferences:
                return "Please specify some ingredients or dietary preferences for me to suggest recipes."
            
            # Find matching recipes
            matching_recipes = find_matching_recipes(
                include_ingredients=include_ingredients,
                exclude_ingredients=exclude_ingredients,
                dietary_preferences=dietary_preferences,
                df_recipes=self.df_recipes,
                config=self.config,
                limit=5
            )
            
            if matching_recipes.empty:
                return f"I couldn't find any recipes matching your criteria. Try different ingredients or preferences."
            
            # Format response with recipe suggestions
            response = "Here are some recipe suggestions for you:\n\n"
            
            for idx, row in matching_recipes.iterrows():
                response += f"🍳 {row['name']}\n"
                response += f"   Ingredients: {', '.join(row['ingredients'][:5])}"
                if len(row['ingredients']) > 5:
                    response += f" and {len(row['ingredients']) - 5} more"
                response += f"\n   Cook time: {row.get('minutes', 'N/A')} minutes\n\n"
            
            return response
        
        else:
            return "I'm not sure what you're asking. You can ask me for recipe suggestions based on ingredients you have or dietary preferences." 