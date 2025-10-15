#!/usr/bin/env python3
"""
AD Hypergraph Repository Mapping - Accessible Repositories Demo
==============================================================

Demo focusing on publicly accessible repositories to showcase the functionality.
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.tools.ad_hypergraph_repo_mapper import ADHypergraphRepoMapper, RepositoryInfo

def run_accessible_demo():
    """Run demo with accessible repositories only"""
    
    print("=" * 80)
    print("🌐 AD HYPERGRAPH MAPPING - ACCESSIBLE REPOSITORIES DEMO")
    print("=" * 80)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Create mapper
    workspace = "/tmp/ad_demo_accessible"
    mapper = ADHypergraphRepoMapper(workspace_dir=workspace)
    
    # Override with accessible repositories + current repo
    accessible_repos = [
        "https://github.com/cogpy/ad-res-j7",
        "https://github.com/EchoCog/analysss"
    ]
    
    # Clear and rebuild repository list
    mapper.repositories = {}
    mapper.target_repos = accessible_repos
    
    for repo_url in accessible_repos:
        owner, name = mapper._parse_repo_url(repo_url)
        repo_info = RepositoryInfo(url=repo_url, name=name, owner=owner)
        mapper.repositories[f"{owner}/{name}"] = repo_info
    
    # Add current repository as "local" source
    current_repo_info = RepositoryInfo(
        url="https://github.com/rzonedevops/avtomaatoctory",
        name="avtomaatoctory", 
        owner="rzonedevops"
    )
    current_repo_info.local_path = Path(__file__).parent
    current_repo_info.accessible = True
    mapper.repositories["rzonedevops/avtomaatoctory"] = current_repo_info
    
    print(f"🎯 Processing {len(mapper.repositories)} repositories:")
    for repo_key in mapper.repositories:
        print(f"   - {repo_key}")
    print()
    
    # Run mapping
    print("🔄 Starting repository mapping...")
    analysis = mapper.map_all_repositories()
    
    print("\n" + "=" * 60)
    print("📊 RESULTS")
    print("=" * 60)
    
    print(f"✅ Total Entities: {analysis.total_entities}")
    print(f"🔗 Total Relations: {analysis.total_relations}")
    print(f"📈 Completeness: {analysis.completeness_score:.2%}")
    print()
    
    # Repository breakdown
    for repo_key, repo_info in mapper.repositories.items():
        if repo_info.accessible:
            coverage = analysis.repository_coverage.get(repo_key, 0)
            print(f"📂 {repo_key}")
            print(f"   Coverage: {coverage:.1%}")
            print(f"   Entities: {repo_info.entity_count}")  
            print(f"   Relations: {repo_info.relation_count}")
            print()
    
    # Show sample entities
    print("📄 SAMPLE ENTITIES:")
    sample_entities = list(mapper.unified_schema.nodes.values())[:5]
    for i, entity in enumerate(sample_entities, 1):
        source_type = entity.metadata.get('source_type', 'unknown')
        print(f"   {i}. {entity.name} ({entity.node_type.value}) [{source_type}]")
        print(f"      ID: {entity.id}")
        print(f"      Source: {entity.metadata.get('source_repo', 'unknown')}")
    print()
    
    # Show sample relations
    if mapper.unified_schema.edges:
        print("🔗 SAMPLE RELATIONS:")
        sample_relations = list(mapper.unified_schema.edges.values())[:3]
        for i, relation in enumerate(sample_relations, 1):
            print(f"   {i}. {relation.edge_type.value}")
            print(f"      {relation.source_id} → {relation.target_ids}")
            print(f"      Source: {relation.metadata.get('source_repo', 'unknown')}")
        print()
    
    # Global entity types
    if analysis.global_entities:
        print("🏷️  ENTITY TYPES FOUND:")
        entity_types = sorted(analysis.global_entities)
        for entity_type in entity_types[:10]:  # Show first 10
            print(f"   • {entity_type}")
        if len(entity_types) > 10:
            print(f"   ... and {len(entity_types)-10} more")
        print()
    
    # Save outputs
    output_dir = Path(workspace)
    output_dir.mkdir(exist_ok=True)
    
    # Save unified hypergraph
    unified_path = output_dir / "unified_hypergraph.json"
    mapper.sync_hypergraph(str(unified_path))
    
    # Save analysis report
    report_path = output_dir / "analysis_report.md"
    mapper.generate_analysis_report(analysis, str(report_path))
    
    print(f"💾 Outputs saved to: {workspace}/")
    print(f"   - {unified_path.name}")
    print(f"   - {report_path.name}")
    print()
    
    print("=" * 80)
    print("✅ DEMO COMPLETE!")
    print("=" * 80)
    
    return analysis, mapper

if __name__ == "__main__":
    try:
        analysis, mapper = run_accessible_demo()
        print(f"🎉 Successfully mapped {analysis.total_entities} entities and {analysis.total_relations} relations!")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)