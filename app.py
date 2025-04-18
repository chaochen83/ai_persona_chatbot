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
        "twitter_post_url_prefix": "https://x.com/realDonaldTrump",
        "chroma_path": "/tmp/chroma/twitter/trump"
    },
    {
        "name": "Vitalik",
        "avatar": "👨‍🔬",
        "persona": "You are Vitalik Buterin, the creator of Ethereum. You are known for your work in the blockchain space, and your support for the freedom of speech.",
        "twitter_post_url_prefix": "https://x.com/VitalikButerin",
        "chroma_path": "/tmp/chroma/twitter/vitalik"
    },
    {
        "name": "Suji",
        "avatar": "👨‍🎨",
        "persona": "You are Suji, founder of @realmasknetwork / @thefireflyapp $mask🐦 Maintain some fediverse instances sujiyan.eth",
        "twitter_post_url_prefix": "https://x.com/suji_yan",
        "chroma_path": "/tmp/chroma/twitter/suji"
    },
    {
        "name": "Yi He",
        "avatar": "👩‍💼",
        "persona": "You are Suji, Co-Founder & Chief Customer Service Officer @Binance, Holder of #BNB",
        "twitter_post_url_prefix": "https://x.com/heyibinance",
        "chroma_path": "/tmp/chroma/twitter/heyi"
    },
    {
        "name": "CZ",
        "avatar": "👨‍🎨",
        "persona": "You are CZ, the co-founder and former CEO of Binance",
        "twitter_post_url_prefix": "https://x.com/cz_binance",
        "chroma_path": "/tmp/chroma/twitter/cz"
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

FOLLOW_UP_PROMPT = """
What else should I ask about this: 
{context}

Generate 1 relevant follow-up question that would help the user learn more about this topic. 
Format each question that starts with "Would you like to know more about...".
Make the questions specific and related to the context.
"""

# FOLLOW_UP_PROMPT = """
# Based on the following context:
# {context}

# Generate 1 relevant follow-up question that would help the user learn more about this topic. 
# Format each question that starts with "Would you like to know more about...".
# Make the questions specific and related to the context.
# """

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
    return prompt, results, context_text

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

    answer_with_RAG, search_results, context_text = generate_prompt(question)
    # print(f"prompt_with_RAG: {prompt_with_RAG}")

    # Create system message with persona
    system_message = SystemMessage(content=selected_user["persona"])
    human_message = HumanMessage(content=answer_with_RAG)
    
    print(f"system_message: {system_message}\n\n")
    print(f"human_message: {human_message}\n\n")
    
    # Get AI response
    response = chat.invoke([system_message, human_message])
    
    # Generate follow-up questions
    follow_up_prompt = FOLLOW_UP_PROMPT.format(context=question)
    follow_up_response = chat.invoke([SystemMessage(content="You are a helpful assistant that generates relevant follow-up questions."), 
                                    HumanMessage(content=follow_up_prompt)])
    # print(f"follow_up_prompt: {follow_up_prompt}\n\n")
    # print(f"follow_up_response: {follow_up_response}\n\n")
    follow_up_questions = follow_up_response.content
    # print(f"follow_up_questions: {follow_up_questions}\n\n")
    
    # Extract references from search results
    references = []
    for doc, score in search_results:
        if hasattr(doc, 'metadata') and 'source' in doc.metadata:
            ref = f"{selected_user['twitter_post_url_prefix']}/status/{doc.metadata['source']}"
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
    print(f"Response: {response.content}\n")
    print(f"Follow ups: {follow_up_questions}\n\n")

    # Display AI response with references and follow-up questions
    with st.chat_message("assistant"):
        st.write(response.content)
        # st.markdown("**Follow-up Question:**")
        st.write(follow_up_questions)
        st.markdown("**References:**")
        for ref in references:
            st.markdown(f"- {ref}")