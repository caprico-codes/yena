function ?? --description 'AI File Helper'
    set -l search_query ""
    set -l flags ""
    set -l script_path (realpath (status filename))
    set -l project_dir (dirname $script_path)

    set -l fd_cmd "fd"
    if not command -v fd >/dev/null; set fd_cmd "fdfind"; end

    for arg in $argv
        if string match -q -- "-*" "$arg"
            set flags $flags "$arg"
        else
            set search_query "$search_query $arg"
        end
    end

    set search_query (string trim "$search_query")
    set -l fuzzy_query (string replace -a ' ' '.*' "$search_query")
    set -l matches ($fd_cmd -HI -t f ".*$fuzzy_query.*")

    if test (count $matches) -eq 0
        echo "No files found."
        return 1
    end

    set -l selected_file $matches[1]
    if test (count $matches) -gt 1
        set selected_file (printf "%s\n" $matches | gum choose)
    end

    if test -n "$selected_file"
        "$project_dir/.venv/bin/python3" "$project_dir/??.py" $flags "$selected_file"
    end
end