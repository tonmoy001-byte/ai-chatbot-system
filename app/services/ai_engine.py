from google import genai
from google.genai import types
from typing import Dict, Any, Optional, List
import logging
import json

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class AIEngine:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = "gemini-2.5-flash"
        self.default_system_prompt = """You are a helpful customer service assistant for a business.
        Respond in a friendly, professional manner.
        Keep responses concise but helpful (under 200 words when possible).
        If you don't know the answer, offer to connect the customer with a human agent.
        Never make up information about orders, products, or services.
        Always be polite and empathetic."""
    
    async def generate_response(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate AI response to customer message."""
        
        contents = []
        
        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history[-10:]:  # Last 10 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                contents.append(types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=content)]
                ))
        
        # Build the user message with context
        user_message = message
        if context:
            context_parts = []
            for k, v in context.items():
                if v:
                    context_parts.append(f"{k}: {v}")
            if context_parts:
                user_message = "Context information:\n" + "\n".join(context_parts) + "\n\nCustomer message: " + message
        
        # Add customer message
        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_message)]
        ))
        
        # Use system prompt or default
        prompt = system_prompt or self.default_system_prompt
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=prompt,
                    max_output_tokens=500,
                    temperature=0.7,
                    top_p=1.0
                )
            )
            
            response_text = response.text
            
            # Log the interaction
            logger.info(f"AI Response generated for message: {message[:50]}...")
            
            return response_text
            
        except Exception as e:
            logger.error(f"AI response generation failed: {str(e)}")
            return "I apologize, but I'm experiencing technical difficulties. Please try again later or contact our support team."
    
    async def analyze_intent(self, message: str) -> str:
        """Analyze customer intent from message."""
        system_prompt = """You are an intent classifier. Analyze the customer message and return ONLY one of these categories:
        - greeting: Hello, hi, hey, good morning, etc.
        - order_status: Asking about order status, tracking, delivery
        - product_info: Asking about products, prices, availability
        - booking: Wanting to schedule, book, or make an appointment
        - complaint: Expressing dissatisfaction, issues, problems
        - question: General questions about services, policies, etc.
        - other: Anything else
        
        Return ONLY the category word, nothing else."""
        
        try:
            response = await self.generate_response(
                message=f"Classify this customer message: {message}",
                system_prompt=system_prompt
            )
            return response.strip().lower()
        except Exception as e:
            logger.error(f"Intent analysis failed: {str(e)}")
            return "other"
    
    async def extract_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities from customer message."""
        system_prompt = """Extract the following entities from the customer message and return as JSON:
        - order_numbers: List of order numbers (format: ORD-XXXXXX or similar)
        - dates: List of dates mentioned
        - products: List of product names mentioned
        - email: Email addresses mentioned
        - phone: Phone numbers mentioned
        
        Return ONLY valid JSON, no other text."""
        
        try:
            response = await self.generate_response(
                message=f"Extract entities from this message: {message}",
                system_prompt=system_prompt
            )
            
            # Try to parse JSON from response
            # Remove any markdown code block markers
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            cleaned = cleaned.strip()
            
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse entity extraction response: {response}")
            return {"order_numbers": [], "dates": [], "products": [], "email": [], "phone": []}
        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
            return {"order_numbers": [], "dates": [], "products": [], "email": [], "phone": []}
    
    async def generate_order_response(
        self,
        order_number: str,
        order_status: str,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a customer-friendly order status response."""
        system_prompt = """You are a helpful order status assistant. Generate a friendly, informative response about the order status.
        Include relevant next steps based on the status.
        Keep the response concise and professional."""
        
        context = f"Order number: {order_number}\nOrder status: {order_status}"
        if additional_info:
            context += f"\nAdditional info: {json.dumps(additional_info)}"
        
        return await self.generate_response(
            message=f"Generate order status response",
            context={"order_info": context},
            system_prompt=system_prompt
        )
    
    async def generate_booking_response(
        self,
        available_slots: List[str],
        customer_request: Optional[str] = None
    ) -> str:
        """Generate a booking availability response."""
        system_prompt = """You are a helpful booking assistant. Generate a friendly response showing available time slots.
        Format the times in a user-friendly way.
        If no slots are available, offer alternatives."""
        
        context = f"Available slots: {', '.join(available_slots)}"
        if customer_request:
            context += f"\nCustomer request: {customer_request}"
        
        return await self.generate_response(
            message="Show available booking slots",
            context={"booking_info": context},
            system_prompt=system_prompt
        )
