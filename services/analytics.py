"""
A simple analytics service.
For now, it just prints events to the console.
This can be expanded to send data to a real analytics service.
"""

def track_event(user_id: str, event_name: str, properties: dict = None):
    """
    Tracks an event with a user ID and optional properties.
    """
    if properties is None:
        properties = {}
    
    print(f"[ANALYTICS] User '{user_id}' triggered event '{event_name}' with properties: {properties}")

