# PixelJunk™ Monsters Archive Extractor

A Python utility to extract and reconstruct the contents of the custom `.pkiwin` and `.pkdwin` archives used in the PC release of *PixelJunk™ Monsters Ultimate*.

## Overview

The game engine uses a proprietary archive format and references files using a custom string-hashing algorithm based on FNV-1. Because of this, the archive index only contains 32-bit hashes, not the original file paths or extensions.

This script accomplishes two main tasks:
1. **Dictionary Resolution**: It uses a pre-computed dictionary file (`asset_paths.txt`) containing original game paths recovered from the game's executable and scripts. By running the hashing algorithm in reverse against these known strings, the script successfully maps internal hashes back to their exact original folder structures and filenames.
2. **Intelligent Fallback**: For any hashes not present in the dictionary, the script analyzes the uncompressed byte headers to intelligently guess the file type (such as `.dds`, `.wav`, `.ogg`). It also features detection for game-specific formats:
    - **GameMonkey Scripts (`.gm`)**: Detects both UTF-8 and UTF-16 LE scripts, and parses their file headers to self-recover their original filenames.
    - **Binary Fonts (`.fnt`)**: Detects `0x10000005` and `FONT` magic headers.
    - **Grid Data (`.grid`)**: Detects custom 8x8 data grids.

Not all hashes have been resolved yet, but the result is 100+ files organized in the original structure when the game was built. The remaining 900+ files will be placed in an _unknown folder organized by their fallback types.

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
