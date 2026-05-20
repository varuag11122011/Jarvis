# Jarvis
It is a pc assistant based on python that can perform different tasks and ask different questions. It can listen or speak and you can text it too. It is inspired by Jarvis from Iron man.


A production-ready, multi-threaded background voice assistant written in Python. This utility sits minimized quietly in your system tray using zero-freeze interface rendering, loops continuously for a hands-free ambient wake-word command, and leverages high-speed language model execution pipelines.

## ✨ Features

*   **System Tray Integration:** Runs discreetly in the background, keeping your working terminal completely clear.
*   **Asynchronous Wake-Word Engine:** Uses a dedicated daemon thread to passively parse audio arrays for your wake word (`Jarvis`) without hanging.
*   **Audio Race-Condition Prevention:** Implements threading primitives (`threading.Lock`) to stop the listener thread from capturing the assistant's synthesized voice outputs.
*   **Cross-Platform OS Automation:** Native OS terminal mappings to adjust hardware volume scales across Windows (PowerShell), macOS (AppleScript), and Linux (ALSA).
*   **Smart Application Execution:** Fires local system paths (`calc`, `notepad`, etc.) cleanly detached from parent process instances.
*   **Web Automation & Scrape Parsers:** Custom routing tables for web layout indexing alongside a BeautifulSoup search snippet fetcher.
*   **Optional OpenAI Pipeline:** Prompts securely on environment initialization for custom key validation. Uses fast `gpt-4o-mini` structures for swift turnaround latency.

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure your machine is running Python 3.8+ and has an active microphonic capture channel. Install the structural framework components via pip:

```bash
pip install pystray Pillow speech_recognition pyttsx3 requests beautifulsoup4 wikipedia openai
