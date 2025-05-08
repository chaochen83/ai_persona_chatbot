import streamlit as st
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.schema import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain.prompts import ChatPromptTemplate
import time
from models import User, get_pgsql_db, STATUS_FULLY_IMPORTED, get_users, insert_new_user_to_pgsql_db
from sqlalchemy.orm import Session
import requests
import json
from langchain.schema import Document
import shutil

def gate_by_invite_code():
    # 1. Define valid invite codes
    VALID_CODES = {"mask", "firefly"}
    # 2. Session state: Check if user is authenticated
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    # 3. Invite code form
    if not st.session_state.authenticated:
        st.title("Enter Invite Code")
        code_input = st.text_input("Invite Code", type="password")
        if st.button("Submit"):
            if code_input in VALID_CODES:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid invite code. Try again.")
        st.stop()  # 🚫 Stop here if not authenticated


gate_by_invite_code()


# Load environment variables
load_dotenv()

# Initialize session state for selected user
if 'selected_user' not in st.session_state:
    st.session_state.selected_user = None
if 'import_status' not in st.session_state:
    st.session_state.import_status = ""

# Initialize the chat model
def get_chat_model():
    return ChatOpenAI(
        model_name="gpt-4.1",
        temperature=0.7,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

# PROMPT_TEMPLATE = """
# Provide a direct response mimicking my style based on the timeline content:\nEthereum\n\n\n\nNFT\n\n\n\nOpensea \n\nand include only the response itself without any additional text.\n\n\n\n\nAnswer the question based on the above context:  web3?\n
# """
PROMPT_TEMPLATE = """
Provide a direct response mimicking my style based on the timeline content:
{context} 

and include only the response itself without any additional text.


---

Answer the question based on the above context:  {question}
"""

FOLLOW_UP_PROMPT = """
What else should I ask about this: 
{context}

Generate 1 relevant follow-up question that would help the user learn more about this topic. 
Format each question that starts with "Would you like to know more about...".
Make the questions specific and related to the context.
"""


def generate_prompt(user_message, selected_user):
    chroma_path = selected_user.chroma_path
    print(f"chroma_path: {chroma_path}")

    # Prepare the VectorDB.
    embedding_function = OpenAIEmbeddings()
    vector_db = Chroma(persist_directory=chroma_path, embedding_function=embedding_function)

    # Search the VectorDB.
    results = vector_db.similarity_search_with_relevance_scores(user_message, k=20)
    print(f"Results: {results}")
    if len(results) == 0 or results[0][1] < 0.7:
        print(f"Unable to find matching results.")

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=user_message)
    # print(f"prompt: {prompt}")
    return prompt, results, context_text

# Initialize chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Get database session
pgsql_db = next(get_pgsql_db())
# users = get_users(pgsql_db)

# Sidebar for user selection and import
with st.sidebar:
    st.title("User Management")
    
    # Search and import section
    st.subheader("Import New User")
    twitter_handle = st.text_input("Enter Twitter handle (without @)", key="twitter_handle")
    if st.button("Import User"):
        if twitter_handle:
            # Clear any existing progress bars and text areas
            st.empty()  # Clear any existing content
            st.empty()  # Clear any existing content
            st.empty()  # Clear any existing content
            
            # Create progress bars with labels
            st.write("Twitter Import Progress:")
            progress_bar_tw = st.progress(0)
            st.write("Farcaster Import Progress:")
            progress_bar_fc = st.progress(0)
            status_text = st.empty()
            
            # Try to insert new user
            result = insert_new_user_to_pgsql_db(twitter_handle, status_text, progress_bar_tw, progress_bar_fc)
            
            if result.startswith("User successfully added"):
                # Update final status
                status_text.text(f"Successfully imported data for @{twitter_handle}!")
                progress_bar_fc.progress(100)
                
                # Store final status
                st.session_state.import_status = result
            else:
                # Show error message
                status_text.text(result)
                st.session_state.import_status = result
        else:
            st.session_state.import_status = "Please enter a Twitter handle"
    
    # Display import status
    if st.session_state.import_status:
        st.text_area("Import Status", value=st.session_state.import_status, height=100, disabled=True)
    
    st.divider()
    
    # User selection
    st.subheader("Select User")
    users = get_users(pgsql_db)
    if not users:
        st.warning("No fully imported users available. Please import a user first.")
    else:
        # Create a two-column layout
        col1, col2 = st.columns([3, 1])

        with col1:
            # Simple dropdown with just names
            user_names = [user.name for user in users]
            selected_name = st.selectbox("Choose a persona:", user_names)
            
            # Update selected user index
            st.session_state.selected_user = user_names.index(selected_name)

        with col2:
            # Add some vertical spacing and show avatar
            st.markdown("<div style='margin-top: 1.6rem;'>", unsafe_allow_html=True)
            if st.session_state.selected_user is not None:
                st.image(users[st.session_state.selected_user].avatar, width=40)
            st.markdown("</div>", unsafe_allow_html=True)


# Main chat interface
st.title("AI Chat Interface")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "follow_ups" in message:
            # st.markdown("**Follow-up Question:**")
            st.write(message["follow_ups"])        
        if "references" in message:
            st.markdown("**References:**")
            for ref in message["references"]:
                st.markdown(f"- {ref}")


# Chat input
if question := st.chat_input("What would you like to ask?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": question})
    
    # Display user message
    with st.chat_message("user"):
        st.write(question)
    
    # Get selected user's persona
    selected_user = users[st.session_state.selected_user]
    
    # Initialize chat model
    chat = get_chat_model()

    answer_with_RAG, search_results, context_text = generate_prompt(question, selected_user)
    # print(f"prompt_with_RAG: {prompt_with_RAG}")

    # Create system message with persona
    system_message = SystemMessage(content=selected_user.persona)
    human_message = HumanMessage(content=answer_with_RAG)
    
    print(f"system_message: {system_message}\n\n")
    print(f"human_message: {human_message}\n\n")
    
    # Get AI response
    response = chat.invoke([system_message, human_message])
    print(f"Response: {response.content}\n")
    
    # Generate follow-up questions
    follow_up_prompt = FOLLOW_UP_PROMPT.format(context=question)
    follow_up_response = chat.invoke([SystemMessage(content="You are a helpful assistant that generates relevant follow-up questions."), 
                                    HumanMessage(content=follow_up_prompt)])
    # print(f"follow_up_prompt: {follow_up_prompt}\n\n")
    # print(f"follow_up_response: {follow_up_response}\n\n")
    follow_up_questions = follow_up_response.content
    print(f"Follow ups: {follow_up_questions}\n\n")
    
    # Extract references from search results
    references = []
    for doc, score in search_results:
        if hasattr(doc, 'metadata') and 'source' in doc.metadata:
            if 'type' not in doc.metadata or doc.metadata['type'] == 'TW':  # Only posts from Twitter has open ref. Old import don't have 'type':
                ref = f"{selected_user.twitter_post_url_prefix}/status/{doc.metadata['source']}"
                references.append(ref)
            elif  doc.metadata['type'] == 'FC': # Farcaster not open
                ref = f"Farcaster: {doc.metadata['source']}"
                references.append(ref)
        else:
            references.append("Source document")
    
    # Add AI response to chat history with references and follow-up questions
    st.session_state.messages.append({
        "role": "assistant", 
        "content": response.content,
        "references": references,
        "follow_ups": follow_up_questions
    })

    # Display AI response with references and follow-up questions
    with st.chat_message("assistant"):
        st.write(response.content)
        # st.markdown("**Follow-up Question:**")
        st.write(follow_up_questions)
        st.markdown("**References:**")
        for ref in references:
            st.markdown(f"- {ref}")