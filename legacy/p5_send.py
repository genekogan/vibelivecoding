"""Send p5.js code to a running server via WebSocket."""

import asyncio
import json
import sys
import websockets


async def send_code(code: str, mode: str = "eval", layer: str = None, host="localhost", port=8775):
    uri = f"ws://{host}:{port}"
    async with websockets.connect(uri) as ws:
        msg = {"type": "execute", "code": code, "mode": mode}
        if layer:
            msg["layer"] = layer
        await ws.send(json.dumps(msg))


def send(code: str, mode: str = "eval", layer: str = None):
    return asyncio.run(send_code(code, mode, layer))


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or "--help" in args:
        print("Usage:")
        print("  python p5_send.py 'code'              # eval mode")
        print("  python p5_send.py --layer NAME 'code'  # set layer")
        print("  python p5_send.py --remove NAME        # remove layer")
        print("  python p5_send.py --clear               # clear all")
        sys.exit(0)

    if "--clear" in args:
        send("", mode="clear")
    elif "--remove" in args:
        idx = args.index("--remove")
        name = args[idx + 1] if idx + 1 < len(args) else "default"
        send("", mode="remove", layer=name)
    elif "--layer" in args:
        idx = args.index("--layer")
        name = args[idx + 1] if idx + 1 < len(args) else "default"
        # Code is any remaining arg that isn't the flag or name
        remaining = [a for i, a in enumerate(args) if i != idx and i != idx + 1]
        code = remaining[0] if remaining else ""
        send(code, mode="layer", layer=name)
    else:
        # Plain eval
        code = args[0]
        send(code)
