#!/usr/bin/env python3
"""
AD Hypergraph Repository Mapping Demo
====================================

Comprehensive demonstration of AD hypergraph mapping across multiple repositories.
This script will:
1. Clone/access all target repositories
2. Extract entities and relations from each
3. Build unified hypergraph
4. Generate analysis report
5. Identify missing nodes/attributes across repositories
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.tools.ad_hypergraph_repo_mapper import ADHypergraphRepoMapper

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'/tmp/ad_hypergraph_demo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )

def print_banner():
    """Print demo banner"""
    print("=" * 80)
    print("🌐 AD HYPERGRAPH REPOSITORY MAPPING DEMO")
    print("=" * 80)
    print("Mapping Analysis Domain hypergraph across target repositories:")
    print("- https://github.com/cogpy/ad-res-j7")
    print("- https://github.com/EchoCog/analysss") 
    print("- https://github.com/rzonedevops/analysis")
    print("- https://github.com/rzonedevops/avtomaatoctory")
    print("- https://github.com/rzonedevops/analyticase")
    print("=" * 80)
    print()

def run_comprehensive_demo():
    """Run comprehensive AD hypergraph mapping demo"""
    
    print_banner()
    setup_logging()
    
    # Create workspace
    workspace = "/tmp/ad_hypergraph_demo"
    print(f"📂 Using workspace: {workspace}")
    
    # Initialize mapper
    print("🚀 Initializing AD Hypergraph Repository Mapper...")
    mapper = ADHypergraphRepoMapper(workspace_dir=workspace)
    
    print(f"🎯 Target repositories: {len(mapper.target_repos)}")
    for repo_url in mapper.target_repos:
        print(f"   - {repo_url}")
    print()
    
    # Run mapping
    print("🔄 Starting repository mapping process...")
    analysis = mapper.map_all_repositories()
    
    # Display results
    print("\n" + "=" * 60)
    print("📊 MAPPING RESULTS SUMMARY")
    print("=" * 60)
    
    print(f"✅ Total Entities Found: {analysis.total_entities}")
    print(f"🔗 Total Relations Found: {analysis.total_relations}")
    print(f"📈 Overall Completeness: {analysis.completeness_score:.2%}")
    print(f"📋 Repositories Processed: {len(mapper.repositories)}")
    print()
    
    # Repository-specific results
    print("🏢 REPOSITORY BREAKDOWN")
    print("-" * 40)
    
    accessible_count = 0
    for repo_key, repo_info in mapper.repositories.items():
        status_icon = "✅" if repo_info.accessible else "❌"
        print(f"{status_icon} {repo_key}")
        
        if repo_info.accessible:
            accessible_count += 1
            coverage = analysis.repository_coverage.get(repo_key, 0)
            print(f"   📊 Coverage: {coverage:.1%}")
            print(f"   📄 Entities: {repo_info.entity_count}")
            print(f"   🔗 Relations: {repo_info.relation_count}")
            
            if repo_info.missing_entities:
                print(f"   ⚠️  Missing Entities: {len(repo_info.missing_entities)}")
                if len(repo_info.missing_entities) <= 5:
                    for entity in list(repo_info.missing_entities)[:5]:
                        print(f"      - {entity}")
                else:
                    print(f"      - {list(repo_info.missing_entities)[0]} (and {len(repo_info.missing_entities)-1} more)")
                        
            if repo_info.missing_relations:
                print(f"   ⚠️  Missing Relations: {len(repo_info.missing_relations)}")
                if len(repo_info.missing_relations) <= 3:
                    for relation in list(repo_info.missing_relations)[:3]:
                        print(f"      - {relation}")
        else:
            print(f"   ❌ Could not access repository")
            
        print()
    
    print(f"📈 Success Rate: {accessible_count}/{len(mapper.repositories)} repositories accessible")
    print()
    
    # Global entity and relation types
    if analysis.global_entities:
        print("🏷️  GLOBAL ENTITY TYPES DISCOVERED")
        print("-" * 40)
        entity_list = sorted(analysis.global_entities)
        for i, entity in enumerate(entity_list[:10]):  # Show first 10
            print(f"   {i+1:2d}. {entity}")
        if len(entity_list) > 10:
            print(f"   ... and {len(entity_list)-10} more")
        print()
    
    if analysis.global_relations:
        print("🔗 GLOBAL RELATION TYPES DISCOVERED")
        print("-" * 40)
        for relation in sorted(analysis.global_relations):
            print(f"   • {relation}")
        print()
    
    # Generate outputs
    print("💾 GENERATING OUTPUTS")
    print("-" * 40)
    
    # Sync unified hypergraph
    unified_path = f"{workspace}/unified_ad_hypergraph.json"
    mapper.sync_hypergraph(unified_path)
    print(f"📄 Unified hypergraph: {unified_path}")
    
    # Generate analysis report
    report_path = f"{workspace}/ad_hypergraph_analysis_report.md"
    mapper.generate_analysis_report(analysis, report_path)
    print(f"📋 Analysis report: {report_path}")
    
    # Generate summary JSON
    summary_path = f"{workspace}/analysis_summary.json"
    summary_data = {
        'timestamp': datetime.now().isoformat(),
        'total_entities': analysis.total_entities,
        'total_relations': analysis.total_relations,
        'completeness_score': analysis.completeness_score,
        'repositories_processed': len(mapper.repositories),
        'repositories_accessible': accessible_count,
        'repository_coverage': analysis.repository_coverage,
        'global_entities_count': len(analysis.global_entities),
        'global_relations_count': len(analysis.global_relations),
        'global_entities': list(analysis.global_entities),
        'global_relations': list(analysis.global_relations)
    }
    
    with open(summary_path, 'w') as f:
        json.dump(summary_data, f, indent=2)
    print(f"📊 Summary data: {summary_path}")
    print()
    
    # Recommendations
    print("🎯 RECOMMENDATIONS")
    print("-" * 40)
    
    if analysis.completeness_score < 0.5:
        print("🔴 LOW COMPLETENESS DETECTED")
        print("   • Consider standardizing entity/relation formats across repositories")
        print("   • Implement automated synchronization between repositories")
        print("   • Add missing entities and relations to incomplete repositories")
    elif analysis.completeness_score < 0.8:
        print("🟡 MODERATE COMPLETENESS")
        print("   • Focus on synchronizing missing elements across repositories")  
        print("   • Establish consistent naming conventions")
        print("   • Add automated validation workflows")
    else:
        print("🟢 HIGH COMPLETENESS")
        print("   • Maintain current synchronization processes")
        print("   • Consider implementing real-time updates")
        print("   • Add advanced analytics and monitoring")
        
    print("   • Ensure all repositories follow standard hypergraph structure")
    print("   • Add metadata standards for cross-repository linking")
    print("   • Implement change detection and notification systems")
    print()
    
    print("=" * 80)
    print("🎉 AD HYPERGRAPH MAPPING DEMO COMPLETE!")
    print("=" * 80)
    print(f"📊 Processed {analysis.total_entities} entities and {analysis.total_relations} relations")
    print(f"📈 Overall completeness: {analysis.completeness_score:.2%}")
    print(f"📂 All outputs saved to: {workspace}/")
    print()
    
    return analysis, mapper

def show_sample_data(mapper):
    """Show sample extracted data"""
    print("🔍 SAMPLE EXTRACTED DATA")
    print("-" * 40)
    
    # Show sample nodes
    sample_nodes = list(mapper.unified_schema.nodes.values())[:3]
    if sample_nodes:
        print("📄 Sample Entities:")
        for i, node in enumerate(sample_nodes, 1):
            print(f"   {i}. {node.name} ({node.node_type.value})")
            print(f"      ID: {node.id}")
            print(f"      Source: {node.metadata.get('source_repo', 'unknown')}")
            if node.properties:
                props = list(node.properties.keys())[:3]
                print(f"      Properties: {', '.join(props)}")
            print()
    
    # Show sample edges  
    sample_edges = list(mapper.unified_schema.edges.values())[:3]
    if sample_edges:
        print("🔗 Sample Relations:")
        for i, edge in enumerate(sample_edges, 1):
            print(f"   {i}. {edge.edge_type.value}")
            print(f"      From: {edge.source_id}")
            print(f"      To: {edge.target_ids}")
            print(f"      Source: {edge.metadata.get('source_repo', 'unknown')}")
            print()

def main():
    """Main demo function"""
    try:
        analysis, mapper = run_comprehensive_demo()
        
        # Show sample data if requested
        if len(sys.argv) > 1 and sys.argv[1] == "--show-samples":
            show_sample_data(mapper)
            
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logging.exception("Demo failed with exception")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)