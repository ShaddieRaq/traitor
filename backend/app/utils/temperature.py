"""
Temperature calculation utilities for bot scoring.
"""

def calculate_bot_temperature(combined_score: float) -> str:
    """
    Calculate bot temperature based on combined signal score.
    
    Temperature levels:
    - Hot 🔥: Very close to trading (score > 0.3 or < -0.3)
    - Warm 🌡️: Moderately close (score > 0.15 or < -0.15)  
    - Cool ❄️: Some interest (score > 0.05 or < -0.05)
    - Frozen 🧊: No trading interest (score between -0.05 and 0.05)
    
    Args:
        combined_score: Bot's combined signal score (-1.0 to 1.0)
        
    Returns:
        Temperature string: "HOT", "WARM", "COOL", or "FROZEN"
    """
    abs_score = abs(combined_score)
    
    if abs_score >= 0.3:
        return "HOT"
    elif abs_score >= 0.15:
        return "WARM"
    elif abs_score >= 0.05:
        return "COOL"
    else:
        return "FROZEN"


def get_temperature_emoji(temperature: str) -> str:
    """
    Get emoji for temperature level.
    
    Args:
        temperature: Temperature string ("HOT", "WARM", "COOL", "FROZEN")
        
    Returns:
        Corresponding emoji
    """
    emoji_map = {
        "HOT": "🔥",
        "WARM": "🌡️", 
        "COOL": "❄️",
        "FROZEN": "🧊"
    }
    return emoji_map.get(temperature, "⚪")
