# Recipe Bot Web Interface

This document explains how to set up and run the web interface for the Recipe Bot project.

## Overview

The Recipe Bot Web Interface provides a modern, user-friendly way to interact with the Recipe Bot through a web browser. It features:

- Clean, attractive UI with a green and purple color scheme
- Chat interface for natural interaction
- Detailed recipe display
- Responsive design that works on desktop and mobile devices

## Setup

### Prerequisites

- Python 3.8 or higher
- All dependencies listed in requirements.txt

### Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Make sure NLTK data is downloaded:

```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
```

## Running the Web Interface

1. Start the Flask web server:

```bash
python app.py
```

2. Open your web browser and navigate to:

```
http://127.0.0.1:5000/
```

3. The Recipe Bot web interface should now be loaded and ready to use.

## Usage

- Type your query in the input box at the bottom of the chat container
- Press Enter or click the send button to submit your query
- The Recipe Bot will process your query and display the results
- If recipes are found, click on a recipe to view its details in the right panel
- On mobile devices, the recipe details will replace the chat interface (use the close button to return to chat)

## Features

- **Chat Interface**: Natural language conversation with the Recipe Bot
- **Recipe Search**: Find recipes based on ingredients, dietary preferences, and categories
- **Recipe Details**: View detailed recipe information including ingredients, instructions, and more
- **Responsive Design**: Works on desktop and mobile devices
- **Modern UI**: Clean, attractive design with smooth animations

## Customization

You can customize the appearance of the web interface by modifying the CSS file at `static/css/styles.css`. The current design uses:

- Green (`#4a9375`) as the primary color
- Purple (`#8e44ad`) as the secondary color
- Poppins font family

To change these, modify the CSS variables in the `:root` selector.

## Troubleshooting

If you encounter any issues:

1. Check the logs in `recipe_bot.log`
2. Ensure all dependencies are installed
3. Make sure the Flask server is running
4. Check browser console for JavaScript errors

## License

This project is licensed under the MIT License - see the LICENSE file for details. 