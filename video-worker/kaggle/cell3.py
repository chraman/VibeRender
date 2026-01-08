# Kill anything running on port 8000
!fuser -k 8000/tcp
# Force ngrok to close all tunnels
from pyngrok import ngrok
ngrok.kill()
print("✅ Port 8000 and Ngrok tunnels cleared.")