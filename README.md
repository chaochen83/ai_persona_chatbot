# Persona Chat Interface

A Streamlit application that allows users to chat with different AI personas. The interface includes a user selection sidebar and a chat interface that adapts its responses based on the selected persona.

## Features

- User selection with avatars and names
- Real-time chat interface
- Different AI personas with unique response styles
- Persistent chat history
- OpenAI GPT-4.1 integration via LangChain
- PostgreSQL database for user management

## Setup

1. Clone this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root and add your API keys and database configuration:
   ```
   OPENAI_API_KEY=your_api_key_here
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=your_db_host
   DB_NAME=persona_users
   DB_PORT=5432
   ```

4. Set up the PostgreSQL database:
   ```bash
   # Create the database
   psql -U your_db_user
   CREATE DATABASE persona_users;
   \q
   
   # Initialize the database with initial user data
   python init_db.py
   ```

## Running the Application

To start the application, run:
```bash
streamlit run app.py
```

The application will open in your default web browser.

## Usage

1. Select a persona from the sidebar dropdown
2. Type your message in the chat input
3. The AI will respond according to the selected persona's characteristics

## Available Personas

- Trump (👩‍💼): 45th & 47th President of the United States
- Vitalik (👨‍🔬): Creator of Ethereum
- Suji (👨‍🎨): Founder of @realmasknetwork
- Yi He (👩‍💼): Co-Founder & Chief Customer Service Officer @Binance
- CZ (👨‍🎨): Co-founder and former CEO of Binance
