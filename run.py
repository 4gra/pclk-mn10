#!/usr/bin/env python3
import stub
from inspect import getmembers, isfunction, signature
from sys import argv


def queries():
    return dict([ (o[0][4:],o[1]) for o in getmembers(stub) if isfunction(o[1]) and o[0][:4] == 'cmd_'])


def get_usage(func):
    """
    Returns introspective usage text for a given function, assuming its name
    follows the "cmd_" format.
    """
    # Print argument as <x> or [x] according to requirement.  Ignore (self, output)
    spec = signature(func)
    shortname = func.__name__[4:]
    doc = func.__doc__ or "   [No documentation provided]"
    sargs = []
    for param in spec.parameters:
        if spec.parameters[param].default == spec.empty:
            sargs += [ f'<{param}>' ]
        else:
            sargs += [ f'[{param}]' ]
    allargs = " ".join(sargs)
    return f"{shortname} {allargs}{doc}" 


def usage(key=None):
    """Prints full usage information."""
    map = queries()
    if key == None:
        keys = list(queries().keys())
        keys.sort()
        text = "Usage: %s [options] <command> [arguments]\n" % argv[0]
        #text += "Where options are:\n\n"
        #text += "  --html   : print output in HTML format (suggest use of -q)\n"
        #text += "  --simple : lists, not tables.\n"
        #text += "  --quiet }. make less noise; \n"
        #text += "  -q      }. do not print source SQL query\n"
        text += "  --bash-completion ...\n"
        #text += "           : display tab completion code\n"
        #text += "\n"
        text += "Where command, arguments are amongst:\n\n"
        text += "\n".join(["  %s" % (get_usage(map[k])) for k in keys])
    else:
        text = "Usage: %s %s" % (argv[0], get_usage(map[key]))
    return text


if __name__ == '__main__':
    from sys import argv, exit
    print ( usage() )

    while '--bash-completion' in argv:
        print('''\
# Source this function to provide bash completion⋅
# Hint: run ". <(run --bash-completion)" to source inline.
# --- begin pclk bash completion ---
function _pclk() {
    local cur prev cmd opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    cmd="${COMP_WORDS[1]}"
    opts=$(./run.py help|grep -oe '^  [^ ]\+')
    case $prev in
        ./run.py|./control|-*)
            COMPREPLY=( $( compgen -W "${opts}" -- ${cur} ) )
            ;;
        *)
            return 0
            ;;
    esac
}; complete -F _pclk control ./run.py
# --- end pclk bash completion ---
        ''')
        exit(0)
    
