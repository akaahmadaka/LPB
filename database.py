import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from datetime import datetime
from models.link_model import Link, Base as LinkBase
from models.user_model import User, Base as UserBase

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URI = 'sqlite:///links.db'

# Create engine with SQLite-specific configurations
engine = create_engine(
    DATABASE_URI,
    connect_args={'check_same_thread': False},  # Required for SQLite
    pool_pre_ping=True  # Connection health checks
)

# Create session factory
SessionFactory = sessionmaker(bind=engine)
Session = scoped_session(SessionFactory)

@contextmanager
def get_db_session():
    """
    Context manager for database sessions.
    Ensures proper handling of sessions including rollback on errors.
    """
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        session.close()

# SQLite specific optimizations
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
    cursor.execute("PRAGMA synchronous=NORMAL")  # Faster synchronization
    cursor.execute("PRAGMA temp_store=MEMORY")  # Store temp tables in memory
    cursor.execute("PRAGMA cache_size=-2000")  # Use 2MB of memory for cache
    cursor.close()

def init_db():
    """Initialize the database by creating all tables."""
    try:
        # Create tables
        LinkBase.metadata.create_all(engine)
        UserBase.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

def update_user_role(user_id: int, new_role: str) -> bool:
    """
    Update a user's role in the database.
    
    Args:
        user_id (int): The Telegram user ID
        new_role (str): The new role to assign
        
    Returns:
        bool: True if successful, False otherwise
    """
    with get_db_session() as session:
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                # Validate the role
                if new_role in [role.value for role in UserRole]:
                    user.role = new_role
                    user.updated_at = datetime.utcnow()
                    logger.info(f"Updated role for user {user_id} to {new_role}")
                    return True
                else:
                    logger.warning(f"Invalid role attempted: {new_role}")
                    return False
            logger.warning(f"User {user_id} not found for role update")
            return False
        except SQLAlchemyError as e:
            logger.error(f"Error updating user role: {str(e)}")
            raise

def save_link(title: str, url: str, user_id: int) -> Link:
    """Save a new link to the database."""
    with get_db_session() as session:
        try:
            link = Link(
                title=title,
                url=url,
                user_id=user_id,
                submission_time=datetime.utcnow()
            )
            session.add(link)
            logger.info(f"Link saved successfully: {title}")
            return link
        except SQLAlchemyError as e:
            logger.error(f"Error saving link: {str(e)}")
            raise

def delete_link(link_id: int) -> bool:
    """Delete a link from the database."""
    with get_db_session() as session:
        try:
            link = session.query(Link).filter_by(id=link_id).first()
            if link:
                session.delete(link)
                logger.info(f"Link {link_id} deleted successfully")
                return True
            logger.warning(f"Link {link_id} not found")
            return False
        except SQLAlchemyError as e:
            logger.error(f"Error deleting link: {str(e)}")
            raise

def get_all_links(session=None):
    """Fetch all links from the database ordered by score."""
    try:
        if session is None:
            with get_db_session() as session:
                return session.query(Link).order_by(Link.score.desc()).all()
        else:
            return session.query(Link).order_by(Link.score.desc()).all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching links: {str(e)}")
        return []

def get_user_by_id(user_id: int) -> User:
    """Fetch a user by their Telegram user ID."""
    with get_db_session() as session:
        try:
            return session.query(User).filter_by(user_id=user_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error fetching user: {str(e)}")
            raise

def save_user(user_id: int) -> User:
    """Save a new user to the database."""
    with get_db_session() as session:
        try:
            # Create user with only user_id
            user = User(user_id=user_id)
            session.add(user)
            logger.info(f"User saved successfully: {user_id}")
            return user
        except SQLAlchemyError as e:
            logger.error(f"Error saving user: {str(e)}")
            raise

def get_link_by_id(link_id: int, session=None) -> Link:
    """Get a link by its ID."""
    try:
        if session is None:
            with get_db_session() as session:
                return session.query(Link).get(link_id)
        return session.query(Link).get(link_id)
    except SQLAlchemyError as e:
        logger.error(f"Error getting link by ID: {str(e)}")
        raise

def check_database_connection() -> bool:
    """Check if the database connection is working."""
    try:
        with get_db_session() as session:
            session.execute("SELECT 1")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False

# Initialize database when the module is imported
init_db()