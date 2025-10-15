"""
Tests for language compliance checker and fixer.
"""

import pytest
import tempfile
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.language_compliance_checker import LanguageComplianceChecker
from scripts.fix_language_compliance import LanguageComplianceFixer


class TestLanguageComplianceChecker:
    """Test the language compliance checker."""
    
    def test_checker_identifies_problematic_language(self):
        """Test that checker identifies problematic language patterns."""
        checker = LanguageComplianceChecker()
        
        # Create a test file with problematic language
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("This is a fabrication and misleading statement.\n")
            f.write("The allegations are reckless and unfounded.\n")
            f.write("This bizarre claim is completely false.\n")
            test_file = Path(f.name)
        
        try:
            issues = checker.check_file(test_file)
            
            # Should find multiple issues
            assert len(issues) > 0, "Checker should identify problematic language"
            
            # Check that specific patterns were caught
            issue_types = {issue.issue_type for issue in issues}
            assert 'derogatory' in issue_types or 'emotional' in issue_types or 'absolute' in issue_types
            
        finally:
            test_file.unlink()
    
    def test_checker_respects_legal_exceptions(self):
        """Test that checker doesn't flag legitimate legal terms."""
        checker = LanguageComplianceChecker()
        
        # Create a test file with legal exceptions
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("The company engaged in reckless trading under the Companies Act.\n")
            f.write("This constitutes malicious prosecution.\n")
            f.write("The defendant was found guilty of misleading the court.\n")
            test_file = Path(f.name)
        
        try:
            issues = checker.check_file(test_file)
            
            # Should not find issues for legal terms
            assert len(issues) == 0, "Checker should not flag legitimate legal terms"
            
        finally:
            test_file.unlink()
    
    def test_checker_clean_file(self):
        """Test that checker passes clean professional language."""
        checker = LanguageComplianceChecker()
        
        # Create a test file with clean language
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("The evidence indicates that the allegations are not supported by available documentation.\n")
            f.write("The claim appears unusual based on the documented facts.\n")
            f.write("Analysis shows the statement is contradicted by available evidence.\n")
            test_file = Path(f.name)
        
        try:
            issues = checker.check_file(test_file)
            
            # Should find no issues
            assert len(issues) == 0, "Checker should pass clean professional language"
            
        finally:
            test_file.unlink()


class TestLanguageComplianceFixer:
    """Test the language compliance fixer."""
    
    def test_fixer_corrects_problematic_language(self):
        """Test that fixer corrects problematic language patterns."""
        fixer = LanguageComplianceFixer(dry_run=False)
        
        # Create a test file with problematic language
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("This is a fabrication.\n")
            f.write("The claim is unfounded.\n")
            test_file = Path(f.name)
        
        try:
            result = fixer.fix_file(test_file)
            
            # Should have made changes
            assert result['lines_changed'] > 0, "Fixer should make changes"
            assert result['success'], "Fixer should succeed"
            
            # Verify the file was actually changed
            with open(test_file, 'r') as f:
                content = f.read()
                assert 'fabrication' not in content.lower(), "Original problematic word should be replaced"
                assert 'unfounded' not in content.lower(), "Original problematic word should be replaced"
            
        finally:
            test_file.unlink()
    
    def test_fixer_dry_run_mode(self):
        """Test that dry run mode doesn't modify files."""
        fixer = LanguageComplianceFixer(dry_run=True)
        
        # Create a test file with problematic language
        original_content = "This is a fabrication.\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(original_content)
            test_file = Path(f.name)
        
        try:
            result = fixer.fix_file(test_file)
            
            # Should detect changes but not apply them
            assert result['lines_changed'] > 0, "Should detect issues"
            
            # Verify the file was NOT changed
            with open(test_file, 'r') as f:
                content = f.read()
                assert content == original_content, "Dry run should not modify file"
            
        finally:
            test_file.unlink()
    
    def test_fixer_preserves_clean_language(self):
        """Test that fixer doesn't change already compliant language."""
        fixer = LanguageComplianceFixer(dry_run=False)
        
        # Create a test file with clean language
        clean_content = "The evidence indicates that the claims are not supported.\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(clean_content)
            test_file = Path(f.name)
        
        try:
            result = fixer.fix_file(test_file)
            
            # Should make no changes
            assert result['lines_changed'] == 0, "Should not change compliant language"
            
            # Verify content unchanged
            with open(test_file, 'r') as f:
                content = f.read()
                assert content == clean_content, "Content should remain unchanged"
            
        finally:
            test_file.unlink()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
