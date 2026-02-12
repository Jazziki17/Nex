"""
Entry point for the Nex API server.
Run with: python -m nex.api
"""

import uvicorn

from nex.api.server import PORT


def main():
    print("\033[36m")
    print("  ╔══════════════════════════════════════╗")
    print(f"  ║        NEX API SERVER v0.1.0          ║")
    print(f"  ║   http://localhost:{PORT}              ║")
    print(f"  ║   ws://localhost:{PORT}/ws              ║")
    print("  ╚══════════════════════════════════════╝")
    print("\033[0m")

    uvicorn.run(
        "nex.api.server:app",
        host="0.0.0.0",
        port=PORT,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    main()
