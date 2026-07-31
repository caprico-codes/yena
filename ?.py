import argparse
import os
import yaml
import re
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.markdown import Markdown
from rich.theme import Theme

from provider import LMStudioProvider
from context_manager import ContextManager

# Define custom theme to enforce consistent colors in markdown and make bolding richer
custom_theme = Theme({
    "markdown.item.bullet": "bold bright_yellow",
    "markdown.strong": "bold bright_magenta",
    "markdown.text": "default"
})
console = Console(theme=custom_theme)

def load_config(base_dir):
    config_path = os.path.join(base_dir, "config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def validate_command(cmd):
    if not cmd or cmd.isspace(): return False
    if re.search(r'(.)\1{12,}', cmd) or "[CMD]" in cmd: return False
    return True

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    tmp_dir = os.path.join(base_dir, "tmp")
    cmd_file_path = os.path.join(tmp_dir, "yena_next_cmd")
    
    config = load_config(base_dir)
    mod_cfg = config['modules']['command_helper']

    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--quick", action="store_true")
    parser.add_argument("-r", "--recall", action="store_true")
    parser.add_argument("-d", "--deepsearch", action="store_true")
    parser.add_argument("query", nargs="+")
    args = parser.parse_args()
    
    user_query = " ".join(args.query)
    provider = LMStudioProvider(
        endpoint=config['lm_studio']['endpoint'], 
        model=mod_cfg['model'],
        temperature=mod_cfg['temperature']
    )
    
    context = ""
    if args.recall:
        with console.status("[bold yellow]Yena is searching your history..."):
            context = ContextManager().get_fish_history()
    elif args.deepsearch:
        from search_engine import SearXNGProvider
        with console.status("[bold magenta]Yena is searching the web..."):
            search_data = SearXNGProvider(endpoint=config['search']['searxng_url']).search(user_query)
        with console.status("[bold cyan]Yena is analysing web results..."):
            context = f"--- WEB SEARCH KNOWLEDGE BASE ---\n{search_data}\n"

    system_prompt = (
        "You are a Fish Shell Expert on Mac OS. You must strictly follow this exact schema:\n\n"
        "[CMD]single line of pure code[/CMD]\n"
        "[EXP]\n- bullet points\n[/EXP]\n\n"
        "RULES:\n"
        "1. NO bolding (**) or backticks (`) inside [CMD] tags.\n"
        "2. ONLY use bullet points inside [EXP] tags. NO paragraphs.\n"
        "3. NO preamble or conversational filler.\n\n"
        "EXAMPLE OUTPUT:\n"
        "[CMD]nmap -sS -p- --script=all -T4 192.168.1.0/24[/CMD]\n"
        "[EXP]\n"
        "- **-sS**: A TCP SYN scan (half-open) that identifies open ports without completing the handshake.\n"
        "- **-p-**: Specifies scanning all 65,535 ports instead of the default top 1,000.\n"
        "- **--script=all**: Executes all available Nmap scripts for vulnerability and service detection.\n"
        "- **-T4**: Aggressive timing template to speed up scans on reliable networks.\n"
        "- **192.168.1.0/24**: The target subnet range for the scan.\n"
        "[/EXP]"
    )
    full_prompt = f"{context}\n\nUSER REQUEST: {user_query}"

    with console.status("[bold green]Yena is thinking...") as status:
        full_response = ""
        gen = provider.generate(system_prompt, full_prompt)
        try:
            first_chunk = next(gen)
            full_response += first_chunk
        except StopIteration:
            return

        with Live(console=console, refresh_per_second=20, vertical_overflow="visible") as live:
            for chunk in gen:
                full_response += chunk
                cmd_text = "..."
                if "[CMD]" in full_response:
                    start_cmd = full_response.find("[CMD]") + 5
                    end_cmd = full_response.find("[/CMD]", start_cmd)
                    cmd_text = full_response[start_cmd:end_cmd].strip() if end_cmd != -1 else full_response[start_cmd:].strip()
                    cmd_text = cmd_text.replace('**', '').replace('`', '')

                exp_render = Markdown("Analyzing...")
                if "[EXP]" in full_response:
                    start_exp = full_response.find("[EXP]") + 5
                    end_exp = full_response.find("[/EXP]", start_exp)
                    raw_exp = full_response[start_exp:end_exp].strip() if end_exp != -1 else full_response[start_exp:].strip()
                    exp_render = Markdown(f"\n{raw_exp}")

                ui_group = Group(Panel(f"[bold bright_green]{cmd_text}[/bold bright_green]", border_style="bright_yellow"), exp_render)
                live.update(Panel(ui_group, border_style="bright_blue"))

    if "[CMD]" in full_response:
        final_cmd = full_response.split("[CMD]")[1].split("[/CMD]")[0].strip().replace('**', '').replace('`', '')
        if validate_command(final_cmd):
            os.makedirs(tmp_dir, exist_ok=True)
            with open(cmd_file_path, "w") as f:
                f.write(final_cmd)

if __name__ == "__main__":
    main()