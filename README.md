# Persona Chat Interface

A Streamlit application that allows users to chat with different AI personas. The interface includes a user selection sidebar and a chat interface that adapts its responses based on the selected persona.

## Features

- User selection with avatars and names
- Real-time chat interface
- Different AI personas with unique response styles
- Persistent chat history
- OpenAI GPT-3.5 integration via LangChain

## Setup

1. Clone this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
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

- Alice (👩‍💼): Professional business consultant
- Bob (👨‍🔬): Scientific researcher
- Charlie (👨‍🎨): Creative artist 