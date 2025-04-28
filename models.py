from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import requests
from crawlers.import_farcaster import checkUserHasFarcaster, import_farcaster_data
from crawlers.import_twitter import import_twitter_data
from sqlalchemy.orm import Session

# Status constants
STATUS_NOT_IMPORTED = 0
STATUS_FULLY_IMPORTED = 9

# Load environment variables
load_dotenv()

# Database configuration
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "persona_users")
DB_PORT = os.getenv("DB_PORT", "5432")

# Create database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine
engine = create_engine(DATABASE_URL)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class
Base = declarative_base()

class User(Base):
    __tablename__ = "ai_persona_users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    avatar = Column(String(10), nullable=False)
    persona = Column(Text, nullable=False)
    twitter_post_url_prefix = Column(String(255), nullable=False)
    chroma_path = Column(String(255), nullable=False)
    twitter_id = Column(Integer, nullable=False)
    farcaster_id = Column(Integer, nullable=True)
    status = Column(Integer, nullable=False, default=0)

# Create tables
Base.metadata.create_all(bind=engine)

def get_pgsql_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_users(pgsql_db: Session):
    print(f"enter get_users()")
    return pgsql_db.query(User).filter(User.status == STATUS_FULLY_IMPORTED).order_by(User.id).all()

def insert_new_user_to_pgsql_db(twitter_handle, status_text, progress_bar_tw, progress_bar_fc):
    # Get database session
    db = next(get_pgsql_db())
    
    # 1. Check if user already exists
    existing_user = db.query(User).filter(User.name == twitter_handle).first()
    if existing_user:
        tw_user_id = existing_user.twitter_id
        if existing_user.status == STATUS_FULLY_IMPORTED:
            return "User already exists and is fully imported"
    else:
        # 2. Make API request to get user info
        url = f"https://twitter241.p.rapidapi.com/user?username={twitter_handle}"
        headers = {
            "X-RapidAPI-Key": os.getenv("RAPID_API_KEY"),
            "X-RapidAPI-Host": "twitter241.p.rapidapi.com"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # 3. Check if user exists in API response
            if not data.get('result', {}).get('data', {}).get('user', {}).get('result'):
                return "Twitter user does not exist"
            
            # 4. Extract user info from API response
            user_data = data['result']['data']['user']['result']
            description = user_data['legacy']['description']
            profile_image_url = user_data['legacy']['profile_image_url_https']
            tw_user_id = user_data['rest_id']  # Get the Twitter user ID
            
            # 5. Create new user record with status 0
            new_user = User(
                name=twitter_handle,
                avatar=profile_image_url,
                persona=f"You are {description}",
                twitter_post_url_prefix=f"https://x.com/{twitter_handle}",
                chroma_path=f"/tmp/chroma/twitter/{twitter_handle}",
                twitter_id=tw_user_id,
                status=STATUS_NOT_IMPORTED
            )
            
            # Add to database
            db.add(new_user)
            db.commit()
            
        except requests.exceptions.RequestException as e:
            return f"Error fetching user data: {str(e)}"
        except Exception as e:
            db.rollback()
            return f"Error adding user: {str(e)}"
    
    # Update progress after successful database insertion
    progress_bar_tw.progress(1)
    status_text.text_area("Status", value=f"Successfully found Twitter user @{twitter_handle}", height=70, disabled=True, key="text1")
    
    # Define progress callback
    def update_tw_progress(progress, status):
        progress_bar_tw.progress(progress)
        status_text.text_area("Status", value=status, height=70, disabled=True)

    def update_fc_progress(progress, status):
        progress_bar_fc.progress(progress)
        # status_text.text_area("Status", value=status, height=70, disabled=True, key="text2")    
        status_text.text(status)    
    
    print(f"twitter id: {tw_user_id}\n\n")
    
    # Import Twitter data with progress updates
    num_tweets = import_twitter_data(tw_user_id, existing_user.chroma_path if existing_user else new_user.chroma_path, progress_callback=update_tw_progress)
    
    # If user has farcaster account, then crawl it as well:
    fid = checkUserHasFarcaster(tw_user_id)
    if fid:
        # Reset progress bar for Farcaster import
        progress_bar_fc.progress(0)
        status_text.text_area("Status", value=f"Found Farcaster profile. Importing Farcaster data...", height=70, disabled=True)
        
        # Import Farcaster data with the Farcaster progress callback
        num_casts = import_farcaster_data(fid, existing_user.chroma_path if existing_user else new_user.chroma_path, progress_callback=update_fc_progress)

        if existing_user:
            existing_user.farcaster_id = fid
        else:
            new_user.farcaster_id = fid
    else:
        progress_bar_fc.progress(100)
        status_text.text_area("Status", value=f"Farcaster profile not found.", height=70, disabled=True)

    # Update user status to 9 after successful import
    if existing_user:
        existing_user.status = STATUS_FULLY_IMPORTED
    else:
        new_user.status = STATUS_FULLY_IMPORTED
    db.commit()
    
    return f"User successfully added/updated with {num_tweets} tweets" 