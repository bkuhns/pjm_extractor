import sys
import struct
import argparse
import os

def fnv1_hash(string):
    """
    Computes the 32-bit FNV-1 hash of a string exactly as the game engine does.
    The engine expects paths to be normalized (forward slashes and lowercased).
    """
    h = 0x811c9dc5
    
    # Normalize the string as the engine does before hashing
    normalized = string.lower().replace('\\', '/')
    
    for char in normalized:
        h = ((h * 0x01000193) & 0xFFFFFFFF) ^ ord(char)
    return h & 0xFFFFFFFF

def load_archive_hashes(pki_path):
    """
    Loads all hashes from the monsters.pkiwin index file.
    """
    hashes = set()
    try:
        with open(pki_path, 'rb') as f:
            f.seek(8)
            num_files, = struct.unpack('<I', f.read(4))
            
            f.seek(16)
            for _ in range(num_files):
                entry = f.read(16)
                if len(entry) < 16:
                    break
                _, _, h, _ = struct.unpack('<IIII', entry)
                hashes.add(h)
    except Exception as e:
        print(f"Error reading {pki_path}: {e}")
        sys.exit(1)
        
    return hashes

def main():
    parser = argparse.ArgumentParser(description="PixelJunk Monsters FNV-1 Hash Tester")
    parser.add_argument("string", nargs='?', help="A specific string/path to hash and test.")
    parser.add_argument("-p", "--pki", help="Path to monsters.pkiwin to test the hash against.", default="monsters.pkiwin")
    parser.add_argument("-f", "--file", help="A text file containing a list of strings (one per line) to test.")
    
    args = parser.parse_args()
    
    if not args.string and not args.file:
        parser.print_help()
        sys.exit(1)

    print(f"Loading target hashes from {args.pki}...")
    target_hashes = set()
    if os.path.exists(args.pki):
        target_hashes = load_archive_hashes(args.pki)
        print(f"Loaded {len(target_hashes)} hashes.\n")
    else:
        print("Warning: PKI file not found. Hashes will only be calculated, not verified against the archive.\n")

    strings_to_test = []
    if args.string:
        strings_to_test.append(args.string)
        
    if args.file and os.path.exists(args.file):
        with open(args.file, 'r', encoding='utf-8', errors='ignore') as f:
            strings_to_test.extend([line.strip() for line in f if line.strip()])
            
    matches = 0
    for s in strings_to_test:
        h = fnv1_hash(s)
        hex_hash = hex(h)
        
        status = ""
        if target_hashes:
            if h in target_hashes:
                status = "[MATCH FOUND IN ARCHIVE]"
                matches += 1
            else:
                status = "[NO MATCH]"
                
        print(f"{hex_hash.ljust(12)} : {s} {status}")

    if target_hashes and len(strings_to_test) > 1:
        print(f"\nTotal matches found in archive: {matches} / {len(strings_to_test)}")

if __name__ == '__main__':
    main()
