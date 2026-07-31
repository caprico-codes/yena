function ? --description 'AI Command Assistant'
    set -l original_args "$argv"
    set -l script_path (realpath (status filename))
    set -l project_dir (dirname $script_path)
    set -l cmd_file "$project_dir/tmp/yena_next_cmd"

    history delete --exact --case-sensitive "? $original_args" 2>/dev/null
    rm -f "$cmd_file"

    "$project_dir/.venv/bin/python3" "$project_dir/?.py" $argv

    if test -f "$cmd_file"
        set -l cmd (cat "$cmd_file" | string collect)
        echo -e "\n\e[1;36m[?] Action:\e[0m"
        
        if gum confirm --affirmative "Execute" --negative "Edit" ""
            set -l timestamp (date +%s)
            echo "- cmd: $cmd" >> ~/.local/share/fish/fish_history
            echo "  when: $timestamp" >> ~/.local/share/fish/fish_history
            history delete --exact --case-sensitive "? $original_args" 2>/dev/null
            eval "$cmd"
            history merge
        else
            history delete --exact --case-sensitive "? $original_args" 2>/dev/null
            commandline -r "$cmd"
        end
    else
        history delete --exact --case-sensitive "? $original_args" 2>/dev/null
    end
end