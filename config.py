"""
Configuration settings for the Recipe Bot application.
"""

import os
from pathlib import Path

# ----- DATASET CONFIGURATION -----

# Path to the dataset file (can be .csv, .json, or .xlsx)
DATASET_PATH = 'D:/chatbot-project/recipe_bot_project/data/recipes_raw_nosource_epi.json'

# Limit the number of recipes to load (set to None for all recipes)
LIMIT_RECIPES = None

# ----- DATA PROCESSING CONFIGURATION -----

# Remove quantities and units from ingredients during preprocessing
REMOVE_QUANTITIES = True

# ----- COLUMN NAME CONFIGURATION -----
# Standardized column names used after loading/cleaning
RECIPE_NAME_COLUMN = "name"
RAW_INGREDIENTS_COLUMN = "ingredients" # Column from initial load/map
CLEANED_INGREDIENTS_COLUMN = "cleaned_ingredients" # Column created by data_cleaner
INSTRUCTIONS_COLUMN = "instructions"

# ----- INGREDIENT MATCHING CONFIGURATION -----

# Minimum match score (0-100) for fuzzy matching ingredients
MIN_MATCH_SCORE = 70

# Boost value for exact ingredient matches
EXACT_MATCH_BOOST = 2.0

# Penalty for recipes containing excluded ingredients
EXCLUDED_INGREDIENT_PENALTY = 5.0

# ----- DIETARY PREFERENCE CONFIGURATION -----

# Define non-vegetarian ingredients
NON_VEGETARIAN_INGREDIENTS = [
    'chicken', 'beef', 'pork', 'lamb', 'bacon', 'ham', 'turkey', 'veal', 
    'duck', 'goose', 'venison', 'bison', 'rabbit', 'anchovy', 'oyster',
    'gelatin', 'lard', 'tallow', 'suet', 'meat', 'prosciutto', 'salami',
    'pepperoni', 'hot dog', 'sausage', 'fish', 'shrimp', 'crab', 'lobster',
    'clam', 'mussel', 'squid', 'octopus', 'scallop'
]

# Define non-vegan ingredients (includes non-vegetarian plus animal products)
NON_VEGAN_INGREDIENTS = NON_VEGETARIAN_INGREDIENTS + [
    'egg', 'milk', 'cream', 'butter', 'cheese', 'yogurt', 'honey', 'mayo',
    'mayonnaise', 'dairy', 'whey', 'casein', 'lactose', 'ghee', 'ice cream',
    'custard', 'sour cream', 'cream cheese', 'cottage cheese', 'ricotta',
    'mozzarella', 'parmesan', 'cheddar', 'brie', 'feta', 'gouda'
]

# Define gluten-containing ingredients
GLUTEN_INGREDIENTS = [
    'wheat', 'barley', 'rye', 'triticale', 'spelt', 'kamut', 'farina',
    'semolina', 'flour', 'bread', 'pasta', 'couscous', 'bulgur', 'seitan',
    'cracker', 'cake', 'cookie', 'pastry', 'cereal', 'beer', 'malt'
]

# Define dairy ingredients
DAIRY_INGREDIENTS = [
    'milk', 'cream', 'butter', 'cheese', 'yogurt', 'dairy', 'whey', 'casein',
    'lactose', 'ghee', 'ice cream', 'custard', 'sour cream', 'cream cheese',
    'cottage cheese', 'ricotta', 'mozzarella', 'parmesan', 'cheddar', 'brie',
    'feta', 'gouda', 'buttermilk', 'half-and-half', 'condensed milk',
    'evaporated milk', 'powdered milk', 'kefir'
]

# Define nut ingredients
NUT_INGREDIENTS = [
    'almond', 'cashew', 'walnut', 'pecan', 'pistachio', 'hazelnut', 'peanut',
    'pine nut', 'macadamia', 'brazil nut', 'chestnut', 'coconut', 'nutmeg',
    'nut butter', 'nut oil', 'nut milk', 'nut flour', 'nut paste', 'marzipan',
    'nougat', 'praline', 'gianduja'
]

# ----- RECIPE MATCHING CONFIGURATION -----

# Maximum number of recipes to return in search results
RESULTS_LIMIT = 10

# Minimum ratio of matched ingredients to total ingredients in recipe
MIN_MATCH_RATIO = 0.3

# ----- DISPLAY CONFIGURATION -----

# Number of recipes to display per page
RECIPES_PER_PAGE = 5

# Number of ingredients to display in recipe summary
MAX_INGREDIENTS_IN_SUMMARY = 5

# ----- LOGGING CONFIGURATION -----

# Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = 'INFO'

# Path to log file (set to None for no file logging)
LOG_FILE = 'recipe_bot.log'

# ----- NLP CONFIGURATION -----

# Flag to enable/disable advanced NLP features
ENABLE_NLP = True
USE_NLTK = True

# Path to NLP model (if applicable)
NLP_MODEL_PATH = None

# ----- UI CONFIGURATION -----

# Enable/disable ASCII art for console UI
USE_ASCII_ART = True

# Enable/disable colorized output (if supported by terminal)
USE_COLORS = True

# ----- OTHER CONFIGURATION -----

# Application version
VERSION = "1.0.0" 