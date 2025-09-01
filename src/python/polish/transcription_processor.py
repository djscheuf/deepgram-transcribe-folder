"""
Module for processing transcriptions using Ollama API.
Handles loading transcriptions, processing them with AI, and saving the results.
"""

import os
import json
import logging
import concurrent.futures
import multiprocessing
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TranscriptionProcessor:
    """Handles processing of transcription files using Ollama API."""
    
    def __init__(
        self,
        input_dir: str = "/data/transcriptions",
        output_dir: str = "/data/polished",
        api_url: str = "http://localhost:19190/api/generate",
        max_workers: Optional[int] = None
    ):
        """Initialize the transcription processor.
        
        Args:
            input_dir: Directory containing transcription files
            output_dir: Directory to save processed files
            api_url: Ollama API endpoint
            max_workers: Maximum number of worker threads (defaults to 50% of CPU count)
        """
        self.input_dir = Path(input_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.api_url = api_url
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set max workers to 50% of CPU count if not specified
        if max_workers is None:
            max_workers = max(1, multiprocessing.cpu_count() // 2)
        self.max_workers = max_workers
        
        logger.info(f"Initialized TranscriptionProcessor with {self.max_workers} workers")
        logger.info(f"Input directory: {self.input_dir}")
        logger.info(f"Output directory: {self.output_dir}")
    
    def load_transcription(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load a transcription file.
        
        Args:
            file_path: Path to the transcription file
            
        Returns:
            Parsed transcription data or None if loading fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading {file_path}: {str(e)}")
            return None
    
    def process_with_ollama(self, text: str) -> Optional[Dict[str, str]]:
        """Send transcription to Ollama API for processing.
        
        Args:
            text: Transcription text to process
            
        Returns:
            Dictionary with processed content or None if processing fails
        """
        prompt = f"""You are an expert transcriptionist with extensive experience as an executive assitant.

Help the user format the provided transcript for reading.

Output format:

Title = propose a 4-7 word title for the note based on the contet
Key Ideas = Summarize the key points of the voice notes
Action Items, if any = Capture any follow-up actions discussed in the transcription
Transcript = Include the initial transcript, with improved whitespace for legibility.
Here is the original transcription: 
        {text}
        """
        
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": "llama3",
                    "prompt": prompt,
                    "format": "json",
                    "stream": False
                },
                timeout=300  # 5 minute timeout
            )
            response.raise_for_status()
            
            # Try to parse the response
            try:
                result = response.json()
                # Some Ollama APIs return the JSON in a 'response' field
                if 'response' in result and isinstance(result['response'], str):
                    return json.loads(result['response'])
                return result
            except json.JSONDecodeError:
                logger.error("Failed to parse API response as JSON")
                return None
                
        except requests.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return None
    
    def process_file(self, file_path: Path) -> bool:
        """Process a single transcription file.
        
        Args:
            file_path: Path to the transcription file
            
        Returns:
            True if processing was successful, False otherwise
        """
        logger.info(f"Processing file: {file_path.name}")
        
        # Load the transcription
        transcription = self.load_transcription(file_path)
        if not transcription:
            return False
        
        if not transcription:
            logger.warning(f"No text content found in {file_path}")
            return False
        
        # Process with Ollama
        result = self.process_with_ollama(transcription)
        if not result:
            logger.error(f"Failed to process {file_path} with Ollama")
            return False
        
        # Generate output filename
        safe_title = "".join(c if c.isalnum() or c in ' -_' else '_' for c in result.get('title', 'untitled'))
        # Extract date from filename (format YYYYMMDDHHMMSS)
        file_stem = file_path.stem
        date_str = file_stem[:10]
        output_filename = f"{date_str} - {safe_title}.md"
        output_path = self.output_dir / output_filename
        
        # Save the result
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"# {result.get('title', 'Untitled')}\n\n")
                
                f.write("## Key Points\n")
                for point in result.get('key_points', []):
                    f.write(f"- {point}\n")
                f.write("\n")
                
                if 'action_items' in result and result['action_items']:
                    f.write("## Action Items\n")
                    for item in result['action_items']:
                        f.write(f"- [ ] {item}\n")
                    f.write("\n")
                
                f.write("## Transcript\n\n")
                f.write(result.get('formatted_transcript', result.get('transcript', 'No transcript available.')))
                
            logger.info(f"Successfully saved processed transcription to {output_path}")
            return True
            
        except IOError as e:
            logger.error(f"Failed to save output file {output_path}: {str(e)}")
            return False
    
    def process_all(self) -> None:
        """Process all transcription files in the input directory."""
        # Find all supported files
        files = list(self.input_dir.glob('*.md'))
        
        if not files:
            logger.warning(f"No transcription files found in {self.input_dir}")
            return
        
        logger.info(f"Found {len(files)} files to process")
        
        # Process files in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self.process_file, file_path): file_path 
                for file_path in files
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    success = future.result()
                    if not success:
                        logger.warning(f"Failed to process {file_path.name}")
                except Exception as e:
                    logger.error(f"Error processing {file_path.name}: {str(e)}")
        
        logger.info("Finished processing all files")


def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process transcriptions with Ollama')
    parser.add_argument('--input-dir', default='/data/transcriptions',
                       help='Directory containing transcription files')
    parser.add_argument('--output-dir', default='/data/polished',
                       help='Directory to save processed files')
    parser.add_argument('--api-url', default='http://localhost:19190/api/generate',
                       help='Ollama API URL')
    parser.add_argument('--workers', type=int, default=None,
                       help='Maximum number of worker threads')
    
    args = parser.parse_args()
    
    processor = TranscriptionProcessor(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        api_url=args.api_url,
        max_workers=args.workers
    )
    
    processor.process_all()


if __name__ == "__main__":
    main()
