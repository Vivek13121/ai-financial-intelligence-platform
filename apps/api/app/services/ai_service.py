import json
import logging
from google import genai
from google.genai import types
from app.config import settings

logger = logging.getLogger(__name__)

client = None
if settings.gemini_api_key:
    client = genai.Client(api_key=settings.gemini_api_key)

def generate_company_summary(company_name: str, articles: list, current_sentiment: float, forecast_direction: str) -> dict:
    if not client:
        logger.error("Gemini API key is not configured.")
        raise ValueError("Gemini API key is not configured. Please set GEMINI_API_KEY in your .env file.")

    news_summaries = "\n".join([f"- {a.title}: {a.content[:200]}..." if a.content else f"- {a.title}" for a in articles])

    sys_prompt = "You are a top-tier financial analyst. Given recent news articles, sentiment scores, and forecast metrics for a company, provide a concise intelligence summary. Output MUST be valid JSON conforming to the requested schema."
    
    user_prompt = f"""
Company: {company_name}
Recent News:
{news_summaries}

Sentiment Score: {current_sentiment}
Forecast Direction: {forecast_direction}

Provide a summary with the following details: Executive Summary, Key Risks, Key Opportunities, and Forecast Outlook.
"""
    
    logger.info(f"Generating AI summary for company: {company_name}")

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=sys_prompt,
                    response_mime_type="application/json",
                    response_schema={
                        "type": "OBJECT",
                        "properties": {
                            "executive_summary": {"type": "STRING"},
                            "risks": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "opportunities": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "forecast_outlook": {"type": "STRING"},
                        },
                        "required": ["executive_summary", "risks", "opportunities", "forecast_outlook"]
                    }
                )
            )
            logger.info(f"AI summary generated successfully for: {company_name}")
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            return json.loads(text.strip())
        except Exception as e:
            if ("503" in str(e) or isinstance(e, json.JSONDecodeError)) and attempt < max_retries - 1:
                logger.warning(f"Google API error ({type(e).__name__}) for {company_name}. Retrying attempt {attempt + 2}/{max_retries}...")
                import time
                time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s
                continue
            
            logger.error(f"Error generating AI summary for {company_name}: {e}")
            raise
