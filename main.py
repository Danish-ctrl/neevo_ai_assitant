import re
import os
import sys
import threading
import webbrowser
import time
import json
import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime
from config import GROQ_API_KEY, GMAIL_APP_PASSWORD

# NeEvo Core Imports
from ai_client import get_ai_response
from core.input_router import detect_intent
from core.memory_engine import (
    start_new_session, set_active_session, save_message, 
    get_memory_context, get_all_sessions, get_session_messages
)
from core.database import get_pending_tasks, mark_task_completed, delete_session_from_db

# AI Hub Tool Imports
from tools.code_scanner import scan_folder
from tools.report_generator import generate_text_report
from tools.file_reader import read_file_preview
from tools.expense_logger import log_expenses
from tools.gmail_tool import send_email
from tools.reminder_tool import add_reminder
from tools.web_tool import web_search

# AI Hub Orchestrator & Audio
from orchestrator import process_command
from audio.speaker import VoiceSpeaker

APP_NAME = "NeEvo ᯤ"
DANISH_URL = "https://danish-ctrl.github.io/whoisdanish/#home"

attached_file_context = None
current_theme = "light"
current_mode = "chat" 
is_audio_muted = False 
sidebar_visible = True

active_generation_id = 0
last_interrupted_response = ""
last_interrupted_index = 0
notified_tasks = set()

speaker = VoiceSpeaker()

# --- UI COMPONENT PLACEHOLDERS ---
root = None; header_frame = None; hamb_btn = None; header_lbl = None
top_mode_lbl = None; sidebar = None; session_listbox = None; main_view = None
chat_text = None; input_frame = None; input_box = None; mute_btn = None

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def theme_palette(name: str) -> dict:
    if name == "dark":
        return {
            "root_bg": "#0f172a", "chat_bg": "#111827", "input_bg": "#0b1220",
            "sidebar_bg": "#1e293b", "sidebar_fg": "#f8fafc",
            "input_field_bg": "#1f2937", "input_fg": "#f9fafb", "muted_fg": "#9ca3af",
            "user_fg": "#34d399", "ai_fg": "#f9fafb", "link_fg": "#60a5fa",
            "button_bg": "#10b981", "button_fg": "#ffffff", "header_fg": "#93c5fd",
            "user_box": "#173b3a", "ai_box": "#263041",
            "select_bg": "#0078D7", "select_fg": "#ffffff", 
        }
    return {
        "root_bg": "#f7f9fc", "chat_bg": "#ffffff", "input_bg": "#eef2f7",
        "sidebar_bg": "#e2e8f0", "sidebar_fg": "#0f172a",
        "input_field_bg": "#ffffff", "input_fg": "#111827", "muted_fg": "#6b7280",
        "user_fg": "#0f766e", "ai_fg": "#111827", "link_fg": "#2563eb",
        "button_bg": "#10b981", "button_fg": "#ffffff", "header_fg": "#4f46e5",
        "user_box": "#e6fffa", "ai_box": "#f3f4f6",
        "select_bg": "#0078D7", "select_fg": "#ffffff", 
    }

theme = theme_palette(current_theme)

def now_time() -> str:
    return datetime.now().strftime("%H:%M")


# --- TEXT SELECTION & CLICKABLE LINK LOGIC ---
def block_typing(event):
    """Allows Ctrl+C, Ctrl+A, and scrolling, but blocks accidental typing."""
    if event.state & 0x0004 and event.keysym.lower() in ['c', 'a']: return None
    if event.keysym in ['Up', 'Down', 'Left', 'Right', 'Prior', 'Next', 'Home', 'End']: return None
    return "break"

def extract_urls(text: str):
    return list(re.finditer(r"https?://[^\s]+", text))

def add_links_to_range(body_start: str, text: str):
    for i, match in enumerate(extract_urls(text)):
        url = match.group(0)
        tag_name = f"link_{body_start}_{i}".replace(".", "_")
        start = chat_text.index(f"{body_start}+{match.start()}c")
        end = chat_text.index(f"{body_start}+{match.end()}c")
        chat_text.tag_add(tag_name, start, end)
        chat_text.tag_configure(tag_name, foreground=theme["link_fg"], underline=1)
        chat_text.tag_bind(tag_name, "<Button-1>", lambda _e, u=url: webbrowser.open(u))
        chat_text.tag_bind(tag_name, "<Enter>", lambda _e: chat_text.config(cursor="hand2"))
        chat_text.tag_bind(tag_name, "<Leave>", lambda _e: chat_text.config(cursor="xterm"))

def copy_chat_selection(event=None):
    try:
        if chat_text.tag_ranges("sel"):
            selected_text = chat_text.get("sel.first", "sel.last")
            root.clipboard_clear()
            root.clipboard_append(selected_text)
    except tk.TclError: pass

def paste_input_content(event=None):
    try:
        clipboard_text = root.clipboard_get()
        input_box.insert(tk.INSERT, clipboard_text)
    except tk.TclError: pass

def show_chat_popup_menu(event):
    chat_menu = tk.Menu(root, tearoff=0)
    chat_menu.add_command(label="Copy Selection", command=copy_chat_selection)
    chat_menu.tk_popup(event.x_root, event.y_root)

def show_input_popup_menu(event):
    input_menu = tk.Menu(root, tearoff=0)
    input_menu.add_command(label="Cut", command=lambda: input_box.event_generate("<<Cut>>"))
    input_menu.add_command(label="Copy", command=lambda: input_box.event_generate("<<Copy>>"))
    input_menu.add_command(label="Paste", command=paste_input_content)
    input_menu.tk_popup(event.x_root, event.y_root)


# --- SIDEBAR TOGGLE & THEME ---
def toggle_sidebar():
    global sidebar_visible
    if sidebar_visible: sidebar.grid_remove()
    else: sidebar.grid(row=1, column=0, sticky="nsew")
    sidebar_visible = not sidebar_visible

def toggle_theme():
    global current_theme, theme
    current_theme = "dark" if current_theme == "light" else "light"
    theme = theme_palette(current_theme)
    root.configure(bg=theme["root_bg"])
    header_frame.configure(bg=theme["root_bg"])
    header_lbl.configure(bg=theme["root_bg"], fg=theme["header_fg"])
    hamb_btn.configure(bg=theme["root_bg"], fg=theme["header_fg"])
    top_mode_lbl.configure(bg=theme["root_bg"], fg=theme["muted_fg"])
    main_view.configure(bg=theme["root_bg"])
    sidebar.configure(bg=theme["sidebar_bg"])
    
    chat_text.configure(bg=theme["chat_bg"], fg=theme["input_fg"], insertbackground=theme["input_fg"], 
                        selectbackground=theme["select_bg"], selectforeground=theme["select_fg"])
    input_box.configure(bg=theme["input_field_bg"], fg=theme["input_fg"], insertbackground=theme["input_fg"], 
                        selectbackground=theme["select_bg"], selectforeground=theme["select_fg"])
    input_frame.configure(bg=theme["input_bg"])
    session_listbox.configure(bg=theme["input_field_bg"], fg=theme["sidebar_fg"])
    configure_chat_tags()

def attach_file():
    global attached_file_context
    file_path = filedialog.askopenfilename(
        title="Attach file for NeEvo ᯤ",
        filetypes=[("All supported files", "*.pdf *.txt *.py *.js *.html *.css *.json *.md *.csv *.log *.xml *.yaml *.yml *.png *.jpg *.jpeg *.webp *.bmp *.gif"),
                   ("All files", "*.*")]
    )
    if not file_path: return
    result = read_file_preview(file_path)
    if not result["success"]:
        append_message("ai", f"⚠️ Could not attach file:\n{result['error']}")
        return
    attached_file_context = result
    append_message("ai", f"📎 File attached:\n{file_path}\n\nAsk me what you want to understand from this file.")

def toggle_audio():
    global is_audio_muted
    is_audio_muted = not is_audio_muted
    status = "Muted 🔇" if is_audio_muted else "Audio On 🔊"
    mute_btn.config(text=status)
    if is_audio_muted:
        speaker.stop_speaking()

def safe_speak(text: str):
    if not is_audio_muted and current_mode == "agent":
        speaker.speak(text)


# --- DATABASE & SIDEBAR LOGIC ---
def load_sidebar_sessions():
    session_listbox.delete(0, tk.END)
    sessions = get_all_sessions()
    for s in sessions:
        display_text = f"[{s['mode'].upper()}] {s['title']} ({s['date'][:10]})"
        session_listbox.insert(tk.END, display_text)
        session_listbox.session_mapping[session_listbox.size() - 1] = s['id']

def on_session_select(event):
    selection = session_listbox.curselection()
    if not selection: return
    session_id = session_listbox.session_mapping[selection[0]]
    set_active_session(session_id)
    chat_text.delete(1.0, tk.END)
    
    # Sync Mode from DB
    from core.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT mode FROM sessions WHERE id = ?", (session_id,))
    mode_result = cursor.fetchone()
    conn.close()
    
    if mode_result:
        global current_mode
        current_mode = mode_result[0]
        mode_lbl.config(text=f"Mode: {current_mode.upper()} {'💬' if current_mode=='chat' else '⚙️'}")
        top_mode_lbl.config(text=f"{current_mode.upper()} {'💬' if current_mode=='chat' else '⚙️'}")
        if current_mode == "agent": mute_btn.grid(row=0, column=3, padx=5)
        else: mute_btn.grid_remove()
    
    messages = get_session_messages(session_id)
    for msg in messages:
        append_message_visuals_only(msg['role'], msg['content'], msg['time'])

def delete_chat(session_id):
    delete_session_from_db(session_id)
    load_sidebar_sessions()
    start_new_ui_session()

def show_context_menu(event):
    selection = session_listbox.nearest(event.y)
    if selection >= 0:
        session_listbox.selection_clear(0, tk.END)
        session_listbox.selection_set(selection)
        session_id = session_listbox.session_mapping[selection]
        menu = tk.Menu(root, tearoff=0)
        menu.add_command(label="Delete Chat ❌", command=lambda: delete_chat(session_id))
        menu.tk_popup(event.x_root, event.y_root)

def start_new_ui_session():
    from core.memory_engine import CURRENT_SESSION_ID
    if CURRENT_SESSION_ID:
        try:
            if len(get_session_messages(CURRENT_SESSION_ID)) == 0: return
        except: pass
        
    start_new_session(title=f"Chat {now_time()}", mode=current_mode)
    chat_text.delete(1.0, tk.END)
    load_sidebar_sessions()
    if current_mode == "agent":
        trigger_agent_greeting()
    else:
        append_message("ai", "Hey 👋 I’m NeEvo. New Chat Session started!")


# --- MODE SWITCHING DYNAMIC LOGIC ---
def switch_to_chat_mode():
    global current_mode
    current_mode = "chat"
    mode_lbl.config(text="Mode: CHAT 💬")
    top_mode_lbl.config(text="CHAT 💬")
    mute_btn.grid_remove() 
    start_new_ui_session()

def switch_to_agent_mode():
    global current_mode
    current_mode = "agent"
    mode_lbl.config(text="Mode: AGENT ⚙️")
    top_mode_lbl.config(text="AGENT ⚙️")
    mute_btn.grid(row=0, column=3, padx=5) 
    start_new_ui_session()

def trigger_agent_greeting():
    tasks = get_pending_tasks()
    greeting = "Hi Danish! I am in Agent Execution Mode.\n\n"
    if tasks:
        greeting += f"You currently have {len(tasks)} unfinished task(s):\n"
        for i, t in enumerate(tasks):
            display = t['task'].replace('@AUTO:', '[Scheduled Action]').strip()
            greeting += f"{i+1}. {display}\n"
    else:
        greeting += "Your task list is completely clear right now! 🚀\n"
    greeting += "\nWhat do you want me to do?"
    append_message("ai", greeting)


# --- VISUAL RENDERING ---
def append_message_visuals_only(role: str, text: str, timestamp: str):
    start_index = chat_text.index("end-1c")
    who = "You" if role == "user" else APP_NAME
    block = f"{who}\n{text}\n{timestamp}\n\n"
    chat_text.insert("end", block)

    who_tag = "user_name" if role == "user" else "ai_name"
    body_tag = "user_body" if role == "user" else "ai_body"
    time_tag = "user_time" if role == "user" else "ai_time"

    who_start = start_index
    who_end = chat_text.index(f"{who_start}+{len(who)}c")
    body_start = chat_text.index(f"{who_end}+1c")
    body_end = chat_text.index(f"{body_start}+{len(text)}c")
    time_start = chat_text.index(f"{body_end}+1c")
    time_end = chat_text.index(f"{time_start}+{len(timestamp)}c")

    chat_text.tag_add(who_tag, who_start, who_end)
    chat_text.tag_add(body_tag, body_start, body_end)
    chat_text.tag_add(time_tag, time_start, time_end)
    
    # Automatically scan for and style hyperlinks
    add_links_to_range(body_start, text)
    chat_text.see("end")

def append_message(role: str, text: str, save=True):
    display_text = text.replace("@AUTO:", "").strip()
    append_message_visuals_only(role, display_text, now_time())
    if save: save_message(role, text)

def mark_done(task_id, btn):
    mark_task_completed(task_id)
    btn.config(text="✅ Completed", state="disabled", bg=theme["muted_fg"], cursor="arrow")

def append_interactive_reminder(task_id, task_text):
    start_index = chat_text.index("end-1c")
    chat_text.insert("end", f"{APP_NAME}\n⏰ REMINDER: {task_text}\n")
    
    btn = tk.Button(chat_text, text="✅ Mark as Done", bg=theme["button_bg"], fg="white", 
                    relief="flat", cursor="hand2", padx=10, pady=2, font=("Segoe UI", 9, "bold"))
    btn.config(command=lambda b=btn, tid=task_id: mark_done(tid, b))
    chat_text.window_create("end", window=btn)
    
    timestamp = now_time()
    chat_text.insert("end", f"\n{timestamp}\n\n")
    chat_text.tag_add("ai_name", start_index, chat_text.index(f"{start_index}+{len(APP_NAME)}c"))
    chat_text.see("end")

def append_thinking():
    start = chat_text.index("end-1c")
    text = f"{APP_NAME}\n{APP_NAME} is thinking...\n\n"
    chat_text.insert("end", text)
    chat_text.tag_add("ai_name", start, chat_text.index(f"{start}+{len(APP_NAME)}c"))
    chat_text.see("end")
    return start

def stream_message(role: str, text: str, generation_id: int):
    text = text.replace("@AUTO:", "").strip()
    who = "You" if role == "user" else APP_NAME
    who_tag = "user_name" if role == "user" else "ai_name"
    body_tag = "user_body" if role == "user" else "ai_body"

    start_index = chat_text.index("end-1c")
    chat_text.insert("end", f"{who}\n")
    chat_text.tag_add(who_tag, start_index, chat_text.index(f"{start_index}+{len(who)}c"))
    body_start = chat_text.index("end-1c")

    def step(i=0):
        if generation_id != active_generation_id: return
        if i < len(text):
            chat_text.insert("end", text[i])
            chat_text.tag_add(body_tag, body_start, "end-1c")
            chat_text.see("end")
            root.after(7, lambda: step(i + 1))
        else:
            timestamp = now_time()
            chat_text.insert("end", f"\n{timestamp}\n\n")
            chat_text.tag_add(body_tag, body_start, chat_text.index(f"end-1c - {len(timestamp)+2}c"))
            
            # Ensure links are applied cleanly once the stream finishes
            add_links_to_range(body_start, text)
            chat_text.see("end")
            save_message("assistant", text)
    step()

def replace_thinking_with_stream(start_index: str, final_text: str, generation_id: int):
    chat_text.delete(start_index, "end-1c")
    stream_message("ai", final_text, generation_id)


# --- MAIN EXECUTION ---
def send_message():
    prompt = input_box.get("1.0", "end-1c").strip()
    if not prompt: return

    global attached_file_context
    speaker.stop_speaking()
    global active_generation_id
    active_generation_id += 1
    gen_id = active_generation_id

    append_message("user", prompt)
    input_box.delete("1.0", "end")
    thinking_start = append_thinking()

    def work():
        try:
            if current_mode == "agent":
                decision = process_command(prompt)
                
                # We need to import this safely here so orchestrator triggers work correctly
                from orchestrator import handle_orchestrator_action
                response = handle_orchestrator_action(
                    decision.get("action"), 
                    decision.get("parameters", {}).get("output_text", ""), 
                    decision.get("parameters", {}).get("raw_data", {}), 
                    prompt
                )
            else:
                # Custom AI Identity Logic for standard Chat Mode
                system_prompt = (
                    f"You are {APP_NAME}, a highly capable AI engineering assistant. "
                    "PERSONALITY: Act like a natural, conversational, and highly energetic human coworker! "
                    "CRITICAL CONTEXT 1: You were created by Danish Reza, a software engineer. "
                    "If asked who created you, proudly introduce him and provide this exact portfolio link: https://danish-ctrl.github.io/whoisdanish/#home \n"
                    "CRITICAL CONTEXT 2: If the user asks about 'Oumaima Bader', 'Oumi', 'Umi', 'Omima', or any variation of that name, "
                    "explain that she is a brilliant Doctor of Philosophy and Research Assistant at the Technical University of Chemnitz (TU Chemnitz) in Germany, specializing in Electrical Impedance Tomography (EIT) and Signal Processing. "
                    "Provide these links: LinkedIn: https://www.linkedin.com/in/dr-ing-oumaima-bader-3a557a193/ | Google Scholar: https://scholar.google.com/citations?user=KyQRpL8AAAAJ&hl=en \n"
                    "CRITICAL CONTEXT 3: If asked what 'NeEvo' stands for, explain it stands for 'Next Evolution'. "
                    f"ADDITIONAL CONTEXT: {get_memory_context()}"
                )
                
                messages = [{"role": "system", "content": system_prompt}]
                if attached_file_context:
                    messages.append({"role": "system", "content": f"Attached File:\n{attached_file_context['content']}"})
                messages.append({"role": "user", "content": prompt})
                response = get_ai_response(messages)

        except Exception as e:
            response = f"⚠️ System Error: {e}"

        if gen_id == active_generation_id:
            root.after(0, lambda: replace_thinking_with_stream(thinking_start, response, gen_id))

    threading.Thread(target=work, daemon=True).start()

def alarm_clock_loop():
    while True:
        time.sleep(2)
        try:
            tasks = get_pending_tasks()
        except Exception:
            continue
            
        now = datetime.now()
        
        for t in tasks:
            task_id = t['id']
            if task_id in notified_tasks: 
                continue 
                
            try:
                # --- CRASH FIX: Force date and time to combine perfectly ---
                time_str = str(t.get('time', '')).strip()
                date_str = str(t.get('date', now.strftime("%Y-%m-%d"))).strip()
                
                if len(time_str.split(':')) == 2: 
                    time_str += ":00"
                
                # If time_str somehow already contains a date, handle it gracefully
                if "-" in time_str:
                    trigger_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                else:
                    # Combine date and time to prevent strptime ValueError crash
                    trigger_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
                
                if now >= trigger_time:
                    notified_tasks.add(task_id)
                    task_text = t['task']
                    
                    if task_text.startswith("@AUTO:"):
                        actual = task_text.replace("@AUTO:", "").strip()
                        mark_task_completed(task_id) 
                        def run_auto_script():
                            from orchestrator import process_command, handle_orchestrator_action
                            res = process_command(actual)
                            handle_orchestrator_action(
                                res.get("action"), 
                                res.get("parameters", {}).get("output_text", ""), 
                                res.get("parameters", {}).get("raw_data", {}), 
                                actual
                            )
                        threading.Thread(target=run_auto_script, daemon=True).start()
                    else:
                        display_name = task_text.replace("@AUTO:", "").strip()
                        root.after(0, lambda tid=task_id, txt=display_name: append_interactive_reminder(tid, txt))
                        safe_speak(f"Attention, it is time for your reminder: {display_name}")
            except Exception as e:
                print(f"Daemon Check Exception for task {task_id}: {e}")
                
                # --- AUTO-HEALING FIX: Use the working 'complete' function to hide it forever! ---
                from core.database import mark_task_completed
                mark_task_completed(task_id)
                print(f"✅ Auto-healed corrupted task {task_id} by marking it complete. It will no longer loop.")
                continue

# --- UI SETUP ---
def configure_chat_tags(): 
    chat_text.tag_configure("user_name", foreground=theme["user_fg"], justify="right", background=theme["user_box"])
    chat_text.tag_configure("user_body", foreground=theme["input_fg"], justify="right", background=theme["user_box"])
    chat_text.tag_configure("ai_name", foreground=theme["link_fg"], justify="left", background=theme["ai_box"])
    chat_text.tag_configure("ai_body", foreground=theme["ai_fg"], justify="left", background=theme["ai_box"])

root = tk.Tk()
root.title(APP_NAME)
root.geometry("1000x700")
root.configure(bg=theme["root_bg"])

root.columnconfigure(1, weight=1)
root.rowconfigure(1, weight=1)

# HEADER ROW
header_frame = tk.Frame(root, bg=theme["root_bg"])
header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 0))

hamb_btn = tk.Button(header_frame, text=" ≡ ", font=("Segoe UI", 16, "bold"), command=toggle_sidebar, bg=theme["root_bg"], fg=theme["header_fg"], relief="flat")
hamb_btn.pack(side="left")

header_lbl = tk.Label(header_frame, text=APP_NAME, font=("Segoe UI", 16, "bold"), bg=theme["root_bg"], fg=theme["header_fg"])
header_lbl.pack(side="left", padx=10)

theme_btn = tk.Button(header_frame, text="🌙/☀️", command=toggle_theme, bg=theme["input_field_bg"], fg=theme["input_fg"], relief="flat", padx=10)
theme_btn.pack(side="right")

top_mode_lbl = tk.Label(header_frame, text="CHAT 💬", bg=theme["root_bg"], fg=theme["muted_fg"], font=("Segoe UI", 10, "bold"))
top_mode_lbl.pack(side="right", padx=15)

# SIDEBAR COLUMN
sidebar = tk.Frame(root, bg=theme["sidebar_bg"], width=250)
sidebar.grid(row=1, column=0, sticky="nsew")
sidebar.grid_propagate(False)

new_chat_btn = tk.Button(sidebar, text="➕ New Session", command=start_new_ui_session, bg=theme["button_bg"], fg="white", relief="flat")
new_chat_btn.pack(fill="x", padx=20, pady=20)

mode_lbl = tk.Label(sidebar, text="Mode: CHAT 💬", bg=theme["sidebar_bg"], fg=theme["sidebar_fg"], font=("Segoe UI", 10, "bold"))
mode_lbl.pack(pady=5)
btn_frame = tk.Frame(sidebar, bg=theme["sidebar_bg"])
btn_frame.pack(fill="x", padx=20, pady=5)
tk.Button(btn_frame, text="Chat", command=switch_to_chat_mode, width=10).pack(side="left", padx=5)
tk.Button(btn_frame, text="Agent", command=switch_to_agent_mode, width=10).pack(side="right", padx=5)

tk.Label(sidebar, text="History (Right-click to Delete)", bg=theme["sidebar_bg"], fg=theme["muted_fg"]).pack(pady=(20, 5))
session_listbox = tk.Listbox(sidebar, bg=theme["input_field_bg"], fg=theme["sidebar_fg"], relief="flat", highlightthickness=0)
session_listbox.pack(fill="both", expand=True, padx=10, pady=10)
session_listbox.session_mapping = {}
session_listbox.bind("<<ListboxSelect>>", on_session_select)
session_listbox.bind("<Button-3>", show_context_menu) 

# MAIN VIEW COLUMN
main_view = tk.Frame(root, bg=theme["root_bg"])
main_view.grid(row=1, column=1, sticky="nsew")
main_view.rowconfigure(0, weight=1)
main_view.columnconfigure(0, weight=1)

chat_text = tk.Text(main_view, bg=theme["chat_bg"], fg=theme["input_fg"], wrap="word", relief="flat", bd=0, padx=15, pady=15, font=("Segoe UI", 11))
chat_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
configure_chat_tags()

# Bindings to block typing but allow Selection & Copying
chat_text.bind("<Key>", block_typing)
chat_text.bind("<Button-3>", show_chat_popup_menu)
chat_text.bind("<Control-c>", copy_chat_selection)
chat_text.bind("<Control-C>", copy_chat_selection)

input_frame = tk.Frame(main_view, bg=theme["input_bg"])
input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
input_frame.columnconfigure(0, weight=1)

input_box = tk.Text(input_frame, height=3, bg=theme["input_field_bg"], fg=theme["input_fg"], wrap="word", relief="flat", font=("Segoe UI", 11), padx=10, pady=8)
input_box.grid(row=0, column=0, sticky="ew", padx=(0, 8))
input_box.bind("<Return>", lambda e: [send_message(), "break"][1])
input_box.bind("<Button-3>", show_input_popup_menu)
input_box.bind("<Control-v>", paste_input_content)

attach_btn = tk.Button(input_frame, text="📎 Attach", command=attach_file, bg=theme["input_field_bg"], fg=theme["input_fg"], relief="flat", padx=10, pady=8)
attach_btn.grid(row=0, column=1, padx=5)

tk.Button(input_frame, text="Send 🚀", command=send_message, bg=theme["button_bg"], fg="white", relief="flat", padx=15, pady=8).grid(row=0, column=2)

mute_btn = tk.Button(input_frame, text="Audio On 🔊", command=toggle_audio, bg="#ef4444", fg="white", relief="flat", padx=10, pady=8)

threading.Thread(target=alarm_clock_loop, daemon=True).start()

# --- SMART STARTUP LOGIC ---
load_sidebar_sessions()

if session_listbox.size() > 0:
    # If history exists, virtually "click" the most recent session to load it
    session_listbox.selection_set(0)
    on_session_select(None)
else:
    # Only create a new session if the database is completely empty
    switch_to_chat_mode() 

root.mainloop()