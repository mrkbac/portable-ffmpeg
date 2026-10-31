# Portable FFmpeg

FFmpeg and FFprobe for Windows x86-64, Linux x86-64/ARM64, and macOS Intel/Apple Silicon. Downloads and installed executables are verified with pinned SHA-256 hashes.

```bash
uv add portable-ffmpeg
```

For an offline installation, use the platform-specific binary bundle instead:

```bash
uv add portable-ffmpeg-full
```

`portable-ffmpeg-full` depends on the matching version of `portable-ffmpeg` and adds only its platform's compressed payload. The Python wrapper is shared. `get_ffmpeg()` prefers that payload, verifies it, and extracts it into the cache without contacting the network. A corrupt or incompatible installed payload raises an error rather than silently downloading another copy.

## Python API

```python
from portable_ffmpeg import get_ffmpeg, add_to_path, remove_from_path

ffmpeg_path, ffprobe_path = get_ffmpeg()
add_to_path()
add_to_path(weak=True)  # Preserve an existing ffmpeg on PATH.
remove_from_path()
```

`get_ffmpeg()` and `get_ffmpeg(FFmpegVersions.V9)` use the same pinned FFmpeg 9 build and share a cache. `LATEST` selects the stable build pinned by this package release. FFmpeg 5–8 selectors have been removed; existing applications using them must switch to V9.

## Command line

```bash
static_ffmpeg -i input.mp4 output.mp3
static_ffprobe -v quiet -print_format json -show_format input.mp4
print_paths
clear_cache
```

## Builds and hardware support

| Platform | FFmpeg build | Minimum runtime |
| --- | --- | --- |
| Windows x86-64 | BtbN 9.0.2, commit `7adfbe40dc` | Windows 10 22H2 |
| Linux x86-64 / ARM64 | Same BtbN snapshot | glibc 2.28, Linux 4.18 |
| macOS Intel / Apple Silicon | Martin Riedl 9.0.2 | macOS 12 |

The executables include software encoding and decoding of H.264, H.265, VP9, and AV1. Windows/Linux builds include NVIDIA, AMD AMF, Vulkan, and (on x86-64) Intel QSV; Linux also includes VAAPI. macOS uses VideoToolbox, with H.264/H.265 hardware encoding and hardware decoding where the machine supports the codec. GPU generation, drivers, codec profiles, and input formats determine actual hardware availability.

This package returns executable paths and forwards CLI arguments. The calling application chooses the encoder and implements software retry when a hardware operation is unsupported.

## Download and cache contract

Each owned release asset is one `.tar.xz` with both executables at the root (`.exe` on Windows), GPL and third-party notices, source references, and provenance. It uses one solid XZ stream with a 256 MiB LZMA2 dictionary. Decoding needs approximately 256 MiB of dictionary memory. No extra compression dependency is required.

The downloader verifies the archive before parsing it, copies only regular root files, then verifies the actual FFmpeg and FFprobe hashes before making the complete cache directory available. Missing, empty, duplicate, linked, nested-only, or checksum-mismatched executables cannot become a valid installation. Socket waits are bounded to 30 seconds. Archive readers and multi-file upstream layouts exist only in release preparation; the installed package reads TAR.XZ only.

Binaries are cached inside the package's `binaries/` directory. Each virtual environment gets its own cache. The cache key includes the pinned artifact configuration, so updates use a fresh cache. Both downloaded and bundled payloads use the same installation path. `clear_cache()` removes cached installations; it leaves an installed offline payload intact.

## Licenses and corresponding source

The Python wrapper is [MIT-licensed](LICENSE). FFmpeg reports GPL version 3 or later; included dependencies retain their respective license and copyright terms. No `--enable-nonfree` binaries are selected. The offline binary distribution includes GPL and third-party notices and source-access directions.

The binary release includes the exact BtbN build-run dependency cache, FFmpeg source and build recipes, reconstructed macOS dependency archives and recipes, locked Rust dependencies, copyright/license notices, and source identity records. The macOS x264 source was identified through the official repository history: master had not changed between the binary build and source collection. [Source locks](licenses) record the evidence and limitations. No bit-for-bit rebuild is claimed.

The source archives are separate release assets; GitHub's automatic archive of this Python repository is not FFmpeg's corresponding source. Preserve the source and notice assets for as long as the binaries remain available.

## Preparing and publishing

The release-preparation command requires reviewed source inputs and refuses incomplete reviews, mismatched source/binary hashes, or existing output directories:

```bash
uv run -m scripts.prepare_release dist/ffmpeg-9.0.2-1 dist/source-inputs-9.0.2
uv run -m scripts.publish_release dist/ffmpeg-9.0.2-1
uv run pytest --release-dir dist/ffmpeg-9.0.2-1
uv build --out-dir dist/python
uv run -m scripts.build_full_wheels dist/ffmpeg-9.0.2-1 dist/python
```

`SOURCE_MANIFEST.json` supplies the reviewed input identities. Final `manifest.json` describes the five executable archives and individual executable hashes; `SHA256SUMS` covers every upload asset. Source ZIPs are split below GitHub's 2 GiB-per-file limit. Binary TARs and offline wheels have fixed archive metadata for repeatable packaging.

To upload the verified binary/source set as a **draft**, without publishing it:

```bash
uv run -m scripts.publish_release dist/ffmpeg-9.0.2-1 --draft
```

The draft uploader requires a clean, committed checkout and targets its exact commit. Push that commit before uploading. Merge the scoped publishing workflow before making any binary release public, and enable immutable releases in the GitHub repository. Publish binary/source release `ffmpeg-9.0.2-1` before releasing Python packages `portable-ffmpeg` and `portable-ffmpeg-full` version 0.5.0. The client URLs become publicly usable only after that binary release is published.

Python package releases use `v` tags. The publication workflow downloads the already-published binary set, runs tests, builds the base package and all five offline wheels, and publishes `dist/python/*`. Both PyPI projects need trusted-publisher configuration: owner `mrkbac`, repository `portable-ffmpeg`, workflow filename `publish.yml`, environment `release`. Configure the existing base project under its Publishing settings; add `portable-ffmpeg-full` as a [pending publisher](https://pypi.org/manage/account/publishing/) before its first upload. Binary release tags do not trigger PyPI publication.
