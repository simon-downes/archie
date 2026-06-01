#!/bin/bash
# Archie sandbox entrypoint — installs CLI, symlinks persona, assembles system prompt.

# Install archie CLI from mounted repo (editable)
uv tool install -e /opt/archie --quiet

# Symlink persona dirs to kiro-cli paths
ln -sfn /opt/archie/persona/skills ~/.kiro/skills
ln -sfn /opt/archie/persona/agents ~/.kiro/agents
ln -sfn /opt/archie/persona/prompts ~/.kiro/prompts
ln -sfn /opt/archie/persona/guidance ~/.kiro/steering

# Resolve paths from archie config
archie_config="$HOME/.archie/config.yaml"
if [ -f "$archie_config" ]; then
    brain_dir=$(yq -r '.brain_dir // "~/.archie/brain"' "$archie_config")
    brain_dir="${brain_dir/#\~/$HOME}"
else
    brain_dir="$HOME/.archie/brain"
fi

agent_dir="$brain_dir/_archie"
user_dir="$brain_dir/simon"
prompt_out="$HOME/.kiro/prompts/archie.prompt.md"

# Assemble system prompt by resolving @ directives in soul.md
if [ -f "$agent_dir/soul.md" ]; then
    > "$prompt_out"

    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in
            @agent\ *)
                file="${line#@agent }"
                if [ -f "$agent_dir/$file" ] && [ -s "$agent_dir/$file" ]; then
                    cat "$agent_dir/$file" >> "$prompt_out"
                    printf '\n\n' >> "$prompt_out"
                fi
                ;;
            @user\ *)
                file="${line#@user }"
                if [ -f "$user_dir/$file" ] && [ -s "$user_dir/$file" ]; then
                    sed '1{/^---$/!b};1,/^---$/d' "$user_dir/$file" >> "$prompt_out"
                    printf '\n\n' >> "$prompt_out"
                fi
                ;;
            @script\ *)
                alias="${line#@script }"
                cmd=$(yq -r ".prompt.scripts.$alias // \"\"" "$archie_config")
                if [ -n "$cmd" ]; then
                    output=$(eval "$cmd" 2>/dev/null)
                    if [ -n "$output" ]; then
                        echo "$output" >> "$prompt_out"
                        printf '\n\n' >> "$prompt_out"
                    fi
                fi
                ;;
            *)
                echo "$line" >> "$prompt_out"
                ;;
        esac
    done < "$agent_dir/soul.md"
fi

# Set terminal title
if [ -n "$ARCHIE_TITLE" ]; then
    printf '\033]0;%s\007' "$ARCHIE_TITLE"
fi

exec "$@"
