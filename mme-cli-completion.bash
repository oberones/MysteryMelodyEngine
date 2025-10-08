# Mystery Music Engine CLI Auto-completion
# Source this file to enable bash auto-completion for mme-cli
#
# Usage:
#   source mme-cli-completion.bash
#   OR add to your ~/.bashrc:
#   source /path/to/rpi-engine/mme-cli-completion.bash

_mme_cli_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # Top-level commands
    local commands="status config state event monitor quick"
    
    # Config subcommands
    local config_commands="get set list"
    
    # State subcommands  
    local state_commands="show reset"
    
    # Event subcommands
    local event_commands="trigger"
    
    # Quick parameter names
    local quick_params="bpm density swing steps gate root"
    
    # Common configuration paths
    local config_paths="sequencer.bpm sequencer.density sequencer.swing sequencer.steps sequencer.root_note sequencer.gate_length sequencer.direction_pattern sequencer.step_pattern midi.input_port midi.output_port midi.cc_profile.active_profile mutation.interval_min_s idle.timeout_ms logging.level"
    
    # Event actions
    local event_actions="set_direction_pattern set_step_pattern reload_cc_profile"
    
    case ${COMP_CWORD} in
        1)
            COMPREPLY=($(compgen -W "${commands}" -- ${cur}))
            return 0
            ;;
        2)
            case ${prev} in
                config)
                    COMPREPLY=($(compgen -W "${config_commands}" -- ${cur}))
                    return 0
                    ;;
                state)
                    COMPREPLY=($(compgen -W "${state_commands}" -- ${cur}))
                    return 0
                    ;;
                event)
                    COMPREPLY=($(compgen -W "${event_commands}" -- ${cur}))
                    return 0
                    ;;
                quick)
                    COMPREPLY=($(compgen -W "${quick_params}" -- ${cur}))
                    return 0
                    ;;
            esac
            ;;
        3)
            case ${COMP_WORDS[1]} in
                config)
                    case ${prev} in
                        get|set)
                            COMPREPLY=($(compgen -W "${config_paths}" -- ${cur}))
                            return 0
                            ;;
                    esac
                    ;;
                event)
                    case ${prev} in
                        trigger)
                            COMPREPLY=($(compgen -W "${event_actions}" -- ${cur}))
                            return 0
                            ;;
                    esac
                    ;;
            esac
            ;;
        4)
            case ${COMP_WORDS[1]} in
                event)
                    case ${COMP_WORDS[2]} in
                        trigger)
                            case ${COMP_WORDS[3]} in
                                set_direction_pattern)
                                    COMPREPLY=($(compgen -W "forward backward ping_pong random fugue song" -- ${cur}))
                                    return 0
                                    ;;
                                set_step_pattern)
                                    COMPREPLY=($(compgen -W "all_on four_on_the_floor syncopated" -- ${cur}))
                                    return 0
                                    ;;
                            esac
                            ;;
                    esac
                    ;;
            esac
            ;;
    esac
    
    return 0
}

# Register the completion function
complete -F _mme_cli_completion mme-cli
complete -F _mme_cli_completion ./mme-cli
