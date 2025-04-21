# from langchain.document_loaders import DirectoryLoader
import json
import time
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
# from langchain.embeddings import OpenAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import openai 
from dotenv import load_dotenv
import os
import shutil

import requests

# Load environment variables. Assumes that project contains .env file with API keys
load_dotenv()
#---- Set OpenAI API key 
# Change environment variable name from "OPENAI_API_KEY" to the name given in 
# your .env file.
openai.api_key = os.environ['OPENAI_API_KEY']

FARCASTER_AUTH_TOKEN = os.environ['FARCASTER_AUTH_TOKEN']

# Need to be a place with write permissions, otherwise it will fail with: OSError: [Errno 30] Read-only file system
# CHROMA_PATH = "/tmp/chroma/twitter/trump"
# tw_user_id = 25073877 # Trump

META_TYPE = "FC" #Farcaster

# vitalik.eth
CHROMA_PATH = "/tmp/chroma/twitter/vitalik"
FID = "5650" 

# suji_yan
# CHROMA_PATH = "/tmp/chroma/twitter/suji"
# FID = "966" 

# heyibinance
# CHROMA_PATH = "/tmp/chroma/twitter/heyi"
# tw_user_id = 1003840309166366721

# cz_binance
# CHROMA_PATH = "/tmp/chroma/twitter/cz"
# tw_user_id = 902926941413453824


how_many_pages = 50

# data = [
#   {
#     "id": "1",
#     "text": "The Eiffel Tower is located in Paris.",
#     "metadata": { "source": "wikipedia" }
#   },
#   {
#     "id": "2",
#     "text": "The Great Wall of China is visible from space.",
#     "metadata": { "source": "myth" }
#   }
# ]
# print(type(data))



# Configuration
url = "https://api-dev.firefly.land/v2/user/timeline/farcaster"
headers = {
    "authorization": FARCASTER_AUTH_TOKEN,  # Replace this with your actual key
    "content-type": "application/json"
}
count = 20

# Storage for all pages
all_responses = []

# Initial request params
param = {
    "fids": [FID]
}



def find_text(data):
    results = []
    
    if not isinstance(data, dict):
        return results
        
    # Check if we have the expected data structure
    if "data" not in data or "casts" not in data["data"]:
        return results
        
    # Process each cast in the response
    for cast in data["data"]["casts"]:
        if "hash" in cast and "text" in cast:
            results.append({
                "metadata": { "source": cast["hash"], "type": META_TYPE },
                "text": cast["text"]
            })
    
    return results

cursor = None

for i in range(how_many_pages):
    if cursor:
        param["cursor"] = cursor

    print(f"Fetching page {i + 1}...\n\n")
    response = requests.post(url, headers=headers, json=param)

    data = response.json() # Converts the JSON into a Python dictionary
    # print(f"data: {data}\n\n")

    # Process the response using find_text
    cast_data = find_text(data)
    # print(f"cast_data: {cast_data}\n\n")

    if cast_data:
        all_responses.extend(cast_data)

    # Too fast will get API rate limited
    time.sleep(1) 
    # Extract next cursor
    try:
        cursor = data.get("data", {}).get("cursor")
        if not cursor:
            print("No more data or cursor not found.\n\n")
            print(f"cursor data: {data.get('data', {}).get('cursor')}\n\n")
            break
    except Exception as e:
        print(f"Error accessing cursor: {e}\n\n")
        print(f"cursor data: {data.get('data', {}).get('cursor')}\n\n")
        break


# print(f"all_responses: {all_responses}")
# exit()


# Convert JSON to LangChain Documents
docs = [
    Document(page_content=item["text"], metadata=item.get("metadata", {}))
    for item in all_responses
]


# Initialize embeddings
embedding_function = OpenAIEmbeddings()  # you can use other embeddings like HuggingFaceEmbeddings

print(docs)
print("\n\n")


def main():
    save_to_chroma(docs)


def save_to_chroma(docs: list[Document]):
    # Initialize embeddings
    embedding_function = OpenAIEmbeddings()
    
    # Check if database exists
    if os.path.exists(CHROMA_PATH):
        # Load existing database
        db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
        
        # Get existing document hashes
        existing_hashes = set()
        existing_docs = db.get()
        if existing_docs and 'metadatas' in existing_docs:
            existing_hashes = {doc['source'] for doc in existing_docs['metadatas'] if 'source' in doc}
        
        # Filter out documents that already exist
        new_docs = [doc for doc in docs if doc.metadata.get('source') not in existing_hashes]
        
        if new_docs:
            # Add only new documents
            db.add_documents(new_docs)
            print(f"Added {len(new_docs)} new documents to {CHROMA_PATH}")
        else:
            print(f"No new documents to add to {CHROMA_PATH}")
    else:
        # Create new database if it doesn't exist
        db = Chroma.from_documents(docs, embedding_function, persist_directory=CHROMA_PATH)
        print(f"Created new database with {len(docs)} documents at {CHROMA_PATH}")


if __name__ == "__main__":
    main()
