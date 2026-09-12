import sys
import os
import struct
import zlib
import string
import argparse

SPECIAL_CASES = {
    0xdcdda077: "_unknown/loc.db",
    0xfc66a1df: "_unknown/gm/credits.gm",
}

def is_text(data):
    if not data:
        return False
    text_chars = sum(1 for b in data[:1024] if b == 9 or b == 10 or b == 13 or (32 <= b <= 255))
    total_chars = len(data[:1024])
    if total_chars > 0 and (text_chars / total_chars) > 0.90 and data[:1024].count(b'\x00') < 5:
        return True
    return False

def guess_file_info(data):
    head = data[:1024]
    if not head:
        return "dat", ".dat"
        
    if head.startswith(b'OggS'):
        return "ogg", ".ogg"
    if head.startswith(b'RIFF') and len(head) >= 12 and head[8:12] == b'WAVE':
        return "wav", ".wav"
    if head.startswith(b'\x89PNG\r\n\x1a\n'):
        return "png", ".png"
    if head.startswith(b'DDS '):
        return "dds", ".dds"
    if head.startswith(b'\xff\xd8\xff'):
        return "jpg", ".jpg"
    if head.startswith(b'BM'):
        return "bmp", ".bmp"
    if head.startswith(b'PK\x03\x04'):
        return "zip", ".zip"
    if head.startswith(b'\x1bLua'):
        return "luac", ".luac"
    if head.startswith(b'<?xml') or (is_text(head) and b'<?xml' in head[:100]):
        return "xml", ".xml"
        
    # Check for UTF-16 LE BOM
    if head.startswith(b'\xff\xfe'):
        return "gm", ".gm"
        
    # Check for FONT magic
    if head.startswith(b'FONT'):
        return "fnt", ".fnt"
        
    if len(data) >= 20:
        v1, size, offset, w, h = struct.unpack('<IIIII', data[:20])
        
        # Check for ajblib::GL::Font::Font magic (0x10000005)
        if v1 == 0x10000005:
            return "fnt", ".fnt"
            
        # Grid files typically have v1=0 or 1, size = w*h, offset=32
        if (v1 == 0 or v1 == 1) and size == w * h and offset == 32 and size > 0:
            return "grid", ".grid"
            
    if is_text(head):
        return "gm", ".gm"
        
    return "dat", ".dat"

def get_gm_internal_name(data):
    # Only check the first 500 bytes for performance
    head = data[:500]
    try:
        if head.startswith(b'\xff\xfe'):
            text = head.decode('utf-16le', errors='ignore')
        else:
            text = head.decode('utf-8', errors='ignore')
            
        lines = text.splitlines()
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            # Match "// filename.gm" or similar
            if line.startswith('//') and line.endswith('.gm'):
                name = line[2:].strip()
                if name.endswith('.gm') and ' ' not in name and '/' not in name and '\\' not in name:
                    return name
    except Exception:
        pass
    return None

def load_dictionary(dict_path):
    hash_to_path = dict(SPECIAL_CASES)
    if not os.path.exists(dict_path):
        return hash_to_path
        
    with open(dict_path, 'r') as f:
        for line in f:
            if ' : ' in line:
                h_str, path = line.strip().split(' : ', 1)
                if path.startswith('./'):
                    path = path[2:]
                h = int(h_str, 16)
                hash_to_path[h] = path
    return hash_to_path

def read_pki_index(pki_path):
    subfiles = []
    with open(pki_path, 'rb') as f:
        f.seek(8)
        num_subfiles = struct.unpack('<I', f.read(4))[0]
        
        f.seek(16)
        for _ in range(num_subfiles):
            entry_data = f.read(16)
            if len(entry_data) < 16:
                break
            sizeCompressed, offset, h, sizeUncompressed = struct.unpack('<IIII', entry_data)
            subfiles.append({
                'sizeUncompressed': sizeUncompressed,
                'sizeCompressed': sizeCompressed,
                'offset': offset,
                'hash': h
            })
    return subfiles

def decompress_data(compressed_data, header):
    try:
        return zlib.decompress(compressed_data, -15)
    except zlib.error:
        try:
            return zlib.decompress(header + compressed_data)
        except zlib.error as e:
            return None

def determine_output_path(h, uncompressed_data, hash_to_path):
    if h in hash_to_path:
        return hash_to_path[h]
        
    folder_name, ext = guess_file_info(uncompressed_data)
    
    custom_name = None
    if ext == ".gm":
        custom_name = get_gm_internal_name(uncompressed_data)
        
    if custom_name:
        return f"_unknown/{folder_name}/{custom_name}"
    else:
        return f"_unknown/{folder_name}/{hex(h)}{ext}"

def extract(pki_path, pkd_path, output_dir, dict_path):
    os.makedirs(output_dir, exist_ok=True)

    print(f"Loading dictionary from {dict_path}...")
    hash_to_path = load_dictionary(dict_path)
    print(f"Loaded {len(hash_to_path)} known paths.")

    print(f"Reading index from {pki_path}...")
    subfiles = read_pki_index(pki_path)
    print(f"Found {len(subfiles)} subfiles.")

    print(f"Extracting data from {pkd_path}...")
    with open(pkd_path, 'rb') as f_pkd:
        for i, sub in enumerate(subfiles):
            f_pkd.seek(sub['offset'])
            
            header = f_pkd.read(2)
            compressed_data = f_pkd.read(sub['sizeCompressed'])
            
            uncompressed_data = decompress_data(compressed_data, header)
            if uncompressed_data is None:
                print(f"Error decompressing file {i}.")
                continue
                
            h = sub['hash']
            rel_path = determine_output_path(h, uncompressed_data, hash_to_path)
            
            out_path = os.path.join(output_dir, rel_path)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, 'wb') as f_out:
                f_out.write(uncompressed_data)
                
            if i > 0 and i % 100 == 0:
                print(f"Extracted {i}/{len(subfiles)} files...")
                
def main():
    parser = argparse.ArgumentParser(description="Extract PixelJunk Monsters PC archives (pkiwin/pkdwin).")
    parser.add_argument("game_dir", help="Path to the game installation directory containing monsters.pkiwin and monsters.pkdwin.")
    parser.add_argument("-o", "--output", help="Output directory for extracted files. Defaults to './monsters_extracted'.")
    parser.add_argument("-d", "--dict", help="Path to the dictionary file containing known paths. Defaults to 'asset_paths.txt' in script directory.")
    parser.add_argument("-f", "--force", action="store_true", help="Force extraction even if output directory is not empty.")
    
    args = parser.parse_args()
    
    pki = os.path.join(args.game_dir, "monsters.pkiwin")
    pkd = os.path.join(args.game_dir, "monsters.pkdwin")
    
    if not os.path.exists(pki) or not os.path.exists(pkd):
        print(f"Error: Could not find monsters.pkiwin or monsters.pkdwin in '{args.game_dir}'")
        sys.exit(1)
        
    out = args.output if args.output else os.path.join(os.getcwd(), "monsters_extracted")
        
    if not args.force and os.path.exists(out) and os.path.isdir(out) and os.listdir(out):
        print(f"Error: Output directory '{out}' already exists and is not empty.")
        print("Use -f/--force to extract anyway.")
        sys.exit(1)
        
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dict_path = args.dict if args.dict else os.path.join(script_dir, "asset_paths.txt")
    
    extract(pki, pkd, out, dict_path)
    print(f"Done! Files extracted to {out}")

if __name__ == '__main__':
    main()
