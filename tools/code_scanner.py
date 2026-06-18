import os
import re


SUPPORTED_EXTENSIONS = [
    ".py", ".js", ".ts", ".html", ".css", ".json",
    ".yaml", ".yml", ".env", ".txt", ".md"
]

IGNORED_FOLDERS = [
    ".git", "__pycache__", "venv", ".venv",
    "node_modules", "dist", "build"
]


SECURITY_RULES = [
    {
        "name": "Possible Hardcoded Secret",
        "category": "SECRET",
        "severity": "HIGH",
        "pattern": r"(api_key|apikey|secret|token|password)\s*=\s*[\"'][^\"']+[\"']",
        "explanation": "A secret, token, password, or API key may be hardcoded in the source code."
    },
    {
        "name": "Unsafe eval usage",
        "category": "DANGEROUS_FUNCTION",
        "severity": "HIGH",
        "pattern": r"\beval\s*\(",
        "explanation": "eval() can execute arbitrary code and may create security risks."
    },
    {
        "name": "Unsafe exec usage",
        "category": "DANGEROUS_FUNCTION",
        "severity": "HIGH",
        "pattern": r"\bexec\s*\(",
        "explanation": "exec() can run dynamic code and should be avoided unless strictly controlled."
    },
    {
        "name": "Subprocess shell=True",
        "category": "COMMAND_INJECTION",
        "severity": "HIGH",
        "pattern": r"shell\s*=\s*True",
        "explanation": "shell=True can create command injection risks if user input reaches the command."
    },
    {
        "name": "Insecure HTTP URL",
        "category": "NETWORK_SECURITY",
        "severity": "MEDIUM",
        "pattern": r"http://",
        "explanation": "HTTP is not encrypted. Prefer HTTPS for communication."
    },
    {
        "name": "Debug Mode Enabled",
        "category": "CONFIG_RISK",
        "severity": "MEDIUM",
        "pattern": r"DEBUG\s*=\s*True",
        "explanation": "Debug mode should not be enabled in production."
    },
]


def should_scan_file(file_path: str) -> bool:
    return any(file_path.endswith(ext) for ext in SUPPORTED_EXTENSIONS)


def is_ignored_folder(path: str) -> bool:
    parts = path.split(os.sep)
    return any(folder in parts for folder in IGNORED_FOLDERS)


def scan_file(file_path: str) -> list[dict]:
    findings = []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            lines = file.readlines()
    except Exception:
        return findings

    for line_number, line in enumerate(lines, start=1):
        for rule in SECURITY_RULES:
            if re.search(rule["pattern"], line, re.IGNORECASE):
                findings.append({
                    "file": file_path,
                    "line": line_number,
                    "rule": rule["name"],
                    "category": rule["category"],
                    "severity": rule["severity"],
                    "snippet": line.strip(),
                    "explanation": rule["explanation"]
                })

    return findings


def scan_folder(folder_path: str) -> list[dict]:
    all_findings = []

    for root, dirs, files in os.walk(folder_path):
        if is_ignored_folder(root):
            continue

        for file_name in files:
            file_path = os.path.join(root, file_name)

            if should_scan_file(file_path):
                all_findings.extend(scan_file(file_path))

    return all_findings