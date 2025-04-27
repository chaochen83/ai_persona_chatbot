from models import User, get_pgsql_db
from sqlalchemy.orm import Session

def init_db():
    db = next(get_pgsql_db())
    
    # Check if users already exist
    if db.query(User).count() == 0:
        # Initial user data
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
                "persona": "You are 一姐, Co-Founder & Chief Customer Service Officer @Binance, Holder of #BNB",
                "twitter_post_url_prefix": "https://x.com/heyibinance",
                "chroma_path": "/tmp/chroma/twitter/heyi"
            },
            {
                "name": "CZ",
                "avatar": "👨‍🎨",
                "persona": "You are 赵长鹏, the co-founder and former CEO of Binance",
                "twitter_post_url_prefix": "https://x.com/cz_binance",
                "chroma_path": "/tmp/chroma/twitter/cz"
            }
        ]
        
        # Add users to database
        for user_data in users:
            user = User(**user_data)
            db.add(user)
        
        db.commit()
        print("Database initialized with initial user data.")
    else:
        print("Database already contains user data.")

if __name__ == "__main__":
    init_db() 