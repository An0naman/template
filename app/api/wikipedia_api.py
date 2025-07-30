# app/api/wikipedia_api.py

from flask import Blueprint, jsonify, current_app
import requests
from urllib.parse import quote

wikipedia_api_bp = Blueprint('wikipedia_api', __name__)

@wikipedia_api_bp.route('/wikipedia/search/<string:query>', methods=['GET'])
def wikipedia_search(query):
    """Search Wikipedia and return article summary"""
    try:
        # First, search for the article to get the exact title
        search_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + quote(query)
        
        # Set a proper User-Agent header as required by Wikipedia API
        headers = {
            'User-Agent': 'YourAppName/1.0 (https://your-domain.com; your-email@domain.com)'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract relevant information
            result = {
                'title': data.get('title', ''),
                'extract': data.get('extract', ''),
                'description': data.get('description', ''),
                'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                'thumbnail': data.get('thumbnail', {}).get('source', '') if data.get('thumbnail') else '',
                'found': True
            }
            
            return jsonify(result)
        
        elif response.status_code == 404:
            # Try a search query if direct lookup fails
            search_api_url = "https://en.wikipedia.org/api/rest_v1/page/search/" + quote(query)
            search_response = requests.get(search_api_url, headers=headers, timeout=10)
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                pages = search_data.get('pages', [])
                
                if pages:
                    # Get the first search result
                    first_result = pages[0]
                    
                    result = {
                        'title': first_result.get('title', ''),
                        'extract': first_result.get('excerpt', ''),
                        'description': first_result.get('description', ''),
                        'url': f"https://en.wikipedia.org/wiki/{quote(first_result.get('key', ''))}",
                        'thumbnail': first_result.get('thumbnail', {}).get('url', '') if first_result.get('thumbnail') else '',
                        'found': True,
                        'search_result': True
                    }
                    
                    return jsonify(result)
            
            return jsonify({
                'found': False,
                'message': f'No Wikipedia article found for "{query}"'
            })
        
        else:
            return jsonify({
                'found': False,
                'message': f'Wikipedia API error: {response.status_code}'
            }), response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({
            'found': False,
            'message': 'Wikipedia request timed out'
        }), 408
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Wikipedia API error: {e}", exc_info=True)
        return jsonify({
            'found': False,
            'message': 'Failed to connect to Wikipedia API'
        }), 500
        
    except Exception as e:
        current_app.logger.error(f"Unexpected error in Wikipedia search: {e}", exc_info=True)
        return jsonify({
            'found': False,
            'message': 'An unexpected error occurred'
        }), 500
