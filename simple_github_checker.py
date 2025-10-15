#!/usr/bin/env python3
"""
Simple GitHub Repository File Checker

This script checks GitHub repositories for file patterns using the GitHub API
without authentication (public repositories only).
"""

import requests
import re
import json
from typing import Dict, List, Any


class SimpleGitHubChecker:
    def __init__(self):
        """Initialize the simple GitHub checker"""
        self.base_url = "https://api.github.com"
        
        # Evidence file patterns we're looking for
        self.evidence_files = [
            "BantjiesInvestmentPayoutDates2026-05.jpg",
            "bantjies_investment_payout_analysis.md",
            "Email-2025-08-11-Outlook.pdf", 
            "LetterofAppointment11082025(1).pdf",
            "august_2025_fraudulent_appointment_analysis.md",
            "faucitt_family_trust_conspiracy_evidence.md",
            "REG-TRIALBALANCE.xlsx",
            "WW-TrialBalanceFEB20.xlsx", 
            "SL-TRIALBALANCE2020.xlsx",
            "VV-TRIALBALANCEAPR20202.xlsx",
            "ICO_GDPR_criminal_prosecution_guide.md",
            "ICO_criminal_complaint_template.txt",
            "RegimA_Zone_UK_Bank_Shopify_Payments.png",
            "Shopify_Invoices_RegimA_2016-2025.txt",
            "UK_Bank_Statement_Shopify_Payments_Analysis.md"
        ]
        
        self.search_patterns = [
            "evidence",
            "trial_balance", 
            "bantjies",
            "faucitt_family_trust",
            "regima",
            "shopify",
            "email_2025"
        ]
    
    def check_repository_exists(self, repo_name: str) -> Dict[str, Any]:
        """Check if a repository exists and get basic info"""
        url = f"{self.base_url}/repos/{repo_name}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                repo_info = response.json()
                return {
                    "exists": True,
                    "name": repo_info["name"],
                    "full_name": repo_info["full_name"],
                    "private": repo_info["private"],
                    "size": repo_info["size"],
                    "updated_at": repo_info["updated_at"],
                    "default_branch": repo_info["default_branch"]
                }
            elif response.status_code == 404:
                return {"exists": False, "error": "Repository not found"}
            elif response.status_code == 403:
                return {"exists": False, "error": "Access forbidden (private repository or rate limited)"}
            else:
                return {"exists": False, "error": f"HTTP {response.status_code}"}
                
        except requests.RequestException as e:
            return {"exists": False, "error": f"Request failed: {str(e)}"}
    
    def search_repository_files(self, repo_name: str) -> Dict[str, Any]:
        """Search for evidence files in a repository using GitHub search API"""
        
        results = {
            "repository": repo_name,
            "evidence_files": {},
            "pattern_matches": {},
            "search_errors": []
        }
        
        # Search for specific evidence files
        for evidence_file in self.evidence_files:
            search_url = f"{self.base_url}/search/code"
            params = {
                "q": f"filename:{evidence_file} repo:{repo_name}",
                "per_page": 10
            }
            
            try:
                response = requests.get(search_url, params=params, timeout=10)
                if response.status_code == 200:
                    search_data = response.json()
                    items = search_data.get("items", [])
                    
                    results["evidence_files"][evidence_file] = {
                        "found": len(items) > 0,
                        "matches": [
                            {
                                "name": item["name"],
                                "path": item["path"],
                                "url": item["html_url"]
                            }
                            for item in items
                        ]
                    }
                elif response.status_code == 403:
                    results["search_errors"].append(f"Rate limited or forbidden for {evidence_file}")
                elif response.status_code == 422:
                    # Unprocessable entity - repository might not be indexed
                    results["evidence_files"][evidence_file] = {
                        "found": False,
                        "error": "Repository not indexed for search"
                    }
                else:
                    results["search_errors"].append(f"Search failed for {evidence_file}: HTTP {response.status_code}")
                    
            except requests.RequestException as e:
                results["search_errors"].append(f"Request failed for {evidence_file}: {str(e)}")
        
        # Search for pattern matches
        for pattern in self.search_patterns:
            search_url = f"{self.base_url}/search/code"
            params = {
                "q": f"{pattern} repo:{repo_name}",
                "per_page": 20
            }
            
            try:
                response = requests.get(search_url, params=params, timeout=10)
                if response.status_code == 200:
                    search_data = response.json()
                    items = search_data.get("items", [])
                    
                    if items:
                        results["pattern_matches"][pattern] = [
                            {
                                "name": item["name"],
                                "path": item["path"],
                                "url": item["html_url"]
                            }
                            for item in items
                        ]
                elif response.status_code == 403:
                    results["search_errors"].append(f"Rate limited for pattern {pattern}")
                    break  # Stop searching patterns if rate limited
                    
            except requests.RequestException as e:
                results["search_errors"].append(f"Pattern search failed for {pattern}: {str(e)}")
        
        return results
    
    def check_repositories(self, repo_list: List[str]) -> Dict[str, Any]:
        """Check multiple repositories"""
        
        all_results = {}
        
        for repo_name in repo_list:
            print(f"📂 Checking {repo_name}...")
            
            # Check if repository exists
            repo_info = self.check_repository_exists(repo_name)
            
            if not repo_info.get("exists", False):
                print(f"   ❌ {repo_info.get('error', 'Unknown error')}")
                all_results[repo_name] = {
                    "accessible": False,
                    "error": repo_info.get("error", "Unknown error")
                }
                continue
            
            if repo_info.get("private", False):
                print(f"   🔒 Private repository - cannot search without token")
                all_results[repo_name] = {
                    "accessible": False,
                    "error": "Private repository"
                }
                continue
            
            print(f"   📊 Public repository found (Size: {repo_info['size']} KB)")
            
            # Search for files
            search_results = self.search_repository_files(repo_name)
            
            # Count found evidence files
            evidence_found = sum(1 for file_data in search_results["evidence_files"].values() 
                               if file_data.get("found", False))
            
            pattern_matches = sum(len(matches) for matches in search_results["pattern_matches"].values())
            
            print(f"   🔎 Evidence files: {evidence_found}/{len(self.evidence_files)}")
            print(f"   🔍 Pattern matches: {pattern_matches}")
            
            if search_results["search_errors"]:
                print(f"   ⚠️  Errors: {len(search_results['search_errors'])}")
            
            all_results[repo_name] = {
                "accessible": True,
                "repo_info": repo_info,
                "search_results": search_results,
                "summary": {
                    "evidence_files_found": evidence_found,
                    "pattern_matches": pattern_matches,
                    "search_errors": len(search_results["search_errors"])
                }
            }
        
        return all_results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive report"""
        
        report = """# GitHub Repository Evidence Check Report

## Overview
This report checks public GitHub repositories for evidence files using the GitHub Search API.

## Repository Results

"""
        
        total_repos = len(results)
        accessible_repos = sum(1 for r in results.values() if r.get("accessible", False))
        total_evidence_found = sum(r.get("summary", {}).get("evidence_files_found", 0) for r in results.values())
        
        report += f"""### Summary
- **Repositories Checked**: {total_repos}
- **Accessible Repositories**: {accessible_repos}
- **Total Evidence Files Found**: {total_evidence_found}

"""
        
        for repo_name, repo_results in results.items():
            report += f"### {repo_name}\n\n"
            
            if not repo_results.get("accessible", False):
                error = repo_results.get("error", "Unknown error")
                report += f"**Status**: ❌ Not accessible ({error})\n\n"
                continue
            
            repo_info = repo_results.get("repo_info", {})
            summary = repo_results.get("summary", {})
            search_results = repo_results.get("search_results", {})
            
            report += f"**Status**: ✅ Accessible (Public repository)\n"
            report += f"**Size**: {repo_info.get('size', 0)} KB\n"
            report += f"**Last Updated**: {repo_info.get('updated_at', 'Unknown')}\n"
            report += f"**Evidence Files Found**: {summary.get('evidence_files_found', 0)}/{len(self.evidence_files)}\n"
            report += f"**Pattern Matches**: {summary.get('pattern_matches', 0)}\n\n"
            
            # Evidence files found
            evidence_files = search_results.get("evidence_files", {})
            found_files = {k: v for k, v in evidence_files.items() if v.get("found", False)}
            
            if found_files:
                report += "#### ✅ Evidence Files Found\n\n"
                for file_name, file_data in found_files.items():
                    matches = file_data.get("matches", [])
                    report += f"**{file_name}**\n"
                    for match in matches:
                        report += f"- Path: `{match['path']}`\n"
                        report += f"- URL: {match['url']}\n"
                    report += "\n"
            
            # Pattern matches
            pattern_matches = search_results.get("pattern_matches", {})
            if pattern_matches:
                report += "#### 🔍 Pattern Matches\n\n"
                for pattern, matches in pattern_matches.items():
                    if matches:
                        report += f"**Pattern: {pattern}** ({len(matches)} files)\n"
                        for match in matches[:5]:  # Show first 5
                            report += f"- {match['name']} (`{match['path']}`)\n"
                        if len(matches) > 5:
                            report += f"- ... and {len(matches) - 5} more files\n"
                        report += "\n"
            
            # Search errors
            search_errors = search_results.get("search_errors", [])
            if search_errors:
                report += "#### ⚠️ Search Errors\n\n"
                for error in search_errors:
                    report += f"- {error}\n"
                report += "\n"
            
            report += "---\n\n"
        
        report += """
## Limitations

This check has the following limitations:
1. **Public repositories only** - Private repositories require authentication
2. **Search API limitations** - Rate limiting and indexing delays
3. **File content search** - Cannot check file contents without downloading
4. **Authentication required** - Use GitHub token for complete access

## Recommendations

1. **Use authenticated access** - Obtain GitHub token for private repositories
2. **Manual verification** - Download and verify found files
3. **Check file integrity** - Ensure files are complete and authentic
4. **Cross-reference** - Compare with local repository findings

---

**Generated**: Evidence repository checker
**Repositories Checked**: """ + str(total_repos) + """
**Public Repositories Found**: """ + str(accessible_repos) + """

"""
        
        return report


def main():
    repositories = [
        "cogpy/ad-res-j7",
        "EchoCog/analysss", 
        "rzonedevops/analysis",
        "rzonedevops/avtomaatoctory",
        "rzonedevops/analyticase"
    ]
    
    checker = SimpleGitHubChecker()
    
    print("🔍 Simple GitHub Repository Evidence Check")
    print(f"📋 Checking {len(repositories)} repositories")
    print("⚠️  Note: Only public repositories can be checked without authentication")
    print()
    
    results = checker.check_repositories(repositories)
    
    # Generate report
    report = checker.generate_report(results)
    
    # Save report
    output_file = "simple_github_evidence_report.md"
    with open(output_file, 'w') as f:
        f.write(report)
    
    print(f"\n📄 Report saved to: {output_file}")
    print("✅ Check completed!")
    
    # Summary
    accessible = sum(1 for r in results.values() if r.get("accessible", False))
    evidence_found = sum(r.get("summary", {}).get("evidence_files_found", 0) for r in results.values())
    
    print(f"📊 Summary: {evidence_found} evidence files found in {accessible} accessible repositories")


if __name__ == "__main__":
    main()