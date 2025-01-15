# Import required modules
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DATABASE_URI
from models.link_model import Link, Base
from models.user_model import User

# Set up the database connection
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Define the Link model
class Link(Base):
    __tablename__ = "links"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    url = Column(String)
    clicks = Column(Integer, default=0)
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    submission_time = Column(DateTime, default=datetime.now)

# Create tables in the database
Base.metadata.create_all(engine)

# Database operations
def save_link(title, url):
    """
    Save a new link to the database.
    """
    session = Session()
    link = Link(title=title, url=url)
    session.add(link)
    session.commit()
    session.close()

def delete_link(link_id):
    """
    Delete a link from the database by its ID.
    """
    session = Session()
    link = session.query(Link).filter_by(id=link_id).first()
    if link:
        session.delete(link)
        session.commit()
    session.close()

def get_all_links():
    """
    Fetch all links from the database.
    """
    session = Session()
    links = session.query(Link).all()
    session.close()
    return links

def increment_clicks(link_id):
    """
    Increment the click count for a link.
    """
    session = Session()
    link = session.query(Link).filter_by(id=link_id).first()
    if link:
        link.clicks += 1
        session.commit()
    session.close()

def increment_upvotes(link_id):
    """
    Increment the upvote count for a link.
    """
    session = Session()
    link = session.query(Link).filter_by(id=link_id).first()
    if link:
        link.upvotes += 1
        session.commit()
    session.close()

def increment_downvotes(link_id):
    """
    Increment the downvote count for a link.
    """
    session = Session()
    link = session.query(Link).filter_by(id=link_id).first()
    if link:
        link.downvotes += 1
        session.commit()
    session.close()

def save_user(user_id, username, first_name, last_name, role="user"):
    """
    Save a new user to the database.
    """
    session = Session()
    user = User(user_id=user_id, username=username, first_name=first_name, last_name=last_name, role=role)
    session.add(user)
    session.commit()
    session.close()

def get_user_by_id(user_id):
    """
    Fetch a user by their Telegram user ID.
    """
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()
    session.close()
    return user

def update_user_role(user_id, role):
    """
    Update a user's role (e.g., promote to admin).
    """
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()
    if user:
        user.role = role
        session.commit()
    session.close()