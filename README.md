# mp3-transcriber
---

I needed to give ChatGPT context without hitting the upload limit, heh

## Requirements
- ffmpeg (required for MP3 processing)

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install ffmpeg:
   - **macOS**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `sudo apt install ffmpeg`
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

## Usage

### Basic Usage
```bash
python main.py input.mp3
```

### Advanced Usage
```bash
# Specify output directory
python main.py input.mp3 -o output_folder

# Set chunk duration to 60 seconds
python main.py input.mp3 -d 60 -o chunks

# Add 5-second overlap between chunks
python main.py input.mp3 -d 30 -l 5 -o output
```
