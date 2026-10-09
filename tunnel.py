from pyngrok import ngrok
import time
import os

# Start a tunnel to port 8000
public_url = ngrok.connect(8000)
print(f"\n\n=======================================================")
print(f"🚀 LIVE URL FOR JUDGES: {public_url}")
print(f"=======================================================\n\n")

# Keep the tunnel alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Closing tunnel")
    ngrok.disconnect(public_url.public_url)
    ngrok.kill()
