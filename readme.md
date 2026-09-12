# PixelJunk™ Monsters Archive Extractor

A Python utility to extract and reconstruct the contents of the custom `.pkiwin` and `.pkdwin` archives used in the PC release of *PixelJunk™ Monsters Ultimate*.

## Overview

The game engine uses a proprietary archive format and references files using a custom string-hashing algorithm based on FNV-1. Because of this, the archive index only contains 32-bit hashes, not the original file paths or extensions.

This script accomplishes two main tasks:
1. **Dictionary Resolution**: It uses a pre-computed dictionary file (`asset_paths.txt`) containing original game paths recovered from the game's executable and scripts. By running the hashing algorithm in reverse against these known strings, the script successfully maps internal hashes back to their exact original folder structures and filenames.
2. **Fallback**: For any hashes not present in the dictionary, the script analyzes the uncompressed byte headers to guess the file type (such as `.dds`, `.wav`, `.ogg`). It also features detection for game-specific formats:
    - **GameMonkey Scripts (`.gm`)**: Detects both UTF-8 and UTF-16 LE scripts, and parses their file headers to self-recover their original filenames.
    - **Binary Fonts (`.fnt`)**: Detects `0x10000005` and `FONT` magic headers.
    - **Grid Data (`.grid`)**: Detects custom 8x8 data grids (their purpose is still a mystery).

Not all hashes have been resolved yet, but the known files are organized in the same structure used when the game was originally built. The remaining files will be placed in an _unknown folder organized by their fallback types.

## Requirements

- Python 3.6 or higher.
- No external dependencies required (uses only standard libraries).

## Usage

You can run the script directly from the command line, pointing it to your game's installation directory (where `monsters.pkiwin` and `monsters.pkdwin` are located).

```bash
python extract_monsters.py <path_to_game_dir>
```

### Options

```text
usage: extract_monsters.py [-h] [-o OUTPUT] [-d DICT] [-f] game_dir

Extract PixelJunk™ Monsters PC archives (pkiwin/pkdwin).

positional arguments:
  game_dir             Path to the game installation directory containing
                       monsters.pkiwin and monsters.pkdwin.

options:
  -h, --help           show this help message and exit
  -o, --output OUTPUT  Output directory for extracted files. Defaults to
                       './monsters_extracted'.
  -d, --dict DICT      Path to the dictionary file containing known paths.
                       Defaults to 'asset_paths.txt' in script directory.
  -f, --force          Force extraction even if output directory is not empty.
```

### Examples

Extract files to the default `monsters_extracted` folder in the current directory:
```bash
python extract_monsters.py "C:\Program Files (x86)\Steam\steamapps\common\Monsters"
```

Extract files to a custom directory, forcing an overwrite if it already exists:
```bash
python extract_monsters.py "C:\Program Files (x86)\Steam\steamapps\common\Monsters" -o "C:\MyExtractFolder" -f
```

## Files
- `extract_monsters.py`: The main extraction tool.
- `asset_paths.txt`: A mapping dictionary of `hash : path` used to reconstruct original folder structures.
- `test_hashes.py`: A utility script for testing arbitrary strings against the game's hashing algorithm.

## Testing Hash Paths

The `test_hashes.py` script can be used to test paths with known hashes from the game's package file. It replicates the engine's internal FNV-1 string normalization and hashing logic.

You can test a single suspected path directly against the game's archive index:
```bash
python test_hashes.py "./data-common/scripts/scene/title.gm" -p "C:\Program Files (x86)\Steam\steamapps\common\Monsters\monsters.pkiwin"
```

Or, you can provide a text file containing multiple paths (one per line) to brute-force matches all at once:
```bash
python test_hashes.py -f my_strings_to_test.txt -p "C:\Program Files (x86)\Steam\steamapps\common\Monsters\monsters.pkiwin"
```

The script will calculate the hash and output whether a `[MATCH FOUND IN ARCHIVE]` or `[NO MATCH]` was hit.
