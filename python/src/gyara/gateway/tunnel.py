"""Serve the live Gyara Gateway through a public Cloudflare quick tunnel.

For sharing a working endpoint with developers without hosting infrastructure: loads
N-ATLAS, serves the Gateway, and prints a public ``https://...trycloudflare.com`` URL
(no Cloudflare account needed) that stays up while the notebook cell runs.

Run from a GPU notebook (Kaggle/Colab)::

    import os
    os.environ["GYARA_API_KEY"] = "a-shared-secret"   # so only your testers can call it
    from gyara.gateway.tunnel import main
    main()

Testers then call ``<url>/v1/structured`` with ``Authorization: Bearer a-shared-secret``.
This is GPU/network glue, so it is not part of the local test suite.
"""

from __future__ import annotations

import os
import re
import stat
import subprocess
import threading
import time
import urllib.error
import urllib.request

_CLOUDFLARED_URL = (
    "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
)
_TUNNEL_RE = re.compile(r"https://[-\w.]+\.trycloudflare\.com")


def _serve(app: object, port: int) -> None:
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def _wait_for_health(port: int, timeout: float = 90) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            time.sleep(1)
    return False


def _download_cloudflared(path: str = "cloudflared") -> str:
    if not os.path.exists(path):
        urllib.request.urlretrieve(_CLOUDFLARED_URL, path)
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
    return path


def main(port: int = 8000) -> None:
    """Load N-ATLAS, serve the Gateway, and print a public tunnel URL (blocks)."""
    from ..runtime import load_dotenv, load_natlas
    from ..structured import PromptedJsonBackend
    from .app import create_app

    load_dotenv()
    api_key = os.environ.get("GYARA_API_KEY")
    if not api_key:
        print("WARNING: GYARA_API_KEY is not set — the tunnel will be open to anyone.")

    print("Loading N-ATLAS (first run downloads ~16 GB)...")
    model, tokenizer = load_natlas()
    app = create_app(PromptedJsonBackend(model, tokenizer), api_key=api_key)

    threading.Thread(target=_serve, args=(app, port), daemon=True).start()
    if not _wait_for_health(port):
        raise RuntimeError("the gateway did not come up on localhost")
    print("Gateway is up locally; opening the public tunnel...")

    binary = _download_cloudflared()
    tunnel = subprocess.Popen(
        [f"./{binary}", "tunnel", "--url", f"http://127.0.0.1:{port}", "--no-autoupdate"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    public_url = None
    assert tunnel.stdout is not None
    for line in tunnel.stdout:
        match = _TUNNEL_RE.search(line)
        if match:
            public_url = match.group(0)
            break

    if public_url is None:
        tunnel.terminate()
        raise RuntimeError("could not obtain a tunnel URL from cloudflared")

    bar = "=" * 64
    print(f"\n{bar}")
    print(f"  PUBLIC ENDPOINT:  {public_url}/v1/structured")
    print(f"  Health check:     {public_url}/health")
    if api_key:
        print("  Auth header:      Authorization: Bearer <your GYARA_API_KEY>")
    print("  Share the endpoint with your testers. Keep this cell running.")
    print(f"{bar}\n")

    try:
        tunnel.wait()  # keep serving until the cell is interrupted
    except KeyboardInterrupt:
        tunnel.terminate()


if __name__ == "__main__":
    main()
