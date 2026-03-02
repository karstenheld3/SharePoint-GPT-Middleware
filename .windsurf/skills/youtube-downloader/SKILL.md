# YouTube Downloader Skill

Download YouTube content as MP3 audio or video using yt-dlp with PowerShell cmdlet parameters.

## Prerequisites

- PowerShell 5.1+ (tested on 5.1.26100 and 7.5.4)
- Internet connection (auto-downloads yt-dlp and ffmpeg)
- Windows Terminal (optional, for parallel tab support)

## Scripts

- **Download-Youtube-To-Mp3.ps1** - Extract audio as MP3
- **Download-Youtube-To-Video.ps1** - Download video files

## MP3 Download

```powershell
# Single URL
.\Download-Youtube-To-Mp3.ps1 -Urls "https://www.youtube.com/watch?v=VIDEO_ID"

# High quality
.\Download-Youtube-To-Mp3.ps1 -Urls "https://youtu.be/abc" -Quality 320k

# Playlist
.\Download-Youtube-To-Mp3.ps1 -Urls "https://youtube.com/watch?v=abc&list=RDxxx" -Playlist
```

### MP3 Parameters

- **-Urls** (required) - YouTube URLs
- **-OutputFolder** - Default: `[WORKSPACE]/../.tools/_downloaded_audio`
- **-Quality** - `128k`, `192k`, `256k`, `320k` (default: `192k`)
- **-Playlist** - Download entire playlist (switch)
- **-UseCookies** - Use Chrome cookies (default: `$true`)
- **-ChromeProfile** - Chrome profile name (auto-detected)
- **-ToolsFolder** - Binaries location (default: `[WORKSPACE]/../.tools/youtube-downloader`)

## Video Download

```powershell
# Best quality
.\Download-Youtube-To-Video.ps1 -Urls "https://www.youtube.com/watch?v=VIDEO_ID"

# Specific format and quality
.\Download-Youtube-To-Video.ps1 -Urls "https://youtu.be/abc" -Format mp4 -Quality 1080p

# Playlist
.\Download-Youtube-To-Video.ps1 -Urls "https://youtube.com/watch?v=abc&list=RDxxx" -Playlist
```

### Video Parameters

- **-Urls** (required) - YouTube URLs
- **-OutputFolder** - Default: `[WORKSPACE]/../.tools/_downloaded_video`
- **-Format** - `best`, `mp4`, `webm`, `mkv` (default: `best`)
- **-Quality** - `best`, `1080p`, `720p`, `480p`, `360p` (default: `best`)
- **-Playlist** - Download entire playlist (switch)
- **-UseCookies** - Use Chrome cookies (default: `$true`)
- **-ChromeProfile** - Chrome profile name (auto-detected)
- **-ToolsFolder** - Binaries location (default: `[WORKSPACE]/../.tools/youtube-downloader`)

## Shared Features

Both scripts share:
- Auto-download yt-dlp and ffmpeg if missing
- yt-dlp version checking and auto-update
- Chrome cookie auto-detection for age-restricted content
- DPAPI error fallback (retries without cookies)
- Pipeline input support
- Playlist support

## Parallel Downloads (Cascade)

When user provides multiple URLs, Cascade spawns multiple terminals:
- 2 URLs → 2 terminals
- 10 URLs → 10 terminals  
- 50 URLs → 10 terminals (max), 5 URLs each

Cascade splits URLs and runs non-blocking commands with `-UseCookies $false`.

## Output Locations

- **Audio**: `[WORKSPACE]/../.tools/_downloaded_audio/`
- **Video**: `[WORKSPACE]/../.tools/_downloaded_video/`
- **Binaries**: `[WORKSPACE]/../.tools/youtube-downloader/`
