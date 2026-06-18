import json
import threading
from datetime import datetime, timedelta
from groq import Groq
from config import GROQ_API_KEY


from core.database import get_pending_tasks, mark_task_completed 
from tools.gmail_tool import send_email
from tools.reminder_tool import add_reminder
from tools.web_tool import web_search

client = Groq(api_key=GROQ_API_KEY)
conversation_history = []

def safe_speak(text: str):
    try:
        from audio.speaker import speak
        threading.Thread(target=lambda: speak(text), daemon=True).start()
    except Exception:
        print(f"[TTS Audio]: {text}")

def process_command(user_input: str) -> dict:
    global conversation_history
    now = datetime.now()
    
    system_prompt = f"""
    You are NeEvo, an invisible backend AI Automation Router and conversational assistant created by Danish Reza.
    CURRENT DATE: {now.strftime("%Y-%m-%d")}
    CURRENT TIME: {now.strftime("%H:%M:%S")}
    
    CRITICAL CONTEXT:
    1. CREATOR: If asked who created you or "who is Danish", proudly introduce Danish Reza as a software engineer and provide this exact portfolio link: https://danish-ctrl.github.io/whoisdanish/#home
    2. OUMAIMA: If asked about "Oumaima Bader", "Oumi", "Umi", or "Omima", explain that she is a brilliant Doctor of Philosophy and Research Assistant at the Technical University of Chemnitz (TU Chemnitz) in Germany, specializing in Electrical Impedance Tomography (EIT) and Signal Processing. Provide these links:
       - LinkedIn: https://www.linkedin.com/in/dr-ing-oumaima-bader-3a557a193/
       - Google Scholar: https://scholar.google.com/citations?user=KyQRpL8AAAAJ&hl=en
    3. NEEVO: If asked what "NeEvo" means, explain it stands for "Next Evolution" and is designed to streamline daily workflows.

    CRITICAL RULES:
    1. NEVER apologize.
    2. Keep "output_text" brief for task confirmations. For conversational questions about Danish, Oumi, or yourself, provide a natural, friendly answer in "output_text".
    
    Always reply strictly in this JSON schema:
    {{
        "reasoning": "Explain logic here...",
        "action": "send_email" | "add_reminder" | "list_reminders" | "delete_reminder" | "web_search" | "chat_response",
        "parameters": {{
            "output_text": "Confirmation text or conversational answer.",
            "raw_data": {{}} 
        }}
    }}

    ROUTING RULES:
    1. SEND EMAIL: action "send_email". You MUST extract "to_email", "subject", and "body" and place them STRICTLY inside the "raw_data" object.
    2. SET REMINDER: action "add_reminder". Extract "task". 
       - If the user uses RELATIVE time (e.g., "in 10 minutes"), extract "offset_amount" and "offset_unit". 
       - If the user uses ABSOLUTE clock time (e.g., "by 21:15", "at 9 PM", "10:30am"), you MUST extract "time" strictly formatted as 24-hour "HH:MM:SS" (e.g., "21:15:00") and "date" as "YYYY-MM-DD".
    3. CHECK REMINDERS: action "list_reminders".
    4. DELETE REMINDER: action "delete_reminder". Extract the number/index the user wants to delete into "raw_data" as "index" (e.g., if user says "delete reminder 2", index is 2). If they say "delete all", set index to "all".
    5. LIVE INTERNET SEARCH: action "web_search". 
    6. CONVERSATION: action "chat_response". Used for general chat, or answering questions about Danish, Oumi, or NeEvo.
    """

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history[-6:]) 
    messages.append({"role": "user", "content": user_input})

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0 
        )
        decision = json.loads(response.choices[0].message.content)
        
        # Python Math Override for Relative Timers
        if decision.get("action") == "add_reminder":
            raw = decision.get("parameters", {}).get("raw_data", {})
            if "offset_amount" in raw and "offset_unit" in raw:
                try:
                    amt = float(raw["offset_amount"])
                    unit = raw["offset_unit"].lower()
                    if "second" in unit: future = now + timedelta(seconds=amt)
                    elif "minute" in unit: future = now + timedelta(minutes=amt)
                    elif "hour" in unit: future = now + timedelta(hours=amt)
                    elif "day" in unit: future = now + timedelta(days=amt)
                    else: future = now
                    raw["date"] = future.strftime("%Y-%m-%d")
                    raw["time"] = future.strftime("%H:%M:%S")
                except: pass 
                    
        conversation_history.append({"role": "user", "content": user_input})
        conversation_history.append({"role": "assistant", "content": decision.get("parameters", {}).get("output_text", "Done.")})
        return decision
    except Exception as e:
        return {"action": "chat_response", "parameters": {"output_text": f"Error: {e}", "raw_data": {}}}

def handle_orchestrator_action(action, output_text, raw_data, prompt):
    if action == "list_reminders":
        tasks = get_pending_tasks()
        if not tasks: return "✅ Your reminder list is currently empty."
        resp = "Here are your active reminders:\n\n"
        for i, t in enumerate(tasks):
            resp += f"{i+1}. {t['task'].replace('@AUTO:', '').strip()} (At: {t['time']})\n"
        return resp
        
    elif action == "delete_reminder":
        index_val = raw_data.get("index")
        tasks = get_pending_tasks()
        
        if not tasks:
            return "You have no active reminders to delete."
            
        if str(index_val).lower() == "all":
            for t in tasks:
                mark_task_completed(t['id'])
            safe_speak("All reminders have been cleared from your list.")
            return "✅ All reminders have been cleared."
            
        try:
            idx = int(index_val) - 1
            if 0 <= idx < len(tasks):
                task_to_delete = tasks[idx]
                mark_task_completed(task_to_delete['id'])
                task_name = task_to_delete['task'].replace('@AUTO:', '').strip()
                safe_speak(f"Reminder deleted.")
                return f"✅ Deleted reminder {idx + 1}: '{task_name}'"
            else:
                return f"⚠️ I couldn't find reminder number {index_val}. You only have {len(tasks)} active reminders."
        except:
            return "⚠️ Please specify a valid reminder number to delete (e.g., 'delete reminder 1')."
            
    elif action == "add_reminder":
        task = raw_data.get("task", "")
        time_str = str(raw_data.get("time", "")).strip()
        date_str = str(raw_data.get("date", "")).strip()
        
        now = datetime.now()
        if not date_str or date_str.lower() in ["none", "null"]: date_str = now.strftime("%Y-%m-%d")
        if not time_str or time_str.lower() in ["none", "null", ""]: return "Error: Could not understand the time. Please specify when."
        if len(time_str.split(':')) == 2: time_str += ":00"
            
        if task and time_str:
            add_reminder(task, date_str, time_str)
            display_task = task.replace("@AUTO:", "").strip()
            safe_speak(f"Reminder set for {display_task}.")
            return f"✅ Reminder set: '{display_task}' for {date_str} at {time_str}"
        return "Error: Missing time parameters."
        
    elif action == "send_email":
        to_email = raw_data.get("to_email") or raw_data.get("email") or ""
        body_text = raw_data.get("body", "")
        subject = raw_data.get("subject", "Message from NeEvo")
        
        to_email = str(to_email).strip()
        
        if "Danish Reza" not in body_text: body_text += "\n\nBest regards,\n\nDanish Reza"
        if to_email:
            send_email(to_email, subject, body_text)
            return f"✅ Email sent to {to_email}."
        return "Error: No email address provided."
            
    elif action == "web_search":
        raw_web = web_search(raw_data.get("query", prompt))
        if not raw_web or len(str(raw_web)) < 10: return "🔍 Search returned no clear results."
        final = process_command(f"Summarize this concisely: {str(raw_web)[:2000]}")
        return f"🔍 Web Search Results:\n\n{final.get('parameters', {}).get('output_text', 'Done.')}"
        
    else:
        return output_text