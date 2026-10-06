# Personal additions for interactive Bash shells.
# Source this file from ~/.bashrc.

case $- in
    *i*) ;;
    *) return 0 ;;
esac

. "${BASH_SOURCE[0]%/*}/path.sh"

alias lstat='laptopctl status'

if command -v zoxide >/dev/null 2>&1; then
    eval "$(zoxide init bash)"
fi

# Optional shortcuts. Uncomment the aliases you want to use.
# alias gui-on='laptopctl gui on'
# alias gui-off='laptopctl gui off'
# alias gui-status='laptopctl gui status'
# alias rdp-on='laptopctl rdp on'
# alias rdp-off='laptopctl rdp off'
# alias rdp-status='laptopctl rdp status'
# alias rdp-sessions='laptopctl sessions'
# alias bl-on='laptopctl backlight on'
# alias bl-off='laptopctl backlight off'
# alias bl-status='laptopctl backlight status'
# alias boot-headless='laptopctl boot headless'
# alias boot-gui='laptopctl boot gui'
# alias boot-status='laptopctl boot status'
