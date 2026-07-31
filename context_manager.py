import os
import re
import time
import pathlib
import stat

class ContextManager:
    def get_fish_history(self):
        """Retrieves the last 100 unique commands from Fish history."""
        history_path = os.path.expanduser("~/.local/share/fish/fish_history")
        if not os.path.exists(history_path):
            return "No fish history found."
        
        commands = []
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                content = f.read()
                matches = re.findall(r'- cmd:\s*(.+)', content)
                seen = set()
                for cmd in reversed(matches):
                    if cmd not in seen:
                        seen.add(cmd)
                        commands.append(f"{len(seen)}. {cmd}")
                        if len(commands) == 100:
                            break
            return "--- COMMAND HISTORY ---\n" + "\n".join(commands) + "\n--- END HISTORY ---"
        except Exception:
            return "Failed to parse history."

    def get_file_metadata(self, file_path):
        """Extracts stats and checks if the file is likely binary."""
        stats = os.stat(file_path)
        ext = os.path.splitext(file_path)[1].lower()
        
        is_bin = self._is_binary(file_path)
        if ext in ['.sh', '.fish', '.py', '.conf', '.yaml', '.json', '.md']:
            is_bin = False
            
        return {
            "name": os.path.basename(file_path),
            "size_kb": round(stats.st_size / 1024, 2),
            "extension": ext,
            "path": file_path,
            "is_binary": is_bin
        }

    def get_rich_metadata(self, file_path):
        """Advanced metadata for the 'meta' command table."""
        path = pathlib.Path(file_path)
        st = path.stat()
        
        try:
            owner = path.owner()
            group = path.group()
        except (NotImplementedError, AttributeError):
            owner = st.st_uid
            group = st.st_gid

        return {
            "name": path.name,
            "path": str(path.absolute()),
            "size": f"{st.st_size} bytes",
            "created": time.ctime(st.st_ctime),
            "modified": time.ctime(st.st_mtime),
            "accessed": time.ctime(st.st_atime),
            "mode": stat.filemode(st.st_mode),
            "octal": oct(st.st_mode & 0o777),
            "owner": owner,
            "group": group
        }

    def _is_binary(self, file_path):
        """Internal check to prevent reading binary data as text."""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk
        except Exception:
            return True