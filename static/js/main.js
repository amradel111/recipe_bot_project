// DOM Elements
const messagesContainer = document.getElementById('messages');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const recipeContainer = document.getElementById('recipe-container');
const recipeContent = document.getElementById('recipe-content');
const closeRecipeButton = document.getElementById('close-recipe');
const recipeTemplate = document.getElementById('recipe-template');

// Session ID for the current user
let sessionId = generateSessionId();

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    userInput.focus();
    
    // Initially hide the recipe container on mobile
    if (window.innerWidth <= 1024) {
        recipeContainer.style.display = 'none';
    }
});

sendButton.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

closeRecipeButton.addEventListener('click', () => {
    if (window.innerWidth <= 1024) {
        recipeContainer.style.display = 'none';
        document.querySelector('.chat-container').style.display = 'flex';
    }
});

// Functions
function generateSessionId() {
    return 'session_' + Math.random().toString(36).substring(2, 15);
}

function sendMessage() {
    const message = userInput.value.trim();
    if (message === '') return;
    
    // Add user message to the chat
    addMessageToChat(message, 'user');
    
    // Clear input
    userInput.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    // Send message to the server
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message,
            session_id: sessionId
        }),
    })
    .then(response => response.json())
    .then(data => {
        // Remove typing indicator
        hideTypingIndicator();
        
        // Add bot response to the chat
        addMessageToChat(data.response, 'bot');
        
        // Update session ID
        sessionId = data.session_id;
        
        // Parse response for recipe numbers
        checkForRecipeNumbers(data.response);
    })
    .catch((error) => {
        // Remove typing indicator
        hideTypingIndicator();
        
        console.error('Error:', error);
        addMessageToChat('Sorry, I encountered an error. Please try again.', 'bot');
    });
}

function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.classList.add('typing-indicator');
    typingDiv.id = 'typing-indicator';
    
    // Create the three dots
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('span');
        typingDiv.appendChild(dot);
    }
    
    messagesContainer.appendChild(typingDiv);
    
    // Scroll to the bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

function addMessageToChat(message, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', `${sender}-message`);
    
    const avatar = document.createElement('div');
    avatar.classList.add('message-avatar');
    
    // Set avatar icon based on sender
    const avatarIcon = document.createElement('i');
    avatarIcon.classList.add('fas', sender === 'user' ? 'fa-user' : 'fa-robot');
    avatar.appendChild(avatarIcon);
    
    const content = document.createElement('div');
    content.classList.add('message-content');
    
    // Process message content
    if (typeof message === 'string') {
        // Handle recipe lists differently
        if (message.includes('Found') && message.includes('recipes:')) {
            // Split message into parts
            const parts = message.split(/(?=^\d+\.)/m);
            
            // Add the header text
            if (parts.length > 0 && !parts[0].match(/^\d+\./)) {
                const header = document.createElement('p');
                header.textContent = parts[0].trim();
                content.appendChild(header);
                parts.shift(); // Remove the header from parts
            }
            
            // Create a list for the recipes
            const recipeList = document.createElement('ol');
            recipeList.classList.add('recipe-list');
            
            // Add each recipe as a list item
            parts.forEach(part => {
                if (part.trim() !== '') {
                    const listItem = document.createElement('li');
                    listItem.textContent = part.trim().replace(/^\d+\./, '').trim();
                    
                    // Extract recipe index
                    const match = part.match(/^(\d+)\./);
                    if (match) {
                        const recipeIndex = parseInt(match[1]) - 1;
                        listItem.style.cursor = 'pointer';
                        listItem.style.color = 'var(--primary-color)';
                        listItem.addEventListener('click', () => {
                            fetchRecipeDetails(recipeIndex);
                        });
                    }
                    
                    recipeList.appendChild(listItem);
                }
            });
            
            content.appendChild(recipeList);
        } else {
            // Process normal message with enhanced formatting
            const processedMessage = message
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold text
                .replace(/\*(.*?)\*/g, '<em>$1</em>') // Italic text
                .replace(/`(.*?)`/g, '<code>$1</code>'); // Code
            
            // Split by newlines and create paragraph for each
            const lines = processedMessage.split('\n');
            
            let inList = false;
            let listElem = null;
            
            lines.forEach((line) => {
                const trimmed = line.trim();
                
                if (trimmed === '') {
                    // Empty line
                    if (inList) {
                        content.appendChild(listElem);
                        inList = false;
                        listElem = null;
                    }
                    return;
                }
                
                // Check if line is a bullet list item
                if (trimmed.startsWith('•') || trimmed.startsWith('-')) {
                    if (!inList || listElem.tagName !== 'UL') {
                        if (inList) {
                            content.appendChild(listElem);
                        }
                        listElem = document.createElement('ul');
                        inList = true;
                    }
                    
                    const listItem = document.createElement('li');
                    listItem.innerHTML = trimmed.replace(/^[•-]\s*/, '');
                    listElem.appendChild(listItem);
                }
                // Check if line is a numbered list item
                else if (trimmed.match(/^\d+\./)) {
                    if (!inList || listElem.tagName !== 'OL') {
                        if (inList) {
                            content.appendChild(listElem);
                        }
                        listElem = document.createElement('ol');
                        inList = true;
                    }
                    
                    const listItem = document.createElement('li');
                    listItem.innerHTML = trimmed.replace(/^\d+\.\s*/, '');
                    listElem.appendChild(listItem);
                }
                // Normal paragraph
                else {
                    if (inList) {
                        content.appendChild(listElem);
                        inList = false;
                        listElem = null;
                    }
                    
                    const paragraph = document.createElement('p');
                    paragraph.innerHTML = trimmed;
                    content.appendChild(paragraph);
                }
            });
            
            // Add any remaining list
            if (inList) {
                content.appendChild(listElem);
            }
        }
    }
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    messagesContainer.appendChild(messageDiv);
    
    // Add animation for smoother appearance
    setTimeout(() => {
        messageDiv.style.opacity = '1';
    }, 10);
    
    // Scroll to the bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function checkForRecipeNumbers(response) {
    // Look for recipe list
    if (response.includes('Found') && response.includes('recipes:')) {
        // Make recipe list items clickable
        setTimeout(() => {
            const lastMessage = messagesContainer.lastElementChild;
            if (lastMessage) {
                const listItems = lastMessage.querySelectorAll('.message-content p');
                
                listItems.forEach(item => {
                    const text = item.textContent;
                    if (text.match(/^\d+\./)) {
                        const recipeIndex = parseInt(text.split('.')[0]) - 1;
                        item.style.cursor = 'pointer';
                        item.style.color = 'var(--primary-color)';
                        item.addEventListener('click', () => {
                            fetchRecipeDetails(recipeIndex);
                        });
                    }
                });
            }
        }, 100);
    }
}

function fetchRecipeDetails(recipeIndex) {
    fetch(`/recipe/${recipeIndex}?session_id=${sessionId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error:', data.error);
                return;
            }
            
            displayRecipeDetails(data.recipe);
            
            // Show recipe container on mobile
            if (window.innerWidth <= 1024) {
                document.querySelector('.chat-container').style.display = 'none';
                recipeContainer.style.display = 'flex';
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function displayRecipeDetails(recipe) {
    // Clear existing content
    recipeContent.innerHTML = '';
    
    // Clone the template
    const recipeCard = recipeTemplate.content.cloneNode(true);
    
    // Set recipe details
    recipeCard.querySelector('.recipe-title').textContent = recipe.name;
    
    // Set time if available
    const timeValue = recipeCard.querySelector('.time-value');
    if (recipe.cook_time) {
        timeValue.textContent = recipe.cook_time;
    } else if (recipe.total_time) {
        timeValue.textContent = recipe.total_time;
    } else {
        timeValue.parentElement.style.display = 'none';
    }
    
    // Set rating if available
    const ratingValue = recipeCard.querySelector('.rating-value');
    if (recipe.rating) {
        ratingValue.textContent = recipe.rating;
    } else {
        ratingValue.parentElement.style.display = 'none';
    }
    
    // Set ingredients
    const ingredientsList = recipeCard.querySelector('.ingredients-list');
    if (recipe.raw_ingredients && recipe.raw_ingredients.length > 0) {
        recipe.raw_ingredients.forEach(ingredient => {
            const li = document.createElement('li');
            li.textContent = ingredient;
            ingredientsList.appendChild(li);
        });
    } else if (recipe.ingredients && recipe.ingredients.length > 0) {
        recipe.ingredients.forEach(ingredient => {
            const li = document.createElement('li');
            li.textContent = ingredient;
            ingredientsList.appendChild(li);
        });
    }
    
    // Set instructions
    const instructionsList = recipeCard.querySelector('.instructions-list');
    if (recipe.instructions) {
        // Check if instructions is a string or array
        let instructionsArray = recipe.instructions;
        if (typeof recipe.instructions === 'string') {
            // Split by newlines or numbers
            instructionsArray = recipe.instructions.split(/\n|\d+\./g).filter(item => item.trim() !== '');
        }
        
        instructionsArray.forEach(instruction => {
            const li = document.createElement('li');
            li.textContent = instruction.trim();
            instructionsList.appendChild(li);
        });
    }
    
    // Set source URL if available
    const sourceLink = recipeCard.querySelector('.recipe-source');
    if (recipe.url) {
        sourceLink.href = recipe.url;
    } else {
        sourceLink.style.display = 'none';
    }
    
    // Add to the recipe content
    recipeContent.appendChild(recipeCard);
}

// Handle window resize for responsive layout
window.addEventListener('resize', () => {
    if (window.innerWidth > 1024) {
        recipeContainer.style.display = 'flex';
        document.querySelector('.chat-container').style.display = 'flex';
    }
}); 