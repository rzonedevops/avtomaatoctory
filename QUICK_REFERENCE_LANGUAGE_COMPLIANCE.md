# Quick Reference: Professional Language Compliance

## Core Principles

**Above all else:**
1. ✓ Truthful and sincere statements
2. ✓ Honest interpretation of facts  
3. ✓ Avoid speculative claims
4. ✓ No insults, name-calling, false accusations, or derogatory language
5. ✓ Professional and neutral at all times
6. ✓ Let facts and evidence speak for themselves

## Common Replacements

| ❌ Avoid | ✓ Use Instead |
|---------|---------------|
| fabrication | statement not supported by available evidence |
| reckless (non-legal) | without adequate consideration |
| malign | mischaracterize |
| misleading | not supported by evidence |
| unfounded | not supported by available evidence |
| devoid of | lacking |
| bizarre | unusual |
| irrational | not consistent with expected behavior |
| designed solely to | appears to |
| entirely speculative | not evidenced |
| completely false | contradicted by available evidence |

## Quick Commands

```bash
# Check before committing
python3 scripts/language_compliance_checker.py yourfile.md

# Auto-fix issues
python3 scripts/fix_language_compliance.py yourfile.md

# See what would change (safe)
python3 scripts/fix_language_compliance.py yourfile.md --dry-run
```

## Legal Terms (OK to use)

These are legitimate legal terms and won't be flagged:
- Reckless trading (Companies Act)
- Malicious prosecution
- Misleading the court
- Gross negligence

## More Info

- Full guide: [PROFESSIONAL_LANGUAGE_STYLE_GUIDE.md](PROFESSIONAL_LANGUAGE_STYLE_GUIDE.md)
- Complete summary: [LANGUAGE_COMPLIANCE_SUMMARY.md](LANGUAGE_COMPLIANCE_SUMMARY.md)
- Tool docs: [scripts/README.md](scripts/README.md)
