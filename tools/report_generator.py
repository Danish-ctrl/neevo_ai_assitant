import os
from datetime import datetime
from collections import Counter


def generate_text_report(findings: list[dict], output_folder: str = "reports") -> str:
    os.makedirs(output_folder, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(output_folder, f"security_report_{timestamp}.txt")

    severity_counter = Counter(finding["severity"] for finding in findings)
    category_counter = Counter(finding["category"] for finding in findings)

    with open(report_path, "w", encoding="utf-8") as report:
        report.write("NEEVA AI Code Safety Review Report\n")
        report.write("=" * 45 + "\n\n")

        report.write("Summary\n")
        report.write("-" * 45 + "\n")
        report.write(f"TOTAL ISSUES: {len(findings)}\n")
        report.write(f"HIGH: {severity_counter.get('HIGH', 0)}\n")
        report.write(f"MEDIUM: {severity_counter.get('MEDIUM', 0)}\n")
        report.write(f"LOW: {severity_counter.get('LOW', 0)}\n\n")

        report.write("Category Summary\n")
        report.write("-" * 45 + "\n")

        if category_counter:
            for category, count in category_counter.items():
                report.write(f"{category}: {count}\n")
        else:
            report.write("No categories found.\n")

        report.write("\n")

        if not findings:
            report.write("No risky patterns found.\n")
            return report_path

        report.write("Detailed Findings\n")
        report.write("-" * 45 + "\n\n")

        for index, finding in enumerate(findings, start=1):
            report.write(f"Issue #{index}\n")
            report.write(f"Severity: {finding['severity']}\n")
            report.write(f"Category: {finding['category']}\n")
            report.write(f"Rule: {finding['rule']}\n")
            report.write(f"File: {finding['file']}\n")
            report.write(f"Line: {finding['line']}\n")
            report.write(f"Code: {finding['snippet']}\n")
            report.write(f"Explanation: {finding['explanation']}\n")
            report.write("-" * 45 + "\n\n")

    return report_path