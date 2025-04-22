"""
Natural Language Understanding module for Recipe Bot.
This module contains functions to parse and understand user input.
"""

import re
import nltk
import logging
import string
from difflib import get_close_matches
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import config
from collections import Counter
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# Set up logging
logger = logging.getLogger(__name__)

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

# Intent keywords - expanded for more capabilities
QUIT_KEYWORDS = ['quit', 'exit', 'bye', 'goodbye', 'stop', 'close', 'end']
HELP_KEYWORDS = ['help', 'instructions', 'guide', 'how', 'commands', 'manual', 'tips', 'usage']
FIND_RECIPE_KEYWORDS = ['find', 'search', 'recipe', 'make', 'cook', 'prepare', 'suggest', 'recommend', 'idea', 'dish', 'meal']

# New intents for dietary restrictions
DIETARY_KEYWORDS = {
    'vegetarian': ['vegetarian', 'veggie', 'no meat', 'meatless', 'plant-based'],
    'vegan': ['vegan', 'no animal', 'plant-based', 'no dairy', 'no eggs'],
    'gluten_free': ['gluten free', 'gluten-free', 'no gluten', 'celiac', 'wheat free'],
    'dairy_free': ['dairy free', 'dairy-free', 'no dairy', 'lactose free', 'no milk'],
    'low_carb': ['low carb', 'low-carb', 'keto', 'ketogenic', 'no carbs'],
    'quick': ['quick', 'fast', 'easy', 'simple', 'under 30', 'quick meal']
}

# Negation terms to detect ingredients to exclude
NEGATION_TERMS = [
    'no', 'not', 'without', 'except', 'but no', 'dont', "don't", 'excluding', 'none', 'no more',
    'avoid', 'free from', 'free of', 'exclude', 'minus', 'leave out', 'skip', 'omit',
    'cannot have', 'can\'t have', 'allergic to', 'allergy to', 'sensitive to',
    'intolerant to', 'intolerance', 'anything but', 'rather not', 'instead of',
    'but not', 'other than', 'remove', 'nothing with', 'nothing containing'
]

# Download required NLTK resources (only needs to be done once)
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

# Set up stemmer, lemmatizer, and stopwords
stemmer = PorterStemmer()
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

# Dictionary of intents and their pattern list
INTENT_PATTERNS = {
    'find_recipe': [
        r'find( me)?( a)?( recipe)?( for)?',
        r'search( for)?( a)?( recipe)?',
        r'look( for)?( a)?( recipe)?',
        r'how (can|do) (i|you) (make|cook|prepare)',
        r'show( me)?( a)?( recipe)?( for)?',
        r'(i want|i\'d like|can i have)( a)?( recipe)?( for)?',
        r'recipe( for)?',
        r'recipes with',
        r'recipes (using|containing)',
        r'what can i (make|cook) with',
        r'suggest( a)? recipe',
        r'i have'
    ],
    'help': [
        r'^help$',
        r'what can you do',
        r'how (does|do) (this|you) work',
        r'what commands',
        r'(help|show) (me|us)( the)? commands',
        r'what can i (ask|say)',
        r'show (options|features)'
    ],
    'quit': [
        r'^(quit|exit|bye|goodbye)$',
        r'(close|end)( the)? (chat|session)',
        r'stop( the)? (chat|session)',
        r'(i( want to)?|let\'s) (quit|exit)',
        r'shut down'
    ],
    'get_recipe_details': [
        r'(show|get|give)( me)?( the)? (details|instructions|steps|recipe|ingredients)',
        r'how (do|can) (i|you) (make|prepare|cook)',
        r'tell me (more|about)',
        r'what(\'s| are| is) (in|the ingredients for)',
        r'(view|see|open) recipe',
        r'recipe details',
        r'ingredients (for|in|of)',
        r'instructions for'
    ]
}

# Dictionary of dietary preferences and their related terms
DIETARY_PREFERENCE_TERMS = {
    'vegetarian': [
        'vegetarian', 'veggie', 'no meat', 'meat free', 'meatless', 
        'no beef', 'no chicken', 'no pork', 'no fish', 'vegetable based',
        'vegetable-based', 'lacto ovo', 'lacto-ovo', 'non-meat',
        'meat-free', 'no animal flesh'
    ],
    'vegan': [
        'vegan', 'plant-based', 'no animal products', 'dairy-free and vegetarian',
        'plant based', 'animal-free', 'no animal', 'purely plant', 
        'entirely plant', 'no eggs', 'no dairy', 'no meat', 'no honey',
        'no animal derivatives', 'plant only', 'no animal ingredients'
    ],
    'gluten-free': [
        'gluten-free', 'gluten free', 'no gluten', 'without gluten', 'gf',
        'celiac friendly', 'celiac-friendly', 'no wheat', 'wheat-free',
        'gluten intolerance', 'gluten sensitivity', 'gluten intolerant',
        'no flour', 'non-gluten', 'sans gluten', 'gluten-less'
    ],
    'dairy-free': [
        'dairy-free', 'dairy free', 'no dairy', 'without dairy', 'lactose-free', 
        'non-dairy', 'no milk', 'milk-free', 'no cheese', 'no butter',
        'no cream', 'no yogurt', 'lactose intolerant', 'lactose intolerance',
        'no lactose', 'dairy intolerance', 'dairy allergy'
    ],
    'nut-free': [
        'nut-free', 'nut free', 'no nuts', 'without nuts', 'peanut-free', 
        'tree nut free', 'almond free', 'cashew free', 'walnut free',
        'pecan free', 'no peanuts', 'nut allergy', 'no tree nuts',
        'peanut allergy', 'nut intolerance', 'no nut', 'no almond'
    ],
    'low-carb': [
        'low-carb', 'low carb', 'keto', 'ketogenic', 'low-carbohydrate', 
        'carb-free', 'low carbohydrate', 'no carbs', 'minimal carbs',
        'reduced carb', 'carb restricted', 'low sugar', 'sugar-free',
        'keto friendly', 'keto-friendly', 'atkins', 'lchf', 'no starch'
    ],
    'paleo': [
        'paleo', 'paleolithic', 'caveman diet', 'stone age diet', 
        'hunter-gatherer', 'primal', 'grain-free', 'no grains',
        'no processed food', 'no dairy', 'no legumes', 'ancestral diet'
    ],
    'whole30': [
        'whole30', 'whole 30', 'no sugar', 'no grains', 'no dairy',
        'no legumes', 'no alcohol', 'no processed foods', 'clean eating',
        'no additives', 'no sulfites', 'no carrageenan'
    ],
    'pescatarian': [
        'pescatarian', 'pescetarian', 'fish but no meat', 'seafood but no meat',
        'no meat except fish', 'fish only', 'seafood only', 'fish vegetarian',
        'fish-eating vegetarian', 'pesco-vegetarian'
    ],
    'halal': [
        'halal', 'no pork', 'halal meat', 'islamically permissible',
        'halal certified', 'zabiha', 'dhabiha', 'no alcohol'
    ],
    'kosher': [
        'kosher', 'kosher food', 'kashrut', 'no pork', 'no shellfish',
        'no mixing meat and dairy', 'pareve', 'parve'
    ]
}

# Combine negation patterns into a regex pattern with word boundaries
NEGATION_PATTERN = r'\b(' + '|'.join(NEGATION_TERMS) + r')\b'

def preprocess_input(text):
    """
    Preprocess user input text.
    
    Parameters:
    -----------
    text : str
        Raw text input from user.
        
    Returns:
    --------
    str
        Preprocessed text.
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation, except commas which separate ingredients
    text = re.sub(r'[^\w\s,]', ' ', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def find_closest_ingredient(word, canonical_ingredients, threshold=0.8):
    """
    Find the closest matching ingredient from the canonical list using fuzzy matching.
    
    Parameters:
    -----------
    word : str
        Word to find a match for.
    canonical_ingredients : set
        Set of canonical ingredient names.
    threshold : float, optional
        Minimum similarity score to consider a match (0-1).
        
    Returns:
    --------
    str or None
        Closest matching ingredient or None if no match found.
    """
    # Handle empty input
    if not word or not word.strip():
        return None
    
    # Convert to lowercase for case-insensitive matching
    word = word.lower().strip()
    
    # Common ingredients with their canonical forms 
    common_ingredient_map = {
        # Meats
        'chicken': 'chicken',
        'chicken breast': 'chicken',
        'chicken thigh': 'chicken',
        'chicken leg': 'chicken',
        'chicken wing': 'chicken',
        'poultry': 'chicken',
        'beef': 'beef',
        'ground beef': 'beef',
        'steak': 'beef',
        'hamburger': 'beef',
        'stewing beef': 'beef',
        'pork': 'pork',
        'ham': 'pork',
        'bacon': 'pork',
        'pork chop': 'pork',
        'sausage': 'sausage',
        'hotdog': 'sausage',
        'bratwurst': 'sausage',
        'kielbasa': 'sausage',
        'lamb': 'lamb',
        'mutton': 'lamb',
        'turkey': 'turkey',
        'duck': 'duck',
        
        # Seafood
        'fish': 'fish',
        'salmon': 'salmon',
        'tuna': 'tuna',
        'cod': 'cod',
        'tilapia': 'tilapia',
        'shrimp': 'shrimp',
        'prawn': 'shrimp',
        'crab': 'crab',
        'lobster': 'lobster',
        'scallop': 'scallop',
        'scallops': 'scallop',
        'mussel': 'mussel',
        'mussels': 'mussel',
        'clam': 'clam',
        'clams': 'clam',
        'oyster': 'oyster',
        'oysters': 'oyster',
        
        # Grains
        'rice': 'rice',
        'brown rice': 'rice',
        'white rice': 'rice',
        'jasmine rice': 'rice',
        'basmati rice': 'rice',
        'arborio rice': 'rice',
        'pasta': 'pasta',
        'spaghetti': 'pasta',
        'penne': 'pasta',
        'linguine': 'pasta',
        'fettuccine': 'pasta',
        'macaroni': 'pasta',
        'noodle': 'noodles',
        'noodles': 'noodles',
        'ramen': 'noodles',
        'udon': 'noodles',
        'quinoa': 'quinoa',
        'couscous': 'couscous',
        'barley': 'barley',
        'oats': 'oats',
        'oatmeal': 'oats',
        
        # Vegetables
        'potato': 'potatoes',
        'potatoes': 'potatoes',
        'spud': 'potatoes',
        'sweet potato': 'sweet potatoes',
        'sweet potatoes': 'sweet potatoes',
        'yam': 'yams',
        'yams': 'yams',
        'tomato': 'tomatoes',
        'tomatoes': 'tomatoes',
        'roma': 'tomatoes',
        'cherry tomato': 'tomatoes',
        'onion': 'onions',
        'onions': 'onions',
        'scallion': 'scallions',
        'scallions': 'scallions',
        'green onion': 'scallions',
        'green onions': 'scallions',
        'garlic': 'garlic',
        'carrot': 'carrots',
        'carrots': 'carrots',
        'celery': 'celery',
        'bell pepper': 'bell peppers',
        'bell peppers': 'bell peppers',
        'capsicum': 'bell peppers',
        'chili': 'chili peppers',
        'chili pepper': 'chili peppers',
        'jalapeno': 'jalapeno',
        'jalapenos': 'jalapeno',
        'lettuce': 'lettuce',
        'romaine': 'lettuce',
        'spinach': 'spinach',
        'kale': 'kale',
        'broccoli': 'broccoli',
        'cauliflower': 'cauliflower',
        'corn': 'corn',
        'maize': 'corn',
        'zucchini': 'zucchini',
        'courgette': 'zucchini',
        'cucumber': 'cucumber',
        'eggplant': 'eggplant',
        'aubergine': 'eggplant',
        
        # Legumes
        'bean': 'beans',
        'beans': 'beans',
        'chickpea': 'chickpeas',
        'chickpeas': 'chickpeas',
        'garbanzo': 'chickpeas',
        'lentil': 'lentils',
        'lentils': 'lentils',
        'pea': 'peas',
        'peas': 'peas',
        
        # Dairy
        'milk': 'milk',
        'cream': 'cream',
        'half and half': 'cream',
        'cheese': 'cheese',
        'cheddar': 'cheddar cheese',
        'mozzarella': 'mozzarella cheese',
        'parmesan': 'parmesan cheese',
        'feta': 'feta cheese',
        'gouda': 'gouda cheese',
        'brie': 'brie cheese',
        'yogurt': 'yogurt',
        'yoghurt': 'yogurt',
        'butter': 'butter',
        
        # Proteins
        'egg': 'eggs',
        'eggs': 'eggs',
        'tofu': 'tofu',
        'tempeh': 'tempeh',
        'seitan': 'seitan',
        
        # Fruits
        'apple': 'apples',
        'apples': 'apples',
        'banana': 'bananas',
        'bananas': 'bananas',
        'orange': 'oranges',
        'oranges': 'oranges',
        'lemon': 'lemons',
        'lemons': 'lemons',
        'lime': 'limes',
        'limes': 'limes',
        'strawberry': 'strawberries',
        'strawberries': 'strawberries',
        'blueberry': 'blueberries',
        'blueberries': 'blueberries',
        'raspberry': 'raspberries',
        'raspberries': 'raspberries',
        'blackberry': 'blackberries',
        'blackberries': 'blackberries',
        'grape': 'grapes',
        'grapes': 'grapes',
        'watermelon': 'watermelon',
        'melon': 'melon',
        'cantaloupe': 'cantaloupe',
        'honeydew': 'honeydew',
        'avocado': 'avocados',
        'avocados': 'avocados',
        
        # Herbs and Spices
        'basil': 'basil',
        'oregano': 'oregano',
        'thyme': 'thyme',
        'rosemary': 'rosemary',
        'sage': 'sage',
        'parsley': 'parsley',
        'cilantro': 'cilantro',
        'coriander': 'cilantro',
        'mint': 'mint',
        'dill': 'dill',
        'chives': 'chives',
        'cinnamon': 'cinnamon',
        'nutmeg': 'nutmeg',
        'cumin': 'cumin',
        'paprika': 'paprika',
        'turmeric': 'turmeric',
        'pepper': 'black pepper',
        'black pepper': 'black pepper',
        'salt': 'salt',
        'cayenne': 'cayenne pepper',
        'chili powder': 'chili powder',
        
        # Baking
        'flour': 'flour',
        'all purpose flour': 'flour',
        'wheat flour': 'flour',
        'bread flour': 'bread flour',
        'cake flour': 'cake flour',
        'sugar': 'sugar',
        'granulated sugar': 'sugar',
        'brown sugar': 'brown sugar',
        'powdered sugar': 'powdered sugar',
        'icing sugar': 'powdered sugar',
        'confectioners sugar': 'powdered sugar',
        'honey': 'honey',
        'maple syrup': 'maple syrup',
        'chocolate': 'chocolate',
        'cocoa': 'cocoa powder',
        'cocoa powder': 'cocoa powder',
        'baking powder': 'baking powder',
        'baking soda': 'baking soda',
        'yeast': 'yeast',
        'vanilla': 'vanilla extract',
        'vanilla extract': 'vanilla extract'
    }
    
    # Direct match for common ingredients
    if word in common_ingredient_map:
        canonical_form = common_ingredient_map[word]
        # Check if the canonical form is in the ingredient list
        if canonical_form in canonical_ingredients:
            return canonical_form
        # If not, return the original form if it's in the ingredient list
        if word in canonical_ingredients:
            return word
    
    # Try exact match first (case-insensitive)
    for ingredient in canonical_ingredients:
        if word == ingredient.lower():
            return ingredient
    
    # Try plural/singular matching
    singular_word = word
    plural_word = word
    
    # Simple pluralization rule (add 's')
    if word.endswith('s'):
        singular_word = word[:-1]
    else:
        plural_word = word + 's'
    
    # Check for singular/plural forms
    for ingredient in canonical_ingredients:
        ing_lower = ingredient.lower()
        if singular_word == ing_lower or plural_word == ing_lower:
            return ingredient
            
    # Look for similar matches using difflib
    matches = get_close_matches(word, [ing.lower() for ing in canonical_ingredients], n=1, cutoff=threshold)
    
    if matches:
        match_lower = matches[0]
        # Find the original case in canonical_ingredients
        for ingredient in canonical_ingredients:
            if ingredient.lower() == match_lower:
                logger.debug(f"Fuzzy matched '{word}' to '{ingredient}'")
                return ingredient
        
    # Try to match as part of a compound ingredient
    for ingredient in canonical_ingredients:
        ing_lower = ingredient.lower()
        if ' ' in ing_lower and word in ing_lower.split():
            logger.debug(f"Partial matched '{word}' to '{ingredient}'")
            return ingredient
            
    return None

def extract_entities(text, canonical_ingredients):
    """
    Extract ingredient entities from preprocessed user text.
    
    Parameters:
    -----------
    text : str
        Preprocessed user text.
    canonical_ingredients : set
        Set of canonical ingredient names.
        
    Returns:
    --------
    dict
        Dictionary containing:
        - 'include': List of ingredients to include
        - 'exclude': List of ingredients to exclude
    """
    # Split text on commas to handle comma-separated lists
    potential_ingredients = [part.strip() for part in text.split(',')]
    
    # Also look for and/with/or to split ingredient lists
    for i, part in enumerate(potential_ingredients):
        for separator in [' and ', ' with ', ' or ']:
            if separator in part:
                words = part.split(separator)
                potential_ingredients[i] = words[0]
                potential_ingredients.extend(words[1:])
    
    include_ingredients = []
    exclude_ingredients = []
    
    for item in potential_ingredients:
        words = word_tokenize(item)
        
        # Check for negations
        has_negation = any(neg in words for neg in NEGATION_TERMS)
        
        # Process each word
        lemmas = [lemmatizer.lemmatize(token) for token in words if token.isalpha()]
        
        for lemma in lemmas:
            # Skip very short words and common stopwords
            if len(lemma) <= 2 or lemma in ['the', 'and', 'but', 'for', 'with']:
                continue
                
            # Try to find the closest match
            ingredient_match = find_closest_ingredient(lemma, canonical_ingredients)
            
            if ingredient_match:
                if has_negation:
                    exclude_ingredients.append(ingredient_match)
                else:
                    include_ingredients.append(ingredient_match)
    
    # Remove duplicates
    return {
        'include': list(set(include_ingredients)),
        'exclude': list(set(exclude_ingredients))
    }

def detect_dietary_preferences(text):
    """
    Detect dietary preferences from user text.
    
    Parameters:
    -----------
    text : str
        Preprocessed user text.
        
    Returns:
    --------
    list
        List of detected dietary preferences.
    """
    preferences = []
    
    for pref, keywords in DIETARY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            preferences.append(pref)
            
    return preferences

def parse_intent(text):
    """
    Parse the intent from preprocessed user text.
    
    Parameters:
    -----------
    text : str
        Preprocessed user text.
        
    Returns:
    --------
    dict
        Dictionary with 'primary' intent and additional metadata.
    """
    tokens = word_tokenize(text)
    
    # Create result dictionary
    intent_data = {
        'primary': 'find_recipe',  # Default intent
        'dietary_preferences': [],
        'description': None
    }
    
    # Check for quit intent
    if any(token in QUIT_KEYWORDS for token in tokens):
        intent_data['primary'] = 'quit'
        return intent_data
    
    # Check for help intent
    if any(token in HELP_KEYWORDS for token in tokens):
        intent_data['primary'] = 'help'
        return intent_data
    
    # Detect dietary preferences
    preferences = detect_dietary_preferences(text)
    if preferences:
        intent_data['dietary_preferences'] = preferences
        
    # Check if this is a recipe detail request (likely a number or recipe name)
    if text.strip().isdigit() or len(text.split()) <= 3:
        # Could be a selection from a list
        intent_data['primary'] = 'recipe_detail'
        intent_data['description'] = text.strip()
    
    return intent_data

def parse_user_query(query, canonical_ingredients):
    """
    Parse the user's query to extract:
    - intent
    - ingredients to include
    - ingredients to exclude
    - dietary preferences
    
    Parameters:
    -----------
    query : str
        The user's query text.
    canonical_ingredients : list
        List of canonical ingredient names for matching.
        
    Returns:
    --------
    dict
        Dictionary containing:
        - intent: The identified intent
        - include_ingredients: List of ingredients to include
        - exclude_ingredients: List of ingredients to exclude
        - dietary_preferences: List of dietary preferences
    """
    # Convert query to lowercase for easier matching
    query_lower = query.lower()
    
    # Initialize result dictionary
    result = {
        'intent': 'unknown',
        'include_ingredients': [],
        'exclude_ingredients': [],
        'dietary_preferences': []
    }
    
    # Common ingredients to prioritize for direct matching
    common_ingredients = [
        'chicken', 'beef', 'pork', 'fish', 'rice', 'pasta', 'noodle', 'noodles',
        'bean', 'beans', 'potato', 'potatoes', 'tomato', 'carrot', 'onion'
    ]
    
    # Direct check for common ingredients
    for ingredient in common_ingredients:
        if re.search(r'\b' + re.escape(ingredient) + r'\b', query_lower):
            # Check if ingredient is mentioned with exclusion terms
            exclusion_context = False
            exclusion_terms = ['no ', 'without ', 'not ', "don't ", 'except ', 'but no ']
            for term in exclusion_terms:
                if re.search(term + r'.*\b' + re.escape(ingredient) + r'\b', query_lower):
                    result['exclude_ingredients'].append(ingredient)
                    exclusion_context = True
                    break
            
            # If not an exclusion, add to include ingredients
            if not exclusion_context and ingredient not in result['include_ingredients']:
                result['include_ingredients'].append(ingredient)
    
    # Detect intent
    if any(x in query_lower for x in ['recipe', 'cook', 'make', 'prepare', 'food']):
        result['intent'] = 'find_recipe'
    elif any(x in query_lower for x in ['help', 'how', 'features', 'do you', 'can you']):
        result['intent'] = 'help'
    elif any(x in query_lower for x in QUIT_KEYWORDS):
        result['intent'] = 'quit'
    elif re.match(r'^\d+$', query_lower.strip()) or re.search(r'(show|get|recipe)\s+(\d+|#\d+)', query_lower):
        result['intent'] = 'get_recipe_details'
    
    # Early return if not a recipe finding intent
    if result['intent'] != 'find_recipe':
        return result
        
    # Extract dietary preferences
    if any(term in query_lower for term in ['vegetarian', 'no meat']):
        result['dietary_preferences'].append('vegetarian')
    
    if any(term in query_lower for term in ['vegan', 'plant-based', 'plant based', 'no animal']):
        result['dietary_preferences'].append('vegan')
    
    if any(term in query_lower for term in ['gluten-free', 'gluten free', 'no gluten']):
        result['dietary_preferences'].append('gluten_free')
    
    if any(term in query_lower for term in ['dairy-free', 'dairy free', 'no dairy', 'lactose']):
        result['dietary_preferences'].append('dairy_free')
    
    if any(term in query_lower for term in ['low-carb', 'low carb', 'keto', 'low carbohydrate']):
        result['dietary_preferences'].append('low_carb')
    
    if any(term in query_lower for term in ['quick', 'fast', 'easy', 'simple', '30 minute', '30-minute', 'under 30']):
        result['dietary_preferences'].append('quick')
    
    # Extract dessert type ONLY if specifically mentioned as a category
    if any(term in query_lower for term in ['dessert recipe', 'sweet recipe', 'dessert dish']):
        if 'dessert' not in result['include_ingredients'] and 'dessert' not in result['exclude_ingredients']:
            result['include_ingredients'].append('dessert')
    
    # Check for negation patterns for ingredients (for ingredients not covered by common_ingredients)
    exclusion_terms = ['no ', 'not ', 'without ', 'exclude ', 'don\'t want ', 'don\'t include ', 'but no ', 'but not ']
    
    # Split the query into parts to analyze for exclusions
    parts = []
    
    # Add parts split by 'but' and 'without'
    if ' but ' in query_lower:
        parts.extend(query_lower.split(' but '))
    if ' without ' in query_lower:
        parts.extend(query_lower.split(' without '))
    
    # If no splitting occurred, use the original query
    if not parts:
        parts = [query_lower]
    
    # Extract excluded ingredients
    for part in parts:
        for term in exclusion_terms:
            if term in part:
                # Extract ingredient after negation term
                remain = part.split(term)[1].strip()
                words = remain.split()
                
                # Check if the next 1-3 words match any canonical ingredient
                for n in range(1, min(4, len(words) + 1)):
                    potential_ingredient = ' '.join(words[:n])
                    # Clean up potential_ingredient to remove punctuation
                    potential_ingredient = potential_ingredient.strip(',.:;!?')
                    
                    # Skip if already processed as a common ingredient
                    if potential_ingredient in common_ingredients:
                        continue
                    
                    # Check against canonical ingredients
                    for ingredient in canonical_ingredients:
                        if potential_ingredient == ingredient or ingredient.startswith(potential_ingredient):
                            if ingredient not in result['exclude_ingredients']:
                                result['exclude_ingredients'].append(ingredient)
                            break
    
    # Extract inclusion ingredients excluding those already handled by common_ingredients
    # Different part of query - before exclusions
    inclusion_part = query_lower
    for part in parts:
        if any(term in part for term in exclusion_terms):
            inclusion_part = inclusion_part.replace(part, '')
    
    # Tokenize the inclusion part
    tokens = word_tokenize(inclusion_part)
    
    # Generate n-grams for ingredient matching
    n_grams = []
    for n in range(1, 4):  # Check 1, 2, and 3-grams
        n_grams.extend(
            [' '.join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]
        )
    
    # Match n-grams against canonical ingredients
    for n_gram in n_grams:
        # Clean up n-gram to remove punctuation
        clean_n_gram = n_gram.strip(',.:;!?')
        
        # Skip if already processed as a common ingredient
        if clean_n_gram in common_ingredients:
            continue
        
        # Direct matching against canonical ingredients
        for ingredient in canonical_ingredients:
            if clean_n_gram == ingredient or ingredient.startswith(clean_n_gram):
                if ingredient not in result['exclude_ingredients'] and ingredient not in result['include_ingredients']:
                    result['include_ingredients'].append(ingredient)
    
    return result

def parse_user_input(text, canonical_ingredients):
    """
    Parse user input to identify intent and extract entities.
    
    Parameters:
    -----------
    text : str
        Raw user input text.
    canonical_ingredients : set
        Set of canonical ingredient names.
        
    Returns:
    --------
    tuple
        (intent_data, entities) where:
        - intent_data is a dictionary with intent information
        - entities is a dictionary with 'include' and 'exclude' lists
    """
    # Preprocess the input
    preprocessed_text = preprocess_input(text)
    
    # Parse the intent
    intent_data = parse_intent(preprocessed_text)
    
    # Extract entities
    entities = {'include': [], 'exclude': []}
    if intent_data['primary'] == 'find_recipe':
        entities = extract_entities(preprocessed_text, canonical_ingredients)
    
    logger.debug(f"Parsed input: {text}")
    logger.debug(f"Intent: {intent_data}")
    logger.debug(f"Entities: {entities}")
    
    return intent_data, entities

def preprocess_text(text):
    """
    Preprocess text by converting to lowercase, removing punctuation, and tokenizing.
    
    Parameters:
    -----------
    text : str
        Input text to preprocess
        
    Returns:
    --------
    list
        List of preprocessed tokens
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation except for hyphens in compound words (e.g., gluten-free)
    # First, replace hyphens with a special character
    text = text.replace('-', '§')
    
    # Remove punctuation
    text = ''.join([char for char in text if char not in string.punctuation])
    
    # Restore hyphens
    text = text.replace('§', '-')
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stopwords, but keep some that might be important for recipe queries
    important_stop_words = {'no', 'not', 'without', 'with', 'and', 'but', 'or', 'for', 'in'}
    filtered_tokens = [token for token in tokens if token not in stop_words or token in important_stop_words]
    
    return filtered_tokens

def identify_intent(query):
    """
    Identify the user's intent from the query.
    
    Parameters:
    -----------
    query : str
        User's query
        
    Returns:
    --------
    str
        Identified intent
    """
    # Check for recipe number pattern first (e.g., "show me recipe 7" or just "7")
    recipe_number_patterns = [
        r'(?:show|get|view|see|display)(?:\s+me)?(?:\s+recipe)?(?:\s+#)?(?:\s+number)?\s+(\d+)',
        r'^(\d+)$'
    ]
    
    for pattern in recipe_number_patterns:
        if re.search(pattern, query.lower()):
            return 'get_recipe_details'
    
    # Check each intent pattern
    for candidate_intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, query.lower()):
                return candidate_intent
    
    # If no specific intent is matched, default to find_recipe
    return 'find_recipe'

def extract_ingredients(tokens, canonical_ingredients=None):
    """
    Extract ingredient entities from tokenized query.
    
    Parameters:
    -----------
    tokens : list
        List of tokens from preprocessed query
    canonical_ingredients : set, optional
        Set of canonical ingredients for matching
        
    Returns:
    --------
    tuple
        Lists of ingredients to include and exclude
    """
    # Initialize include and exclude lists
    include_ingredients = []
    exclude_ingredients = []
    
    # Join tokens back to text for regex processing
    text = ' '.join(tokens)
    
    # Get dietary preference terms (to avoid including them as ingredients)
    dietary_terms = []
    for terms_list in DIETARY_PREFERENCE_TERMS.values():
        dietary_terms.extend(terms_list)
    
    # Define meal type and category terms (to avoid treating these as ingredients)
    # IMPORTANT: Removed common ingredients like "rice", "chicken", "pasta" from this list
    category_terms = [
        'dessert', 'desserts', 'breakfast', 'lunch', 'dinner', 'appetizer', 'appetizers',
        'snack', 'snacks', 'meal', 'meals', 'dish', 'dishes', 'recipe', 'recipes',
        'soup', 'soups', 'salad', 'salads', 'side', 'sides', 'main course', 'main',
        'drink', 'drinks', 'beverage', 'beverages', 'cocktail', 'cocktails',
        'baked goods', 'bread', 'cake', 'cakes', 'pie', 'pies', 'cookie', 'cookies',
        'grains', 'legume', 'legumes'
    ]
    
    # Common ingredients that might be confused with categories but should be treated as ingredients
    common_ingredients = [
        'chicken', 'beef', 'pork', 'fish', 'rice', 'pasta', 'noodle', 'noodles',
        'bean', 'beans', 'breads', 'potato', 'potatoes'
    ]
    
    # Find negated phrases (ingredients to exclude)
    negated_phrases = []
    for negation in NEGATION_TERMS:
        # Pattern: negation term followed by words (potential ingredients)
        pattern = r'\b' + re.escape(negation) + r'\b\s+(\w+(\s+\w+){0,3})'
        matches = re.finditer(pattern, text)
        for match in matches:
            negated_phrases.append(match.group(1))
    
    # Direct check for common ingredients first
    for token in tokens:
        if token.lower() in common_ingredients:
            if canonical_ingredients:
                match = find_closest_ingredient(token, canonical_ingredients)
                if match and match not in include_ingredients:
                    include_ingredients.append(match)
    
    # Extract n-grams (1 to 3 words) as potential ingredients
    n_grams = []
    for n in range(1, 4):  # 1-gram, 2-gram, 3-gram
        for i in range(len(tokens) - n + 1):
            n_gram = ' '.join(tokens[i:i+n])
            n_grams.append((n_gram, i, i+n-1))  # Store n-gram with start/end indices
    
    # Process negated phrases first
    negated_indices = set()
    for phrase in negated_phrases:
        phrase_tokens = phrase.split()
        phrase_len = len(phrase_tokens)
        
        # Look for matching n-grams
        for n_gram, start_idx, end_idx in n_grams:
            # Check if this n-gram is similar to the negated phrase
            if n_gram.startswith(phrase) or phrase.startswith(n_gram):
                # Mark these indices as negated
                for idx in range(start_idx, end_idx + 1):
                    negated_indices.add(idx)
                
                # Find closest ingredient match if canonical ingredients provided
                if canonical_ingredients:
                    match = find_closest_ingredient(n_gram, canonical_ingredients)
                    if match and match not in exclude_ingredients:
                        # Skip dietary preference terms and category terms
                        if not any(term in n_gram.lower() for term in dietary_terms) and \
                           not any(n_gram.lower() == term for term in category_terms):
                            exclude_ingredients.append(match)
    
    # Process remaining n-grams for inclusion
    included_indices = set()
    for n_gram, start_idx, end_idx in n_grams:
        # Skip if any token in this n-gram is in negated_indices
        if any(idx in negated_indices for idx in range(start_idx, end_idx + 1)):
            continue
        
        # Skip if any token in this n-gram is already included
        if any(idx in included_indices for idx in range(start_idx, end_idx + 1)):
            continue
        
        # Skip category terms but not common ingredients
        if any(n_gram.lower() == term for term in category_terms) and not any(n_gram.lower() == ing for ing in common_ingredients):
            continue
        
        # Find closest ingredient match if canonical ingredients provided
        if canonical_ingredients:
            match = find_closest_ingredient(n_gram, canonical_ingredients)
            if match and match not in include_ingredients:
                # Skip dietary preference terms but not categories that are also common ingredients
                if not any(term in n_gram.lower() for term in dietary_terms):
                    include_ingredients.append(match)
                    # Mark these indices as included
                    for idx in range(start_idx, end_idx + 1):
                        included_indices.add(idx)
    
    return include_ingredients, exclude_ingredients

def extract_dietary_preferences(query):
    """
    Extract dietary preferences from a query.
    
    Parameters:
    -----------
    query : str
        User's query
        
    Returns:
    --------
    list
        List of dietary preferences found in the query
    """
    query_lower = query.lower()
    preferences = []
    
    # Define normalized preference mapping
    preference_mapping = {
        'vegetarian': ['vegetarian', 'veggie', 'no meat', 'meatless', 'meat-free', 'meat free'],
        'vegan': ['vegan', 'plant-based', 'plant based', 'no animal', 'no animal products'],
        'gluten-free': ['gluten-free', 'gluten free', 'gluten_free', 'no gluten', 'without gluten', 'gluten-less'],
        'dairy-free': ['dairy-free', 'dairy free', 'no dairy', 'lactose-free', 'lactose free', 'without dairy', 'non-dairy'],
        'nut-free': ['nut-free', 'nut free', 'no nuts', 'without nuts', 'peanut-free', 'tree nut free'],
        'low-carb': ['low-carb', 'low carb', 'keto', 'ketogenic', 'keto-friendly', 'low carbohydrate', 'low-carbohydrate']
    }
    
    # Check for each dietary preference
    for normalized_pref, terms in preference_mapping.items():
        for term in terms:
            if re.search(r'\b' + re.escape(term) + r'\b', query_lower):
                if normalized_pref not in preferences:
                    preferences.append(normalized_pref)
                break  # Once we've found one term for this preference, move to the next
    
    # Log extracted preferences
    if preferences:
        logger.debug(f"Extracted dietary preferences: {preferences}")
    
    return preferences

def extract_recipe_index(query):
    """
    Extract a recipe index number from a query.
    
    Parameters:
    -----------
    query : str
        User's query
        
    Returns:
    --------
    int or None
        Recipe index if found, None otherwise
    """
    # Look for patterns like "#3", "number 3", "recipe 3", "option 3"
    patterns = [
        r'#(\d+)',
        r'number\s+(\d+)',
        r'recipe\s+(\d+)',
        r'option\s+(\d+)',
        r'(\d+)(?:st|nd|rd|th)',
        r'^(\d+)$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            try:
                index = int(match.group(1)) - 1  # Convert to 0-based index
                return index if index >= 0 else None
            except ValueError:
                continue
    
    return None

def extract_recipe_name(query, intent):
    """
    Extract a recipe name from a query.
    
    Parameters:
    -----------
    query : str
        User's query
    intent : str
        Identified intent
        
    Returns:
    --------
    str or None
        Recipe name if found, None otherwise
    """
    if intent != 'get_recipe_details':
        return None
    
    # Patterns for extracting recipe names
    recipe_patterns = [
        r'(?:details|instructions|steps|recipe|ingredients)(?:\s+for\s+|\s+of\s+|\s+to\s+)(.+?)(?:$|\?)',
        r'how\s+(?:do|can)\s+(?:i|you)\s+(?:make|prepare|cook)\s+(.+?)(?:$|\?)',
        r'tell\s+me\s+(?:more|about)\s+(.+?)(?:$|\?)',
        r'ingredients\s+(?:for|of|in)\s+(.+?)(?:$|\?)',
        r'instructions\s+for\s+(.+?)(?:$|\?)'
    ]
    
    for pattern in recipe_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    # If no specific pattern matched, try to extract the recipe name from the remaining text
    for pattern in INTENT_PATTERNS['get_recipe_details']:
        if re.search(pattern, query, re.IGNORECASE):
            # Remove the matched pattern and consider the rest as the recipe name
            remainder = re.sub(pattern, '', query, flags=re.IGNORECASE).strip()
            if remainder:
                # Clean up any leading/trailing articles or connectors
                remainder = re.sub(r'^(?:the|a|an|for|of|to)\s+', '', remainder, flags=re.IGNORECASE)
                remainder = re.sub(r'\s+(?:the|a|an|for|of|to)$', '', remainder, flags=re.IGNORECASE)
                if remainder:
                    return remainder
    
    return None

def extract_recipe_category(query):
    """
    Extract a recipe category from a query.
    
    Parameters:
    -----------
    query : str
        User's query
        
    Returns:
    --------
    str or None
        Recipe category if found, None otherwise
    """
    query_lower = query.lower()
    
    # Define common ingredients that should not be treated as categories
    common_ingredients = [
        'chicken', 'beef', 'pork', 'fish', 'rice', 'pasta', 'noodle', 'noodles',
        'bean', 'beans', 'potato', 'potatoes'
    ]
    
    # Handle "recipes without X" queries - these should be treated as exclusion queries, not category
    exclusion_phrases = ['without', 'no', 'not containing', 'excluding']
    for phrase in exclusion_phrases:
        if phrase in query_lower:
            # This is an exclusion query, not a category query
            return None
    
    # Handle special categories and qualifiers
    special_categories = {
        'quick': 'quick',
        'fast': 'quick',
        'easy': 'easy',
        'simple': 'easy', 
        'fancy': 'fancy',
        'elegant': 'fancy',
        'gourmet': 'fancy',
        'party': 'party',
        'celebration': 'party',
        'holiday': 'holiday',
        'spicy': 'spicy',
        'hot': 'spicy',
        'dinner party': 'dinner party',
        'picnic': 'picnic',
        'bbq': 'bbq',
        'barbecue': 'bbq',
        'grilled': 'grilled',
        'baked': 'baked',
        'roasted': 'roasted',
        'fried': 'fried',
        'healthy': 'healthy',
        'light': 'healthy'
    }
    
    # Check for special modifiers
    for special, category in special_categories.items():
        if re.search(r'\b' + re.escape(special) + r'\b', query_lower):
            logger.debug(f"Found special category modifier: '{special}' -> '{category}'")
            
            # Look for associated primary category (like "quick breakfast")
            for primary in ['breakfast', 'lunch', 'dinner', 'dessert', 'soup', 'salad', 'appetizer']:
                if primary in query_lower:
                    combined = f"{category} {primary}"
                    logger.debug(f"Detected combined category: '{combined}'")
                    return combined
            
            # If no primary category, return special as the category
            return category
    
    # Check for explicit ingredient phrases
    ingredient_phrases = [
        'recipe with', 'recipes with', 'using', 'made with', 'that has', 'that have',
        'containing', 'that contains', 'recipes using', 'recipe using', 'dishes with'
    ]
    
    # If query contains phrases indicating ingredients, prioritize ingredient extraction
    for phrase in ingredient_phrases:
        if phrase in query_lower:
            # Look for common ingredients after these phrases
            for ingredient in common_ingredients:
                if re.search(phrase + r'.*\b' + re.escape(ingredient) + r'\b', query_lower):
                    # This is likely an ingredient query, not a category query
                    logger.debug(f"Found '{ingredient}' as ingredient, not category")
                    return None
    
    # Define category mapping with variations
    category_mapping = {
        'dessert': ['dessert', 'desserts', 'sweet', 'cake', 'cookies', 'pie', 'pastry', 'pastries', 'baked goods'],
        'breakfast': ['breakfast', 'morning meal', 'brunch'],
        'lunch': ['lunch', 'midday meal'],
        'dinner': ['dinner', 'supper', 'evening meal'],
        'appetizer': ['appetizer', 'appetizers', 'starter', 'starters', 'hors d\'oeuvre', 'hors d\'oeuvres', 'snack', 'snacks'],
        'main': ['main course', 'main dish', 'entree', 'entrée', 'main'],
        'side': ['side', 'side dish', 'sides', 'accompaniment'],
        'soup': ['soup', 'soups', 'stew', 'stews', 'broth', 'bisque', 'chowder'],
        'salad': ['salad', 'salads'],
        'bread': ['bread', 'breads', 'roll', 'rolls', 'bun', 'buns'],
        'drink': ['drink', 'drinks', 'beverage', 'beverages', 'cocktail', 'cocktails', 'smoothie', 'smoothies', 'juice', 'juices'],
        'seafood': ['seafood', 'fish', 'shrimp', 'crab', 'lobster', 'scallop', 'scallops', 'oyster', 'oysters'],
        'meat': ['meat', 'beef', 'pork', 'lamb', 'chicken', 'turkey', 'duck', 'goose'],
        'pasta': ['pasta', 'noodle', 'spaghetti', 'lasagna', 'macaroni']
    }
    
    # Check for each category
    for category, terms in category_mapping.items():
        for term in terms:
            if re.search(r'\b' + re.escape(term) + r'\b', query_lower):
                # Check if this term should be prioritized as an ingredient
                if term in common_ingredients:
                    # Check if the context suggests this is a category, not an ingredient
                    category_indicators = [
                        'recipe', 'recipes', 'dish', 'dishes', 'meal', 'meals',
                        'breakfast', 'lunch', 'dinner', 'dessert'
                    ]
                    
                    # Look for category indicators before the term
                    for indicator in category_indicators:
                        if re.search(r'\b' + re.escape(indicator) + r'\b.*\b' + re.escape(term) + r'\b', query_lower):
                            logger.debug(f"Found '{term}' as category based on context")
                            return category
                    
                    # If no category indicators, prioritize as ingredient
                    logger.debug(f"Prioritizing '{term}' as ingredient over category")
                    return None
                
                logger.debug(f"Found recipe category: {category}")
                return category
    
    return None

def extract_common_ingredients(query):
    """
    Extract common ingredients directly from a query using pattern matching.
    This is a simpler approach that works reliably for common ingredients.
    
    Parameters:
    -----------
    query : str
        User query
        
    Returns:
    --------
    tuple
        (include_ingredients, exclude_ingredients)
    """
    query_lower = query.lower()
    
    # Define common ingredients to look for
    common_ingredients = [
        'chicken', 'beef', 'pork', 'lamb', 'turkey', 'fish', 'salmon', 'tuna',
        'rice', 'pasta', 'noodles', 'potato', 'potatoes', 'tomato', 'tomatoes',
        'onion', 'onions', 'garlic', 'carrot', 'carrots', 'broccoli', 'spinach',
        'beans', 'lentils', 'cheese', 'milk', 'cream', 'yogurt', 'egg', 'eggs',
        'bread', 'flour', 'sugar', 'salt', 'pepper', 'oil', 'butter',
        'chocolate', 'vanilla', 'cinnamon', 'apple', 'banana', 'orange', 'lemon',
        'nuts', 'peanut', 'walnut', 'almond', 'cashew', 'spicy', 'spice', 'hot'
    ]
    
    # Categories that should be treated as ingredients in some contexts
    category_as_ingredients = [
        'nuts', 'seafood', 'meat', 'spicy', 'dairy'
    ]
    
    # Standardize ingredients (singular forms)
    singular_mapping = {
        'potatoes': 'potato',
        'tomatoes': 'tomato',
        'onions': 'onion',
        'carrots': 'carrot',
        'eggs': 'egg',
        'noodles': 'noodle',
        'nuts': 'nut'
    }
    
    # Define groups of related ingredients for exclusion queries
    ingredient_groups = {
        'nut': ['nut', 'nuts', 'peanut', 'walnut', 'almond', 'cashew', 'pecan', 'hazelnut', 'pistachio'],
        'spicy': ['spicy', 'spice', 'hot', 'chili', 'pepper', 'jalapeño', 'cayenne'],
        'meat': ['meat', 'beef', 'pork', 'lamb', 'chicken', 'turkey', 'duck', 'bacon', 'sausage'],
        'dairy': ['dairy', 'milk', 'cheese', 'cream', 'yogurt', 'butter'],
        'seafood': ['seafood', 'fish', 'salmon', 'tuna', 'shrimp', 'crab', 'lobster', 'squid', 'clam', 'mussel']
    }
    
    # Define exclusion phrase patterns
    exclusion_patterns = [
        r'without\s+(\w+)',
        r'no\s+(\w+)',
        r'not\s+(\w+)',
        r"don't\s+(?:want|like)\s+(\w+)",
        r'exclude\s+(\w+)',
    ]
    
    # Find excluded ingredients
    exclude_ingredients = []
    for pattern in exclusion_patterns:
        matches = re.finditer(pattern, query_lower)
        for match in matches:
            word = match.group(1)
            # Use singular form if available
            if word in singular_mapping:
                word = singular_mapping[word]
            
            # Check if we need to expand to a group
            for group_name, group_items in ingredient_groups.items():
                if word in group_items:
                    for group_item in group_items:
                        if group_item not in exclude_ingredients:
                            exclude_ingredients.append(group_item)
                    break
            # If not part of a group, just add the word if it's a common ingredient
            if word in common_ingredients and word not in ingredient_groups.get(word, []):
                exclude_ingredients.append(word)
    
    # Find included ingredients 
    include_ingredients = []
    
    # Check for special negation-only queries where the category becomes ingredients to exclude
    exclusion_keywords = ['without', 'no', 'not', "don't", 'exclude']
    if any(keyword in query_lower for keyword in exclusion_keywords):
        for category in category_as_ingredients:
            if category in query_lower and category not in exclude_ingredients:
                # If the category is mentioned in an exclusion context, add it and its group to exclude
                if category in ingredient_groups:
                    for group_item in ingredient_groups[category]:
                        if group_item not in exclude_ingredients:
                            exclude_ingredients.append(group_item)
    
    # Common inclusion phrases
    inclusion_phrases = [
        'with', 'using', 'made with', 'that has', 'contains', 'containing',
        'recipe for', 'recipes with', 'i have', 'using', 'and', 'or'
    ]
    
    # If the query contains inclusion phrases, extract ingredients after them
    for phrase in inclusion_phrases:
        if phrase in query_lower:
            parts = query_lower.split(phrase)
            if len(parts) > 1:
                for ingredient in common_ingredients:
                    # Only consider the part after the phrase
                    if ingredient in parts[1]:
                        # Use singular form if available
                        if ingredient in singular_mapping:
                            ingredient = singular_mapping[ingredient]
                        
                        # Don't include if it's excluded or already included
                        if ingredient not in exclude_ingredients and ingredient not in include_ingredients:
                            include_ingredients.append(ingredient)
    
    # Also check for ingredients without specific phrases
    for ingredient in common_ingredients:
        if ingredient in query_lower:
            # Use singular form if available
            if ingredient in singular_mapping:
                ingredient = singular_mapping[ingredient]
                
            # Don't include if it's excluded or already included
            if ingredient not in exclude_ingredients and ingredient not in include_ingredients:
                # Verify it's not part of another word
                if re.search(r'\b' + re.escape(ingredient) + r'\b', query_lower):
                    include_ingredients.append(ingredient)
    
    # Check for full negation of the query
    for phrase in ['without', 'no', 'not', "don't want", "don't like"]:
        if phrase in query_lower and include_ingredients:
            # If the query is purely about exclusion, move all includes to excludes
            if len(include_ingredients) <= 1 and any(ex_kw in query_lower for ex_kw in ['without', 'no', 'not', "don't"]):
                exclude_ingredients.extend([ing for ing in include_ingredients if ing not in exclude_ingredients])
                include_ingredients = []
                break
    
    # Special case for "recipes without X" queries
    if query_lower.startswith('find recipes without') or query_lower.startswith('recipes without') or 'recipe without' in query_lower:
        # Make sure we don't have any includes for pure exclusion queries
        include_ingredients = []
        
        # Ensure we have at least some excluded ingredients
        if not exclude_ingredients:
            # Try to find common categories that might be treated as ingredients
            for category in ['nuts', 'meat', 'dairy', 'seafood', 'spicy']:
                if category in query_lower and category not in exclude_ingredients:
                    if category in ingredient_groups:
                        # Add all items from the ingredient group
                        for group_item in ingredient_groups[category]:
                            if group_item not in exclude_ingredients:
                                exclude_ingredients.append(group_item)
    
    return include_ingredients, exclude_ingredients

def parse_query(query, canonical_ingredients=None):
    """
    Parse a user query to extract intent and entities.
    
    Parameters:
    -----------
    query : str
        User's query
    canonical_ingredients : set, optional
        Set of canonical ingredients for matching
        
    Returns:
    --------
    dict
        Dictionary containing:
        - intent: Identified user intent
        - include_ingredients: List of ingredients to include
        - exclude_ingredients: List of ingredients to exclude
        - dietary_preferences: List of dietary preferences
        - recipe_index: Recipe index if specified, None otherwise
        - recipe_name: Recipe name if specified, None otherwise
        - recipe_category: Category of recipes to search for
    """
    try:
        # Basic validation
        if not query or not isinstance(query, str):
            logger.warning(f"Invalid query type or empty query: {query}")
            return {
                'intent': 'unknown',
                'include_ingredients': [],
                'exclude_ingredients': [],
                'dietary_preferences': [],
                'recipe_index': None,
                'recipe_name': None,
                'recipe_category': None
            }
        
        # Identify intent
        intent = identify_intent(query)
        
        # Extract recipe index (for get_recipe_details intent)
        recipe_index = extract_recipe_index(query)
        
        # Extract recipe name (for get_recipe_details intent)
        recipe_name = extract_recipe_name(query, intent)
        
        # For simple number-only queries, handle as recipe selection
        if re.match(r'^\s*\d+\s*$', query) and recipe_index is not None:
            return {
                'intent': 'get_recipe_details',
                'include_ingredients': [],
                'exclude_ingredients': [],
                'dietary_preferences': [],
                'recipe_index': recipe_index,
                'recipe_name': None,
                'recipe_category': None
            }
        
        # Extract dietary preferences
        dietary_preferences = extract_dietary_preferences(query)
        
        # Extract recipe category - do this before ingredients
        recipe_category = extract_recipe_category(query)
        
        # Use simple pattern matching for common ingredients
        include_ingredients, exclude_ingredients = extract_common_ingredients(query)
        
        # Only use the more complex tokenization if we didn't find enough ingredients
        if not include_ingredients and not exclude_ingredients and canonical_ingredients:
            # Preprocess query
            tokens = preprocess_text(query)
            # Extract ingredients using more sophisticated method
            include_from_tokens, exclude_from_tokens = extract_ingredients(tokens, canonical_ingredients)
            include_ingredients.extend(include_from_tokens)
            exclude_ingredients.extend(exclude_from_tokens)
        
        # Remove duplicates
        include_ingredients = list(dict.fromkeys(include_ingredients))
        exclude_ingredients = list(dict.fromkeys(exclude_ingredients))
        
        # Remove 'dessert' from include_ingredients if it's clearly a category
        if 'dessert' in include_ingredients and any(term in query.lower() for term in ['find dessert', 'dessert recipes', 'sweet recipes']):
            include_ingredients.remove('dessert')
        
        # Log the parse results for debugging
        logger.debug(f"Parsed query: Intent={intent}, Include={include_ingredients}, "
                     f"Exclude={exclude_ingredients}, Preferences={dietary_preferences}, "
                     f"Category={recipe_category}, Index={recipe_index}, Name={recipe_name}")
        
        return {
            'intent': intent,
            'include_ingredients': include_ingredients,
            'exclude_ingredients': exclude_ingredients,
            'dietary_preferences': dietary_preferences,
            'recipe_index': recipe_index,
            'recipe_name': recipe_name,
            'recipe_category': recipe_category
        }
    except Exception as e:
        logger.error(f"Error parsing query: {e}")
        return {
            'intent': 'unknown',
            'include_ingredients': [],
            'exclude_ingredients': [],
            'dietary_preferences': [],
            'recipe_index': None,
            'recipe_name': None,
            'recipe_category': None
        }

if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Test the parser with some example queries
    test_queries = [
        "Find recipes with chicken and broccoli",
        "I want a vegetarian pasta dish",
        "How do I make chocolate chip cookies?",
        "Show me gluten-free dinner ideas",
        "I want to make a cake without eggs",
        "What can I cook with potatoes but no meat?",
        "Help",
        "Quit",
        "Show me recipe number 3",
        "Give me the details for Spaghetti Carbonara",
        "Find me vegan recipes with no nuts",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = parse_query(query)
        print(f"Intent: {result['intent']}")
        print(f"Include ingredients: {result['include_ingredients']}")
        print(f"Exclude ingredients: {result['exclude_ingredients']}")
        print(f"Dietary preferences: {result['dietary_preferences']}")
        print(f"Recipe index: {result['recipe_index']}")
        print(f"Recipe name: {result['recipe_name']}")
        print(f"Recipe category: {result['recipe_category']}") 