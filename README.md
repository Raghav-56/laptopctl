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
