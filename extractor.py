import os
import subprocess

class Extractor:
    def get_text(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mp3', '.zip', '.exe']:
            return "[Error: Binary file cannot be processed.]"

        try:
            if ext == '.pdf':
                return subprocess.check_output(['pdftotext', '-q', file_path, '-'], text=True)
            elif ext in ['.epub', '.docx']:
                return subprocess.check_output(['pandoc', '-t', 'plain', file_path], text=True)
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            return f"[Extraction Error: {e}]"