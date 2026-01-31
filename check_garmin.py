from garminconnect import Garmin
import inspect

try:
    print("Checking Garmin class attributes...")
    # We won't login, just inspect the class or a dummy instance
    client = Garmin("dummy", "dummy")
    if hasattr(client, 'garth'):
        print("client.garth exists!")
        from garth.http import Client as GarthClient
        if isinstance(client.garth, GarthClient):
             print("client.garth is a GarthClient instance.")
    else:
        print("client.garth does NOT exist.")
        
    print(f"Dir of client: {dir(client)}")

except Exception as e:
    print(f"Error: {e}")
