#!/bin/bash
# Archie sandbox entrypoint — sets terminal title and assembles system prompt.

# Set terminal title
if [ -n "$ARCHIE_TITLE" ]; then
    printf '\033]0;%s\007' "$ARCHIE_TITLE"
fi

# Resolve paths from agent-kit config
ak_config="$HOME/.agent-kit/config.yaml"
if [ -f "$ak_config" ]; then
    brain_dir=$(yq -r '.brain.dir // "~/.archie/brain"' "$ak_config")
    brain_dir="${brain_dir/#\~/$HOME}"
    agent_name=$(yq -r '.agent // "archie"' "$ak_config")
    user_name=$(yq -r '.user // ""' "$ak_config")
else
    brain_dir="$HOME/.archie/brain"
    agent_name="archie"
    user_name=""
fi

agent_dir="$brain_dir/_${agent_name}"
user_dir="$brain_dir/${user_name}"
prompt_out="$HOME/.kiro/prompts/archie.prompt.md"

# Assemble system prompt from brain-resident sources
if [ -d "$brain_dir" ]; then
    > "$prompt_out"

    # 1. Soul — identity, personality, rules
    # 2. Brain guide — knowledge structure, conventions
    # 3. Memory — consolidated observations
    for file in \
        "$agent_dir/soul.md" \
        "$brain_dir/BRAIN.md" \
        "$agent_dir/memory.md"; do
        if [ -f "$file" ] && [ -s "$file" ]; then
            cat "$file" >> "$prompt_out"
            printf '\n\n' >> "$prompt_out"
        fi
    done

    # 4. Signals — computed from signals.yaml
    if [ -f "$agent_dir/signals.yaml" ] && [ -s "$agent_dir/signals.yaml" ]; then
        signals=$(python3 "$HOME/.kiro/prompts/build-signals.py" "$agent_dir/signals.yaml" 2>/dev/null)
        if [ -n "$signals" ]; then
            echo "$signals" >> "$prompt_out"
            printf '\n\n' >> "$prompt_out"
        fi
    fi

    # 5. Tools — available tools and usage patterns
    if [ -f "$agent_dir/tools.md" ] && [ -s "$agent_dir/tools.md" ]; then
        cat "$agent_dir/tools.md" >> "$prompt_out"
        printf '\n\n' >> "$prompt_out"
    fi

    # 6. User profile — who the user is, informs communication style and decisions
    if [ -n "$user_name" ] && [ -f "$user_dir/profile.md" ] && [ -s "$user_dir/profile.md" ]; then
        # Strip YAML frontmatter if present
        sed '1{/^---$/!b};1,/^---$/d' "$user_dir/profile.md" >> "$prompt_out"
        printf '\n\n' >> "$prompt_out"
    fi
fi

exec "$@"
