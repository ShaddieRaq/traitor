"""
Temperature calculation utilities for bot scoring.
"""

def calculate_bot_temperature(combined_score: float) -> str:
    """
    Calculate bot temperature based on combined signal score.
    
    Temperature levels (TESTING MODE - Very Sensitive):
    - Hot 🔥: Strong signal (score > 0.08 or < -0.08)
    - Warm 🌡️: Moderate signal (score > 0.03 or < -0.03)  
    - Cool ❄️: Weak signal (score > 0.005 or < -0.005)
    - Frozen 🧊: Very minimal activity (score between -0.005 and 0.005)
    
    NOTE: These are sensitive testing thresholds. For production, consider:
    - Hot: >= 0.3, Warm: >= 0.15, Cool: >= 0.05, Frozen: < 0.05
    
    Args:
        combined_score: Bot's combined signal score (-1.0 to 1.0)
        
    Returns:
        Temperature string: "HOT", "WARM", "COOL", or "FROZEN"
    """
    abs_score = abs(combined_score)
    
    if abs_score >= 0.08:
        return "HOT"
    elif abs_score >= 0.03:
        return "WARM"
    elif abs_score >= 0.005:
        return "COOL"
    else:
        return "FROZEN"


def calculate_bot_temperature_production(combined_score: float) -> str:
    """
    Production temperature calculation with conservative thresholds.
    
    Temperature levels (PRODUCTION MODE - Conservative):
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
