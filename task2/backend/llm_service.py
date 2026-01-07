"""
LLM Service for generating AI responses, summaries, and recommendations
Uses Gemini API (free tier)
"""

import google.generativeai as genai
import os
from typing import Optional
import asyncio

class LLMService:
    """Service class for all LLM operations"""
    
    def __init__(self):
        """Initialize Gemini API"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Generation config for consistent, concise responses
        self.generation_config = {
            'temperature': 0.7,
            'top_p': 0.95,
            'top_k': 40,
            'max_output_tokens': 500,
        }
    
    async def _generate(self, prompt: str) -> str:
        """
        Internal method to call Gemini API
        Wraps sync API in async for consistency
        """
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(
                    prompt,
                    generation_config=self.generation_config
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"LLM Generation Error: {e}")
            raise
    
    async def generate_user_response(self, rating: int, review_text: str) -> str:
        """
        Generate a personalized response to show the user immediately
        
        Args:
            rating: Star rating (1-5)
            review_text: User's review text
        
        Returns:
            Personalized thank you message
        """
        
        # Handle empty reviews
        if not review_text or review_text == "[No review text provided]":
            prompt = f"""Generate a brief, professional thank you message for a customer who submitted a {rating}-star rating without any written review.

Keep it warm, genuine, and under 50 words."""
        else:
            prompt = f"""A customer submitted a {rating}-star review:

"{review_text}"

Generate a personalized, professional response thanking them for their feedback. 

Guidelines:
- For 4-5 stars: Express gratitude and enthusiasm
- For 3 stars: Thank them and acknowledge room for improvement
- For 1-2 stars: Apologize sincerely and commit to improvement

Keep response under 100 words, warm and genuine."""
        
        return await self._generate(prompt)
    
    async def generate_summary(self, rating: int, review_text: str) -> str:
        """
        Generate a concise summary for admin dashboard
        
        Args:
            rating: Star rating (1-5)
            review_text: User's review text
        
        Returns:
            Brief summary of key points
        """
        
        if not review_text or review_text == "[No review text provided]":
            return f"Customer submitted {rating}-star rating with no written feedback."
        
        prompt = f"""Summarize this {rating}-star customer review in 1-2 sentences, highlighting key points:

"{review_text}"

Focus on main concerns, praise, or issues mentioned. Be concise and factual."""
        
        return await self._generate(prompt)
    
    async def generate_recommended_action(self, rating: int, review_text: str) -> str:
        """
        Generate recommended next actions for admin
        
        Args:
            rating: Star rating (1-5)
            review_text: User's review text
        
        Returns:
            Recommended action items
        """
        
        sentiment_map = {
            1: "extremely negative",
            2: "negative",
            3: "neutral/mixed",
            4: "positive",
            5: "very positive"
        }
        
        sentiment = sentiment_map.get(rating, "unknown")
        
        if not review_text or review_text == "[No review text provided]":
            prompt = f"""A customer submitted a {rating}-star rating ({sentiment} feedback) with no written review.

Recommend specific actions the business should take. Consider:
- Follow-up communication needs
- Urgency level
- Investigation requirements

Provide 2-3 specific, actionable recommendations in bullet points."""
        else:
            prompt = f"""A customer submitted {sentiment} feedback ({rating} stars):

"{review_text}"

Recommend specific actions the business should take. Consider:
- Specific issues/praise mentioned
- Urgency and priority
- Follow-up needs
- Process improvements

Provide 2-3 specific, actionable recommendations in bullet points."""
        
        return await self._generate(prompt)


# ============================================================================
# Fallback responses (if LLM fails)
# ============================================================================

def get_fallback_user_response(rating: int) -> str:
    """Fallback responses if LLM fails"""
    responses = {
        5: "Thank you so much for your wonderful 5-star review! We're thrilled that you had such a positive experience.",
        4: "Thank you for your 4-star review! We appreciate your feedback and are glad you had a good experience.",
        3: "Thank you for your feedback. We appreciate you taking the time to share your thoughts and will work to improve.",
        2: "We're sorry to hear that your experience didn't meet expectations. Thank you for bringing this to our attention.",
        1: "We sincerely apologize for your negative experience. Your feedback is very important to us, and we will address these issues immediately."
    }
    return responses.get(rating, "Thank you for your feedback.")

def get_fallback_summary(rating: int) -> str:
    """Fallback summaries if LLM fails"""
    return f"Customer provided a {rating}-star rating."

def get_fallback_action(rating: int) -> str:
    """Fallback actions if LLM fails"""
    actions = {
        5: "• Send thank you email\n• Consider featuring as testimonial\n• Monitor for continued satisfaction",
        4: "• Send thank you note\n• Investigate any minor issues mentioned\n• Follow up in 2 weeks",
        3: "• Contact customer for more details\n• Investigate mentioned concerns\n• Implement improvements",
        2: "• Priority follow-up within 24 hours\n• Investigate issues thoroughly\n• Offer compensation if appropriate",
        1: "• URGENT: Contact customer immediately\n• Escalate to management\n• Conduct full investigation and remediation"
    }
    return actions.get(rating, "• Review feedback and take appropriate action")