#!/usr/bin/env python3
"""
Professional Language Compliance Checker

Scans documentation for non-professional language patterns and suggests
evidence-based alternatives that maintain factual accuracy while ensuring
professional tone.
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class LanguageIssue:
    """Represents a language compliance issue."""
    file_path: str
    line_number: int
    issue_type: str
    problematic_text: str
    suggestion: str
    context: str


class LanguageComplianceChecker:
    """Checks documentation for professional language compliance."""
    
    # Problematic patterns that should be avoided
    PROBLEMATIC_PATTERNS = {
        'derogatory': [
            (r'\bfabrication\b', 'statement not supported by available evidence'),
            (r'\breckless\b(?! trading)', 'without adequate consideration of'),
            (r'\bmalign\b', 'mischaracterize'),
            (r'\bmislead(?:ing)?\b', 'provide inaccurate information to'),
            (r'\bunfounded\b', 'not supported by available evidence'),
            (r'\bdevoid of\b', 'lacking'),
            (r'\bsweeping accusations?\b', 'broad allegations'),
            (r'\bdesigned solely to\b', 'appears to'),
        ],
        'speculative': [
            (r'\bappear(?:s)? designed\b', 'may be intended'),
            (r'\bentire(?:ly)? speculative\b', 'not evidenced'),
            (r'\bwholly speculative\b', 'not supported by documentation'),
            (r'\bsensational\b', 'dramatic'),
        ],
        'emotional': [
            (r'\bbizarre\b', 'unusual'),
            (r'\birrational\b', 'not consistent with'),
            (r'\bshocking\b', 'notable'),
            (r'\bdangerous\b(?! goods)', 'concerning'),
        ],
        'absolute': [
            (r'\bentirely devoid\b', 'lacking'),
            (r'\bwholly unfounded\b', 'not evidenced'),
            (r'\bcompletely false\b', 'contradicted by available evidence'),
            (r'\bmust be rejected in its entirety\b', 'is not supported by the evidence'),
        ]
    }
    
    # Acceptable legal terminology that should not be flagged
    LEGAL_EXCEPTIONS = [
        'reckless trading',  # Legal term from Companies Act
        'gross negligence',   # Legal standard
        'malicious prosecution',  # Legal cause of action
        'misleading the court',  # Legal term of art
    ]
    
    def __init__(self, repo_root: Path = None):
        """Initialize the checker with repository root."""
        self.repo_root = repo_root or Path.cwd()
        self.issues: List[LanguageIssue] = []
    
    def check_file(self, file_path: Path) -> List[LanguageIssue]:
        """Check a single file for language compliance issues."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, start=1):
                # Skip if line contains legal exception
                if any(exception.lower() in line.lower() for exception in self.LEGAL_EXCEPTIONS):
                    continue
                
                for issue_type, patterns in self.PROBLEMATIC_PATTERNS.items():
                    for pattern, suggestion in patterns:
                        matches = re.finditer(pattern, line, re.IGNORECASE)
                        for match in matches:
                            # Get context (surrounding lines)
                            start_idx = max(0, line_num - 2)
                            end_idx = min(len(lines), line_num + 1)
                            context = ''.join(lines[start_idx:end_idx])
                            
                            try:
                                rel_path = str(file_path.relative_to(self.repo_root))
                            except ValueError:
                                rel_path = str(file_path)
                            
                            issue = LanguageIssue(
                                file_path=rel_path,
                                line_number=line_num,
                                issue_type=issue_type,
                                problematic_text=match.group(0),
                                suggestion=suggestion,
                                context=context.strip()
                            )
                            issues.append(issue)
        
        except Exception as e:
            # Only log actual errors, not path issues
            if 'not in the subpath' not in str(e):
                print(f"Error checking {file_path}: {e}", file=sys.stderr)
        
        return issues
    
    def check_directory(self, directory: Path, pattern: str = "*.md") -> List[LanguageIssue]:
        """Check all matching files in a directory recursively."""
        all_issues = []
        
        for file_path in directory.rglob(pattern):
            # Skip certain directories
            if any(skip in file_path.parts for skip in ['.git', 'node_modules', 'venv', '__pycache__']):
                continue
            
            issues = self.check_file(file_path)
            all_issues.extend(issues)
        
        return all_issues
    
    def generate_report(self, issues: List[LanguageIssue]) -> str:
        """Generate a human-readable report of issues."""
        if not issues:
            return "✓ No language compliance issues found.\n"
        
        report = [f"Found {len(issues)} language compliance issues:\n"]
        report.append("=" * 80 + "\n")
        
        # Group by file
        issues_by_file: Dict[str, List[LanguageIssue]] = {}
        for issue in issues:
            if issue.file_path not in issues_by_file:
                issues_by_file[issue.file_path] = []
            issues_by_file[issue.file_path].append(issue)
        
        for file_path, file_issues in sorted(issues_by_file.items()):
            report.append(f"\n📄 {file_path}\n")
            report.append("-" * 80 + "\n")
            
            for issue in sorted(file_issues, key=lambda x: x.line_number):
                report.append(f"  Line {issue.line_number}: [{issue.issue_type.upper()}]\n")
                report.append(f"    Found: '{issue.problematic_text}'\n")
                report.append(f"    Suggest: '{issue.suggestion}'\n")
                report.append(f"    Context:\n")
                for ctx_line in issue.context.split('\n')[:3]:
                    report.append(f"      {ctx_line}\n")
                report.append("\n")
        
        return ''.join(report)
    
    def check_repository(self) -> Tuple[List[LanguageIssue], str]:
        """Check entire repository for language compliance."""
        print("Scanning repository for language compliance issues...")
        
        # Check key directories
        issues = []
        for directory in ['docs', 'case_2025_137857', 'case_2025_137857_professional_court_docs']:
            dir_path = self.repo_root / directory
            if dir_path.exists():
                print(f"Checking {directory}/...")
                issues.extend(self.check_directory(dir_path))
        
        report = self.generate_report(issues)
        return issues, report


def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Check documentation for professional language compliance'
    )
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Path to check (file or directory)'
    )
    parser.add_argument(
        '--output',
        '-o',
        help='Output report to file'
    )
    args = parser.parse_args()
    
    checker = LanguageComplianceChecker(repo_root=Path('.').resolve())
    path = Path(args.path)
    
    if path.is_file():
        issues = checker.check_file(path)
        report = checker.generate_report(issues)
    elif path.is_dir():
        issues = checker.check_directory(path)
        report = checker.generate_report(issues)
    else:
        print(f"Error: {path} is not a valid file or directory", file=sys.stderr)
        return 1
    
    # Print report
    print(report)
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"\nReport saved to {args.output}")
    
    # Return exit code based on issues found
    return 1 if issues else 0


if __name__ == '__main__':
    sys.exit(main())
