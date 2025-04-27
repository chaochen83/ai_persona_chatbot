import os
import time
import requests
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import shutil
from dotenv import load_dotenv
from typing import Callable

# Load environment variables
load_dotenv()

def import_twitter_data(tw_user_id, CHROMA_PATH, progress_callback: Callable[[int, str], None] = None):
    RAPID_API_KEY = os.getenv("RAPID_API_KEY")
    how_many_pages = 50
    count = 20

    # Configuration
    url = "https://twitter241.p.rapidapi.com/user-tweets"
    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "twitter241.p.rapidapi.com"
    }

    # Storage for all pages
    all_responses = []

    # Initial request params
    params = {
        "user": tw_user_id,
        "count": count
    }

    cursor = None

    for i in range(how_many_pages):
        if cursor:
            params["cursor"] = cursor

        print(f"Fetching page {i + 1}...\n\n")
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        all_responses.append(data)

        # Update progress every 10 pages
        # if progress_callback and (i + 1) % 10 == 0:
        progress = int((i + 1) / how_many_pages * 100)
        status = f"Processed {i + 1} pages of tweets..."
        progress_callback(progress, status)

        # Too fast will get API rate limited
        time.sleep(0.5)
        # Extract next cursor
        try:
            cursor = data.get("cursor", {}).get("bottom")
            if not cursor:
                print("No more data or cursor not found.\n\n")
                print(f"cursor data: {data.get('cursor')}\n\n")
                break
        except Exception as e:
            print(f"Error accessing cursor: {e}\n\n")
            print(f"cursor data: {data.get('cursor')}\n\n")
            break

    def find_full_text_with_ids(data, current_id=None, seen=None):
        if seen is None:
            seen = set()

        results = []

        if isinstance(data, dict):
            local_id = current_id  # Carry current ID through recursion
            for key, value in data.items():
                if key == "rest_id":
                    local_id = value  # Update current ID
                elif key == "text":  # If the tweet is long, then this API will return a "text" which contains all content
                    if local_id not in seen and value != None and isinstance(value, str) and local_id != None:
                        seen.add(local_id)
                        results.append({"metadata": {"source": local_id}, "text": value})
                elif key == "full_text" and value != None and isinstance(value, str) and local_id != None:
                    if local_id not in seen:
                        seen.add(local_id)
                        results.append({"metadata": {"source": local_id}, "text": value})
                else:
                    results.extend(find_full_text_with_ids(value, local_id, seen))

        elif isinstance(data, list):
            for item in data:
                results.extend(find_full_text_with_ids(item, current_id, seen))

        return results

    progress_callback(progress, f"Initializing embeddings, please wait...")

    data = find_full_text_with_ids(all_responses)

    # Convert JSON to LangChain Documents
    docs = [
        Document(page_content=item["text"], metadata=item.get("metadata", {}))
        for item in data
    ]

    # Initialize embeddings
    embedding_function = OpenAIEmbeddings()

    print(docs)
    print("\n\n")

    # Clear out the database first
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    # Create a new DB from the documents
    db = Chroma.from_documents(
        docs, embedding_function, persist_directory=CHROMA_PATH
    )
    print(f"Saved {len(docs)} chunks to {CHROMA_PATH}.")
    return len(docs) 