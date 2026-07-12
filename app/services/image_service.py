import httpx
from typing import Optional, List, Dict, Any
import logging

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class ImageService:
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v18.0"
        self.access_token = settings.FACEBOOK_PAGE_ACCESS_TOKEN
    
    async def send_image(
        self,
        recipient_id: str,
        image_url: str,
        platform: str = "facebook"
    ) -> bool:
        """Send image to user."""
        message = {
            "attachment": {
                "type": "image",
                "payload": {"url": image_url}
            }
        }
        
        return await self._send_message(recipient_id, message, platform)
    
    async def send_product_card(
        self,
        recipient_id: str,
        product: Dict[str, Any],
        platform: str = "facebook"
    ) -> bool:
        """Send product card with image and details."""
        message = {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": [
                        {
                            "title": product.get("name", "Product"),
                            "image_url": product.get("image_url", ""),
                            "subtitle": f"${product.get('price', 0):.2f}",
                            "buttons": [
                                {
                                    "type": "postback",
                                    "title": "View Details",
                                    "payload": f"PRODUCT_{product.get('sku', '')}"
                                },
                                {
                                    "type": "postback",
                                    "title": "Order Now",
                                    "payload": f"ORDER_{product.get('sku', '')}"
                                }
                            ]
                        }
                    ]
                }
            }
        }
        
        return await self._send_message(recipient_id, message, platform)
    
    async def send_product_gallery(
        self,
        recipient_id: str,
        products: List[Dict[str, Any]],
        platform: str = "facebook"
    ) -> bool:
        """Send multiple products as a carousel."""
        elements = []
        
        for product in products[:10]:  # Facebook limits to 10 elements
            elements.append({
                "title": product.get("name", "Product"),
                "image_url": product.get("image_url", ""),
                "subtitle": f"${product.get('price', 0):.2f}",
                "buttons": [
                    {
                        "type": "postback",
                        "title": "View Details",
                        "payload": f"PRODUCT_{product.get('sku', '')}"
                    }
                ]
            })
        
        message = {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": elements
                }
            }
        }
        
        return await self._send_message(recipient_id, message, platform)
    
    async def send_order_confirmation(
        self,
        recipient_id: str,
        order: Dict[str, Any],
        platform: str = "facebook"
    ) -> bool:
        """Send order confirmation card."""
        items = order.get("items", [])
        item_summary = "\n".join([
            f"• {item.get('name', 'Item')} x{item.get('quantity', 1)}"
            for item in items[:5]
        ])
        
        message = {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "receipt",
                    "recipient_name": order.get("customer_name", "Customer"),
                    "order_number": order.get("order_number", ""),
                    "currency": order.get("currency", "USD"),
                    "payment_method": "Online",
                    "order_url": order.get("order_url", ""),
                    "timestamp": order.get("timestamp", ""),
                    "elements": [
                        {
                            "title": item.get("name", "Item"),
                            "subtitle": f"Qty: {item.get('quantity', 1)}",
                            "price": item.get("price", 0),
                            "currency": order.get("currency", "USD")
                        }
                        for item in items[:5]
                    ],
                    "address": {
                        "name": order.get("shipping_name", ""),
                        "street_1": order.get("shipping_address", ""),
                        "city": order.get("shipping_city", ""),
                        "state": order.get("shipping_state", ""),
                        "postal_code": order.get("shipping_zip", ""),
                        "country": "US"
                    },
                    "summary": {
                        "subtotal": order.get("subtotal", 0),
                        "shipping": order.get("shipping_cost", 0),
                        "total_tax": order.get("tax", 0),
                        "total_cost": order.get("total", 0)
                    }
                }
            }
        }
        
        return await self._send_message(recipient_id, message, platform)
    
    async def send_shipping_update(
        self,
        recipient_id: str,
        order_number: str,
        tracking_url: Optional[str] = None,
        platform: str = "facebook"
    ) -> bool:
        """Send shipping update with tracking."""
        message = {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": f"Your order {order_number} has been shipped!",
                    "buttons": [
                        {
                            "type": "web_url",
                            "url": tracking_url or f"https://track.example.com/{order_number}",
                            "title": "Track Package"
                        }
                    ]
                }
            }
        }
        
        return await self._send_message(recipient_id, message, platform)
    
    async def _send_message(
        self,
        recipient_id: str,
        message: Dict[str, Any],
        platform: str
    ) -> bool:
        """Send message to platform."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/me/messages",
                    params={"access_token": self.access_token},
                    json={
                        "recipient": {"id": recipient_id},
                        "message": message
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                return True
            except Exception as e:
                logger.error(f"Failed to send image: {str(e)}")
                return False
    
    async def upload_image(self, image_path: str) -> Optional[str]:
        """Upload image to Facebook and get attachment ID."""
        async with httpx.AsyncClient() as client:
            try:
                with open(image_path, "rb") as image_file:
                    response = await client.post(
                        f"{self.base_url}/me/message_attachments",
                        params={"access_token": self.access_token},
                        files={"filedata": image_file},
                        timeout=60.0
                    )
                    response.raise_for_status()
                    return response.json().get("attachment_id")
            except Exception as e:
                logger.error(f"Failed to upload image: {str(e)}")
                return None
    
    async def get_image_url(self, attachment_id: str) -> Optional[str]:
        """Get image URL from attachment ID."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/{attachment_id}",
                    params={
                        "fields": "url",
                        "access_token": self.access_token
                    }
                )
                response.raise_for_status()
                return response.json().get("url")
            except Exception as e:
                logger.error(f"Failed to get image URL: {str(e)}")
                return None
