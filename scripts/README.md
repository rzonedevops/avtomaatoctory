# Scripts Documentation

This directory contains utility scripts for maintaining documentation quality and compliance.

## Language Compliance Tools

### language_compliance_checker.py

Scans documentation for non-professional language patterns that violate professional standards.

**Usage:**
```bash
# Check a single file
python3 scripts/language_compliance_checker.py docs/enhanced_affidavit.md

# Check a directory
python3 scripts/language_compliance_checker.py case_2025_137857/

# Save report to file
python3 scripts/language_compliance_checker.py . --output report.txt
```

**What it checks:**
- Derogatory language (fabrication, malign, reckless, etc.)
- Speculative statements (designed solely to, entirely speculative, etc.)
- Emotional language (bizarre, irrational, shocking, etc.)
- Absolute statements (completely false, must be rejected, etc.)

**Legal exceptions:**
The checker respects legitimate legal terminology like:
- Reckless trading (Companies Act term)
- Malicious prosecution (legal cause of action)
- Misleading the court (legal term of art)
- Gross negligence (legal standard)

### fix_language_compliance.py

Automatically fixes non-professional language patterns while maintaining factual accuracy.

**Usage:**
```bash
# Dry run - show what would be changed without modifying files
python3 scripts/fix_language_compliance.py docs/enhanced_affidavit.md --dry-run

# Apply fixes to a file
python3 scripts/fix_language_compliance.py docs/enhanced_affidavit.md

# Apply fixes to all files in a directory
python3 scripts/fix_language_compliance.py case_2025_137857/

# Save detailed report
python3 scripts/fix_language_compliance.py . --output fix_report.txt
```

**Replacement examples:**
- `fabrication` → `statement not supported by available evidence`
- `misleading` → `not supported by evidence`
- `unfounded` → `not supported by available evidence`
- `bizarre` → `unusual`
- `irrational` → `not consistent with expected behavior`
- `completely false` → `contradicted by available evidence`

## Professional Language Standards

All documentation should adhere to the following principles:

1. **Truthful and sincere** - Based on documented facts
2. **Honest interpretation** - Aligned with available evidence
3. **Free from speculation** - Avoid unsupported claims
4. **Professional and neutral** - No insults, name-calling, or derogatory language
5. **Evidence-based** - Let facts and evidence speak for themselves

See [PROFESSIONAL_LANGUAGE_STYLE_GUIDE.md](../PROFESSIONAL_LANGUAGE_STYLE_GUIDE.md) for detailed guidelines.

## Testing

Language compliance tools are tested in `tests/test_language_compliance.py`.

Run tests with:
```bash
python3 -m pytest tests/test_language_compliance.py -v
```

## Integration with CI/CD

These tools can be integrated into pre-commit hooks or CI/CD pipelines to ensure all documentation maintains professional standards before being committed or merged.

Example pre-commit hook:
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check staged markdown files for language compliance
git diff --cached --name-only --diff-filter=ACM | grep '\.md$' | while read file; do
    python3 scripts/language_compliance_checker.py "$file" || exit 1
done
```

## Contributing

When adding new language patterns to check:

1. Add the pattern to `REPLACEMENTS` in `fix_language_compliance.py`
2. Add corresponding pattern to `PROBLEMATIC_PATTERNS` in `language_compliance_checker.py`
3. Update tests in `tests/test_language_compliance.py`
4. Update the PROFESSIONAL_LANGUAGE_STYLE_GUIDE.md

Always ensure:
- Replacements maintain factual accuracy
- Legal terminology is not incorrectly flagged
- Changes improve professionalism without changing meaning
