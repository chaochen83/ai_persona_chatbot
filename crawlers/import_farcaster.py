import os
import time
import requests
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import shutil
from dotenv import load_dotenv
from typing import Callable, Optional

# Load environment variables
load_dotenv()

def checkUserHasFarcaster(twitter_id: str) -> Optional[str]:
    url = f"https://api-dev.firefly.land/v2/wallet/profileinfo?twitterId={twitter_id}"
    print(f"checkUserHasFarcaster - twitter_id: {twitter_id}")
    headers = {
        "content-type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        # Check if the response has the expected structure and contains Farcaster profiles
        if (data.get("data") and 
            data["data"].get("farcasterProfiles") and 
            len(data["data"]["farcasterProfiles"]) > 0):
            
            # Return the FID of the first Farcaster profile as a string
            fid = data["data"]["farcasterProfiles"][0].get("fid")
            if fid is not None:
                return str(fid)
            
            print(f"checkUserHasFarcaster - fid: {fid}")

    except Exception as e:
        print(f"Error checking Farcaster profile: {e}")
    
    return None

def import_farcaster_data(fid, CHROMA_PATH, progress_callback: Callable[[int, str], None] = None):
    FARCASTER_AUTH_TOKEN = os.getenv("FARCASTER_AUTH_TOKEN")
    how_many_pages = 50
    META_TYPE = "FC"  # Farcaster

    # Configuration
    url = "https://api-dev.firefly.land/v2/user/timeline/farcaster"
    headers = {
        "authorization": FARCASTER_AUTH_TOKEN,
        "content-type": "application/json"
    }
    count = 20

    # Storage for all pages
    all_responses = []

    # Initial request params
    param = {
        "fids": [fid]
    }

    cursor = None

    for i in range(how_many_pages):
        if cursor:
            param["cursor"] = cursor

        print(f"Fetching page {i + 1}...\n\n")
        response = requests.post(url, headers=headers, json=param)

        data = response.json()


        # Process the response using find_text
        cast_data = find_text(data)
        if cast_data:
            all_responses.extend(cast_data)

        # Update progress
        progress = int((i + 1) / how_many_pages * 100)
        status = f"Processed {i + 1} pages of casts..."
        if progress_callback:
            progress_callback(progress, status)

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

    if progress_callback:
        progress_callback(progress, "Initializing embeddings, please wait...")

    # Convert JSON to LangChain Documents
    docs = [
        Document(page_content=item["text"], metadata=item.get("metadata", {}))
        for item in all_responses
    ]

    message = save_to_chroma(CHROMA_PATH, docs)
    if progress_callback:
        progress_callback(progress, message)


def save_to_chroma(CHROMA_PATH, docs: list[Document]):
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
            return "Added {len(new_docs)} new documents from Farcaster."
        else:
            return "No new documents to add."
    else:
        # Create new database if it doesn't exist
        db = Chroma.from_documents(docs, embedding_function, persist_directory=CHROMA_PATH)
        return "Created new database with {len(docs)} documents."

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
                "metadata": { "source": cast["hash"], "type": "FC" },
                "text": cast["text"]
            })
    
    return results 