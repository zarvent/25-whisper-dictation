import asyncio
import subprocess
import sys
import time
import os
from pathlib import Path
from v2m.sdk import V2MClient

async def run_test():
    print("Starting Daemon...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")

    daemon_process = subprocess.Popen(
        [sys.executable, "-m", "v2m.daemon"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    time.sleep(2)
    client = V2MClient()

    try:
        print("Connecting...")
        connected = await client.connect()
        assert connected
        print("✅ Connected")

        print("Killing Daemon...")
        daemon_process.terminate()
        daemon_process.wait()

        print("Starting Daemon again (simulating restart)...")
        daemon_process = subprocess.Popen(
            [sys.executable, "-m", "v2m.daemon"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Don't sleep here, let the retry logic handle the wait

        print("Sending ping (should retry)...")
        start_time = time.time()
        pong = await client._send_request("ping")
        end_time = time.time()

        print(f"Ping response: {pong}")
        assert pong == "pong"
        print(f"✅ Reconnected and Ping successful (took {end_time - start_time:.2f}s)")

    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        if daemon_process:
            daemon_process.terminate()
            try:
                daemon_process.wait(timeout=2)
            except:
                daemon_process.kill()

if __name__ == "__main__":
    asyncio.run(run_test())
