# Portable FFmpeg

Downloads static FFmpeg builds for Windows, macOS, and Linux.

- Supports Windows, macOS, and Linux
- Supports x86_64 architecture on all platforms, ARM64 on macOS and Linux
- Automatic platform detection and binary caching
- Explicit FFmpeg 9.0 support on Windows amd64 and macOS amd64/arm64

## Usage

### Python API

```python
from portable_ffmpeg import get_ffmpeg
ffmpeg_path, ffprobe_path = get_ffmpeg()
print(ffmpeg_path)  # Path to ffmpeg executable
```

### Command Line Interface

After installation, you can use `static_ffmpeg` and `static_ffprobe` directly from the command line:

```bash
# Use static ffmpeg
static_ffmpeg -i input.mp4 output.mp3

# Use static ffprobe
static_ffprobe -v quiet -print_format json -show_format input.mp4

# Print paths to the binaries
print_paths
```

The CLI commands automatically download and cache the appropriate static binaries for your platform.

### PATH Management

You can also programmatically manage your PATH:

```python
from portable_ffmpeg import add_to_path, remove_from_path

# Add FFmpeg binaries to PATH
add_to_path()

# Add only if FFmpeg is not already available (weak mode)
add_to_path(weak=True)

# Remove from PATH
remove_from_path()
```

## Sources of Static Builds

This package downloads static FFmpeg binaries from the following trusted sources:

### Windows (x86_64)

- **Source**: [BtbN FFmpeg Builds](https://github.com/BtbN/FFmpeg-Builds)
- **Description**: GitHub Actions-built GPL static binaries with daily automated releases and tagged version builds
- **Versions**: LATEST remains the rolling BtbN master build; V8 selects the current BtbN 8.1 asset and V7 retains its existing 7.1 mapping
- **V9**: [GyanD/codexffmpeg 9.0 essentials](https://github.com/GyanD/codexffmpeg/releases/download/9.0/ffmpeg-9.0-essentials_build.zip), with SHA256 `e6b54767a6065919048f1a098eb27211ca4e12b4348a05d88777a5855d0b6e71`
- **License**: The verified GyanD archive includes a GNU GPLv3 `LICENSE` file.

### Linux (x86_64 and arm64)

- **Source**: [BtbN FFmpeg Builds](https://github.com/BtbN/FFmpeg-Builds) for LATEST, V8, and V7
- **V9**: Not configured until BtbN or another trusted source publishes a redistributable stable 9.0 build. Martin Riedl's Linux 9.0 build metadata enables nonfree DeckLink support, so it is not used as a package default.
- **Legacy V5/V6 (Linux only)**: Older builds are sourced from [John Van Sickle](https://johnvansickle.com/ffmpeg/)

### macOS

#### FFmpeg 9.0 (Intel and Apple Silicon)

- **Source**: [Martin Riedl's FFmpeg Build Server](https://ffmpeg.martin-riedl.de/)
- **LATEST and V9**: Both select the verified stable FFmpeg 9.0 release assets below. Each asset has a matching `.sha256` sidecar.
- **License**: The verified macOS V9 binaries report GPLv3.

| Architecture | FFmpeg | FFprobe |
| --- | --- | --- |
| Intel (amd64) | `https://ffmpeg.martin-riedl.de/download/macos/amd64/1785871427_9.0/ffmpeg.zip` | `https://ffmpeg.martin-riedl.de/download/macos/amd64/1785871427_9.0/ffprobe.zip` |
| Apple Silicon (arm64) | `https://ffmpeg.martin-riedl.de/download/macos/arm64/1785863997_9.0/ffmpeg.zip` | `https://ffmpeg.martin-riedl.de/download/macos/arm64/1785863997_9.0/ffprobe.zip` |

The existing OSXExperts mappings remain available for explicit V8 and V7 selections.

### Version coverage

| Selector | Windows amd64 | Linux amd64/arm64 | macOS amd64/arm64 |
| --- | --- | --- | --- |
| `LATEST` | BtbN rolling master | BtbN rolling master | Martin Riedl stable 9.0 |
| `V9` | GyanD/codexffmpeg stable 9.0 | Not configured pending a redistributable stable 9.0 asset | Martin Riedl stable 9.0 |
| `V8`, `V7` | BtbN 8.1/7.1 | BtbN 8.1/7.1 | Existing OSXExperts 8.0/7.x mappings |
| `V6`, `V5` | Not configured | Existing John Van Sickle mappings | Not configured |


### Alternative Sources

The following sources provide FFmpeg static builds but are not currently used by this package:

- **[EverMeet FFmpeg](https://evermeet.cx/ffmpeg/)**
  - **Platforms**: macOS only
  - **Architectures**: x86_64
  - **Description**: Long-standing macOS static builds provider

- **[FreeBSD FFmpeg Static](https://github.com/Thefrank/ffmpeg-static-freebsd/)**
  - **Platforms**: FreeBSD only
  - **Architectures**: Various
  - **Description**: Static builds specifically for FreeBSD systems

- **[John Van Sickle](https://johnvansickle.com/ffmpeg/)**
  - **Platforms**: Linux
  - **Architectures**: x86_64, ARM64, i686, armhf, armel
  - **Description**: Static Linux builds (used for legacy V5/V6 version support)

## Caching

Downloaded binaries are cached in the package's `binaries/` directory to avoid re-downloading. Each virtual environment gets its own copy of the binaries.

The cache is organized by platform and architecture (e.g., `linux-amd64`, `windows-amd64`, `osx-arm64`).

### Cache Management

```python
from portable_ffmpeg import clear_cache

# Clear all cached binaries
clear_cache()
```

Or use the command line:

```bash
clear_cache
```
