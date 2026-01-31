import garth
import os
import shutil

token_dir = "test_tokens"
if os.path.exists(token_dir):
    shutil.rmtree(token_dir)
os.makedirs(token_dir)

# Create a dummy client
client = garth.Client()
# Manually set some dummy data so it has something to save
client.username = "test_user"
# Garth saves if there are tokens. 
# Let's see what garth.save does.
try:
    print("Attempting garth.save(token_dir)...")
    garth.client = client
    garth.save(token_dir)
    print(f"Files in {token_dir}: {os.listdir(token_dir)}")
    for f in os.listdir(token_dir):
        print(f"{f} size: {os.path.getsize(os.path.join(token_dir, f))}")
except Exception as e:
    print(f"Error: {e}")
