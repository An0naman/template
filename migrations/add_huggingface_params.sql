-- Migration: Add Hugging Face API parameters to SystemParameters
-- This ensures that Hugging Face settings can be saved and loaded correctly

-- Add huggingface_api_key parameter (if not exists)
INSERT OR IGNORE INTO SystemParameters (parameter_name, parameter_value) 
VALUES ('huggingface_api_key', '');

-- Add huggingface_model parameter with default value (if not exists)
INSERT OR IGNORE INTO SystemParameters (parameter_name, parameter_value) 
VALUES ('huggingface_model', 'stabilityai/stable-diffusion-xl-base-1.0');

-- Add huggingface_image_size parameter with default value (if not exists)
INSERT OR IGNORE INTO SystemParameters (parameter_name, parameter_value) 
VALUES ('huggingface_image_size', '1024x576');

-- Also add groq_api_key if missing (for diagram generation)
INSERT OR IGNORE INTO SystemParameters (parameter_name, parameter_value) 
VALUES ('groq_api_key', '');
