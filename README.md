# Portable FFmpeg

Downloads static ffmpeg builds for Windows, macOS, and Linux.

- Supports Windows, macOS, and Linux
- Supports x86_64 architecture on all platforms, ARM64 on macOS and Linux
- Automatic platform detection and binary caching

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

### Windows (x86_64) and Linux (x86_64 and arm64)

- **Source**: [BtbN FFmpeg Builds](https://github.com/BtbN/FFmpeg-Builds)
- **Description**: GitHub Actions-built GPL static binaries with daily automated releases, supporting tagged version builds (8.0, 7.1)
- **Versions**: LATEST (master), V8 (8.0), V7 (7.1)
- **Legacy V5/V6 (Linux only)**: Older builds are sourced from [John Van Sickle](https://johnvansickle.com/ffmpeg/)

### macOS

#### Intel (x86_64)

- **Source**: [OSXExperts.net](http://www.osxexperts.net/)
- **URLs**:
  - FFmpeg: `https://www.osxexperts.net/ffmpeg80intel.zip`
  - FFprobe: `https://www.osxexperts.net/ffprobe80intel.zip`
- **Description**: Static FFmpeg 8.0 binaries for macOS Intel processors

#### Apple Silicon (arm64)

- **Source**: [OSXExperts.net](http://www.osxexperts.net/)
- **URLs**:
  - FFmpeg: `https://www.osxexperts.net/ffmpeg80arm.zip`
  - FFprobe: `https://www.osxexperts.net/ffprobe80arm.zip`
- **Description**: Static FFmpeg 8.0 binaries optimized for Apple Silicon processors


### Alternative Sources

The following sources provide FFmpeg static builds but are not currently used by this package:

- **[CODEX FFMPEG @ gyan.dev](https://www.gyan.dev/ffmpeg/builds/)**
  - **Platforms**: Windows only
  - **Architectures**: x86_64
  - **Description**: Official Windows builds with essentials and full variants

- **[FFmpeg Martin Riedl](https://ffmpeg.martin-riedl.de/)**
  - **Platforms**: macOS, Linux
  - **Architectures**: x86_64, ARM64
  - **Description**: Regularly updated static builds with comprehensive codec support

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
