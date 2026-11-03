# fun_overlay

Overlay animated GIFs on your Hyprland desktop.

## Install

```sh
git clone https://github.com/ShibamDey69/fun_overlay.git
cd fun_overlay
```

Dependencies (Arch):
```sh
sudo pacman -S python-gobject python-pillow gtk-layer-shell python-cairo
```

## Run

```sh
python3 main.py your_gif.gif
```

## Autostart with systemd (user service)

Create `~/.config/systemd/user/fun_overlay.service`:

```ini
[Unit]
Description=Fun Overlay
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /path/to/fun_overlay/main.py /path/to/fun_overlay/your_gif.gif
Restart=on-failure
Environment=DISPLAY=:0
Environment=XDG_RUNTIME_DIR=%t
Environment=WAYLAND_DISPLAY=wayland-1

[Install]
WantedBy=graphical-session.target
```

Then enable and start:
```sh
systemctl --user daemon-reload
systemctl --user enable --now fun_overlay.service
```

> Replace `/path/to/fun_overlay/` with the actual path.

## Files
```
 main.py
 your_gif.gif
```

## ✅ Supported

- Hyprland  
- Sway  
- KDE Plasma (Wayland)  
- Any compositor with `zwlr_layer_shell_v1` support

## ❌ Not supported

- GNOME (Wayland or X11)  
- Weston  
- X11-only setups (no true overlay)  
- Any compositor that doesn’t implement layer-shell protocol
