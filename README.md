# N1MM+ to ExpertSDR3 spot bridge

This Python script displays N1MM Logger+ DX spots on the ExpertSDR3 panorama. It receives N1MM+ spot broadcasts over UDP, including spots N1MM+ receives from Telnet clusters, and forwards spot additions and deletions to ExpertSDR3 over a TCI WebSocket. The bridge reconnects automatically if the TCI connection drops.

## Setup

1. In ExpertSDR3, enable the TCI server on port `50001`.
2. In N1MM+, open **Config → Configure Ports → Broadcast Data**, enable **Spots**, and set the destination to `127.0.0.1:12060` if N1MM+ and the bridge run on the same computer.
3. From this folder, install the dependency and start the bridge with Python 3.9 or later.

   ```sh
   python3 -m pip install -r requirements.txt
   python3 main.py
   ```

The bridge logs when it connects to TCI and when it forwards a spot. Press **Ctrl+C** to stop it.

## Build a Windows executable

Install Windows Python 3.9 or later and Git for Windows. From this folder in Git Bash on Windows, run:

```sh
bash build-windows.sh
```

The script installs the build dependencies in a virtual environment under `build/windows` and uses PyInstaller to create `dist/spotscript.exe`. The build runs on Windows. The resulting executable bundles Python and its dependencies, so it can run on a compatible Windows computer without Python installed. [PyInstaller documentation](https://www.pyinstaller.org/en/stable/)

Run `./dist/spotscript.exe` in Git Bash. The executable accepts the same options as `main.py`.

## Network settings

| Option | Default | Use |
| --- | --- | --- |
| `--listen-host` | `127.0.0.1` | Local address that receives N1MM+ broadcasts |
| `--listen-port` | `12060` | UDP port that receives N1MM+ broadcasts |
| `--tci-url` | `ws://127.0.0.1:50001` | WebSocket address of the TCI server |

If N1MM+ runs on a different computer, set its broadcast destination to the bridge computer’s LAN IP and port `12060`. For example, if the bridge computer’s IP is `192.168.1.50`, use `192.168.1.50:12060` in N1MM+ and run:

```sh
python3 main.py --listen-host 192.168.1.50
```

If ExpertSDR3 also runs on a different computer, pass that computer’s WebSocket address with `--tci-url`.

## References

- [N1MM+ spot broadcasts](https://n1mmwp.hamdocs.com/appendices/external-udp-broadcasts/#spot-data)
- [TCI 2.1 protocol](https://raw.githubusercontent.com/ExpertSDR3/TCI/main/TCI%20Protocol%202.1.pdf)
