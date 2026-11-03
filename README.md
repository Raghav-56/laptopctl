# laptopctl

A small Bash command-line tool for checking and controlling common laptop services and hardware state on systemd-based Linux.

## Requirements

- Bash
- systemd tools (`systemctl`, `loginctl`)
- Common status utilities such as `awk`, `df`, `free`, `ps`, and `uptime`
- Optional: `nmcli` and `tailscale` for network and Tailscale details
- `sudo` for commands that change system state
- Python 3 for RAM-cap commands

The status commands read information from systemd, `/proc`, and `/sys`. Control commands use `sudo` to start or stop services, change the default boot target, set backlight power, or terminate a login session. Review the script before running it, especially before using commands that change state.

## Install

```sh
install -Dm755 laptopctl ~/.local/bin/laptopctl
sudo install -Dm755 laptopctl-ram /usr/local/libexec/laptopctl-ram
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

The commands are installed copies. Rerun the install commands after editing either script. The RAM helper must remain root-owned because systemd uses it to restore timed changes.

## Usage

```text
laptopctl [status] [--all]
laptopctl gui {on|off|status}
laptopctl rdp {on|off|status}
laptopctl backlight {on|off|status}
laptopctl boot {gui|headless|status}
laptopctl sessions [-x|--exclude-xrdp]
laptopctl kill SESSION_ID
laptopctl ram [status [USER]]
laptopctl ram set USER RAM_CAP [--high SIZE] [--swap SIZE]
laptopctl ram boost USER RAM_CAP [--high SIZE] [--swap SIZE] [--for DURATION]
laptopctl ram restore USER
```

Short aliases are available for the command groups (`g`, `r`, `bl`, `b`, `s`, and `k`). Run `laptopctl --help` for examples and all options.

## Manage account RAM caps

Show host memory availability and the current caps for each login account:

```sh
laptopctl ram
laptopctl ram status agrima
```

Save permanent caps, using whole sizes such as `512M` or `8G`:

```sh
laptopctl ram set agrima 8G --high 6G --swap 2G
laptopctl ram set ubuntu 22G --high 20G --swap 7G
```

`RAM_CAP` is the hard RAM limit. `--high` is the threshold for memory reclaim and throttling; it defaults to 90% of the RAM cap. `--swap` keeps the current account swap cap when omitted. Caps must fit within the host's installed RAM and configured swap.

Grant a two-hour increase:

```sh
laptopctl ram boost agrima 12G --high 10G --swap 3G --for 2h
```

A systemd timer restores the previous caps even if you close your terminal. Durations accept seconds, minutes, hours, or days, such as `30s`, `30m`, `2h`, or `1d`. Without `--for`, the increase lasts one hour. Reboot clears temporary changes and restores the saved limits. A second boost replaces the previous deadline and retains the original restoration values.

End the increase early:

```sh
laptopctl ram restore agrima
```

Saving permanent caps with `ram set` also ends any active boost for that account. The tool rejects caps below current memory use unless you pass `--force`, because lowering a hard cap can terminate processes. Check usage before restoring a lower limit, including before a timed increase expires.

Changes require `sudo`; status does not. Timers and temporary state are kept under systemd and `/run/laptopctl-ram`. Existing caps do not change when you install the extension.

These limits cover the account's login sessions and user services in `user-UID.slice`. System services in `system.slice` need their own limits. Account caps share the host's capacity; raising a cap does not reserve RAM.

## Platform notes

This tool targets Linux systems that use systemd. Battery, lid, thermal, and backlight details depend on the hardware and kernel interfaces exposed by the machine, so some fields may report `unavailable`.
