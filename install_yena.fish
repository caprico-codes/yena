#!/opt/homebrew/bin/fish

# Detect the actual project directory, even if this script is called via symlink
set -l project_dir (realpath (dirname (status filename)))
set -l fish_func_dir "$HOME/.config/fish/functions"

echo -e "\e[1;34m==> Yena Project Unified Installer\e[0m"

# Ensure .venv exists for the python logic
if not test -d "$project_dir/.venv"
    echo -e "\e[1;33m[!] Creating .venv in $project_dir...\e[0m"
    python3 -m venv "$project_dir/.venv"
    "$project_dir/.venv/bin/pip" install -r "$project_dir/requirements.txt"
end

# Link all .fish command files (except the installer itself)
for func_file in "$project_dir/"*.fish
    set -l func_name (basename "$func_file")
    if test "$func_name" != "install_yena.fish"
        echo "Installing symlink: "(string replace ".fish" "" "$func_name")
        ln -sf "$func_file" "$fish_func_dir/$func_name"
    end
end

echo -e "\e[1;32m[!] Installation Complete. Run 'exec fish' to refresh.\e[0m"