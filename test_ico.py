from PIL import Image
import os

# Test creating a simple multi-size ico
img = Image.new('RGB', (256, 256), 'red')
img.save('test.ico', format='ICO', sizes=[(256,256), (128,128), (64,64), (32,32), (16,16)])
print(f"Test ico size: {os.path.getsize('test.ico')} bytes")

# Check our actual icon
print(f"AAS ico size: {os.path.getsize('artifacts/aas_hub.ico')} bytes")
