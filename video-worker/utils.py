"""
Utility functions for VibeRender Video Worker.
"""


def mask_api_key(key: str, show_chars: int = 4) -> str:
    """
    Mask an API key for safe logging.
    Shows first and last N characters with asterisks in between.
    
    Args:
        key: The API key to mask
        show_chars: Number of characters to show at start and end
        
    Returns:
        Masked API key string
    """
    if not key or len(key) <= show_chars * 2:
        return '*' * len(key) if key else 'None'
    
    return f'{key[:show_chars]}...{key[-show_chars:]}'

