# Stat FFMPEG

Downloads static ffmpeg builds for Windows, macOS, and Linux.

- Supports Windows, macOS, and Linux
- Supports x86_64 architecture on all platforms, ARM64 on macOS and Linux
- Automatic platform detection and binary caching

## Usage

### Python API

```python
from stat_ffmpeg import get_ffmpeg
ffmpeg_path, ffprobe_path = get_ffmpeg()
print(ffmpeg_path)  # Path to ffmpeg executable
```

### Command Line Interface

After installation, you can use `ffmpeg` and `ffprobe` directly from the command line:

```bash
# Use ffmpeg
ffmpeg -i input.mp4 output.mp3

# Use ffprobe
ffprobe -v quiet -print_format json -show_format input.mp4
```

The CLI commands automatically download and cache the appropriate static binaries for your platform.

### PATH Management

You can also programmatically manage your PATH:

```python
from stat_ffmpeg import add_to_path, remove_from_path

# Add FFmpeg binaries to PATH
add_to_path()

# Add only if FFmpeg is not already available (weak mode)
add_to_path(weak=True)

# Remove from PATH
remove_from_path()
```

## Sources of Static Builds

This package downloads static FFmpeg binaries from the following trusted sources:

### Windows (x86_64 only)

- **Source**: [CODEX FFMPEG @ gyan.dev](https://www.gyan.dev/ffmpeg/builds/)
- **URL**: `https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip`
- **Description**: Official Windows builds, 64-bit static binaries licensed as GPLv3

### macOS

#### Intel (x86_64)

- **Source**: [OSXExperts.net](http://www.osxexperts.net/)
- **URLs**:
  - FFmpeg: `https://www.osxexperts.net/ffmpeg71intel.zip`
  - FFprobe: `https://www.osxexperts.net/ffprobe71intel.zip`
- **Description**: Static FFmpeg 7.1 binaries for macOS Intel processors

#### Apple Silicon (arm64)

- **Source**: [OSXExperts.net](http://www.osxexperts.net/)
- **URLs**:
  - FFmpeg: `https://www.osxexperts.net/ffmpeg711arm.zip`
  - FFprobe: `https://www.osxexperts.net/ffprobe711arm.zip`
- **Description**: Static FFmpeg 7.1.1 binaries optimized for Apple Silicon processors

### Linux (x86_64 and arm64)

- **Source**: [John Van Sickle - FFmpeg Static Builds](https://johnvansickle.com/ffmpeg/)
- **URLs**:
  - x86_64: `https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz`
  - arm64: `https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz`
- **Description**: Latest versions of FFmpeg for Linux kernels 3.2.0+, statically linked

## Caching

Downloaded binaries are cached in the package's `binaries/` directory to avoid re-downloading. Each virtual environment gets its own copy of the binaries.

The cache is organized by platform and architecture (e.g., `linux-amd64`, `windows-amd64`, `osx-arm64`).

### Cache Management

```python
from stat_ffmpeg import clear_cache

# Clear all cached binaries
clear_cache()
```

Or use the command line:

```bash
clear_cache
```
