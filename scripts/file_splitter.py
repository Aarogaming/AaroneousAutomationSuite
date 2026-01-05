import os
import math
from pathlib import Path
from typing import List

def split_file(file_path: str, chunk_size_mb: int = 45) -> List[str]:
    """
    Splits a large file into smaller chunks.
    
    Args:
        file_path: Path to the file to split
        chunk_size_mb: Size of each chunk in MB (default 45MB to stay under 50MB limit)
        
    Returns:
        List of created chunk paths
    """
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"Error: File {file_path} not found.")
        return []

    file_size = file_path.stat().st_size
    chunk_size_bytes = chunk_size_mb * 1024 * 1024
    num_chunks = math.ceil(file_size / chunk_size_bytes)
    
    print(f"Splitting {file_path.name} ({file_size / (1024*1024):.2f} MB) into {num_chunks} chunks...")
    
    chunk_paths = []
    with open(file_path, 'rb') as f:
        for i in range(num_chunks):
            chunk_name = f"{file_path.name}.part{i+1:03d}"
            chunk_path = file_path.parent / chunk_name
            
            chunk_data = f.read(chunk_size_bytes)
            with open(chunk_path, 'wb') as chunk_file:
                chunk_file.write(chunk_data)
            
            chunk_paths.append(str(chunk_path))
            print(f"  Created {chunk_name}")
            
    return chunk_paths

def join_files(original_filename: str, directory: str):
    """
    Reassembles chunks into the original file.
    """
    dir_path = Path(directory)
    chunks = sorted(list(dir_path.glob(f"{original_filename}.part*")))
    
    if not chunks:
        print(f"No chunks found for {original_filename} in {directory}")
        return

    output_path = dir_path / original_filename
    print(f"Reassembling {original_filename} from {len(chunks)} chunks...")
    
    with open(output_path, 'wb') as output_file:
        for chunk in chunks:
            with open(chunk, 'rb') as f:
                output_file.write(f.read())
            print(f"  Joined {chunk.name}")
            
    print(f"Successfully reassembled {output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage:")
        print("  Split: python scripts/file_splitter.py split <file_path> [chunk_size_mb]")
        print("  Join:  python scripts/file_splitter.py join <original_filename> <directory>")
        sys.exit(1)
        
    action = sys.argv[1].lower()
    if action == "split":
        path = sys.argv[2]
        size = int(sys.argv[3]) if len(sys.argv) > 3 else 45
        split_file(path, size)
    elif action == "join":
        filename = sys.argv[2]
        directory = sys.argv[3]
        join_files(filename, directory)
