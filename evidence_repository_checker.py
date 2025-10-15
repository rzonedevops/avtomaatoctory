#!/usr/bin/env python3
"""
Evidence Repository Checker

This script checks multiple GitHub repositories for evidence files that are 
needed based on the evidence requirements found in this repository.
"""

import json
import re
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Any
from github import Github
import argparse


class EvidenceRepositoryChecker:
    def __init__(self, github_token: str = None):
        """Initialize the evidence repository checker"""
        self.github_token = github_token
        self.github = Github(github_token) if github_token else None
        
        # Repositories to check
        self.target_repositories = [
            "cogpy/ad-res-j7",
            "EchoCog/analysss", 
            "rzonedevops/analysis",
            "rzonedevops/avtomaatoctory",
            "rzonedevops/analyticase"
        ]
        
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
        
    def get_repository_files(self, repo_name: str) -> Dict[str, Any]:
        """Get all files from a repository using GitHub API"""
        try:
            if not self.github:
                return {"error": "GitHub token not provided", "files": []}
                
            repo = self.github.get_repo(repo_name)
            
            # Get repository contents recursively
            contents = repo.get_contents("")
            files = []
            
            def process_contents(contents_list, path=""):
                for content in contents_list:
                    if content.type == "dir":
                        # Recursively get directory contents
                        subcontents = repo.get_contents(content.path)
                        process_contents(subcontents, content.path + "/")
                    else:
                        files.append({
                            "name": content.name,
                            "path": content.path, 
                            "size": content.size,
                            "download_url": content.download_url
                        })
            
            process_contents(contents)
            
            return {
                "repo": repo_name,
                "total_files": len(files),
                "files": files,
                "last_updated": str(repo.updated_at),
                "default_branch": repo.default_branch
            }
            
        except Exception as e:
            return {
                "repo": repo_name,
                "error": str(e),
                "files": []
            }
    
    def check_evidence_files(self, repo_files: Dict[str, Any]) -> Dict[str, Any]:
        """Check which evidence files are present in the repository"""
        if "error" in repo_files:
            return {"repo": repo_files.get("repo", "unknown"), "error": repo_files["error"]}
            
        repo_name = repo_files["repo"]
        files = repo_files["files"]
        
        # Extract file names and paths
        file_names = [f["name"].lower() for f in files]
        file_paths = [f["path"].lower() for f in files]
        
        results = {
            "repo": repo_name,
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
                for i, file_info in enumerate(files):
                    if (evidence_lower in file_info["name"].lower() or 
                        evidence_lower in file_info["path"].lower()):
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
    
    def generate_report(self, all_results: List[Dict[str, Any]]) -> str:
        """Generate a comprehensive report of evidence file findings"""
        
        report = """# Evidence File Repository Check Report

## Executive Summary

This report shows which evidence files needed for the Faucitt Family Trust case
are available in the specified GitHub repositories.

"""
        
        # Summary statistics
        total_repos_checked = len(all_results)
        repos_with_evidence = sum(1 for r in all_results if r.get("summary", {}).get("total_evidence_files", 0) > 0)
        
        report += f"""
### Summary Statistics
- **Repositories Checked**: {total_repos_checked}
- **Repositories with Evidence**: {repos_with_evidence}
- **Total Evidence Files Found**: {sum(r.get("summary", {}).get("total_evidence_files", 0) for r in all_results)}

"""

        # Repository-by-repository breakdown
        report += "## Repository Analysis\n\n"
        
        for result in all_results:
            repo_name = result.get("repo", "Unknown")
            report += f"### {repo_name}\n\n"
            
            if "error" in result:
                report += f"**STATUS**: ❌ Error accessing repository\n"
                report += f"**ERROR**: {result['error']}\n\n"
                continue
            
            summary = result.get("summary", {})
            total_files = result.get("total_files", 0)
            evidence_files = summary.get("total_evidence_files", 0)
            
            report += f"**STATUS**: {'✅ Evidence Found' if evidence_files > 0 else '⚠️ No Evidence Found'}\n"
            report += f"**Total Files**: {total_files}\n"
            report += f"**Evidence Files**: {evidence_files}\n\n"
            
            # Critical files found
            found_files = summary.get("found_critical_files", [])
            if found_files:
                report += "#### ✅ Critical Evidence Files Found\n"
                for file in found_files:
                    report += f"- {file}\n"
                report += "\n"
            
            # Missing critical files
            missing_files = summary.get("missing_critical_files", [])
            if missing_files:
                report += "#### ❌ Missing Critical Evidence Files\n"
                for file in missing_files:
                    report += f"- {file}\n"
                report += "\n"
            
            # Pattern matches
            pattern_matches = result.get("pattern_matches", {})
            if pattern_matches:
                report += "#### 🔍 Pattern Matches (Potential Evidence)\n"
                for pattern, matches in pattern_matches.items():
                    if matches:
                        report += f"**Pattern**: `{pattern}`\n"
                        for match in matches[:5]:  # Limit to first 5 matches
                            report += f"- {match['path']} ({match['size']} bytes)\n"
                        if len(matches) > 5:
                            report += f"- ... and {len(matches) - 5} more files\n"
                        report += "\n"
            
            report += "---\n\n"
        
        # Comprehensive evidence status
        report += "## Critical Evidence File Status\n\n"
        
        all_evidence_files = {}
        for category, files in self.evidence_patterns.items():
            all_evidence_files[category] = {}
            for file in files:
                # Check across all repositories
                found_in = []
                for result in all_results:
                    if "error" not in result:
                        evidence_found = result.get("evidence_found", {}).get(category, {})
                        if evidence_found.get(file, {}).get("found", False):
                            found_in.append(result["repo"])
                
                all_evidence_files[category][file] = found_in
        
        for category, files in all_evidence_files.items():
            report += f"### {category.replace('_', ' ').title()}\n\n"
            for file, repos in files.items():
                status = "✅" if repos else "❌"
                repo_list = ", ".join(repos) if repos else "Not found"
                report += f"- {status} **{file}**: {repo_list}\n"
            report += "\n"
        
        # Recommendations
        report += "## Recommendations\n\n"
        
        # Count missing files
        missing_count = sum(1 for category in all_evidence_files.values() 
                          for repos in category.values() if not repos)
        total_count = sum(len(category) for category in all_evidence_files.values())
        
        if missing_count == 0:
            report += "✅ **All critical evidence files found!** The repositories contain all necessary evidence.\n\n"
        elif missing_count < total_count / 2:
            report += f"⚠️ **Partially Complete**: {total_count - missing_count}/{total_count} evidence files found. Missing {missing_count} files.\n\n"
            report += "**Actions Needed**:\n"
            report += "1. Locate and upload missing evidence files\n"
            report += "2. Verify file integrity of found evidence\n"
            report += "3. Ensure proper access permissions\n\n"
        else:
            report += f"❌ **Significant Gaps**: Only {total_count - missing_count}/{total_count} evidence files found. {missing_count} files missing.\n\n"
            report += "**Urgent Actions Needed**:\n"
            report += "1. Immediate evidence collection and upload\n" 
            report += "2. Verify evidence sources and authenticity\n"
            report += "3. Establish proper evidence management procedures\n"
            report += "4. Consider legal implications of missing evidence\n\n"
        
        report += f"""
## Generated Information

**Report Generated**: {Path(__file__).name}
**Date**: {os.popen('date').read().strip()}
**Repositories Checked**: {len(self.target_repositories)}
**Evidence Categories**: {len(self.evidence_patterns)}
**Total Evidence Files Sought**: {sum(len(files) for files in self.evidence_patterns.values())}

---

**END OF REPORT**
"""
        
        return report
    
    def run_check(self, output_file: str = None) -> Dict[str, Any]:
        """Run the evidence check across all repositories"""
        
        print("🔍 Starting evidence repository check...")
        print(f"📋 Checking {len(self.target_repositories)} repositories")
        print(f"🔎 Looking for {sum(len(files) for files in self.evidence_patterns.values())} specific evidence files")
        print()
        
        all_results = []
        
        for repo_name in self.target_repositories:
            print(f"📂 Checking {repo_name}...")
            
            if self.github:
                repo_files = self.get_repository_files(repo_name)
                results = self.check_evidence_files(repo_files)
                all_results.append(results)
                
                # Print quick summary
                if "error" in results:
                    print(f"   ❌ Error: {results['error']}")
                else:
                    evidence_count = results.get("summary", {}).get("total_evidence_files", 0)
                    total_files = results.get("total_files", 0)
                    print(f"   📊 {evidence_count} evidence files found ({total_files} total files)")
            else:
                print(f"   ⚠️  Skipping {repo_name} (no GitHub token provided)")
                all_results.append({
                    "repo": repo_name,
                    "error": "No GitHub token provided - cannot access repository"
                })
            
            print()
        
        # Generate report
        report = self.generate_report(all_results)
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
            print(f"📄 Report saved to: {output_file}")
        
        return {
            "results": all_results,
            "report": report,
            "summary": {
                "repositories_checked": len(self.target_repositories),
                "repositories_accessible": len([r for r in all_results if "error" not in r]),
                "total_evidence_files_found": sum(r.get("summary", {}).get("total_evidence_files", 0) for r in all_results)
            }
        }


def main():
    parser = argparse.ArgumentParser(description="Check GitHub repositories for evidence files")
    parser.add_argument("--token", help="GitHub personal access token")
    parser.add_argument("--output", help="Output file for report", default="evidence_repository_report.md")
    parser.add_argument("--list-patterns", action="store_true", help="List evidence patterns and exit")
    
    args = parser.parse_args()
    
    checker = EvidenceRepositoryChecker(github_token=args.token)
    
    if args.list_patterns:
        print("Evidence File Patterns:")
        for category, files in checker.evidence_patterns.items():
            print(f"\n{category}:")
            for file in files:
                print(f"  - {file}")
        return
    
    if not args.token:
        print("⚠️  WARNING: No GitHub token provided. Repository access will be limited.")
        print("   Use --token YOUR_TOKEN to access private repositories.")
        print("   For public repositories, continuing with limited access...")
        print()
    
    results = checker.run_check(args.output)
    
    print("✅ Evidence repository check completed!")
    print(f"📊 Summary: {results['summary']['total_evidence_files_found']} evidence files found across {results['summary']['repositories_accessible']}/{results['summary']['repositories_checked']} accessible repositories")


if __name__ == "__main__":
    main()