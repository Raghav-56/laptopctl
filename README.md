# laptopctl

A small Bash command-line tool for checking and controlling desktop services, remote access, and hardware state on systemd-based Linux laptops and servers.

## Requirements

- Bash
- systemd tools (`systemctl`, `loginctl`)
- Common status utilities such as `awk`, `df`, `free`, `ps`, and `uptime`
- Optional: `nmcli` and `tailscale` for network and Tailscale details
- `sudo` for commands that change system state
- Python 3 for RAM and storage commands
- The `quota` package (`repquota` and `setquota`) for storage commands
- Active Linux user quotas on the root filesystem for storage commands

The status commands read information from systemd, `/proc`, and `/sys`. System service and hardware controls use `sudo`; user-level KRdp controls run as the current user. Review the script before running it, especially before using commands that change state.

## Install

```sh
install -Dm755 laptopctl ~/.local/bin/laptopctl
sudo install -Dm755 laptopctl-ram /usr/local/libexec/laptopctl-ram
sudo install -Dm755 laptopctl-storage /usr/local/libexec/laptopctl-storage
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
laptopctl storage [status [USER]]
laptopctl storage set USER SIZE
laptopctl storage remove USER
laptopctl ram [status [USER]]
laptopctl ram set USER RAM_CAP [--high SIZE] [--swap SIZE]
laptopctl ram boost USER RAM_CAP [--high SIZE] [--swap SIZE] [--for DURATION]
laptopctl ram restore USER
```

Short aliases are available for the command groups (`g`, `r`, `bl`, `b`, `s`, and `k`). Run `laptopctl --help` for examples and all options.

## Desktop and remote access

`laptopctl gui` controls the configured `display-manager.service` alias, so it follows the machine's selected display manager, such as SDDM or LightDM. It does not assume a particular desktop or install one. Stopping the display manager ends its desktop session and can lose unsaved work.

`laptopctl rdp` selects an enabled or running user-level `app-org.kde.krdpserver.service` when available. Otherwise it controls the system `xrdp` and `xrdp-sesman` services. Override selection for a command with `LAPTOPCTL_RDP_BACKEND=krdp` or `LAPTOPCTL_RDP_BACKEND=xrdp`; `auto` is the default. KRdp requires an already running KDE session. `rdp off` stops remote access without stopping the desktop; `gui off` stops the desktop itself.

```sh
laptopctl gui on
laptopctl rdp status
laptopctl rdp off
laptopctl rdp on
LAPTOPCTL_RDP_BACKEND=xrdp laptopctl rdp status
```

`laptopctl boot gui` and `boot headless` change the system's default boot target. They do not start or stop the current desktop immediately. A user-only desktop service needs its own lifecycle; it is not controlled by the display-manager alias.

Run the tool on the machine being controlled. For example, `ssh HOST laptopctl status` uses that host's desktop and RDP services. SSH transport and client-side RDP applications remain separate from the local service controller; no remote OS needs to be guessed.

This tool does not configure TLS, credentials, firewall exposure, or Tailscale routing. Restrict the RDP listener appropriately before enabling access. For KRdp, use the systemd user manager and KDE session belonging to the desktop account, rather than running `sudo laptopctl rdp ...`.

Verify changes with:

```sh
bash -n laptopctl
python3 -B -m unittest test_desktop.py test_ram.py test_storage.py
```

## Manage account RAM caps

Show host memory availability and the current caps for each login account:

```sh
laptopctl ram
laptopctl ram status USER
```

Save permanent caps, using whole sizes such as `512M` or `8G`:

```sh
laptopctl ram set USER 8G --high 6G --swap 2G
```

`RAM_CAP` is the hard RAM limit. `--high` is the threshold for memory reclaim and throttling; it defaults to 90% of the RAM cap. `--swap` keeps the current account swap cap when omitted. Caps must fit within the host's installed RAM and configured swap.

Grant a two-hour increase:

```sh
laptopctl ram boost USER 12G --high 10G --swap 3G --for 2h
```

A systemd timer restores the previous caps even if you close your terminal. Durations accept seconds, minutes, hours, or days, such as `30s`, `30m`, `2h`, or `1d`. Without `--for`, the increase lasts one hour. Reboot clears temporary changes and restores the saved limits. A second boost replaces the previous deadline and retains the original restoration values.

End the increase early:

```sh
laptopctl ram restore USER
```

Saving permanent caps with `ram set` also ends any active boost for that account. The tool rejects caps below current memory use unless you pass `--force`, because lowering a hard cap can terminate processes. Check usage before restoring a lower limit, including before a timed increase expires.

Changes require `sudo`; status does not. Timers and temporary state are kept under systemd and `/run/laptopctl-ram`. Existing caps do not change when you install the extension.

These limits cover the account's login sessions and user services in `user-UID.slice`. System services in `system.slice` need their own limits. Account caps share the host's capacity; raising a cap does not reserve RAM.

## Manage account storage limits

The storage helper requires user quota accounting and enforcement to be enabled on the root filesystem before use. Installing it does not enable quotas or set limits. Filesystems and distributions differ; follow the system's quota setup procedure and verify accounting before setting limits.

```sh
laptopctl storage status
laptopctl storage status USER
laptopctl storage set USER 20G
laptopctl storage remove USER
```

The hard limit applies to disk space owned by the user anywhere on the root filesystem. It does not cover separate filesystems. Sizes are whole numbers in MiB, GiB, or TiB, such as `512M`, `20G`, or `1T`. Writes that allocate space fail when the limit is reached. A limit cannot be set below current usage. Removing a limit makes block usage unlimited. These commands preserve existing inode limits, require sudo, and take effect immediately without a reboot. Avoid changing the same user’s quota concurrently with another tool: `setquota` requires the helper to read and then write the inode limits as well. Quotas do not reserve space, so the filesystem can fill before users reach their limits.

## Platform notes

This tool targets Linux systems that use systemd. Battery, lid, thermal, and backlight details depend on the hardware and kernel interfaces exposed by the machine, so some fields may report `unavailable`.
