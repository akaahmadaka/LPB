from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    url = Column(String)
    clicks = Column(Integer, default=0)
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    submission_time = Column(DateTime, default=datetime.now)
    user_id = Column(Integer, ForeignKey("users.user_id"))  # Link to the user who submitted it
    user = relationship("User", back_populates="links")  # Relationship to the User model