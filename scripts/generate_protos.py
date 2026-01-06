import os
import subprocess
import sys

def generate_protos():
    """
    Generates Python gRPC code from bridge.proto.
    """
    proto_path = "core/ipc/protos/bridge.proto"
    output_path = "core/ipc/protos"
    
    print(f"Generating gRPC code from {proto_path}...")
    
    command = [
        sys.executable,
        "-m", "grpc_tools.protoc",
        f"-I.",
        f"--python_out=.",
        f"--grpc_python_out=.",
        proto_path
    ]
    
    try:
        # Run from the AAS root directory
        subprocess.run(command, check=True, cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        print("Successfully generated gRPC code.")
    except subprocess.CalledProcessError as e:
        print(f"Error generating gRPC code: {e}")
        sys.exit(1)

if __name__ == "__main__":
    generate_protos()
