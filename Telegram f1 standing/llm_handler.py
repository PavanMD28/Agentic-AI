import google.generativeai as genai
from typing import Optional
from models import MessageContext, F1Standings
import os

class LLMHandler:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        print(f"Attempting to initialize LLM with API key: {'present' if api_key else 'missing'}")
        if not api_key:
            raise ValueError("Gemini API key not found in environment variables")
        
        # Configure Gemini 2.0
        genai.configure(api_key=api_key)
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        
        # Initialize Gemini 2.0 model
        self.model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',  # Updated model name
            generation_config=generation_config
        )
        print("LLM initialized successfully with Gemini 2.0 configuration")
    
    async def analyze_standings(self, message_context: MessageContext) -> Optional[str]:
        try:
            standings = message_context.content.standings
            
            # Create a more detailed prompt for better analysis
            prompt = f"""
            Analyze these F1 standings and provide a concise, insightful analysis:
            
            Current Standings:
            {[f"{d.driver_name}: {d.points} points (P{d.position})" for d in standings]}
            
            Please provide:
            1. Points gaps between key positions (especially top 3)
            2. Championship battle analysis
            3. Notable performance trends
            4. Potential strategic implications
            
            Format the response in a clear, bullet-point style.
            """
            
            # Generate response
            response = await self.model.generate_content_async(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Error in LLM analysis: {e}")
            print(f"Error type: {type(e).__name__}")
            return None