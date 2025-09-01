"""
Deepgram transcription functionality for processing audio files.
"""
import asyncio
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import aiofiles
from deepgram import Deepgram
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DeepgramTranscriber:
    """Handles transcription of audio files using Deepgram API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the transcriber with an optional API key."""
        self.api_key = api_key or os.getenv('DEEPGRAM_API_KEY')
        if not self.api_key:
            raise ValueError("Deepgram API key not provided and not found in environment variables")
        self.client = Deepgram(self.api_key)
    
    async def transcribe_file(self, file_path: str) -> str:
        """Transcribe a single audio file."""
        try:
            async with aiofiles.open(file_path, 'rb') as audio_file:
                source = {'buffer': await audio_file.read(), 'mimetype': 'audio/mp3'}
                
            response = await self.client.transcription.prerecorded(
                source,
                {
                    'model': 'nova-2',
                    'smart_format': True,
                }
            )
            
            if 'results' in response and 'channels' in response['results']:
                return response['results']['channels'][0]['alternatives'][0]['transcript']
            return ""
            
        except Exception as e:
            print(f"Error transcribing {file_path}: {str(e)}")
            return ""

async def save_transcript(output_dir: str, file_path: str, transcript: str) -> None:
    """Save transcription to a markdown file."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        output_path = Path(output_dir) / f"{Path(file_path).stem}.md"
        
        async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
            await f.write(transcript)
        print(f"Saved transcription to: {output_path}")
        
    except Exception as e:
        print(f"Error saving transcription for {file_path}: {str(e)}")

def get_audio_files(input_dir: str, prefix: str = '') -> List[str]:
    """Get list of audio files in the input directory with optional prefix filter."""
    audio_extensions = ('.mp3', '.wav', '.m4a', '.ogg', '.flac')
    input_path = Path(input_dir)
    
    if not input_path.exists() or not input_path.is_dir():
        raise ValueError(f"Input directory does not exist: {input_dir}")
    
    return [
        str(file_path) for file_path in input_path.glob('*')
        if file_path.suffix.lower() in audio_extensions and 
           (not prefix or file_path.name.startswith(prefix))
    ]

async def process_batch(transcriber: DeepgramTranscriber, files: List[str], output_dir: str) -> None:
    """Process a batch of files for transcription."""
    tasks = []
    for file_path in files:
        print(f"Processing: {file_path}")
        transcript = await transcriber.transcribe_file(file_path)
        tasks.append(save_transcript(output_dir, file_path, transcript))
    
    await asyncio.gather(*tasks)

def group_by_seventh_char(files: List[str]) -> Dict[str, List[str]]:
    """Group files by the 7th character of their filenames."""
    groups = {"0": [], "1": [], "2": [], "3": []}
    for file_path in files:
        try:
            # Get the 7th character (0-based index 6) from the filename
            key = Path(file_path).stem[6] if len(Path(file_path).stem) > 6 else "0"
            groups.setdefault(key, []).append(file_path)
        except (IndexError, TypeError):
            groups["0"].append(file_path)
    return groups

async def transcribe_folder(
    input_dir: str = "./in",
    output_dir: str = "./out",
    prefix: str = "2025080",
    batch_size: int = 4
) -> None:
    """
    Transcribe all audio files in the input directory.
    
    Args:
        input_dir: Directory containing audio files
        output_dir: Directory to save transcriptions
        prefix: Optional prefix to filter files
        batch_size: Number of files to process in parallel (default: 4)
    """
    try:
        # Get and filter audio files
        audio_files = get_audio_files(input_dir, prefix)
        if not audio_files:
            print(f"No audio files found in {input_dir} with prefix '{prefix}'")
            return
            
        print(f"Found {len(audio_files)} files to process")
        
        # Initialize transcriber
        transcriber = DeepgramTranscriber()
        
        # Group files by 7th character for batching
        file_groups = group_by_seventh_char(audio_files)
        
        # Process each group
        for group_name, files in file_groups.items():
            if not files:
                continue
                
            print(f"\nProcessing group {group_name} with {len(files)} files")
            print("-" * 50)
            
            # Process in batches to avoid overwhelming the API
            for i in range(0, len(files), batch_size):
                batch = files[i:i + batch_size]
                print(f"Processing batch {i//batch_size + 1}/{(len(files)-1)//batch_size + 1}")
                await process_batch(transcriber, batch, output_dir)
                
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise

def main():
    """Command-line entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Transcribe audio files using Deepgram')
    parser.add_argument('--input', '-i', default='./in', help='Input directory containing audio files')
    parser.add_argument('--output', '-o', default='./out', help='Output directory for transcriptions')
    parser.add_argument('--prefix', '-p', default='2025080', 
                       help='Optional prefix to filter files (default: 2025080)')
    parser.add_argument('--batch-size', '-b', type=int, default=4,
                       help='Number of files to process in parallel (default: 4)')
    
    args = parser.parse_args()
    
    # Run the async function
    asyncio.run(transcribe_folder(
        input_dir=args.input,
        output_dir=args.output,
        prefix=args.prefix,
        batch_size=args.batch_size
    ))

if __name__ == "__main__":
    main()
