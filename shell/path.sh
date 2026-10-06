# Shared environment for Bash and POSIX login shells.
# Source this file; do not run it as a command.

if [ -d "$HOME/.bun/bin" ]; then
    export BUN_INSTALL="$HOME/.bun"
fi

# Prepend each installed directory once. The last new entry has priority.
for _laptopctl_path in \
    /sbin /usr/sbin /usr/local/sbin \
    "$HOME/.local/bin" "$HOME/.opencode/bin" "$HOME/.bun/bin"
do
    [ -d "$_laptopctl_path" ] || continue
    case ":${PATH-}:" in
        *:"$_laptopctl_path":*) ;;
        *) PATH="$_laptopctl_path${PATH:+:$PATH}" ;;
    esac
done
export PATH
unset _laptopctl_path
