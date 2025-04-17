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

RAPID_API_KEY = os.environ['RAPID_API_KEY']

# Need to be a place with write permissions, otherwise it will fail with: OSError: [Errno 30] Read-only file system
CHROMA_PATH = "/tmp/chroma/twitter/trump"
tw_user_id = 25073877 # Trump

# vitalik.eth
#CHROMA_PATH = "/tmp/chroma/twitter/vitalik"
#tw_user_id = 295218901 

# suji_yan
# CHROMA_PATH = "/tmp/chroma/twitter/suji"
# tw_user_id = 635682749


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
url = "https://twitter241.p.rapidapi.com/user-tweets"
headers = {
    "X-RapidAPI-Key": RAPID_API_KEY,  # Replace this with your actual key
    "X-RapidAPI-Host": "twitter241.p.rapidapi.com"
}
count = 20

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
    data = response.json() # Converts the JSON into a Python dictionary

    all_responses.append(data)

    # Too fast will get API rate limited
    time.sleep(1) 
    # Extract next cursor
    try:
        cursor = data["cursor"]["bottom"]
    except KeyError:
        print("No more data or cursor not found.\n\n")
        break

# Optionally: print number of tweets collected
# total_tweets = sum(len(page.get("response", {}).get("result", {}).get("timeline", {}).get("instructions", []).get("entries", [])) for page in all_responses)
# print(f"Total tweets collected: {total_tweets}\n\n")





def find_full_text_with_ids(data, current_id=None, seen = None):
    if seen is None:
        seen = set()

    results = []

    if isinstance(data, dict):
        local_id= current_id  # Carry current ID through recursion
        for key, value in data.items():
            if key == "rest_id":
                local_id = value  # Update current ID
            elif key == "text": # If the tweet is long, then this API will return a "text" which contains all content, besides "full_text" which contains truncated content ending with "..."
                if local_id not in seen and value != None and local_id != None:  # "who-to-follow" item has no "rest_id"(local_id)
                    seen.add(local_id)
                    results.append({"metadata": { "source": local_id }, "text": value})
            elif key == "full_text" and value != None and local_id != None: # if used "text" then don't use "full_text"
                if local_id not in seen:
                    seen.add(local_id)
                    results.append({"metadata": { "source": local_id }, "text": value})
            else:
                results.extend(find_full_text_with_ids(value, local_id, seen))
    
    elif isinstance(data, list):
        for item in data:
            results.extend(find_full_text_with_ids(item, current_id, seen))
    
    return results

data = find_full_text_with_ids(all_responses)
# print(type(data))
# print(data)
# print("\n\n")


# Convert JSON to LangChain Documents
docs = [
    Document(page_content=item["text"], metadata=item.get("metadata", {}))
    for item in data
]


# Initialize embeddings
embedding_function = OpenAIEmbeddings()  # you can use other embeddings like HuggingFaceEmbeddings

print(docs)
print("\n\n")


def main():
    save_to_chroma(docs)


def save_to_chroma(docs: list[Document]):
    # Clear out the database first.
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    # Create a new DB from the documents.
    db = Chroma.from_documents(
        docs, embedding_function, persist_directory=CHROMA_PATH
    )
    # db.persist()
    print(f"Saved {len(docs)} chunks to {CHROMA_PATH}.")


if __name__ == "__main__":
    main()
