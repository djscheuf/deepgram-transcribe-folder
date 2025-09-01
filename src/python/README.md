# Deepgram Audio Transcription (Python)

This is a Python implementation of the Deepgram transcription functionality, equivalent to the Node.js version.

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up your environment variables:
   - Create a `.env` file in the `src/python` directory
   - Add your Deepgram API key:
     ```
     DEEPGRAM_API_KEY=your_api_key_here
     ```

## Usage

### Command Line

```bash
python -m transcribe.transcriber [options]

Options:
  -h, --help            show help message and exit
  --input DIR, -i DIR   Input directory containing audio files (default: ./in)
  --output DIR, -o DIR  Output directory for transcriptions (default: ./out)
  --prefix PREFIX, -p PREFIX
                        Optional prefix to filter files (default: 2025080)
  --batch-size N, -b N  Number of files to process in parallel (default: 4)
```

### Python API

```python
from transcribe import transcribe_folder

# Basic usage
await transcribe_folder()

# With custom parameters
await transcribe_folder(
    input_dir="./my_audio_files",
    output_dir="./transcriptions",
    prefix="2025",
    batch_size=4
)
```

## Features

- Processes audio files in parallel for better performance
- Groups files by the 7th character of their filenames (matching Node.js behavior)
- Saves transcriptions as markdown files
- Includes error handling and progress reporting
- Supports various audio formats (mp3, wav, m4a, ogg, flac)

## Note

Make sure your Deepgram API key has sufficient credits before processing large numbers of files.
