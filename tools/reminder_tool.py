import os
from datetime import datetime
from core.database import add_task_to_db

def add_reminder(task: str, date: str, time_str: str) -> str:
    """Saves a high-precision reminder to the SQLite database."""
    try:
        # Failsafe for missing seconds
        if time_str.count(':') == 1:
            time_str += ":00"
            
        trigger_time_str = f"{date} {time_str}"
        
        # Send it directly to our new Database!
        add_task_to_db(task, trigger_time_str)
        
        return f"Success: Reminder '{task}' has been saved for {trigger_time_str}."
    except Exception as e:
        return f"Error: Could not save reminder. {e}"