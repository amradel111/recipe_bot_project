# Recipe Bot

A conversational chatbot that helps users find recipes based on ingredients they have.

## Features

- Natural language processing to understand user requests
- Ingredient extraction from user input
- Recipe matching based on available ingredients
- Detailed recipe information
- Modern web interface with responsive design

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd recipe_bot_project
   ```

2. Set up a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Download NLTK data:
   ```python
   import nltk
   nltk.download('punkt')
   nltk.download('wordnet')
   nltk.download('stopwords')
   ```

## Dataset

The bot requires a recipe dataset in CSV or JSON format with at least the following columns:
- `name`: Recipe name
- `ingredients`: List of ingredients (comma-separated string)

Optional columns:
- `instructions`: Cooking instructions
- `cuisine`: Type of cuisine

A sample dataset is provided in `data/recipes.csv`.

## Configuration

Edit the `config.py` file to customize:
- Dataset path and column names
- NLP settings
- Recipe matching threshold

## Usage

### Command Line Interface

1. Run the bot:
   ```
   python main.py
   ```

2. Interact with the bot by typing ingredients you have:
   ```
   What can I make with eggs, cheese, and milk?
   ```

3. Type `help` for assistance or `quit` to exit.

### Web Interface

1. Run the Flask web server:
   ```
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

3. Interact with the bot through the web interface.

See `WEB_INTERFACE.md` for more details about the web interface.

## Module Structure

- `config.py`: Configuration settings
- `data_loader.py`: Data loading functions
- `data_cleaner.py`: Data cleaning and ingredient extraction
- `nlu_parser.py`: Natural language understanding
- `recipe_matcher.py`: Recipe matching logic
- `response_generator.py`: Response generation
- `main.py`: Main chat loop
- `app.py`: Flask web application
- `templates/`: HTML templates for web interface
- `static/`: CSS, JavaScript, and images for web interface

## License

MIT 