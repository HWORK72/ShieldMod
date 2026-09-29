🇷🇺 [Читать на русском](README_RU.md)

A hybrid dual-language automation architecture bridging an asynchronous Python speech recognition daemon with a native Java Minecraft mod over low-latency local IPC sockets.

### Key Architectural Highlights:
* **Inter-Process Communication (IPC):** Low-latency local TCP socket architecture establishing deterministic signal bridging between the Python audio listener and the Java game client.
* **Non-Blocking Acoustic Processing:** Real-time microphone audio capture stream decoupling voice recognition compute from the Minecraft main render thread to prevent frame drops.
* **State-Aware Inventory Manipulation:** Bidirectional inventory slot caching that automatically equips the shield upon trigger detection and restores it to its original slot upon dismissal.
* **Decoupled Architecture:** Hybrid polyglot design leveraging Python's audio ecosystem alongside native Java modding APIs (Forge/Fabric).

### Tech Stack:
* Python 3.12 (Voice recognition daemon & socket host)
* Java 17+ (Native Minecraft modding lifecycle)
* SpeechRecognition / PyAudio (Acoustic stream processing)
* TCP/IP Local Sockets (Sub-millisecond IPC)

### Quick Start:
```bash
pip install -r requirements.txt
python main.py
