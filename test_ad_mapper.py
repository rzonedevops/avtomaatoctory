#!/usr/bin/env python3
"""
Test script for AD Hypergraph Mapper
"""

import sys
import os
import logging
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.tools.ad_hypergraph_repo_mapper import ADHypergraphRepoMapper

def test_local_analysis():
    """Test analysis on current repository"""
    print("🔍 Testing AD Hypergraph Mapper with current repository...")
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Create mapper with limited scope (just local repo)
    mapper = ADHypergraphRepoMapper(workspace_dir="/tmp/ad_test")
    
    # Override target repos to just include locally accessible ones
    mapper.target_repos = [
        "https://github.com/rzonedevops/avtomaatoctory"
    ]
    
    # Re-initialize repositories
    mapper.repositories = {}
    for repo_url in mapper.target_repos:
        owner, name = mapper._parse_repo_url(repo_url)
        from src.tools.ad_hypergraph_repo_mapper import RepositoryInfo
        repo_info = RepositoryInfo(url=repo_url, name=name, owner=owner)
        mapper.repositories[f"{owner}/{name}"] = repo_info
    
    # Use current directory as "local clone" of avtomaatoctory
    current_path = Path(__file__).parent
    mapper.repositories["rzonedevops/avtomaatoctory"].local_path = current_path
    mapper.repositories["rzonedevops/avtomaatoctory"].accessible = True
    
    print("📊 Scanning current repository structure...")
    mapper._scan_repository_structure(mapper.repositories["rzonedevops/avtomaatoctory"])
    
    print("🔗 Extracting entities and relations...")
    entities = mapper._extract_entities_from_repo(mapper.repositories["rzonedevops/avtomaatoctory"])
    relations = mapper._extract_relations_from_repo(mapper.repositories["rzonedevops/avtomaatoctory"])
    
    print(f"✅ Found {len(entities)} entities and {len(relations)} relations")
    
    # Add to unified schema
    for entity in entities:
        mapper.unified_schema.add_node(entity)
    for relation in relations:
        mapper.unified_schema.add_edge(relation)
    
    # Analyze coverage
    analysis = mapper._analyze_coverage()
    
    print(f"📋 Analysis Results:")
    print(f"  - Total entities: {analysis.total_entities}")
    print(f"  - Total relations: {analysis.total_relations}")
    print(f"  - Completeness score: {analysis.completeness_score:.2%}")
    
    # Generate report
    report_path = mapper.generate_analysis_report(analysis, "/tmp/test_report.md")
    print(f"📄 Report generated: {report_path}")
    
    # Sample some entities
    if entities:
        print("\n📌 Sample entities found:")
        for entity in entities[:5]:
            print(f"  - {entity.name} ({entity.node_type.value})")
            
    if relations:
        print("\n🔗 Sample relations found:")
        for relation in relations[:5]:
            print(f"  - {relation.edge_type.value}")
    
    return True

if __name__ == "__main__":
    success = test_local_analysis()
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!")
        sys.exit(1)