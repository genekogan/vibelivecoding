"""Send Strudel code to a running server via WebSocket."""

import asyncio
import json
import sys
import websockets


async def send_code(code: str, evaluate: bool = False, host="localhost", port=8765):
    uri = f"ws://{host}:{port}"
    async with websockets.connect(uri) as ws:
        msg = {"type": "execute", "code": code}
        if evaluate:
            msg["evaluate"] = True
        await ws.send(json.dumps(msg))


def send(code: str, evaluate: bool = False):
    asyncio.run(send_code(code, evaluate))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python strudel_send.py 'code here'")
        sys.exit(1)
    send(sys.argv[1], evaluate="--eval" in sys.argv)
