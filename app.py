#!/usr/bin/env python
# coding: utf-8

from flask import Flask, render_template, request, jsonify
import logging
import sys
import os
from pathlib import Path

# Add the project directory to the path
project_dir = Path(__file__).parent
sys.path.append(str(project_dir))

# Import our custom modules
import config
from nlu_parser import parse_query
from recipe_matcher import find_matching_recipes, get_detailed_recipe
from data_loader import load_recipe_data, preprocess_ingredients
from data_cleaner import apply_cleaning_to_dataframe
from main import process_user_input, load_and_prepare_data

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

# Initialize Flask app
app = Flask(__name__)

# Load and prepare recipe data at startup
recipes_df, canonical_ingredients = load_and_prepare_data()

# Initialize session context
session_contexts = {}

@app.route('/')
def index():
    """Render the main page of the web application."""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Process chat messages from the user."""
    try:
        # Get the user input from the request
        user_input = request.json.get('message', '').strip()
        session_id = request.json.get('session_id', 'default_session')
        
        # Initialize session context if it doesn't exist
        if session_id not in session_contexts:
            session_contexts[session_id] = {
                'last_search_results': None,
                'current_page': 0,
                'recipes_per_page': 5
            }
        
        # Process the user input
        response, updated_context = process_user_input(
            user_input, 
            recipes_df, 
            canonical_ingredients, 
            session_contexts[session_id]
        )
        
        # Update the session context
        session_contexts[session_id] = updated_context
        
        # Return the response
        return jsonify({
            'response': response,
            'session_id': session_id
        })
    
    except Exception as e:
        logger.error(f"Error processing chat: {e}", exc_info=True)
        return jsonify({
            'response': "Sorry, I encountered an error. Please try again.",
            'session_id': request.json.get('session_id', 'default_session')
        })

@app.route('/recipe/<recipe_index>', methods=['GET'])
def get_recipe(recipe_index):
    """Get detailed information about a specific recipe."""
    try:
        session_id = request.args.get('session_id', 'default_session')
        
        if session_id not in session_contexts:
            return jsonify({'error': 'Invalid session ID'})
        
        # Convert recipe_index to integer
        recipe_idx = int(recipe_index)
        
        # Check if we have search results and if the index is valid
        if (session_contexts[session_id]['last_search_results'] is None or 
            recipe_idx < 0 or 
            recipe_idx >= len(session_contexts[session_id]['last_search_results'])):
            return jsonify({'error': 'Invalid recipe index'})
        
        # Get the recipe ID
        recipe_id = session_contexts[session_id]['last_search_results'][recipe_idx]
        
        # Use 'id' column for lookup if available
        if 'id' in recipes_df.columns:
            recipe_row = recipes_df[recipes_df['id'] == recipe_id]
            if not recipe_row.empty:
                recipe_details = get_detailed_recipe(recipe_row.iloc[0]['name'], recipes_df, config)
                return jsonify({'recipe': recipe_details})
        else:
            # Fallback to index lookup
            if recipe_id in recipes_df.index:
                recipe_details = get_detailed_recipe(recipes_df.loc[recipe_id]['name'], recipes_df, config)
                return jsonify({'recipe': recipe_details})
        
        return jsonify({'error': 'Recipe not found'})
    
    except Exception as e:
        logger.error(f"Error getting recipe: {e}", exc_info=True)
        return jsonify({'error': 'An error occurred while retrieving the recipe'})

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True) 