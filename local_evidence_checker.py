#!/usr/bin/env python3
"""
Local Evidence File Checker

This script checks the current local repository for evidence files.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Any


class LocalEvidenceChecker:
    def __init__(self, repository_path: str = "."):
        """Initialize the local evidence checker"""
        self.repository_path = Path(repository_path)
        
        # Evidence file patterns we're looking for
        self.evidence_patterns = {
            # Core evidence files from EVIDENCE_REPOSITORY_SUMMARY.md
            "investment_payout": [
                "BantjiesInvestmentPayoutDates2026-05.jpg",
                "bantjies_investment_payout_analysis.md"
            ],
            "august_2025_fraud": [
                "Email-2025-08-11-Outlook.pdf", 
                "LetterofAppointment11082025(1).pdf",
                "LetterofAppointment11082025.pdf",  # Alternative name
                "august_2025_fraudulent_appointment_analysis.md"
            ],
            "trust_conspiracy": [
                "faucitt_family_trust_conspiracy_evidence.md"
            ],
            "financial_evidence": [
                "REG-TRIALBALANCE.xlsx",
                "WW-TrialBalanceFEB20.xlsx", 
                "SL-TRIALBALANCE2020.xlsx",
                "VV-TRIALBALANCEAPR20202.xlsx"
            ],
            "regulatory_compliance": [
                "ICO_GDPR_criminal_prosecution_guide.md",
                "ICO_criminal_complaint_template.txt"
            ],
            "supporting_documents": [
                "RegimA_Zone_UK_Bank_Shopify_Payments.png",
                "Shopify_Invoices_RegimA_2016-2025.txt",
                "UK_Bank_Statement_Shopify_Payments_Analysis.md"
            ]
        }
        
        # Additional patterns to search for
        self.search_patterns = [
            r".*evidence.*\.pdf$",
            r".*evidence.*\.xlsx?$", 
            r".*evidence.*\.jpg$",
            r".*evidence.*\.png$",
            r".*evidence.*\.md$",
            r".*trial.*balance.*\.xlsx?$",
            r".*bantjies.*investment.*",
            r".*faucitt.*family.*trust.*",
            r".*regima.*financial.*",
            r".*shopify.*evidence.*",
            r".*email.*2025-08-11.*"
        ]
        
    def scan_repository(self) -> Dict[str, Any]:
        """Scan the local repository for all files"""
        files = []
        
        for root, dirs, filenames in os.walk(self.repository_path):
            # Skip .git directory
            if '.git' in dirs:
                dirs.remove('.git')
                
            for filename in filenames:
                full_path = Path(root) / filename
                relative_path = full_path.relative_to(self.repository_path)
                
                try:
                    file_size = full_path.stat().st_size
                except OSError:
                    file_size = 0
                
                files.append({
                    "name": filename,
                    "path": str(relative_path),
                    "full_path": str(full_path),
                    "size": file_size
                })
        
        return {
            "repository": str(self.repository_path.resolve()),
            "total_files": len(files),
            "files": files
        }
    
    def check_evidence_files(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check which evidence files are present in the repository"""
        
        files = repo_data["files"]
        
        results = {
            "repository": repo_data["repository"],
            "total_files": len(files),
            "evidence_found": {},
            "pattern_matches": {},
            "summary": {
                "total_evidence_files": 0,
                "missing_critical_files": [],
                "found_critical_files": []
            }
        }
        
        # Check for specific evidence files
        for category, file_list in self.evidence_patterns.items():
            results["evidence_found"][category] = {}
            
            for evidence_file in file_list:
                found = False
                matching_files = []
                
                # Check exact matches and partial matches
                evidence_lower = evidence_file.lower()
                for file_info in files:
                    if (evidence_lower in file_info["name"].lower() or 
                        evidence_lower.replace('.pdf', '').replace('.jpg', '').replace('.md', '').replace('.xlsx', '') 
                        in file_info["name"].lower()):
                        found = True
                        matching_files.append({
                            "name": file_info["name"],
                            "path": file_info["path"],
                            "size": file_info["size"]
                        })
                
                results["evidence_found"][category][evidence_file] = {
                    "found": found,
                    "matches": matching_files
                }
                
                if found:
                    results["summary"]["found_critical_files"].append(evidence_file)
                    results["summary"]["total_evidence_files"] += len(matching_files)
                else:
                    results["summary"]["missing_critical_files"].append(evidence_file)
        
        # Check pattern matches
        for pattern in self.search_patterns:
            matches = []
            regex = re.compile(pattern, re.IGNORECASE)
            
            for file_info in files:
                if (regex.match(file_info["name"]) or 
                    regex.match(file_info["path"])):
                    matches.append({
                        "name": file_info["name"],
                        "path": file_info["path"],
                        "size": file_info["size"]
                    })
            
            if matches:
                results["pattern_matches"][pattern] = matches
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive report of evidence file findings"""
        
        report = f"""# Local Evidence File Check Report

## Repository: {results['repository']}

This report shows which evidence files needed for the Faucitt Family Trust case
are available in the current local repository.

"""
        
        # Summary statistics
        total_files = results.get("total_files", 0)
        evidence_files = results.get("summary", {}).get("total_evidence_files", 0)
        
        report += f"""
### Summary Statistics
- **Total Files Scanned**: {total_files:,}
- **Evidence Files Found**: {evidence_files}
- **Evidence Categories**: {len(self.evidence_patterns)}

"""

        summary = results.get("summary", {})
        
        # Status indicator
        missing_count = len(summary.get("missing_critical_files", []))
        found_count = len(summary.get("found_critical_files", []))
        total_count = missing_count + found_count
        
        if missing_count == 0:
            status = "✅ COMPLETE"
            color = "green"
        elif missing_count <= total_count / 3:
            status = "⚠️ MOSTLY COMPLETE" 
            color = "orange"
        else:
            status = "❌ INCOMPLETE"
            color = "red"
        
        report += f"### Overall Status: {status}\n"
        report += f"- **Found**: {found_count}/{total_count} critical evidence files\n"
        report += f"- **Missing**: {missing_count}/{total_count} critical evidence files\n\n"
        
        # Critical files found
        found_files = summary.get("found_critical_files", [])
        if found_files:
            report += "## ✅ Critical Evidence Files Found\n\n"
            for file in found_files:
                # Find the actual matches to show paths
                for category, files_dict in results.get("evidence_found", {}).items():
                    if file in files_dict:
                        matches = files_dict[file].get("matches", [])
                        if matches:
                            report += f"### {file}\n"
                            for match in matches:
                                size_kb = match['size'] / 1024 if match['size'] > 0 else 0
                                report += f"- **Path**: `{match['path']}`\n"
                                report += f"- **Size**: {size_kb:.1f} KB\n\n"
                            break
        
        # Missing critical files
        missing_files = summary.get("missing_critical_files", [])
        if missing_files:
            report += "## ❌ Missing Critical Evidence Files\n\n"
            for file in missing_files:
                report += f"- {file}\n"
            report += "\n"
        
        # Evidence by category
        report += "## Evidence Files by Category\n\n"
        
        for category, files_dict in results.get("evidence_found", {}).items():
            report += f"### {category.replace('_', ' ').title()}\n\n"
            
            category_found = 0
            category_total = len(files_dict)
            
            for file, file_data in files_dict.items():
                found = file_data.get("found", False)
                matches = file_data.get("matches", [])
                
                if found:
                    category_found += 1
                    report += f"✅ **{file}**\n"
                    for match in matches:
                        report += f"   - {match['path']} ({match['size']:,} bytes)\n"
                else:
                    report += f"❌ **{file}** - Not found\n"
            
            report += f"\n**Category Status**: {category_found}/{category_total} files found\n\n"
        
        # Pattern matches (potential evidence)
        pattern_matches = results.get("pattern_matches", {})
        if pattern_matches:
            report += "## 🔍 Pattern Matches (Potential Evidence)\n\n"
            
            for pattern, matches in pattern_matches.items():
                if matches:
                    report += f"### Pattern: `{pattern}`\n\n"
                    
                    # Group by directory for better organization
                    dirs = {}
                    for match in matches:
                        dir_path = str(Path(match['path']).parent)
                        if dir_path not in dirs:
                            dirs[dir_path] = []
                        dirs[dir_path].append(match)
                    
                    for dir_path, dir_matches in dirs.items():
                        if dir_path != ".":
                            report += f"**Directory**: `{dir_path}`\n"
                        
                        for match in dir_matches[:10]:  # Limit to first 10 matches per directory
                            size_kb = match['size'] / 1024 if match['size'] > 0 else 0
                            report += f"- {match['name']} ({size_kb:.1f} KB)\n"
                        
                        if len(dir_matches) > 10:
                            report += f"- ... and {len(dir_matches) - 10} more files\n"
                        
                        report += "\n"
        
        # Recommendations
        report += "## Recommendations\n\n"
        
        if missing_count == 0:
            report += "✅ **All critical evidence files found!** The repository contains all necessary evidence.\n\n"
            report += "**Next Steps**:\n"
            report += "1. Verify file integrity and authenticity\n"
            report += "2. Ensure proper access permissions\n" 
            report += "3. Create backups of critical evidence\n"
            report += "4. Document chain of custody\n\n"
        elif missing_count < total_count / 2:
            report += f"⚠️ **Partially Complete**: {found_count}/{total_count} evidence files found. Missing {missing_count} files.\n\n"
            report += "**Actions Needed**:\n"
            report += "1. Locate and add missing evidence files\n"
            report += "2. Check other repositories for missing files\n"
            report += "3. Verify existing file integrity\n"
            report += "4. Update file organization if needed\n\n"
        else:
            report += f"❌ **Significant Gaps**: Only {found_count}/{total_count} evidence files found. {missing_count} files missing.\n\n"
            report += "**Urgent Actions Needed**:\n"
            report += "1. Immediate evidence collection and organization\n" 
            report += "2. Search other repositories systematically\n"
            report += "3. Verify evidence sources and authenticity\n"
            report += "4. Establish proper evidence management procedures\n"
            report += "5. Consider legal implications of missing evidence\n\n"
        
        report += f"""
## Technical Information

**Script**: {__file__}
**Repository Scanned**: {results['repository']}
**Files Scanned**: {total_files:,}
**Evidence Categories**: {len(self.evidence_patterns)}
**Search Patterns**: {len(self.search_patterns)}

---

**END OF REPORT**
"""
        
        return report
    
    def run_check(self, output_file: str = None) -> Dict[str, Any]:
        """Run the evidence check on the local repository"""
        
        print("🔍 Starting local evidence file check...")
        print(f"📂 Scanning repository: {self.repository_path.resolve()}")
        
        # Scan repository
        repo_data = self.scan_repository()
        print(f"📊 Found {repo_data['total_files']:,} total files")
        
        # Check for evidence files
        results = self.check_evidence_files(repo_data)
        
        evidence_count = results.get("summary", {}).get("total_evidence_files", 0)
        missing_count = len(results.get("summary", {}).get("missing_critical_files", []))
        found_count = len(results.get("summary", {}).get("found_critical_files", []))
        
        print(f"🔎 Evidence files found: {evidence_count}")
        print(f"✅ Critical files found: {found_count}")
        print(f"❌ Critical files missing: {missing_count}")
        
        # Generate report
        report = self.generate_report(results)
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
            print(f"📄 Report saved to: {output_file}")
        
        return {
            "results": results,
            "report": report,
            "summary": {
                "total_files": repo_data['total_files'],
                "evidence_files_found": evidence_count,
                "critical_files_found": found_count,
                "critical_files_missing": missing_count
            }
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Check local repository for evidence files")
    parser.add_argument("--path", help="Repository path to scan", default=".")
    parser.add_argument("--output", help="Output file for report", default="local_evidence_report.md")
    
    args = parser.parse_args()
    
    checker = LocalEvidenceChecker(args.path)
    results = checker.run_check(args.output)
    
    print("\n✅ Local evidence file check completed!")
    summary = results['summary']
    print(f"📊 Summary: {summary['evidence_files_found']} evidence files found")
    print(f"   Critical files: {summary['critical_files_found']} found, {summary['critical_files_missing']} missing")


if __name__ == "__main__":
    main()