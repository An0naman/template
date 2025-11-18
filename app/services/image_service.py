"""
Image Generation Service for Hugging Face API
Generates wallpapers and background images using Stable Diffusion models
"""

import os
import logging
import requests
import base64
from typing import Optional, Dict, Any
from flask import current_app
import time

logger = logging.getLogger(__name__)

class ImageService:
    """Service for generating images with Hugging Face API"""
    
    def __init__(self):
        self.api_key = None
        self.model = None
        self.image_size = None
        self.is_configured = False
        self._configure()
    
    def _configure(self):
        """Configure the Hugging Face API"""
        try:
            # Check environment variable first, then system parameters
            api_key = os.getenv('HUGGINGFACE_API_KEY')
            model = 'stabilityai/stable-diffusion-xl-base-1.0'
            image_size = '1024x576'
            
            if not api_key:
                # Try to get from system parameters
                try:
                    from flask import has_app_context
                    if has_app_context():
                        from ..db import get_system_parameters
                        params = get_system_parameters()
                        api_key = params.get('huggingface_api_key', '')
                        model = params.get('huggingface_model', 'stabilityai/stable-diffusion-xl-base-1.0')
                        image_size = params.get('huggingface_image_size', '1024x576')
                except Exception as e:
                    logger.debug(f"Could not access system parameters: {e}")
            
            if not api_key:
                logger.warning("HUGGINGFACE_API_KEY not found. Image generation will be disabled.")
                self.is_configured = False
                return
            
            self.api_key = api_key
            self.model = model
            self.image_size = image_size
            self.is_configured = True
            logger.info(f"Hugging Face image service configured with model: {model}")
            
        except Exception as e:
            logger.error(f"Failed to configure Hugging Face: {str(e)}")
            self.is_configured = False
    
    def reconfigure(self):
        """Force reconfiguration of the service"""
        logger.info("Forcing image service reconfiguration...")
        self._configure()
        return self.is_configured
    
    def is_available(self) -> bool:
        """Check if image service is available"""
        self._configure()
        return self.is_configured and self.api_key is not None
    
    def generate_image(self, prompt: str, negative_prompt: str = None) -> Optional[Dict[str, Any]]:
        """
        Generate an image using Hugging Face API
        
        Args:
            prompt: Description of the image to generate
            negative_prompt: What to avoid in the image
            
        Returns:
            Dict with 'success', 'image_data' (base64), and 'error' if failed
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'Hugging Face API not configured. Please add your API token in System Settings.'
            }
        
        try:
            # Parse image dimensions
            width, height = map(int, self.image_size.split('x'))
            
            # Prepare the API request (using new router endpoint)
            api_url = f"https://router.huggingface.co/hf-inference/models/{self.model}"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            # Build payload
            payload = {
                "inputs": prompt,
                "parameters": {
                    "width": width,
                    "height": height,
                    "num_inference_steps": 30,  # Good balance of quality and speed
                    "guidance_scale": 7.5  # How closely to follow the prompt
                }
            }
            
            if negative_prompt:
                payload["parameters"]["negative_prompt"] = negative_prompt
            
            logger.info(f"Generating image with prompt: {prompt[:100]}...")
            
            # Make the API request
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=60  # Can take a while for first generation
            )
            
            if response.status_code == 503:
                # Model is loading, wait and retry
                logger.info("Model is loading, waiting...")
                time.sleep(20)
                response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                # Convert image bytes to base64
                image_data = base64.b64encode(response.content).decode('utf-8')
                
                logger.info("Image generated successfully")
                return {
                    'success': True,
                    'image_data': image_data,
                    'content_type': 'image/jpeg'
                }
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except requests.exceptions.Timeout:
            error_msg = "Image generation timed out. The model might be loading. Try again in a minute."
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
            
        except Exception as e:
            error_msg = f"Failed to generate image: {str(e)}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}


# Global instance
_image_service = None

def get_image_service() -> ImageService:
    """Get the global image service instance"""
    global _image_service
    if _image_service is None:
        _image_service = ImageService()
    return _image_service
