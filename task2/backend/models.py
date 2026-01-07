"""
Database and Pydantic models for the feedback system
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field
from datetime import datetime

Base = declarative_base()

# ============================================================================
# SQLAlchemy Models (Database Tables)
# ============================================================================

class ReviewSubmission(Base):
    """Database model for review submissions"""
    __tablename__ = "review_submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    rating = Column(Integer, nullable=False)
    review_text = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)  # Response shown to user
    ai_summary = Column(Text, nullable=False)    # Summary for admin
    recommended_action = Column(Text, nullable=False)  # Suggested next steps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ReviewSubmission(id={self.id}, rating={self.rating})>"

# ============================================================================
# Pydantic Models (API Request/Response Schemas)
# ============================================================================

class SubmissionCreate(BaseModel):
    """Schema for creating a new review submission"""
    rating: int = Field(..., ge=1, le=5, description="Star rating from 1 to 5")
    review_text: str = Field(default="", description="User's review text")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rating": 5,
                "review_text": "Excellent service! The staff was very helpful and friendly."
            }
        }

class ReviewResponse(BaseModel):
    """Schema for review submission response"""
    id: int
    rating: int
    review_text: str
    ai_response: str
    ai_summary: str
    recommended_action: str
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "rating": 5,
                "review_text": "Excellent service!",
                "ai_response": "Thank you so much for your wonderful feedback!",
                "ai_summary": "Customer very satisfied with service quality",
                "recommended_action": "Send personalized thank you email",
                "created_at": "2026-01-06T10:30:00"
            }
        }

class ErrorResponse(BaseModel):
    """Schema for error responses"""
    detail: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Rating must be between 1 and 5"
            }
        }