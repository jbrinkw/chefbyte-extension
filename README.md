# ChefByte 🍳

ChefByte is an AI-powered kitchen assistant that helps you manage your pantry inventory and provides personalized recipe suggestions based on your taste profile. The app leverages OpenAI's API to understand your requests and seamlessly update your inventory, making meal planning and pantry management easier than ever.

## Features

- **Inventory Management**: Add, remove, or update items in your pantry inventory with simple commands.
- **Taste Profile**: Store and update your taste profile to get recipe suggestions that match your preferences.
- **Recipe Suggestions**: Receive personalized recipe recommendations based on the ingredients you have on hand and your taste preferences.
- **Interactive Chat**: Use the chat interface to interact with the AI assistant and manage your kitchen effortlessly.

## Installation

To run ChefByte locally, follow these steps:

1. **Obtain Your OpenAI API Key**: Replace `'openai_api_key'` in the code with your OpenAI API key.

2. **Initial Setup**: Refer to `cmds.txt` for the initial setup commands, including how to install Docker, set up the PostgreSQL database, and configure the Python environment.

3. **Restart After Shutdown**: `cmds.txt` also includes the commands needed to restart the application after a shutdown.

## Usage

### Inventory Management

Use the chat interface to add or remove items from your inventory. For example:
- "Add 2 apples"
- "Remove 1 milk"

### Taste Profile

Update your taste profile by clicking the "Update Taste Profile" button in the sidebar. Enter your preferences, and ChefByte will use this information to tailor recipe suggestions.

### Recipe Suggestions

Ask the AI assistant for recipe ideas, and it will provide 2-3 options that align with your current inventory and taste profile.

## Database Schema

ChefByte uses a PostgreSQL database with the following tables:

- **inventory**: Stores items in your pantry with fields for item name, quantity, and expiration date.
- **taste_profile**: Stores the user's taste profile as a text field.
