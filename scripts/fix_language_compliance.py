#!/usr/bin/env python3
"""
Professional Language Compliance Fixer

Automatically fixes non-professional language patterns in documentation
while maintaining factual accuracy and evidence-based statements.
"""

import re
import sys
from pathlib import Path
from typing import Dict, Tuple
import argparse


class LanguageComplianceFixer:
    """Fixes documentation for professional language compliance."""
    
    # Replacement patterns that maintain factual accuracy
    # Order matters - more specific patterns first to avoid double replacements
    REPLACEMENTS = [
        # Multi-word phrases first (case-insensitive handled in regex)
        (r'\bdesigned solely to\b', 'appears to', 'less absolute term'),
        (r'\bappear(?:s)? designed to\b', 'may be intended to', 'less absolute term'),
        (r'\bentire(?:ly)? devoid of\b', 'lacking', 'neutral term'),
        (r'\bwholly unfounded\b', 'not evidenced', 'evidence-based term'),
        (r'\bsweeping accusations?\b', 'broad allegations', 'neutral term'),
        (r'\bentire(?:ly)? speculative\b', 'not evidenced', 'factual term'),
        (r'\bwholly speculative\b', 'not supported by documentation', 'factual term'),
        (r'\bcompletely false\b', 'contradicted by available evidence', 'evidence-based term'),
        (r'\bmust be rejected in its entirety\b', 'is not supported by the evidence', 'evidence-based term'),
        (r'\bfalse and misleading\b', 'false and not supported by evidence', 'evidence-based term'),
        (r'\bincorrect and misleading\b', 'incorrect and not supported by evidence', 'evidence-based term'),
        (r'\bmisplaced and misleading\b', 'misplaced and not supported by evidence', 'evidence-based term'),
        (r'\breckless, unfounded, and\b', 'without adequate basis, not evidenced, and', 'neutral evidence-based'),
        
        # Then single words
        (r'\bdevoid of\b', 'lacking', 'neutral term'),
        (r'\bfabrication\b', 'statement not supported by available evidence', 'neutral factual term'),
        (r'\breckless\b(?! trading)', 'without adequate consideration', 'factual description'),
        (r'\bmalign\b', 'mischaracterize', 'neutral term'),
        (r'\bmisleading to\b', 'not supported by evidence to', 'factual description'),
        (r'\bmisleading\b', 'not supported by evidence', 'factual description'),
        (r'\bmislead\b', 'provide inaccurate information', 'factual description'),
        (r'\bunfounded\b', 'not supported by available evidence', 'evidence-based term'),
        (r'\bbizarre\b', 'unusual', 'neutral term'),
        (r'\birrational\b', 'not consistent with expected behavior', 'factual description'),
        (r'\bshocking\b', 'notable', 'neutral term'),
        (r'\bdangerous\b(?! goods)', 'concerning', 'neutral term'),
        (r'\bsensational\b', 'dramatic', 'neutral term'),
    ]
    
    # Phrases that need special handling to preserve legal terminology
    LEGAL_EXCEPTIONS = [
        'reckless trading',
        'gross negligence',
        'malicious prosecution',
        'misleading the court',
        'dangerous goods',
    ]
    
    def __init__(self, dry_run: bool = False):
        """Initialize the fixer."""
        self.dry_run = dry_run
        self.changes_made = []
    
    def fix_line(self, line: str) -> Tuple[str, list]:
        """Fix a single line and return the modified line and changes made."""
        original = line
        changes = []
        
        # Skip lines with legal exceptions
        line_lower = line.lower()
        if any(exception in line_lower for exception in self.LEGAL_EXCEPTIONS):
            return line, changes
        
        # Apply replacements (using list now instead of dict)
        for pattern, replacement, description in self.REPLACEMENTS:
            if re.search(pattern, line, re.IGNORECASE):
                new_line = re.sub(pattern, replacement, line, flags=re.IGNORECASE)
                if new_line != line:
                    changes.append({
                        'pattern': pattern,
                        'replacement': replacement,
                        'description': description,
                        'before': line.strip(),
                        'after': new_line.strip()
                    })
                    line = new_line
        
        return line, changes
    
    def fix_file(self, file_path: Path) -> Dict:
        """Fix a single file and return statistics."""
        result = {
            'file': str(file_path),
            'lines_changed': 0,
            'changes': [],
            'success': False
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            new_lines = []
            for line_num, line in enumerate(lines, start=1):
                new_line, changes = self.fix_line(line)
                new_lines.append(new_line)
                
                if changes:
                    result['lines_changed'] += 1
                    for change in changes:
                        change['line_number'] = line_num
                        result['changes'].append(change)
            
            # Write back if not dry run and changes were made
            if not self.dry_run and result['lines_changed'] > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                result['success'] = True
            elif result['lines_changed'] > 0:
                result['success'] = True  # Would have succeeded
            else:
                result['success'] = True  # No changes needed
        
        except Exception as e:
            result['error'] = str(e)
            print(f"Error fixing {file_path}: {e}", file=sys.stderr)
        
        return result
    
    def fix_directory(self, directory: Path, pattern: str = "*.md") -> Dict:
        """Fix all matching files in a directory recursively."""
        results = {
            'files_processed': 0,
            'files_changed': 0,
            'total_changes': 0,
            'file_results': []
        }
        
        for file_path in directory.rglob(pattern):
            # Skip certain directories
            if any(skip in file_path.parts for skip in ['.git', 'node_modules', 'venv', '__pycache__']):
                continue
            
            result = self.fix_file(file_path)
            results['files_processed'] += 1
            
            if result['lines_changed'] > 0:
                results['files_changed'] += 1
                results['total_changes'] += result['lines_changed']
                results['file_results'].append(result)
        
        return results
    
    def generate_report(self, results: Dict) -> str:
        """Generate a human-readable report of changes."""
        lines = []
        lines.append("=" * 80)
        lines.append("PROFESSIONAL LANGUAGE COMPLIANCE FIX REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        if self.dry_run:
            lines.append("🔍 DRY RUN MODE - No files were modified")
            lines.append("")
        
        lines.append(f"Files processed: {results['files_processed']}")
        lines.append(f"Files changed: {results['files_changed']}")
        lines.append(f"Total changes: {results['total_changes']}")
        lines.append("")
        
        if results['file_results']:
            lines.append("=" * 80)
            lines.append("CHANGES BY FILE")
            lines.append("=" * 80)
            lines.append("")
            
            for file_result in results['file_results']:
                lines.append(f"📄 {file_result['file']}")
                lines.append(f"   Lines changed: {file_result['lines_changed']}")
                lines.append("")
                
                for change in file_result['changes']:
                    lines.append(f"   Line {change['line_number']}:")
                    lines.append(f"     Before: {change['before'][:100]}")
                    lines.append(f"     After:  {change['after'][:100]}")
                    lines.append(f"     Reason: {change['description']}")
                    lines.append("")
        else:
            lines.append("✓ No changes needed - all files are compliant!")
            lines.append("")
        
        return '\n'.join(lines)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Fix documentation for professional language compliance'
    )
    parser.add_argument(
        'path',
        help='Path to fix (file or directory)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )
    parser.add_argument(
        '--output',
        '-o',
        help='Output report to file'
    )
    args = parser.parse_args()
    
    fixer = LanguageComplianceFixer(dry_run=args.dry_run)
    path = Path(args.path)
    
    if path.is_file():
        result = fixer.fix_file(path)
        results = {
            'files_processed': 1,
            'files_changed': 1 if result['lines_changed'] > 0 else 0,
            'total_changes': result['lines_changed'],
            'file_results': [result] if result['lines_changed'] > 0 else []
        }
    elif path.is_dir():
        results = fixer.fix_directory(path)
    else:
        print(f"Error: {path} is not a valid file or directory", file=sys.stderr)
        return 1
    
    # Generate and print report
    report = fixer.generate_report(results)
    print(report)
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"\nReport saved to {args.output}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
