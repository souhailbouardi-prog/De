"""Shell completion script generation for hermes CLI.

Walks the live argparse parser tree to generate accurate, always-up-to-date
completion scripts — no hardcoded subcommand lists, no extra dependencies.

Supports bash, zsh, and fish.
"""

from __future__ import annotations

import argparse
from typing import Any


def _walk(parser: argparse.ArgumentParser) -> dict[str, Any]:
    """Recursively extract subcommands and flags from a parser.

    Uses _SubParsersAction._choices_actions to get canonical names (no aliases)
    along with their help text.
    """
    flags: list[str] = []
    subcommands: dict[str, Any] = {}

    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            # _choices_actions has one entry per canonical name; aliases are
            # omitted, which keeps completion lists clean.
            seen: set[str] = set()
            for pseudo in action._choices_actions:
                name = pseudo.dest
                if name in seen:
                    continue
                seen.add(name)
                subparser = action.choices.get(name)
                if subparser is None:
                    continue
                info = _walk(subparser)
                info["help"] = _clean(pseudo.help or "")
                subcommands[name] = info
        elif action.option_strings:
            flags.extend(o for o in action.option_strings if o.startswith("-"))

    return {"flags": flags, "subcommands": subcommands}


# ---------------------------------------------------------------------------
# Rich argparse walker for fish (extracts flags, value types, aliases)
# ---------------------------------------------------------------------------

def _walk_rich(parser: argparse.ArgumentParser) -> list[dict[str, Any]]:
    """Extract subcommand groups with aliases, plus all actions, for fish."""
    from collections import defaultdict

    groups: list[dict[str, Any]] = []
    for action in parser._actions:
        if not isinstance(action, argparse._SubParsersAction):
            continue
        # Group aliased parsers (same id() means same parser object).
        names_by_id: dict[int, list[str]] = defaultdict(list)
        parser_by_id: dict[int, argparse.ArgumentParser] = {}
        for name, child in action.choices.items():
            key = id(child)
            names_by_id[key].append(name)
            parser_by_id[key] = child

        help_by_name = {
            getattr(c, "dest", ""): getattr(c, "help", "")
            for c in getattr(action, "_choices_actions", [])
        }
        for key, names in names_by_id.items():
            child = parser_by_id[key]
            desc = help_by_name.get(names[0]) or ""
            groups.append({"names": names, "parser": child, "help": desc})
    return groups


def _action_takes_value(action: argparse.Action) -> bool:
    if isinstance(action, argparse.BooleanOptionalAction):
        return False
    if getattr(action, "nargs", None) == 0:
        return False
    return not isinstance(action, (argparse._StoreTrueAction, argparse._StoreFalseAction,
                                   argparse._StoreConstAction, argparse._CountAction))


def _classify_value(action: argparse.Action) -> str:
    """Heuristic: decide what kind of value an argument accepts."""
    if getattr(action, "choices", None):
        return "choices"
    blob = " ".join(
        part for part in [
            getattr(action, "dest", ""),
            getattr(action, "metavar", "") or "",
            getattr(action, "help", "") or "",
        ] if part
    ).lower()
    if any(t in blob for t in ("profile", "clone-from", "old_name")):
        return "profiles"
    if any(t in blob for t in ("directory", "dir", "folder")):
        return "directory"
    if any(t in blob for t in ("path", "file", "archive", "pem", "jsonl",
                                "json file", "config file", "env file")):
        return "file"
    return "value"


def _clean(text: str, maxlen: int = 60) -> str:
    """Strip shell-unsafe characters and truncate."""
    return text.replace("'", "").replace('"', "").replace("\\", "")[:maxlen]


# ---------------------------------------------------------------------------
# Bash
# ---------------------------------------------------------------------------

def generate_bash(parser: argparse.ArgumentParser) -> str:
    tree = _walk(parser)
    top_cmds = " ".join(sorted(tree["subcommands"]))

    cases: list[str] = []
    for cmd in sorted(tree["subcommands"]):
        info = tree["subcommands"][cmd]
        if cmd == "profile" and info["subcommands"]:
            # Profile subcommand: complete actions, then profile names for
            # actions that accept a profile argument.
            subcmds = " ".join(sorted(info["subcommands"]))
            profile_actions = "use delete show alias rename export"
            cases.append(
                f"        profile)\n"
                f"            case \"$prev\" in\n"
                f"                profile)\n"
                f"                    COMPREPLY=($(compgen -W \"{subcmds}\" -- \"$cur\"))\n"
                f"                    return\n"
                f"                    ;;\n"
                f"                {profile_actions.replace(' ', '|')})\n"
                f"                    COMPREPLY=($(compgen -W \"$(_hermes_profiles)\" -- \"$cur\"))\n"
                f"                    return\n"
                f"                    ;;\n"
                f"            esac\n"
                f"            ;;"
            )
        elif info["subcommands"]:
            subcmds = " ".join(sorted(info["subcommands"]))
            cases.append(
                f"        {cmd})\n"
                f"            COMPREPLY=($(compgen -W \"{subcmds}\" -- \"$cur\"))\n"
                f"            return\n"
                f"            ;;"
            )
        elif info["flags"]:
            flags = " ".join(info["flags"])
            cases.append(
                f"        {cmd})\n"
                f"            COMPREPLY=($(compgen -W \"{flags}\" -- \"$cur\"))\n"
                f"            return\n"
                f"            ;;"
            )

    cases_str = "\n".join(cases)

    return f"""# Hermes Agent bash completion
# Add to ~/.bashrc:
#   eval "$(hermes completion bash)"

_hermes_profiles() {{
    local profiles_dir="$HOME/.hermes/profiles"
    local profiles="default"
    if [ -d "$profiles_dir" ]; then
        profiles="$profiles $(ls "$profiles_dir" 2>/dev/null)"
    fi
    echo "$profiles"
}}

_hermes_completion() {{
    local cur prev
    COMPREPLY=()
    cur="${{COMP_WORDS[COMP_CWORD]}}"
    prev="${{COMP_WORDS[COMP_CWORD-1]}}"

    # Complete profile names after -p / --profile
    if [[ "$prev" == "-p" || "$prev" == "--profile" ]]; then
        COMPREPLY=($(compgen -W "$(_hermes_profiles)" -- "$cur"))
        return
    fi

    if [[ $COMP_CWORD -ge 2 ]]; then
        case "${{COMP_WORDS[1]}}" in
{cases_str}
        esac
    fi

    if [[ $COMP_CWORD -eq 1 ]]; then
        COMPREPLY=($(compgen -W "{top_cmds}" -- "$cur"))
    fi
}}

complete -F _hermes_completion hermes
"""


# ---------------------------------------------------------------------------
# Zsh
# ---------------------------------------------------------------------------

def generate_zsh(parser: argparse.ArgumentParser) -> str:
    tree = _walk(parser)

    top_cmds_lines: list[str] = []
    for cmd in sorted(tree["subcommands"]):
        help_text = _clean(tree["subcommands"][cmd].get("help", ""))
        top_cmds_lines.append(f"                '{cmd}:{help_text}'")
    top_cmds_str = "\n".join(top_cmds_lines)

    sub_cases: list[str] = []
    for cmd in sorted(tree["subcommands"]):
        info = tree["subcommands"][cmd]
        if not info["subcommands"]:
            continue
        if cmd == "profile":
            # Profile subcommand: complete actions, then profile names for
            # actions that accept a profile argument.
            sub_lines: list[str] = []
            for sc in sorted(info["subcommands"]):
                sh = _clean(info["subcommands"][sc].get("help", ""))
                sub_lines.append(f"                        '{sc}:{sh}'")
            sub_str = "\n".join(sub_lines)
            sub_cases.append(
                f"                profile)\n"
                f"                    case ${{line[2]}} in\n"
                f"                        use|delete|show|alias|rename|export)\n"
                f"                            _hermes_profiles\n"
                f"                            ;;\n"
                f"                        *)\n"
                f"                            local -a profile_cmds\n"
                f"                            profile_cmds=(\n"
                f"{sub_str}\n"
                f"                            )\n"
                f"                            _describe 'profile command' profile_cmds\n"
                f"                            ;;\n"
                f"                    esac\n"
                f"                    ;;"
            )
        else:
            sub_lines = []
            for sc in sorted(info["subcommands"]):
                sh = _clean(info["subcommands"][sc].get("help", ""))
                sub_lines.append(f"                    '{sc}:{sh}'")
            sub_str = "\n".join(sub_lines)
            safe = cmd.replace("-", "_")
            sub_cases.append(
                f"                {cmd})\n"
                f"                    local -a {safe}_cmds\n"
                f"                    {safe}_cmds=(\n"
                f"{sub_str}\n"
                f"                    )\n"
                f"                    _describe '{cmd} command' {safe}_cmds\n"
                f"                    ;;"
            )
    sub_cases_str = "\n".join(sub_cases)

    return f"""#compdef hermes
# Hermes Agent zsh completion
# Add to ~/.zshrc:
#   eval "$(hermes completion zsh)"

_hermes_profiles() {{
    local -a profiles
    profiles=(default)
    if [[ -d "$HOME/.hermes/profiles" ]]; then
        profiles+=("${{(@f)$(ls $HOME/.hermes/profiles 2>/dev/null)}}")
    fi
    _describe 'profile' profiles
}}

_hermes() {{
    local context state line
    typeset -A opt_args

    _arguments -C \\
        '(-h --help){{-h,--help}}[Show help and exit]' \\
        '(-V --version){{-V,--version}}[Show version and exit]' \\
        '(-p --profile){{-p,--profile}}[Profile name]:profile:_hermes_profiles' \\
        '1:command:->commands' \\
        '*::arg:->args'

    case $state in
        commands)
            local -a subcmds
            subcmds=(
{top_cmds_str}
            )
            _describe 'hermes command' subcmds
            ;;
        args)
            case ${{line[1]}} in
{sub_cases_str}
            esac
            ;;
    esac
}}

_hermes "$@"
"""


# ---------------------------------------------------------------------------
# Fish
# ---------------------------------------------------------------------------

def _fish_scope(path_groups: list[list[str]],
                child_groups: list[list[str]] | None = None) -> str:
    """Build a fish -n condition for the current scope depth.

    ``path_groups`` is a list of name-groups we must have seen (one per depth
    level).  ``child_groups`` lists sibling subcommand names at the current
    depth so we can emit ``not __fish_seen_subcommand_from …`` to prevent
    completing options once a deeper subcommand has been typed.
    """
    if not path_groups:
        return "__fish_use_subcommand"
    parts = [f"__fish_seen_subcommand_from {' '.join(g)}" for g in path_groups]
    if child_groups:
        siblings = []
        for g in child_groups:
            siblings.extend(n for n in g if n not in siblings)
        if siblings:
            parts.append(f"not __fish_seen_subcommand_from {' '.join(siblings)}")
    return "; and ".join(parts)


def _fish_option(command: str, cond: str, action: argparse.Action,
                 option: str) -> str:
    """Format a single ``complete`` line for an option flag."""
    parts = [f"complete -c {command}", f"-n '{cond}'"]
    if option.startswith("--"):
        parts.append(f"-l {option[2:]}")
    elif option.startswith("-"):
        parts.append(f"-s {option[1:]}")

    desc = _clean(getattr(action, "help", "") or "")
    if desc:
        parts.append(f"-d '{desc}'")

    if _action_takes_value(action):
        kind = _classify_value(action)
        if kind == "choices":
            choices = " ".join(str(c) for c in action.choices)
            parts.append(f"-xa '{choices}'")
        elif kind == "profiles":
            parts.append("-xa '(__hermes_profiles)'")
        elif kind == "directory":
            parts.append("-xa '(__fish_complete_directories)'")
        elif kind == "file":
            parts.append("-rF")
        else:
            parts.append("-r")
    return " ".join(parts)


def _fish_positional(command: str, cond: str,
                     action: argparse.Action) -> str | None:
    """Format a ``complete`` line for a positional arg, or None if generic."""
    kind = _classify_value(action)
    desc = _clean(getattr(action, "help", "") or getattr(action, "dest", "") or "")
    desc_part = f" -d '{desc}'" if desc else ""
    if kind == "choices" and getattr(action, "choices", None):
        choices = " ".join(str(c) for c in action.choices)
        return f"complete -c {command} -n '{cond}' -xa '{choices}'{desc_part}"
    if kind == "profiles":
        return f"complete -c {command} -n '{cond}' -xa '(__hermes_profiles)'{desc_part}"
    return None


def _fish_walk(parser: argparse.ArgumentParser, command: str,
               path_groups: list[list[str]] | None = None) -> list[str]:
    """Recursively generate fish completions for a parser and its children."""
    path_groups = path_groups or []
    lines: list[str] = []
    child_entries = _walk_rich(parser)
    child_name_groups = [e["names"] for e in child_entries]
    cond = _fish_scope(path_groups,
                       child_name_groups if path_groups else None)

    # Options and positionals at this level.
    for action in getattr(parser, "_actions", []):
        if isinstance(action, argparse._SubParsersAction):
            continue
        if not getattr(action, "option_strings", None):
            line = _fish_positional(command, cond, action)
            if line:
                lines.append(line)
            continue
        for opt in action.option_strings:
            lines.append(_fish_option(command, cond, action, opt))

    # Subcommands (including aliases) and recurse.
    for entry in child_entries:
        names = entry["names"]
        desc = _clean(str(entry["help"] or ""))
        desc_part = f" -d '{desc}'" if desc else ""
        for name in names:
            lines.append(f"complete -c {command} -n '{cond}' -a {name}{desc_part}")
        lines.extend(_fish_walk(entry["parser"], command,
                                [*path_groups, names]))
    return lines


def generate_fish(parser: argparse.ArgumentParser) -> str:
    """Generate a complete fish completion script from the live argparse tree.

    Produces completions for every flag, positional, and subcommand at all
    nesting depths — including aliases, value-type hints (file, directory,
    choices, profile names), and proper scope guards to prevent stale
    suggestions.
    """
    command = "hermes"
    lines = [
        f"# fish completions for {command}",
        f"# Install: hermes completion fish --install",
        "",
        "function __hermes_profiles",
        "    set -l profiles default",
        "    if test -d $HOME/.hermes/profiles",
        "        for p in $HOME/.hermes/profiles/*",
        "            if test -d $p",
        "                set profiles $profiles (path basename $p)",
        "            end",
        "        end",
        "    end",
        "    printf '%s\\n' $profiles",
        "end",
        "",
        f"complete -c {command} -f",
        f"complete -c {command} -n '__fish_use_subcommand'"
        f" -s p -l profile -xa '(__hermes_profiles)' -d 'Use a named profile'",
    ]
    lines.extend(_fish_walk(parser, command))
    lines.append("")
    return "\n".join(lines)
