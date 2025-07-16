#!/usr/bin/env python3
"""
Bulk text replacement tool for rebranding operations.
Performs case-sensitive replacements based on a JSON mapping file.
"""

import json
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Set
import mimetypes

class BulkReplacer:
    """Handles bulk text replacement operations with filtering and dry-run capabilities."""
    
    def __init__(self, constants_file: str = "constants.json"):
        """Initialize with constants file path."""
        self.constants_file = constants_file
        self.replacements: Dict[str, str] = {}
        self.whitelisted_extensions = {
            '.py', '.sh', '.html', '.js', '.css', '.json', 
            '.md', '.txt', '.xml', '.conf'
        }
        self.skip_dirs = {
            'venv', '.git', 'node_modules', 'dist', '__pycache__',
            '.venv', 'env', '.env'
        }
        self.stats = {
            'files_processed': 0,
            'files_modified': 0,
            'total_replacements': 0,
            'files_skipped': 0
        }
        
    def load_constants(self) -> bool:
        """Load replacement constants from JSON file."""
        try:
            constants_path = Path(__file__).parent / self.constants_file
            with open(constants_path, 'r', encoding='utf-8') as f:
                self.replacements = json.load(f)
            print(f"Loaded {len(self.replacements)} replacement pairs from {constants_path}")
            return True
        except FileNotFoundError:
            print(f"Error: Constants file '{constants_path}' not found.")
            return False
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in constants file: {e}")
            return False
        except Exception as e:
            print(f"Error loading constants: {e}")
            return False
    
    def is_binary_file(self, file_path: Path) -> bool:
        """Check if file is binary based on mime type and content sampling."""
        try:
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type and not mime_type.startswith('text/'):
                return True
            
            # Sample first 1024 bytes to check for binary content
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                if b'\x00' in chunk:
                    return True
                    
        except Exception:
            return True
        return False
    
    def should_skip_file(self, file_path: Path) -> Tuple[bool, str]:
        """Determine if file should be skipped based on extension and type."""
        if file_path.suffix.lower() not in self.whitelisted_extensions:
            return True, f"extension '{file_path.suffix}' not whitelisted"
        
        if self.is_binary_file(file_path):
            return True, "binary file"
        
        return False, ""
    
    def should_skip_directory(self, dir_path: Path) -> bool:
        """Check if directory should be skipped."""
        return dir_path.name in self.skip_dirs
    
    def process_file_content(self, content: str) -> Tuple[str, int]:
        """Process file content and apply all replacements."""
        modified_content = content
        replacement_count = 0
        
        for search_term, replace_term in self.replacements.items():
            if search_term in modified_content:
                occurrences = modified_content.count(search_term)
                modified_content = modified_content.replace(search_term, replace_term)
                replacement_count += occurrences
        
        return modified_content, replacement_count
    
    def process_file(self, file_path: Path, dry_run: bool = False) -> Tuple[bool, int]:
        """Process a single file and return (modified, replacement_count)."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()
            
            modified_content, replacement_count = self.process_file_content(original_content)
            
            if replacement_count > 0:
                if not dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(modified_content)
                return True, replacement_count
            
            return False, 0
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False, 0
    
    def find_files(self, root_path: Path) -> List[Path]:
        """Find all files to process, respecting skip rules."""
        files_to_process = []
        
        for root, dirs, files in os.walk(root_path):
            root_path_obj = Path(root)
            
            # Skip directories in-place to avoid traversing them
            dirs[:] = [d for d in dirs if not self.should_skip_directory(Path(d))]
            
            for file in files:
                file_path = root_path_obj / file
                skip, reason = self.should_skip_file(file_path)
                
                if skip:
                    self.stats['files_skipped'] += 1
                    continue
                    
                files_to_process.append(file_path)
        
        return files_to_process
    
    def run(self, root_path: str = ".", dry_run: bool = False) -> None:
        """Run the bulk replacement operation."""
        if not self.load_constants():
            return
        
        root_path_obj = Path(root_path).resolve()
        print(f"\nStarting bulk replacement in: {root_path_obj}")
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print(f"Whitelisted extensions: {', '.join(sorted(self.whitelisted_extensions))}")
        print(f"Skipped directories: {', '.join(sorted(self.skip_dirs))}")
        print("-" * 60)
        
        files_to_process = self.find_files(root_path_obj)
        print(f"Found {len(files_to_process)} files to process")
        
        if not files_to_process:
            print("No files found to process.")
            return
        
        for file_path in files_to_process:
            self.stats['files_processed'] += 1
            was_modified, replacement_count = self.process_file(file_path, dry_run)
            
            if was_modified:
                self.stats['files_modified'] += 1
                self.stats['total_replacements'] += replacement_count
                relative_path = file_path.relative_to(root_path_obj)
                print(f"{'[DRY RUN] ' if dry_run else ''}Modified: {relative_path} ({replacement_count} replacements)")
        
        self.print_summary(dry_run)
    
    def print_summary(self, dry_run: bool) -> None:
        """Print operation summary statistics."""
        print("\n" + "=" * 60)
        print(f"{'DRY RUN ' if dry_run else ''}SUMMARY")
        print("=" * 60)
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Files modified: {self.stats['files_modified']}")
        print(f"Files skipped: {self.stats['files_skipped']}")
        print(f"Total replacements: {self.stats['total_replacements']}")
        
        if self.stats['files_modified'] > 0:
            print(f"\nReplacement breakdown:")
            for search_term, replace_term in self.replacements.items():
                print(f"  '{search_term}' → '{replace_term}'")
        
        if dry_run and self.stats['files_modified'] > 0:
            print(f"\nTo apply changes, run without --dry-run flag")


def main():
    """Main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Bulk text replacement tool for rebranding operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Run replacement in current directory
  %(prog)s --dry-run                 # Preview changes without applying
  %(prog)s --path /path/to/project   # Run in specific directory
  %(prog)s --constants custom.json   # Use custom constants file
        """
    )
    
    parser.add_argument(
        '--path', '-p',
        default='.',
        help='Root path to process (default: current directory)'
    )
    
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='Preview changes without applying them'
    )
    
    parser.add_argument(
        '--constants', '-c',
        default='constants.json',
        help='Path to constants JSON file (default: constants.json)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Validate path
    if not os.path.exists(args.path):
        print(f"Error: Path '{args.path}' does not exist.")
        sys.exit(1)
    
    # Run bulk replacement
    replacer = BulkReplacer(args.constants)
    replacer.run(args.path, args.dry_run)


if __name__ == "__main__":
    main()


