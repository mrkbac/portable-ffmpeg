# Portable FFmpeg

Downloads static FFmpeg builds for Windows, macOS, and Linux.

- Supports Windows, macOS, and Linux
- Supports x86_64 architecture on all platforms, ARM64 on macOS and Linux
- Automatic platform detection and binary caching
- Explicit FFmpeg 9.0 support on Windows amd64, Linux amd64/arm64, and macOS amd64/arm64

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
- **Versions**: LATEST is the rolling BtbN master build; V9 and V8 select the rolling BtbN 9.0 and 8.1 assets
- **V7**: BtbN only keeps its two newest release branches in `latest`, so V7 is pinned to the last tagged 7.1 build ([autobuild-2026-07-31-14-10](https://github.com/BtbN/FFmpeg-Builds/releases/tag/autobuild-2026-07-31-14-10), FFmpeg 7.1.5)

### Linux (x86_64 and arm64)

- **Source**: [BtbN FFmpeg Builds](https://github.com/BtbN/FFmpeg-Builds) for LATEST, V9, V8, and V7 (V7 pinned as on Windows)
- **Legacy V5/V6 (Linux only)**: Older builds are sourced from [John Van Sickle](https://johnvansickle.com/ffmpeg/)

### macOS

#### FFmpeg 9.0.2 (Intel and Apple Silicon)

- **Source**: [Martin Riedl's FFmpeg Build Server](https://ffmpeg.martin-riedl.de/)
- **LATEST and V9**: Both select the verified stable FFmpeg 9.0.2 release assets below. Each asset has a matching `.sha256` sidecar.
- **License**: The verified macOS V9 binaries report GPLv3.

| Architecture | FFmpeg | FFprobe |
| --- | --- | --- |
| Intel (amd64) | `https://ffmpeg.martin-riedl.de/download/macos/amd64/1789931006_9.0.2/ffmpeg.zip` | `https://ffmpeg.martin-riedl.de/download/macos/amd64/1789931006_9.0.2/ffprobe.zip` |
| Apple Silicon (arm64) | `https://ffmpeg.martin-riedl.de/download/macos/arm64/1789931890_9.0.2/ffmpeg.zip` | `https://ffmpeg.martin-riedl.de/download/macos/arm64/1789931890_9.0.2/ffprobe.zip` |

The existing OSXExperts mappings remain available for explicit V8 and V7 selections.

### Version coverage

| Selector | Windows amd64 | Linux amd64/arm64 | macOS amd64/arm64 |
| --- | --- | --- | --- |
| `LATEST` | BtbN rolling master | BtbN rolling master | Martin Riedl stable 9.0.2 |
| `V9`, `V8` | BtbN rolling 9.0/8.1 | BtbN rolling 9.0/8.1 | Martin Riedl stable 9.0.2 / OSXExperts 8.0 |
| `V7` | BtbN pinned 7.1.5 | BtbN pinned 7.1.5 | OSXExperts 7.x |
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
