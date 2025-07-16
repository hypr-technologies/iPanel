#!/usr/bin/env python3
"""
Version Manager Script for iPanel
Provides manual version management and release utilities
"""

import os
import sys
import re
import subprocess
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class VersionManager:
    """Manages version information and releases for iPanel"""
    
    def __init__(self, root_dir: str = "."):
        self.root_dir = os.path.abspath(root_dir)
        self.version_files = {
            'init': os.path.join(self.root_dir, 'iPanel', '__init__.py'),
            'setup': os.path.join(self.root_dir, 'setup.py'),
            'pyproject': os.path.join(self.root_dir, 'pyproject.toml'),
            'package': os.path.join(self.root_dir, 'package.json')
        }
        
    def get_current_version(self) -> Optional[str]:
        """Get the current version from __init__.py"""
        init_file = self.version_files['init']
        if not os.path.exists(init_file):
            return None
            
        with open(init_file, 'r') as f:
            content = f.read()
            
        match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
        return match.group(1) if match else None
    
    def get_git_version(self) -> Optional[str]:
        """Get the latest git tag version"""
        try:
            result = subprocess.run(
                ['git', 'describe', '--tags', '--abbrev=0'],
                capture_output=True,
                text=True,
                cwd=self.root_dir
            )
            if result.returncode == 0:
                return result.stdout.strip().lstrip('v')
            return None
        except Exception:
            return None
    
    def parse_version(self, version: str) -> Tuple[int, int, int, str]:
        """Parse semantic version string"""
        # Handle prerelease versions
        if '-' in version:
            version_part, prerelease = version.split('-', 1)
        else:
            version_part, prerelease = version, ''
            
        parts = version_part.split('.')
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        
        return major, minor, patch, prerelease
    
    def increment_version(self, version: str, increment_type: str) -> str:
        """Increment version based on type"""
        major, minor, patch, prerelease = self.parse_version(version)
        
        if increment_type == 'major':
            major += 1
            minor = 0
            patch = 0
            prerelease = ''
        elif increment_type == 'minor':
            minor += 1
            patch = 0
            prerelease = ''
        elif increment_type == 'patch':
            patch += 1
            prerelease = ''
        elif increment_type == 'prerelease':
            if prerelease:
                # Increment prerelease number
                if prerelease.startswith('alpha'):
                    num = int(prerelease.split('.')[-1]) if '.' in prerelease else 0
                    prerelease = f"alpha.{num + 1}"
                elif prerelease.startswith('beta'):
                    num = int(prerelease.split('.')[-1]) if '.' in prerelease else 0
                    prerelease = f"beta.{num + 1}"
                else:
                    prerelease = f"{prerelease}.1"
            else:
                prerelease = 'alpha.1'
        
        new_version = f"{major}.{minor}.{patch}"
        if prerelease:
            new_version += f"-{prerelease}"
            
        return new_version
    
    def update_version_files(self, new_version: str) -> None:
        """Update all version files with new version"""
        # Update __init__.py
        init_file = self.version_files['init']
        if os.path.exists(init_file):
            with open(init_file, 'r') as f:
                content = f.read()
            
            content = re.sub(
                r'__version__\s*=\s*["\'][^"\']*["\']',
                f'__version__ = "{new_version}"',
                content
            )
            
            with open(init_file, 'w') as f:
                f.write(content)
        else:
            os.makedirs(os.path.dirname(init_file), exist_ok=True)
            with open(init_file, 'w') as f:
                f.write(f'__version__ = "{new_version}"\n')
        
        # Update setup.py
        setup_file = self.version_files['setup']
        if os.path.exists(setup_file):
            with open(setup_file, 'r') as f:
                content = f.read()
            
            content = re.sub(
                r'version\s*=\s*["\'][^"\']*["\']',
                f'version="{new_version}"',
                content
            )
            
            with open(setup_file, 'w') as f:
                f.write(content)
        
        # Update pyproject.toml
        pyproject_file = self.version_files['pyproject']
        if os.path.exists(pyproject_file):
            with open(pyproject_file, 'r') as f:
                content = f.read()
            
            content = re.sub(
                r'version\s*=\s*["\'][^"\']*["\']',
                f'version = "{new_version}"',
                content
            )
            
            with open(pyproject_file, 'w') as f:
                f.write(content)
        
        # Update package.json
        package_file = self.version_files['package']
        if os.path.exists(package_file):
            with open(package_file, 'r') as f:
                data = json.load(f)
            
            data['version'] = new_version
            
            with open(package_file, 'w') as f:
                json.dump(data, f, indent=2)
    
    def create_git_tag(self, version: str, message: str = None) -> bool:
        """Create a git tag for the version"""
        try:
            tag_name = f"v{version}"
            if message is None:
                message = f"Release {version}"
            
            subprocess.run(
                ['git', 'tag', '-a', tag_name, '-m', message],
                check=True,
                cwd=self.root_dir
            )
            
            print(f"Created git tag: {tag_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error creating git tag: {e}")
            return False
    
    def build_package(self) -> bool:
        """Build Python package"""
        try:
            subprocess.run([sys.executable, '-m', 'build'], check=True, cwd=self.root_dir)
            print("Package built successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error building package: {e}")
            return False
    
    def generate_changelog_entry(self, version: str, previous_version: str = None) -> str:
        """Generate changelog entry for version"""
        if previous_version is None:
            previous_version = self.get_git_version()
        
        date = datetime.now().strftime('%Y-%m-%d')
        changelog_entry = f"\n## [{version}] - {date}\n\n"
        
        if previous_version:
            try:
                # Get git log between versions
                result = subprocess.run([
                    'git', 'log', f"v{previous_version}..HEAD", 
                    '--pretty=format:- %s', '--no-merges'
                ], capture_output=True, text=True, cwd=self.root_dir)
                
                if result.returncode == 0 and result.stdout:
                    changelog_entry += "### Changes\n\n"
                    changelog_entry += result.stdout + "\n\n"
                else:
                    changelog_entry += "### Changes\n\n- Version update\n\n"
            except Exception:
                changelog_entry += "### Changes\n\n- Version update\n\n"
        else:
            changelog_entry += "### Changes\n\n- Initial release\n\n"
        
        return changelog_entry
    
    def update_changelog(self, version: str, previous_version: str = None) -> None:
        """Update CHANGELOG.md with new version"""
        changelog_file = os.path.join(self.root_dir, 'CHANGELOG.md')
        entry = self.generate_changelog_entry(version, previous_version)
        
        if os.path.exists(changelog_file):
            with open(changelog_file, 'r') as f:
                content = f.read()
            
            # Insert new entry after the header
            lines = content.split('\n')
            header_end = 0
            for i, line in enumerate(lines):
                if line.startswith('## '):
                    header_end = i
                    break
            
            if header_end > 0:
                lines.insert(header_end, entry)
            else:
                lines.append(entry)
            
            content = '\n'.join(lines)
        else:
            content = "# Changelog\n\n" + entry
        
        with open(changelog_file, 'w') as f:
            f.write(content)
        
        print(f"Updated CHANGELOG.md for version {version}")

def main():
    parser = argparse.ArgumentParser(description='iPanel Version Manager')
    parser.add_argument('--root', default='.', help='Root directory of the project')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Current version command
    current_parser = subparsers.add_parser('current', help='Show current version')
    
    # Set version command
    set_parser = subparsers.add_parser('set', help='Set specific version')
    set_parser.add_argument('version', help='Version to set (e.g., 1.2.3)')
    set_parser.add_argument('--no-tag', action='store_true', help='Don\'t create git tag')
    set_parser.add_argument('--no-changelog', action='store_true', help='Don\'t update changelog')
    
    # Increment version command
    increment_parser = subparsers.add_parser('increment', help='Increment version')
    increment_parser.add_argument('type', choices=['major', 'minor', 'patch', 'prerelease'],
                                help='Type of increment')
    increment_parser.add_argument('--no-tag', action='store_true', help='Don\'t create git tag')
    increment_parser.add_argument('--no-changelog', action='store_true', help='Don\'t update changelog')
    
    # Build command
    build_parser = subparsers.add_parser('build', help='Build package')
    
    # Tag command
    tag_parser = subparsers.add_parser('tag', help='Create git tag for current version')
    tag_parser.add_argument('--message', help='Tag message')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    vm = VersionManager(args.root)
    
    if args.command == 'current':
        current = vm.get_current_version()
        git_version = vm.get_git_version()
        
        print(f"Current version: {current or 'Not set'}")
        print(f"Git version: {git_version or 'No tags'}")
        
        if current and git_version and current != git_version:
            print("⚠️  Version mismatch detected!")
    
    elif args.command == 'set':
        previous_version = vm.get_current_version()
        vm.update_version_files(args.version)
        
        if not args.no_changelog:
            vm.update_changelog(args.version, previous_version)
        
        if not args.no_tag:
            vm.create_git_tag(args.version)
        
        print(f"Version set to {args.version}")
    
    elif args.command == 'increment':
        current = vm.get_current_version()
        if not current:
            print("No current version found, starting from 0.1.0")
            current = "0.1.0"
        
        new_version = vm.increment_version(current, args.type)
        vm.update_version_files(new_version)
        
        if not args.no_changelog:
            vm.update_changelog(new_version, current)
        
        if not args.no_tag:
            vm.create_git_tag(new_version)
        
        print(f"Version incremented from {current} to {new_version}")
    
    elif args.command == 'build':
        if vm.build_package():
            print("Build completed successfully")
        else:
            print("Build failed")
            return 1
    
    elif args.command == 'tag':
        current = vm.get_current_version()
        if not current:
            print("No current version found")
            return 1
        
        if vm.create_git_tag(current, args.message):
            print(f"Tag created for version {current}")
        else:
            print("Tag creation failed")
            return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
