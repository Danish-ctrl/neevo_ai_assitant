def detect_intent(user_message: str) -> dict:
    message = user_message.lower().strip()

    if "who is danish" in message:
        return {"intent": "personal_link"}

    scan_keywords = [
        "scan folder",
        "scan project",
        "scan code",
        "review code",
        "check security",
        "find secrets",
        "code safety",
    ]

    if any(keyword in message for keyword in scan_keywords):
        return {
            "intent": "code_scan",
            "folder_path": extract_folder_path(user_message),
        }

    return {"intent": "chat"}


def extract_folder_path(user_message: str) -> str:
    lowered = user_message.lower()

    for phrase in ["scan folder", "scan project", "scan code"]:
        if phrase in lowered:
            index = lowered.find(phrase)
            folder = user_message[index + len(phrase):].strip()
            return folder if folder else "sample_project"

    return "sample_project"