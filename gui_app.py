import re
import os
import sys
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime
from config import GROQ_API_KEY, GMAIL_APP_PASSWORD

from ai_client import get_ai_response
from core.input_router import detect_intent
from core.memory_engine import save_message, get_memory_context
from tools.code_scanner import scan_folder
from tools.report_generator import generate_text_report
from tools.file_reader import read_file_preview

APP_NAME = "NeEvo ᯤ"
DANISH_URL = "https://danish-ctrl.github.io/whoisdanish/#home"

chat_history = []
attached_file_context = None
current_theme = "light"

active_generation_id = 0
last_interrupted_response = ""
last_interrupted_index = 0

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def theme_palette(name: str) -> dict:
    if name == "dark":
        return {
            "root_bg": "#0f172a", "chat_bg": "#111827", "input_bg": "#0b1220",
            "input_field_bg": "#1f2937", "input_fg": "#f9fafb", "muted_fg": "#9ca3af",
            "user_fg": "#34d399", "ai_fg": "#f9fafb", "link_fg": "#60a5fa",
            "button_bg": "#10b981", "button_fg": "#ffffff", "header_fg": "#93c5fd",
            "user_box": "#173b3a", "ai_box": "#263041",
            "select_bg": "#0078D7", "select_fg": "#ffffff", 
        }
    return {
        "root_bg": "#f7f9fc", "chat_bg": "#ffffff", "input_bg": "#eef2f7",
        "input_field_bg": "#ffffff", "input_fg": "#111827", "muted_fg": "#6b7280",
        "user_fg": "#0f766e", "ai_fg": "#111827", "link_fg": "#2563eb",
        "button_bg": "#10b981", "button_fg": "#ffffff", "header_fg": "#4f46e5",
        "user_box": "#e6fffa", "ai_box": "#f3f4f6",
        "select_bg": "#0078D7", "select_fg": "#ffffff", 
    }

theme = theme_palette(current_theme)

def now_time() -> str:
    return datetime.now().strftime("%H:%M")

def extract_urls(text: str):
    return list(re.finditer(r"https?://[^\s]+", text))

def configure_chat_tags():
    chat_text.tag_configure("user_name", foreground=theme["user_fg"], font=("Segoe UI", 9, "bold"),
                            lmargin1=360, lmargin2=360, rmargin=18, justify="right", spacing1=8, background=theme["user_box"])
    chat_text.tag_configure("user_body", foreground=theme["input_fg"], font=("Segoe UI", 10),
                            lmargin1=360, lmargin2=360, rmargin=18, justify="right", background=theme["user_box"])
    chat_text.tag_configure("user_time", foreground=theme["muted_fg"], font=("Segoe UI", 8),
                            lmargin1=360, lmargin2=360, rmargin=18, justify="right", spacing3=10, background=theme["user_box"])

    chat_text.tag_configure("ai_name", foreground=theme["link_fg"], font=("Segoe UI", 9, "bold"),
                            lmargin1=18, lmargin2=18, rmargin=360, justify="left", spacing1=8, background=theme["ai_box"])
    chat_text.tag_configure("ai_body", foreground=theme["ai_fg"], font=("Segoe UI", 10),
                            lmargin1=18, lmargin2=18, rmargin=360, justify="left", background=theme["ai_box"])
    chat_text.tag_configure("ai_time", foreground=theme["muted_fg"], font=("Segoe UI", 8),
                            lmargin1=18, lmargin2=18, rmargin=360, justify="left", spacing3=10, background=theme["ai_box"])
    chat_text.tag_configure("thinking", foreground=theme["muted_fg"], font=("Segoe UI", 10, "italic"),
                            lmargin1=18, lmargin2=18, rmargin=360, justify="left", spacing3=10, background=theme["ai_box"])

    chat_text.tag_configure("sel", background=theme["select_bg"], foreground=theme["select_fg"])
    chat_text.tag_raise("sel")

def apply_window_responsive_tags(event=None):
    width = max(root.winfo_width(), 720)
    side_margin = int(width * 0.38)
    for tag in ["user_name", "user_body", "user_time"]:
        chat_text.tag_configure(tag, lmargin1=side_margin, lmargin2=side_margin, rmargin=18)
    for tag in ["ai_name", "ai_body", "ai_time", "thinking"]:
        chat_text.tag_configure(tag, lmargin1=18, lmargin2=18, rmargin=side_margin)

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

def append_message(role: str, text: str, save=True):
    start_index = chat_text.index("end-1c")
    who = "You" if role == "user" else APP_NAME
    timestamp = now_time()
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
    add_links_to_range(body_start, text)
    chat_text.see("end")

    if save:
        role_name = "user" if role == "user" else "assistant"
        chat_history.append({"role": role_name, "content": text})
        save_message(role_name, text)

def append_thinking():
    start = chat_text.index("end-1c")
    text = f"{APP_NAME}\n{APP_NAME} is thinking...\n\n"
    chat_text.insert("end", text)
    who_end = chat_text.index(f"{start}+{len(APP_NAME)}c")
    body_start = chat_text.index(f"{who_end}+1c")
    body_end = chat_text.index(f"{body_start}+{len(APP_NAME + ' is thinking...')}c")
    chat_text.tag_add("ai_name", start, who_end)
    chat_text.tag_add("thinking", body_start, body_end)
    chat_text.see("end")
    return start

def replace_thinking_with_stream(start_index: str, final_text: str, generation_id: int):
    chat_text.delete(start_index, "end-1c")
    stream_message("ai", final_text, generation_id)

def stream_message(role: str, text: str, generation_id: int):
    global last_interrupted_response, last_interrupted_index
    who = "You" if role == "user" else APP_NAME
    who_tag = "user_name" if role == "user" else "ai_name"
    body_tag = "user_body" if role == "user" else "ai_body"
    time_tag = "user_time" if role == "user" else "ai_time"

    start_index = chat_text.index("end-1c")
    chat_text.insert("end", f"{who}\n")
    who_end = chat_text.index(f"{start_index}+{len(who)}c")
    chat_text.tag_add(who_tag, start_index, who_end)

    body_start = chat_text.index("end-1c")

    def step(i=0):
        global last_interrupted_response, last_interrupted_index
        if generation_id != active_generation_id:
            last_interrupted_response = text
            last_interrupted_index = i
            chat_text.insert("end", "\n[Response stopped]\n\n")
            return

        if i < len(text):
            chat_text.insert("end", text[i])
            chat_text.tag_add(body_tag, body_start, "end-1c")
            chat_text.see("end")
            root.after(7, lambda: step(i + 1))
        else:
            timestamp = now_time()
            chat_text.insert("end", f"\n{timestamp}\n\n")

            body_end = chat_text.index(f"end-1c - {len(timestamp)+2}c")
            time_start = chat_text.index(f"{body_end}+1c")
            time_end = chat_text.index(f"{time_start}+{len(timestamp)}c")

            chat_text.tag_add(body_tag, body_start, body_end)
            chat_text.tag_add(time_tag, time_start, time_end)
            add_links_to_range(body_start, text)
            chat_text.see("end")

            chat_history.append({"role": "assistant", "content": text})
            save_message("assistant", text)
            last_interrupted_response = ""
            last_interrupted_index = 0
    step()

def export_chat():
    path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text file", "*.txt")])
    if not path: return
    with open(path, "w", encoding="utf-8") as f:
        for item in chat_history:
            who = "You" if item["role"] == "user" else APP_NAME
            f.write(f"{who}: {item['content']}\n\n")

def build_scan_response(folder_path: str) -> str:
    findings = scan_folder(folder_path)
    report_path = generate_text_report(findings)
    if not findings:
        return f"✅ Scan complete.\nNo risky patterns found.\n\nReport saved at:\n{report_path}"
    response = f"🔍 Scan complete.\nFound {len(findings)} risky pattern(s).\n\n"
    for finding in findings[:5]:
        category = finding.get("category", "GENERAL")
        response += (f"• [{finding['severity']}] [{category}] {finding['rule']}\n"
                     f"  File: {finding['file']}\n  Line: {finding['line']}\n"
                     f"  Code: {finding['snippet']}\n\n")
    response += f"Full report saved at:\n{report_path}"
    return response

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

def is_continue_prompt(prompt: str) -> bool:
    return prompt.lower().strip() in ["continue", "continue please", "go on", "keep going"]

def continue_interrupted_response():
    global active_generation_id
    if not last_interrupted_response:
        append_message("ai", "There is no stopped response to continue.")
        return
    active_generation_id += 1
    new_id = active_generation_id
    remaining = last_interrupted_response[last_interrupted_index:]
    stream_message("ai", remaining, new_id)

def send_message():
    global attached_file_context, active_generation_id
    prompt = input_box.get("1.0", "end-1c").strip()
    if not prompt: return

    active_generation_id += 1
    generation_id = active_generation_id

    append_message("user", prompt)
    input_box.delete("1.0", "end")

    if is_continue_prompt(prompt):
        continue_interrupted_response()
        return

    thinking_start = append_thinking()

    def work():
        messages = [
            {"role": "system", "content": (
                f"You are {APP_NAME}, a highly capable AI engineering assistant. "
                "PERSONALITY: Act like a natural, conversational, and highly energetic human coworker! "
                "Use a variety of fun emojis (🚀, ✨, 💡, 🙌, etc.) to make your responses colorful, engaging, and friendly.\n"
                "STRICT RULE: NEVER output a bulleted list of your features or capabilities unless the user explicitly asks 'what can you do?'. If the user just says 'hi', respond warmly and genuinely without listing features.\n"
                "CRITICAL CONTEXT 1: You were created by Danish Reza, a software engineer. "
                "If asked who created you, proudly introduce him and provide this exact portfolio link: https://danish-ctrl.github.io/whoisdanish/#home \n"
                "CRITICAL CONTEXT 2: If the user asks about 'Oumaima Bader', 'Oumi', 'Umi', 'Omima', or any variation of that name, "
                "you MUST explain that she is a brilliant Doctor of Philosophy and Research Assistant at the Technical University of Chemnitz (TU Chemnitz) in Germany, specializing in Electrical Impedance Tomography (EIT) and Signal Processing. "
                "You MUST provide these two links so the user can learn more about her: \n"
                "LinkedIn: https://www.linkedin.com/in/dr-ing-oumaima-bader-3a557a193/ \n"
                "Google Scholar: https://scholar.google.com/citations?user=KyQRpL8AAAAJ&hl=en \n"
                "CRITICAL CONTEXT 3: If the user asks what 'NeEvo' (or 'NeEvo') means or stands for, explain that it stands for 'Next Evolution'. "
                "Briefly explain that the app is designed as the next step in smart personal assistance—built to help users chat seamlessly, analyze files, and streamline their daily workflows."
            )},
            {"role": "system", "content": get_memory_context()}
        ]
        
        for item in chat_history[:-1][-10:]: 
            messages.append(item)
            
        try:
            route = detect_intent(prompt)
            if route["intent"] == "personal_link":
                response = f"Danish Reza? 👀 Here you go:\n{DANISH_URL}"
            elif route["intent"] == "code_scan":
                folder_path = route.get("folder_path", "sample_project")
                response = build_scan_response(folder_path)
            else:
                if attached_file_context:
                    messages.append({"role": "system", "content": ("Attached file context:\n" f"File path: {attached_file_context['file_path']}\n" f"File type: {attached_file_context.get('type', 'unknown')}\n\n" f"Content preview:\n{attached_file_context['content']}")})
                
                messages.append({"role": "user", "content": prompt})
                response = get_ai_response(messages)
        except Exception as e:
            response = f"⚠️ {APP_NAME} is busy right now or something went wrong. Try again in a moment."
            print("AI Error:", e)

        if generation_id == active_generation_id:
            root.after(0, lambda: finish_response(thinking_start, response, generation_id))

    threading.Thread(target=work, daemon=True).start()

def finish_response(thinking_start: str, response: str, generation_id: int):
    replace_thinking_with_stream(thinking_start, response, generation_id)

def toggle_theme():
    global current_theme, theme
    current_theme = "dark" if current_theme == "light" else "light"
    theme = theme_palette(current_theme)
    root.configure(bg=theme["root_bg"])
    header.configure(bg=theme["root_bg"], fg=theme["header_fg"])
    main_frame.configure(bg=theme["root_bg"])
    
    chat_text.configure(bg=theme["chat_bg"], fg=theme["input_fg"], insertbackground=theme["input_fg"], 
                        selectbackground=theme["select_bg"], selectforeground=theme["select_fg"])
    input_box.configure(bg=theme["input_field_bg"], fg=theme["input_fg"], insertbackground=theme["input_fg"], 
                        selectbackground=theme["select_bg"], selectforeground=theme["select_fg"])
    
    input_frame.configure(bg=theme["input_bg"])
    attach_btn.configure(bg=theme["input_field_bg"], fg=theme["input_fg"])
    send_btn.configure(bg=theme["button_bg"], fg=theme["button_fg"])
    export_btn.configure(bg=theme["input_field_bg"], fg=theme["input_fg"])
    theme_btn.configure(bg=theme["input_field_bg"], fg=theme["input_fg"])
    configure_chat_tags()
    apply_window_responsive_tags()

def copy_selected_chat_text(event=None):
    try:
        if chat_text.tag_ranges("sel"):
            selected = chat_text.get("sel.first", "sel.last")
            root.clipboard_clear()
            root.clipboard_append(selected)
    except tk.TclError:
        pass

def read_only_text(event):
    if event.state & 0x0004 and event.keysym.lower() in ['c', 'a']:
        return None
    if event.keysym in ['Up', 'Down', 'Left', 'Right', 'Prior', 'Next', 'Home', 'End']:
        return None
    return "break"

# ---------- UI ----------
root = tk.Tk()
root.title(APP_NAME)

try:
    logo_path = resource_path("logo.png")
    logo_img = tk.PhotoImage(file=logo_path)
    root.iconphoto(False, logo_img)
except Exception as e:
    pass 

root.geometry("960x700")
root.minsize(720, 520)
root.configure(bg=theme["root_bg"])

root.rowconfigure(1, weight=1)
root.columnconfigure(0, weight=1)

header = tk.Label(root, text=APP_NAME, font=("Segoe UI", 16, "bold"), bg=theme["root_bg"], fg=theme["header_fg"])
header.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 4))

main_frame = tk.Frame(root, bg=theme["root_bg"])
main_frame.grid(row=1, column=0, sticky="nsew")
main_frame.rowconfigure(0, weight=1)
main_frame.columnconfigure(0, weight=1)

chat_text = tk.Text(main_frame, bg=theme["chat_bg"], fg=theme["input_fg"], 
                    selectbackground=theme["select_bg"], selectforeground=theme["select_fg"], 
                    exportselection=False,
                    wrap="word", relief="flat", bd=0, padx=8, pady=8, font=("Segoe UI", 10))
chat_text.grid(row=0, column=0, sticky="nsew")

chat_text.bind("<Key>", read_only_text)

scrollbar = ttk.Scrollbar(main_frame, command=chat_text.yview)
scrollbar.grid(row=0, column=1, sticky="ns")
chat_text.configure(yscrollcommand=scrollbar.set)

configure_chat_tags()
apply_window_responsive_tags()

chat_menu = tk.Menu(root, tearoff=0)
chat_menu.add_command(label="Copy", command=copy_selected_chat_text)
chat_text.bind("<Button-3>", lambda e: chat_menu.tk_popup(e.x_root, e.y_root)) 
chat_text.bind("<Control-c>", copy_selected_chat_text)

input_frame = tk.Frame(root, bg=theme["input_bg"])
input_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
input_frame.columnconfigure(0, weight=1)

input_box = tk.Text(input_frame, height=3, bg=theme["input_field_bg"], fg=theme["input_fg"], 
                    selectbackground=theme["select_bg"], selectforeground=theme["select_fg"],
                    insertbackground=theme["input_fg"], wrap="word", relief="flat", bd=0, font=("Segoe UI", 10), padx=10, pady=8)
input_box.grid(row=0, column=0, sticky="ew", padx=(0, 8))

input_menu = tk.Menu(root, tearoff=0)
input_menu.add_command(label="Cut", command=lambda: input_box.event_generate("<<Cut>>"))
input_menu.add_command(label="Copy", command=lambda: input_box.event_generate("<<Copy>>"))
input_menu.add_command(label="Paste", command=lambda: input_box.event_generate("<<Paste>>"))
input_box.bind("<Button-3>", lambda e: input_menu.tk_popup(e.x_root, e.y_root))

attach_btn = tk.Button(input_frame, text="Attach", command=attach_file, bg=theme["input_field_bg"], fg=theme["input_fg"], relief="flat", padx=12, pady=8)
attach_btn.grid(row=0, column=1, padx=(0, 8))

send_btn = tk.Button(input_frame, text="Send", command=send_message, bg=theme["button_bg"], fg=theme["button_fg"], relief="flat", padx=14, pady=8)
send_btn.grid(row=0, column=2, padx=(0, 8))

export_btn = tk.Button(input_frame, text="Export", command=export_chat, bg=theme["input_field_bg"], fg=theme["input_fg"], relief="flat", padx=12, pady=8)
export_btn.grid(row=0, column=3, padx=(0, 8))

theme_btn = tk.Button(input_frame, text="Light/Dark", command=toggle_theme, bg=theme["input_field_bg"], fg=theme["input_fg"], relief="flat", padx=12, pady=8)
theme_btn.grid(row=0, column=4)

def on_enter(event):
    send_message()
    return "break"

input_box.bind("<Return>", on_enter)
root.bind("<Configure>", apply_window_responsive_tags)

append_message(
    "ai",
    "Hey 👋 I’m NeEvo — your AI Buddy.\n\n"
    "What are we working on today?"
)

root.mainloop()