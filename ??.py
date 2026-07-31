import sys
import os
import yaml
import argparse
import time
from rich.console import Console, Group
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.align import Align

from provider import LMStudioProvider
from context_manager import ContextManager
from big_data_handler import BigDataHandler
from search_engine import SearXNGProvider

console = Console()

def get_persona_config(meta):
    """Dynamic dispatcher for Technical vs. Literary contexts."""
    code_exts = ['.sh', '.fish', '.py', '.js', '.c', '.cpp', '.html', '.css', '.yaml', '.json', '.md']
    if meta['extension'] in code_exts:
        return {
            "name": "Architect",
            "prompt": (
                f"You are Nemo, a Technical Architect analyzing '{meta['name']}'.\n\n"
                "## Summary\n(Brief overview)\n\n"
                "## Analysis\n> (Insight)\n- (Points)\n\n"
                "## Technical Details\n```(lang)\n(Code)\n```"
                "RULE: Use only code snippets in 'Technical Details' and not the entire code."
            )
        }
    else:
        return {
            "name": "Scholar",
            "prompt": (
                f"You are Nemo, a Scholarly Companion discussing '{meta['name']}'.\n\n"
                "## Core Themes\n(Main ideas)\n\n"
                "## Analysis\n> (Insightful observation)\n- (Key points)\n\n"
                "RULE: No 'Technical Details' section unless quoting text."
            )
        }

def get_brain_display_name(model_id):
    mapping = {
        "qwen/qwen2.5-coder-14b": "Qwen 2.5 Coder 14B",
    }
    return mapping.get(model_id, model_id)

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("file_path", nargs='?')
    parser.add_argument("-d", "--deepsearch", action="store_true")
    
    args, unknown = parser.parse_known_args()
    for u in unknown:
        if u.startswith("-"):
            console.print(f"[bold red]Error:[/bold red] Unrecognized flag '{u}'")
            sys.exit(1)

    file_target = args.file_path if args.file_path else (unknown[0] if unknown else None)

    if not file_target or not os.path.exists(file_target):
        console.print("[bold red]Error:[/bold red] File not found.")
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base_dir, "config.yaml"), "r") as f:
        config = yaml.safe_load(f)
    
    ctx_mgr = ContextManager()
    bd_handler = BigDataHandler(config)
    search_engine = SearXNGProvider(config['search']['searxng_url'])
    meta = ctx_mgr.get_file_metadata(file_target)
    
    file_content = bd_handler.process_file(file_target)
    
    if bd_handler.status == "TOO_LARGE":
        console.print(Panel(f"File: {meta['name']}\nSize: {meta['size_kb']} KB\nStatus: Exceeds 28k token limit.", border_style="yellow"))
        return

    provider = LMStudioProvider(config['lm_studio']['endpoint'], bd_handler.active_model, config['modules']['file_helper']['temperature'])
    persona = get_persona_config(meta)
    chat_history = []

    # Centered Horizontal Header
    brain_name = get_brain_display_name(bd_handler.active_model)
    header_info = Columns([
        Text(f"AI Brain: {brain_name}", style="bold cyan"),
        Text(f"File Size: {meta['size_kb']} KB", style="bold green"),
        Text(f"File Extension: {meta['extension']}", style="bold yellow")
    ], padding=(0, 6)) # Space them out horizontally
    
    console.print(Panel(Align.center(header_info), border_style="bright_blue"))

    while True:
        try:
            user_input = console.input(f"\n[bold green]?? {meta['name']} > [/bold green]").strip()
            if not user_input or user_input.lower() in ["exit", "quit"]: break

            if user_input.lower() == "meta":
                rich_meta = ctx_mgr.get_rich_metadata(file_target)
                console.print() # spacing
                table = Table(show_header=False, border_style="bright_blue")
                for k, v in rich_meta.items():
                    table.add_row(Text(k.capitalize(), style="bold cyan"), str(v))
                console.print(table)
                continue

            if user_input.lower() == "sum":
                user_input = "Provide a detailed summary of this file. Use bullet points."

            web_context = ""
            if args.deepsearch:
                with console.status("[bold blue]Searching the web..."):
                    web_context = search_engine.search(f"{meta['name']} {user_input}")

            hist_str = "\n".join([f"Friend: {h['u']}\nNemo: {h['a']}" for h in chat_history[-3:]])
            full_prompt = f"--- FILE CONTENT ---\n{file_content}\n{web_context}\n--- END ---\n{hist_str}\nFriend: {user_input}\nNemo:"
            
            console.print()
            nemo_header = Text(f"Nemo ({meta['name']}) > \n", style="bold magenta")
            full_response = ""
            
            with Live(nemo_header, refresh_per_second=20, console=console) as live:
                for chunk in provider.generate(persona['prompt'], full_prompt):
                    full_response += chunk
                    live.update(Group(nemo_header, Markdown(full_response)))
            
            chat_history.append({"u": user_input, "a": full_response})

        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()