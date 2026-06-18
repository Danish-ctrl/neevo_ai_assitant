import json
import os
from datetime import datetime

def log_expenses(expense_list) -> str:
    """Appends structured expense data to a local JSON tracking file."""
    if not expense_list:
        return "No valid data found to log."
        
    file_path = os.path.join("data", "expenses.json")
    os.makedirs("data", exist_ok=True)
    
    # Read existing file content or initialize an empty list
    existing_data = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception:
            existing_data = []

    # Inject timestamp and add items
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for item in expense_list:
        item["logged_at"] = timestamp
        existing_data.append(item)
        
    # Write back to file
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=4)
        return f"Successfully saved {len(expense_list)} transactions to records."
    except Exception as e:
        return f"Failed to write log file: {str(e)}"