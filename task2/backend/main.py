"""
Fynd AI Assessment - Task 2: Backend API
FastAPI server with LLM integration
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import os
from dotenv import load_dotenv
load_dotenv()


from models import ReviewSubmission, ReviewResponse, SubmissionCreate
from database import get_db, init_db
from llm_service import LLMService

app = FastAPI(title="Fynd Feedback System API")

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://fynd-user-dashboard-akash91.vercel.app",  # Your user dashboard URL
        "https://fynd-admin-dashboard-akash91.vercel.app",  # Your admin dashboard URL
    ],  # Update with specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLM service
llm_service = LLMService()

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    print("✓ Database initialized")

@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Fynd Feedback System",
        "version": "1.0"
    }

@app.post("/api/reviews", response_model=ReviewResponse)
async def submit_review(
    submission: SubmissionCreate,
    db: Session = Depends(get_db)
):
    """
    Submit a new review (User Dashboard endpoint)
    
    Request Body:
    {
        "rating": 1-5,
        "review_text": "User review content"
    }
    
    Returns:
    {
        "id": 1,
        "rating": 5,
        "review_text": "...",
        "ai_response": "Thank you for your feedback...",
        "ai_summary": "Positive review about...",
        "recommended_action": "Respond within 24 hours...",
        "created_at": "2026-01-06T..."
    }
    """
    
    # Validate rating
    if not 1 <= submission.rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    # Handle empty review
    review_text = submission.review_text.strip() if submission.review_text else ""
    
    if not review_text:
        review_text = "[No review text provided]"
    
    # Truncate very long reviews (10,000 chars max)
    if len(review_text) > 10000:
        review_text = review_text[:10000] + "..."
    
    try:
        # Generate AI responses using LLM service
        ai_response = await llm_service.generate_user_response(
            rating=submission.rating,
            review_text=review_text
        )
        
        ai_summary = await llm_service.generate_summary(
            rating=submission.rating,
            review_text=review_text
        )
        
        recommended_action = await llm_service.generate_recommended_action(
            rating=submission.rating,
            review_text=review_text
        )
        
    except Exception as e:
        # Graceful error handling - use fallback responses
        print(f"LLM Error: {e}")
        ai_response = "Thank you for your feedback. We appreciate you taking the time to share your thoughts with us."
        ai_summary = f"Customer provided a {submission.rating}-star rating."
        recommended_action = "Review and respond to customer feedback."
    
    # Store in database
    db_review = ReviewSubmission(
        rating=submission.rating,
        review_text=review_text,
        ai_response=ai_response,
        ai_summary=ai_summary,
        recommended_action=recommended_action
    )
    
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    
    return ReviewResponse(
        id=db_review.id,
        rating=db_review.rating,
        review_text=db_review.review_text,
        ai_response=db_review.ai_response,
        ai_summary=db_review.ai_summary,
        recommended_action=db_review.recommended_action,
        created_at=db_review.created_at
    )

@app.get("/api/reviews", response_model=List[ReviewResponse])
def get_all_reviews(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all reviews (Admin Dashboard endpoint)
    
    Query Parameters:
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: 100)
    
    Returns list of all submissions with AI analysis
    """
    reviews = db.query(ReviewSubmission)\
        .order_by(ReviewSubmission.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return [
        ReviewResponse(
            id=review.id,
            rating=review.rating,
            review_text=review.review_text,
            ai_response=review.ai_response,
            ai_summary=review.ai_summary,
            recommended_action=review.recommended_action,
            created_at=review.created_at
        )
        for review in reviews
    ]

@app.get("/api/analytics")
def get_analytics(db: Session = Depends(get_db)):
    """
    Get analytics summary (Admin Dashboard)
    
    Returns:
    {
        "total_reviews": 150,
        "average_rating": 4.2,
        "rating_distribution": {
            "1": 5,
            "2": 10,
            "3": 20,
            "4": 50,
            "5": 65
        }
    }
    """
    from sqlalchemy import func
    
    total = db.query(ReviewSubmission).count()
    
    if total == 0:
        return {
            "total_reviews": 0,
            "average_rating": 0,
            "rating_distribution": {str(i): 0 for i in range(1, 6)}
        }
    
    avg_rating = db.query(func.avg(ReviewSubmission.rating)).scalar()
    
    # Get rating distribution
    distribution = {}
    for i in range(1, 6):
        count = db.query(ReviewSubmission)\
            .filter(ReviewSubmission.rating == i)\
            .count()
        distribution[str(i)] = count
    
    return {
        "total_reviews": total,
        "average_rating": round(float(avg_rating), 2),
        "rating_distribution": distribution
    }

@app.delete("/api/reviews/{review_id}")
def delete_review(review_id: int, db: Session = Depends(get_db)):
    """Delete a review (Admin functionality)"""
    review = db.query(ReviewSubmission).filter(ReviewSubmission.id == review_id).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    db.delete(review)
    db.commit()
    
    return {"message": "Review deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)