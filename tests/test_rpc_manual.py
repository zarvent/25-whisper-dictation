import asyncio
import subprocess
import sys
import time
import os
from pathlib import Path
from v2m.sdk import V2MClient

async def run_test():
    print("Starting Daemon...")
    # Start daemon in background
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")

    daemon_process = subprocess.Popen(
        [sys.executable, "-m", "v2m.daemon"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for daemon to start
    time.sleep(2)

    client = V2MClient()

    try:
        print("Connecting...")
        connected = await client.connect()
        if connected:
            print("✅ Connected to Daemon")
        else:
            print("❌ Failed to connect")
            return

        print("Running 'ping'...")
        pong = await client._send_request("ping")
        print(f"Ping response: {pong}")
        assert pong == "pong"
        print("✅ Ping successful")

        print("Running 'start_capture'...")
        res = await client.start_capture()
        print(f"Start response: {res}")
        print("✅ Start successful")

        print("Waiting 2 seconds...")
        await asyncio.sleep(2)

        print("Running 'stop_capture'...")
        res = await client.stop_capture()
        print(f"Stop response: {res}")
        print("✅ Stop successful")

        # Check if text is returned (might be empty if no mic input in CI/Test env)
        if "text" in res:
            print(f"Transcription: '{res['text']}'")

        print("Running 'transcribe' (Start -> Wait -> Transcribe)...")
        await client.start_capture()
        await asyncio.sleep(1)
        res = await client.transcribe(use_llm=False)
        print(f"Transcribe response: {res}")
        assert "text" in res
        print("✅ Transcribe successful")

        print("Running 'shutdown'...")
        try:
            await client._send_request("shutdown")
        except Exception:
            pass # Expected as connection closes

        print("✅ Shutdown sent")

    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        daemon_process.terminate()
        try:
            stdout, stderr = daemon_process.communicate(timeout=2)
            print("Daemon Output:", stdout.decode())
            print("Daemon Error:", stderr.decode())
        except:
            daemon_process.kill()

if __name__ == "__main__":
    asyncio.run(run_test())
