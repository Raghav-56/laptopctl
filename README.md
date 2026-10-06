# laptopctl

A small Bash command-line tool for checking and controlling common laptop services and hardware state on systemd-based Linux.

## Requirements

- Bash
- systemd tools (`systemctl`, `loginctl`)
- Common status utilities such as `awk`, `df`, `free`, `ps`, and `uptime`
- Optional: `nmcli` and `tailscale` for network and Tailscale details
- `sudo` for commands that change system state

The status commands read information from systemd, `/proc`, and `/sys`. Control commands use `sudo` to start or stop services, change the default boot target, set backlight power, or terminate a login session. Review the script before running it, especially before using commands that change state.

## Install

```sh
install -Dm755 laptopctl ~/.local/bin/laptopctl
```

Make sure `~/.local/bin` is on your `PATH`. Then run `laptopctl --help`.

## Shell setup

The `shell/` directory tracks the personal additions used on this laptop:

- `shell/path.sh` adds the installed local, Bun, OpenCode, and system administration directories to `PATH`, without adding duplicates. It also sets `BUN_INSTALL` when Bun is installed. Bash and POSIX shells can source it.
- `shell/bashrc.bash` loads that environment, defines `lstat`, and initializes zoxide when installed. It includes commented shortcuts for laptop controls and only runs in interactive Bash shells.

With this checkout at `~/laptopctl`, add this at the end of `~/.bashrc`:

```bash
if [ -r "$HOME/laptopctl/shell/bashrc.bash" ]; then
    . "$HOME/laptopctl/shell/bashrc.bash"
fi
```

Add this at the end of `~/.profile` so login shells also get the tool paths:

```sh
if [ -r "$HOME/laptopctl/shell/path.sh" ]; then
    . "$HOME/laptopctl/shell/path.sh"
fi
```

Replace the existing personal PATH, Bun, OpenCode, `lstat`, and zoxide additions with these hooks. Keep the rest of your shell configuration. Adjust both hook paths if you move the checkout. Edit the tracked files to change these settings, then open a new shell or run `source ~/.bashrc`.

The command in `~/.local/bin/laptopctl` is an installed copy. Rerun the install command after editing the CLI.

## Usage

```text
laptopctl [status] [--all]
laptopctl gui {on|off|status}
laptopctl rdp {on|off|status}
laptopctl backlight {on|off|status}
laptopctl boot {gui|headless|status}
laptopctl sessions [-x|--exclude-xrdp]
laptopctl kill SESSION_ID
```

Short aliases are available for the command groups (`g`, `r`, `bl`, `b`, `s`, and `k`). Run `laptopctl --help` for examples and all options.

## Platform notes

This tool targets Linux systems that use systemd. Battery, lid, thermal, and backlight details depend on the hardware and kernel interfaces exposed by the machine, so some fields may report `unavailable`.
