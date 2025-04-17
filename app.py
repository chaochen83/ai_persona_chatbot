import streamlit as st
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.schema import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()

# Initialize session state for selected user
if 'selected_user' not in st.session_state:
    st.session_state.selected_user = None

# Define users with their personas and Chroma paths
users = [
    {
        "name": "Trump",
        "avatar": "👩‍💼",
        "persona": "You are Donald Trump, 45th & 47th President of the United States of America. You are known for your brash personality, and your use of social media to communicate with the public.",
        "chroma_path": "/tmp/chroma/twitter/trump"
    },
    {
        "name": "Vitalik",
        "avatar": "👨‍🔬",
        "persona": "You are Vitalik Buterin, the creator of Ethereum. You are known for your work in the blockchain space, and your support for the freedom of speech.",
        "chroma_path": "/tmp/chroma/twitter/vitalik"
    },
    {
        "name": "Suji",
        "avatar": "👨‍🎨",
        "persona": "You are Suji, founder of @realmasknetwork / @thefireflyapp $mask🐦 Maintain some fediverse instances sujiyan.eth",
        "chroma_path": "/tmp/chroma/twitter/suji"
    }
]



# Initialize the chat model
def get_chat_model():
    return ChatOpenAI(
        model_name="gpt-4.1",
        temperature=0.7,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

PROMPT_TEMPLATE = """
Provide a direct response mimicking my style based on the timeline content:
{context} 

and include only the response itself without any additional text.


---

Answer the question based on the above context:  {question}
"""


def generate_prompt(user_message):
    chroma_path = users[st.session_state.selected_user]['chroma_path']
    print(f"chroma_path: {chroma_path}")

    # Prepare the DB.
    embedding_function = OpenAIEmbeddings()
    db = Chroma(persist_directory=chroma_path, embedding_function=embedding_function)

    # Search the DB.
    results = db.similarity_search_with_relevance_scores(user_message, k=3)
    print(f"Results: {results}")
    if len(results) == 0 or results[0][1] < 0.7:
        print(f"Unable to find matching results.")

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=user_message)
    # print(f"prompt: {prompt}")
    return prompt

# Initialize chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Sidebar for user selection
with st.sidebar:
    st.title("Select User")
    
    # Create a dropdown with user avatars and names
    user_options = [f"{user['avatar']} {user['name']}" for user in users]
    selected_user_display = st.selectbox(
        "Choose a persona:",
        user_options,
        index=0 if st.session_state.selected_user is None else user_options.index(f"{users[st.session_state.selected_user]['avatar']} {users[st.session_state.selected_user]['name']}")
    )
    
    # Update selected user
    selected_user_index = user_options.index(selected_user_display)
    st.session_state.selected_user = selected_user_index

# Main chat interface
st.title("AI Chat Interface")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to ask?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Get selected user's persona
    selected_user = users[st.session_state.selected_user]
    
    # Initialize chat model
    chat = get_chat_model()

    prompt_with_RAG = generate_prompt(prompt)
    # print(f"prompt_with_RAG: {prompt_with_RAG}")

    # Create system message with persona
    system_message = SystemMessage(content=selected_user["persona"])
    human_message = HumanMessage(content=prompt_with_RAG)
    
    print(f"system_message: {system_message}\n\n")
    print(f"human_message: {human_message}\n\n")
    
    # Get AI response
    response = chat.invoke([system_message, human_message])
    
    # Add AI response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response.content})
    
    # Display AI response
    with st.chat_message("assistant"):
        st.write(response.content) 