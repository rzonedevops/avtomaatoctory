#!/usr/bin/env python3
"""
AD Hypergraph Repository Mapper
===============================

Maps the AD (Analysis Domain) hypergraph over all specified repositories:
- https://github.com/cogpy/ad-res-j7
- https://github.com/EchoCog/analysss
- https://github.com/rzonedevops/analysis
- https://github.com/rzonedevops/avtomaatoctory
- https://github.com/rzonedevops/analyticase

Capabilities:
1. Clone/access all repositories
2. Extract entities and relations from each repository
3. Sync to unified AD hypergraph
4. Analyze coverage and identify missing nodes/attributes
"""

import json
import logging
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

# Import hypergraph components
from ..api.hypergraphql_schema import (
    HyperGraphQLSchema,
    HyperGraphQLNode,
    HyperGraphQLEdge,
    EntityTypeQL,
    RelationTypeQL,
    OrgLevel
)
from ..api.hypergraphql_github import OrgAwareManager

logger = logging.getLogger(__name__)


@dataclass
class RepositoryInfo:
    """Information about a repository in the AD hypergraph mapping"""
    url: str
    name: str
    owner: str
    local_path: Optional[Path] = None
    accessible: bool = False
    entity_count: int = 0
    relation_count: int = 0
    coverage_score: float = 0.0
    missing_entities: Set[str] = field(default_factory=set)
    missing_relations: Set[str] = field(default_factory=set)
    last_analyzed: Optional[datetime] = None


@dataclass
class ADHypergraphAnalysis:
    """Analysis results for AD hypergraph coverage across repositories"""
    total_entities: int = 0
    total_relations: int = 0
    repository_coverage: Dict[str, float] = field(default_factory=dict)
    global_entities: Set[str] = field(default_factory=set)
    global_relations: Set[str] = field(default_factory=set)
    missing_by_repo: Dict[str, Dict[str, Set[str]]] = field(default_factory=dict)
    completeness_score: float = 0.0


class ADHypergraphRepoMapper:
    """
    Main class for mapping AD hypergraph across multiple repositories
    """
    
    def __init__(self, 
                 workspace_dir: str = "/tmp/ad_hypergraph_workspace",
                 github_token: Optional[str] = None):
        """
        Initialize AD hypergraph repository mapper
        
        Args:
            workspace_dir: Directory for cloning repositories
            github_token: GitHub token for accessing private repos
        """
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.github_token = github_token
        
        # Target repositories for AD hypergraph mapping
        self.target_repos = [
            "https://github.com/cogpy/ad-res-j7",
            "https://github.com/EchoCog/analysss", 
            "https://github.com/rzonedevops/analysis",
            "https://github.com/rzonedevops/avtomaatoctory",
            "https://github.com/rzonedevops/analyticase"
        ]
        
        self.repositories: Dict[str, RepositoryInfo] = {}
        self.unified_schema = HyperGraphQLSchema()
        self.org_manager = OrgAwareManager("AD_HYPERGRAPH", OrgLevel.ENTERPRISE)
        
        # Initialize repositories
        for repo_url in self.target_repos:
            owner, name = self._parse_repo_url(repo_url)
            repo_info = RepositoryInfo(
                url=repo_url,
                name=name,
                owner=owner
            )
            self.repositories[f"{owner}/{name}"] = repo_info

    def _parse_repo_url(self, repo_url: str) -> Tuple[str, str]:
        """Parse GitHub repository URL to extract owner and name"""
        parts = repo_url.rstrip('/').split('/')
        return parts[-2], parts[-1]

    def _clone_or_update_repo(self, repo_info: RepositoryInfo) -> bool:
        """
        Clone repository or update if already exists
        
        Returns:
            True if successful, False otherwise
        """
        repo_key = f"{repo_info.owner}/{repo_info.name}"
        local_path = self.workspace_dir / repo_info.owner / repo_info.name
        
        try:
            if local_path.exists():
                # Update existing repository
                logger.info(f"Updating repository {repo_key}")
                result = subprocess.run(
                    ["git", "pull"], 
                    cwd=local_path, 
                    capture_output=True, 
                    text=True
                )
                if result.returncode != 0:
                    logger.warning(f"Failed to update {repo_key}: {result.stderr}")
                    return False
            else:
                # Clone new repository
                logger.info(f"Cloning repository {repo_key}")
                local_path.parent.mkdir(parents=True, exist_ok=True)
                
                clone_url = repo_info.url
                if self.github_token:
                    # Use token for authentication
                    clone_url = repo_info.url.replace(
                        "https://github.com/", 
                        f"https://{self.github_token}@github.com/"
                    )
                
                result = subprocess.run(
                    ["git", "clone", clone_url, str(local_path)],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    logger.error(f"Failed to clone {repo_key}: {result.stderr}")
                    return False
            
            repo_info.local_path = local_path
            repo_info.accessible = True
            return True
            
        except Exception as e:
            logger.error(f"Error accessing repository {repo_key}: {e}")
            return False

    def _scan_repository_structure(self, repo_info: RepositoryInfo) -> None:
        """
        Scan repository for hypergraph entities and relations
        """
        if not repo_info.local_path or not repo_info.accessible:
            return
            
        repo_key = f"{repo_info.owner}/{repo_info.name}"
        
        # Look for standard hypergraph structure
        entities_path = repo_info.local_path / "entities"
        relations_path = repo_info.local_path / "relations"
        
        entity_count = 0
        relation_count = 0
        
        # Count entities
        if entities_path.exists():
            entity_count = len(list(entities_path.rglob("*.json")))
            
        # Count relations  
        if relations_path.exists():
            relation_count = len(list(relations_path.rglob("*.json")))
            
        # Also check for other potential entity/relation files
        for pattern in ["*.json", "*.md", "*.txt"]:
            for file_path in repo_info.local_path.rglob(pattern):
                # Skip hidden and git files
                if any(part.startswith('.') for part in file_path.parts):
                    continue
                    
                # Check for entity-like content
                if any(keyword in file_path.name.lower() 
                       for keyword in ["person", "organization", "event", "evidence", 
                                     "entity", "agent", "location", "document"]):
                    entity_count += 1
                    
                # Check for relation-like content
                if any(keyword in file_path.name.lower()
                       for keyword in ["relation", "owns", "controls", "participates", 
                                     "communicates", "transacts", "evidences"]):
                    relation_count += 1
        
        repo_info.entity_count = entity_count
        repo_info.relation_count = relation_count
        repo_info.last_analyzed = datetime.now()
        
        logger.info(f"Repository {repo_key}: {entity_count} entities, {relation_count} relations")

    def _extract_entities_from_repo(self, repo_info: RepositoryInfo) -> List[HyperGraphQLNode]:
        """
        Extract hypergraph entities from repository
        """
        entities = []
        
        if not repo_info.local_path or not repo_info.accessible:
            return entities
            
        repo_key = f"{repo_info.owner}/{repo_info.name}"
        
        # Standard entities folder
        entities_path = repo_info.local_path / "entities"
        if entities_path.exists():
            entities.extend(self._load_entities_from_folder(entities_path, repo_key))
            
        # Look for other entity files (JSON, markdown, etc.)
        for pattern in ["*.json", "*.md", "*.txt"]:
            for file_path in repo_info.local_path.rglob(pattern):
                if "entities" in file_path.name.lower() and file_path.parent != entities_path:
                    if file_path.suffix == ".json":
                        entities.extend(self._load_entities_from_file(file_path, repo_key))
                    elif file_path.suffix == ".md":
                        entities.extend(self._load_entities_from_markdown(file_path, repo_key))
                        
        return entities

    def _load_entities_from_folder(self, entities_path: Path, repo_key: str) -> List[HyperGraphQLNode]:
        """Load entities from standard entities folder structure"""
        entities = []
        
        # Handle both subdirectory structure and flat structure
        for item in entities_path.iterdir():
            if item.is_dir():
                # Subdirectory structure (entities/persons/, entities/organizations/)
                entity_type = self._determine_entity_type(item.name)
                
                for pattern in ["*.json", "*.md"]:
                    for entity_file in item.glob(pattern):
                        try:
                            if entity_file.suffix == ".json":
                                with open(entity_file, 'r') as f:
                                    data = json.load(f)
                                node = self._create_node_from_data_with_type(data, entity_type, repo_key, entity_file)
                            elif entity_file.suffix == ".md":
                                node = self._create_node_from_markdown_with_type(entity_file, entity_type, repo_key)
                            else:
                                continue
                            entities.append(node)
                        except Exception as e:
                            logger.error(f"Error loading entity from {entity_file}: {e}")
            else:
                # Flat structure (entities/person.json, entities/person_123.md)
                if item.suffix in [".json", ".md"]:
                    try:
                        entity_type = self._determine_entity_type(item.stem)
                        if item.suffix == ".json":
                            with open(item, 'r') as f:
                                data = json.load(f)
                            node = self._create_node_from_data_with_type(data, entity_type, repo_key, item)
                        elif item.suffix == ".md":
                            node = self._create_node_from_markdown_with_type(item, entity_type, repo_key)
                        else:
                            continue
                        entities.append(node)
                    except Exception as e:
                        logger.error(f"Error loading entity from {item}: {e}")
                    
        return entities

    def _determine_entity_type(self, name: str) -> EntityTypeQL:
        """Determine entity type from folder/file name"""
        name_lower = name.lower()
        
        # Map common terms to entity types
        type_mappings = {
            'person': EntityTypeQL.PERSON,
            'people': EntityTypeQL.PERSON,
            'persons': EntityTypeQL.PERSON,
            'organization': EntityTypeQL.ORGANIZATION,
            'organizations': EntityTypeQL.ORGANIZATION,
            'company': EntityTypeQL.ORGANIZATION,
            'companies': EntityTypeQL.ORGANIZATION,
            'event': EntityTypeQL.EVENT,
            'events': EntityTypeQL.EVENT,
            'evidence': EntityTypeQL.EVIDENCE,
            'location': EntityTypeQL.LOCATION,
            'locations': EntityTypeQL.LOCATION,
            'document': EntityTypeQL.DOCUMENT,
            'documents': EntityTypeQL.DOCUMENT,
            'transaction': EntityTypeQL.TRANSACTION,
            'transactions': EntityTypeQL.TRANSACTION,
            'agent': EntityTypeQL.AGENT,
            'agents': EntityTypeQL.AGENT,
        }
        
        # Check for exact matches first
        if name_lower in type_mappings:
            return type_mappings[name_lower]
            
        # Check for partial matches
        for key, entity_type in type_mappings.items():
            if key in name_lower:
                return entity_type
                
        return EntityTypeQL.AGENT  # Default

    def _load_entities_from_markdown(self, file_path: Path, repo_key: str) -> List[HyperGraphQLNode]:
        """Load entities from markdown files"""
        entities = []
        
        try:
            # Simple markdown entity extraction
            entity_type = self._determine_entity_type(file_path.stem)
            node = self._create_node_from_markdown_with_type(file_path, entity_type, repo_key)
            entities.append(node)
        except Exception as e:
            logger.error(f"Error loading entity from markdown {file_path}: {e}")
            
        return entities

    def _create_node_from_data_with_type(self, data: Dict, entity_type: EntityTypeQL, repo_key: str, file_path: Path) -> HyperGraphQLNode:
        """Create HyperGraphQLNode from data with specified type"""
        return HyperGraphQLNode(
            id=f"{repo_key}:{data.get('id', file_path.stem)}",
            node_type=entity_type,
            name=data.get('name', file_path.stem),
            properties=data.get('properties', {}),
            org_level=OrgLevel.ENTERPRISE,
            repo_path=str(file_path.parent),
            folder_path=str(file_path.name),
            metadata={
                **data.get('metadata', {}),
                'source_repo': repo_key,
                'source_file': str(file_path),
                'source_type': 'json'
            }
        )

    def _create_node_from_markdown_with_type(self, file_path: Path, entity_type: EntityTypeQL, repo_key: str) -> HyperGraphQLNode:
        """Create HyperGraphQLNode from markdown file with specified type"""
        # Read markdown content for properties
        properties = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                properties['content'] = content[:500]  # Store first 500 chars
                properties['file_size'] = len(content)
                
                # Extract title from first line if it's a heading
                lines = content.split('\n')
                if lines and lines[0].startswith('#'):
                    properties['title'] = lines[0].strip('#').strip()
                    
        except Exception as e:
            logger.warning(f"Could not read content from {file_path}: {e}")
            
        return HyperGraphQLNode(
            id=f"{repo_key}:{file_path.stem}",
            node_type=entity_type,
            name=properties.get('title', file_path.stem),
            properties=properties,
            org_level=OrgLevel.ENTERPRISE,
            repo_path=str(file_path.parent),
            folder_path=str(file_path.name),
            metadata={
                'source_repo': repo_key,
                'source_file': str(file_path),
                'source_type': 'markdown'
            }
        )

    def _load_entities_from_file(self, file_path: Path, repo_key: str) -> List[HyperGraphQLNode]:
        """Load entities from a single JSON file"""
        entities = []
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Handle different JSON structures
            if isinstance(data, list):
                # Array of entities
                for item in data:
                    if isinstance(item, dict) and 'id' in item:
                        entities.append(self._create_node_from_data(item, repo_key, file_path))
            elif isinstance(data, dict):
                if 'entities' in data:
                    # Object with entities array
                    for item in data['entities']:
                        entities.append(self._create_node_from_data(item, repo_key, file_path))
                elif 'id' in data:
                    # Single entity
                    entities.append(self._create_node_from_data(data, repo_key, file_path))
                    
        except Exception as e:
            logger.error(f"Error loading entities from {file_path}: {e}")
            
        return entities

    def _create_node_from_data(self, data: Dict, repo_key: str, file_path: Path) -> HyperGraphQLNode:
        """Create HyperGraphQLNode from data dictionary"""
        # Determine entity type from data or filename
        entity_type = EntityTypeQL.AGENT  # Default
        
        if 'type' in data:
            try:
                entity_type = EntityTypeQL[data['type'].upper()]
            except KeyError:
                pass
        
        return HyperGraphQLNode(
            id=f"{repo_key}:{data['id']}",
            node_type=entity_type,
            name=data.get('name', data['id']),
            properties=data.get('properties', {}),
            org_level=OrgLevel.ENTERPRISE,
            repo_path=str(file_path.parent),
            folder_path=str(file_path.name),
            metadata={
                **data.get('metadata', {}),
                'source_repo': repo_key,
                'source_file': str(file_path)
            }
        )

    def _extract_relations_from_repo(self, repo_info: RepositoryInfo) -> List[HyperGraphQLEdge]:
        """
        Extract hypergraph relations from repository
        """
        relations = []
        
        if not repo_info.local_path or not repo_info.accessible:
            return relations
            
        repo_key = f"{repo_info.owner}/{repo_info.name}"
        
        # Standard relations folder
        relations_path = repo_info.local_path / "relations"
        if relations_path.exists():
            relations.extend(self._load_relations_from_folder(relations_path, repo_key))
            
        # Look for relation files in various formats
        for pattern in ["*.json", "*.md"]:
            for file_path in repo_info.local_path.rglob(pattern):
                if "relations" in file_path.name.lower() and file_path.parent != relations_path:
                    if file_path.suffix == ".json":
                        relations.extend(self._load_relations_from_file(file_path, repo_key))
                        
        # Also extract implicit relations from entity connections
        relations.extend(self._extract_implicit_relations(repo_info, repo_key))
                
        return relations

    def _extract_implicit_relations(self, repo_info: RepositoryInfo, repo_key: str) -> List[HyperGraphQLEdge]:
        """Extract implicit relations from file patterns and content analysis"""
        relations = []
        
        try:
            # Look for timeline files that might contain relationships
            for pattern in ["*.json", "*timeline*.md", "*analysis*.json"]:
                for file_path in repo_info.local_path.rglob(pattern):
                    if any(keyword in file_path.name.lower() for keyword in 
                           ["timeline", "analysis", "connection", "relationship"]):
                        # Extract relations from content
                        if file_path.suffix == ".json":
                            try:
                                with open(file_path, 'r') as f:
                                    data = json.load(f)
                                # Look for relationship patterns in JSON
                                relations.extend(self._extract_relations_from_json_data(data, repo_key, file_path))
                            except Exception as e:
                                logger.debug(f"Could not parse {file_path} for relations: {e}")
                                
        except Exception as e:
            logger.debug(f"Error extracting implicit relations from {repo_key}: {e}")
            
        return relations

    def _extract_relations_from_json_data(self, data: Any, repo_key: str, file_path: Path) -> List[HyperGraphQLEdge]:
        """Extract relations from JSON data structure"""
        relations = []
        
        try:
            if isinstance(data, dict):
                # Look for explicit relations arrays
                if 'relations' in data and isinstance(data['relations'], list):
                    for rel_data in data['relations']:
                        if isinstance(rel_data, dict) and 'source' in rel_data:
                            relation = self._create_edge_from_data(rel_data, repo_key, file_path)
                            relations.append(relation)
                            
                # Look for connection patterns
                for key, value in data.items():
                    if key in ['connects', 'links', 'references', 'related_to'] and isinstance(value, list):
                        for target in value:
                            relation = HyperGraphQLEdge(
                                id=f"{repo_key}:{file_path.stem}_{key}_{len(relations)}",
                                edge_type=RelationTypeQL.RELATED_TO,
                                source_id=f"{repo_key}:{file_path.stem}",
                                target_ids=[f"{repo_key}:{target}"],
                                strength=0.5,
                                properties={'extracted_from': key},
                                org_level=OrgLevel.ENTERPRISE,
                                metadata={
                                    'source_repo': repo_key,
                                    'source_file': str(file_path),
                                    'extraction_method': 'implicit'
                                }
                            )
                            relations.append(relation)
                            
        except Exception as e:
            logger.debug(f"Error extracting relations from JSON data in {file_path}: {e}")
            
        return relations

    def _load_relations_from_folder(self, relations_path: Path, repo_key: str) -> List[HyperGraphQLEdge]:
        """Load relations from standard relations folder structure"""
        relations = []
        
        for relation_type_folder in relations_path.iterdir():
            if not relation_type_folder.is_dir():
                continue
                
            # Determine relation type
            try:
                relation_type = RelationTypeQL[relation_type_folder.name.upper()]
            except KeyError:
                relation_type = RelationTypeQL.RELATED_TO  # Default
                
            for relation_file in relation_type_folder.glob("*.json"):
                try:
                    with open(relation_file, 'r') as f:
                        data = json.load(f)
                        
                    edge = HyperGraphQLEdge(
                        id=f"{repo_key}:{data.get('id', relation_file.stem)}",
                        edge_type=relation_type,
                        source_id=f"{repo_key}:{data['source']}",
                        target_ids=[f"{repo_key}:{t}" for t in data.get('targets', [])],
                        strength=data.get('strength', 0.5),
                        properties=data.get('properties', {}),
                        org_level=OrgLevel.ENTERPRISE,
                        evidence_refs=data.get('evidence_refs', []),
                        timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else None,
                        metadata={
                            **data.get('metadata', {}),
                            'source_repo': repo_key,
                            'source_file': str(relation_file)
                        }
                    )
                    relations.append(edge)
                    
                except Exception as e:
                    logger.error(f"Error loading relation from {relation_file}: {e}")
                    
        return relations

    def _load_relations_from_file(self, file_path: Path, repo_key: str) -> List[HyperGraphQLEdge]:
        """Load relations from a single JSON file"""
        relations = []
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Handle different JSON structures
            if isinstance(data, list):
                # Array of relations
                for item in data:
                    if isinstance(item, dict) and 'source' in item:
                        relations.append(self._create_edge_from_data(item, repo_key, file_path))
            elif isinstance(data, dict):
                if 'relations' in data:
                    # Object with relations array
                    for item in data['relations']:
                        relations.append(self._create_edge_from_data(item, repo_key, file_path))
                elif 'source' in data:
                    # Single relation
                    relations.append(self._create_edge_from_data(data, repo_key, file_path))
                    
        except Exception as e:
            logger.error(f"Error loading relations from {file_path}: {e}")
            
        return relations

    def _create_edge_from_data(self, data: Dict, repo_key: str, file_path: Path) -> HyperGraphQLEdge:
        """Create HyperGraphQLEdge from data dictionary"""
        # Determine relation type from data
        relation_type = RelationTypeQL.RELATED_TO  # Default
        
        if 'type' in data:
            try:
                relation_type = RelationTypeQL[data['type'].upper()]
            except KeyError:
                pass
        
        return HyperGraphQLEdge(
            id=f"{repo_key}:{data.get('id', f'{data["source"]}_rel')}",
            edge_type=relation_type,
            source_id=f"{repo_key}:{data['source']}",
            target_ids=[f"{repo_key}:{t}" for t in data.get('targets', data.get('target', []))],
            strength=data.get('strength', 0.5),
            properties=data.get('properties', {}),
            org_level=OrgLevel.ENTERPRISE,
            evidence_refs=data.get('evidence_refs', []),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else None,
            metadata={
                **data.get('metadata', {}),
                'source_repo': repo_key,
                'source_file': str(file_path)
            }
        )

    def map_all_repositories(self) -> ADHypergraphAnalysis:
        """
        Main method to map AD hypergraph across all repositories
        
        Returns:
            Analysis results with coverage and missing elements
        """
        logger.info("Starting AD hypergraph repository mapping...")
        
        # Step 1: Clone/access all repositories
        for repo_key, repo_info in self.repositories.items():
            logger.info(f"Processing repository: {repo_key}")
            
            success = self._clone_or_update_repo(repo_info)
            if not success:
                logger.warning(f"Could not access repository {repo_key}")
                continue
                
            # Scan repository structure
            self._scan_repository_structure(repo_info)
            
            # Register with org manager
            if repo_info.local_path:
                self.org_manager.register_repo(repo_key, str(repo_info.local_path))
        
        # Step 2: Extract and merge all entities and relations
        all_entities = []
        all_relations = []
        
        for repo_key, repo_info in self.repositories.items():
            if not repo_info.accessible:
                continue
                
            entities = self._extract_entities_from_repo(repo_info)
            relations = self._extract_relations_from_repo(repo_info)
            
            all_entities.extend(entities)
            all_relations.extend(relations)
            
            logger.info(f"Extracted {len(entities)} entities and {len(relations)} relations from {repo_key}")
        
        # Step 3: Build unified schema
        for entity in all_entities:
            self.unified_schema.add_node(entity)
            
        for relation in all_relations:
            self.unified_schema.add_edge(relation)
        
        # Step 4: Analyze coverage and gaps
        analysis = self._analyze_coverage()
        
        logger.info(f"AD hypergraph mapping complete. "
                   f"Total: {analysis.total_entities} entities, {analysis.total_relations} relations")
        
        return analysis

    def _analyze_coverage(self) -> ADHypergraphAnalysis:
        """
        Analyze hypergraph coverage across repositories
        """
        analysis = ADHypergraphAnalysis()
        
        # Collect all entities and relations globally
        global_entities = set()
        global_relations = set()
        
        for node in self.unified_schema.nodes.values():
            # Extract base entity ID (without repo prefix)
            base_id = node.id.split(':', 1)[1] if ':' in node.id else node.id
            global_entities.add(base_id)
            
        for edge in self.unified_schema.edges.values():
            # Extract base relation type
            global_relations.add(edge.edge_type.value)
        
        analysis.global_entities = global_entities
        analysis.global_relations = global_relations
        analysis.total_entities = len(self.unified_schema.nodes)
        analysis.total_relations = len(self.unified_schema.edges)
        
        # Analyze per-repository coverage
        for repo_key, repo_info in self.repositories.items():
            if not repo_info.accessible:
                analysis.repository_coverage[repo_key] = 0.0
                continue
                
            # Find entities and relations for this repo
            repo_entities = set()
            repo_relations = set()
            
            for node in self.unified_schema.nodes.values():
                if node.metadata.get('source_repo') == repo_key:
                    base_id = node.id.split(':', 1)[1] if ':' in node.id else node.id
                    repo_entities.add(base_id)
                    
            for edge in self.unified_schema.edges.values():
                if edge.metadata.get('source_repo') == repo_key:
                    repo_relations.add(edge.edge_type.value)
            
            # Calculate coverage scores
            entity_coverage = len(repo_entities) / len(global_entities) if global_entities else 0
            relation_coverage = len(repo_relations) / len(global_relations) if global_relations else 0
            
            overall_coverage = (entity_coverage + relation_coverage) / 2
            analysis.repository_coverage[repo_key] = overall_coverage
            
            # Find missing elements
            missing_entities = global_entities - repo_entities  
            missing_relations = global_relations - repo_relations
            
            analysis.missing_by_repo[repo_key] = {
                'entities': missing_entities,
                'relations': missing_relations
            }
            
            repo_info.missing_entities = missing_entities
            repo_info.missing_relations = missing_relations
            repo_info.coverage_score = overall_coverage
        
        # Calculate overall completeness
        if analysis.repository_coverage:
            analysis.completeness_score = sum(analysis.repository_coverage.values()) / len(analysis.repository_coverage)
        
        return analysis

    def sync_hypergraph(self, output_path: str = None) -> None:
        """
        Sync unified hypergraph to output location
        """
        if output_path is None:
            output_path = str(self.workspace_dir / "unified_ad_hypergraph.json")
            
        # Export unified schema
        unified_data = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'total_entities': len(self.unified_schema.nodes),
                'total_relations': len(self.unified_schema.edges),
                'source_repositories': list(self.repositories.keys())
            },
            'nodes': {node_id: node.to_graphql_type() for node_id, node in self.unified_schema.nodes.items()},
            'edges': {edge_id: edge.to_graphql_type() for edge_id, edge in self.unified_schema.edges.items()}
        }
        
        with open(output_path, 'w') as f:
            json.dump(unified_data, f, indent=2)
            
        logger.info(f"Unified AD hypergraph saved to: {output_path}")

    def generate_analysis_report(self, analysis: ADHypergraphAnalysis, output_path: str = None) -> str:
        """
        Generate comprehensive analysis report
        """
        if output_path is None:
            output_path = str(self.workspace_dir / "ad_hypergraph_analysis_report.md")
            
        report_lines = [
            "# AD Hypergraph Repository Mapping Analysis Report",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Executive Summary",
            f"- **Total Entities**: {analysis.total_entities}",
            f"- **Total Relations**: {analysis.total_relations}",
            f"- **Overall Completeness**: {analysis.completeness_score:.2%}",
            f"- **Repositories Analyzed**: {len(self.repositories)}",
            "",
            "## Repository Coverage Analysis",
            ""
        ]
        
        for repo_key, coverage in analysis.repository_coverage.items():
            repo_info = self.repositories[repo_key]
            status = "✅ Accessible" if repo_info.accessible else "❌ Inaccessible"
            
            report_lines.extend([
                f"### {repo_key} - {status}",
                f"- **Coverage Score**: {coverage:.2%}",
                f"- **Local Entities**: {repo_info.entity_count}",
                f"- **Local Relations**: {repo_info.relation_count}",
                f"- **Missing Entities**: {len(repo_info.missing_entities)}",
                f"- **Missing Relations**: {len(repo_info.missing_relations)}",
                ""
            ])
            
            if repo_info.missing_entities:
                report_lines.append("**Missing Entities:**")
                for entity in sorted(repo_info.missing_entities):
                    report_lines.append(f"  - {entity}")
                report_lines.append("")
                
            if repo_info.missing_relations:
                report_lines.append("**Missing Relations:**")
                for relation in sorted(repo_info.missing_relations):
                    report_lines.append(f"  - {relation}")
                report_lines.append("")
        
        report_lines.extend([
            "## Global Entity Types",
            ""
        ])
        
        for entity in sorted(analysis.global_entities):
            report_lines.append(f"- {entity}")
            
        report_lines.extend([
            "",
            "## Global Relation Types", 
            ""
        ])
        
        for relation in sorted(analysis.global_relations):
            report_lines.append(f"- {relation}")
        
        report_lines.extend([
            "",
            "## Recommendations",
            "",
            "### High Priority",
            "- Ensure all repositories follow standard hypergraph structure (`entities/` and `relations/` folders)",
            "- Synchronize missing entities and relations across repositories",
            "- Implement automated hypergraph validation",
            "",
            "### Medium Priority", 
            "- Establish consistent entity and relation naming conventions",
            "- Add metadata standards for cross-repository linking",
            "- Implement automated synchronization workflows",
            "",
            "### Low Priority",
            "- Consider repository-specific entity namespacing",
            "- Add hypergraph visualization tools",
            "- Implement change detection and notification systems"
        ])
        
        report_content = "\n".join(report_lines)
        
        with open(output_path, 'w') as f:
            f.write(report_content)
            
        logger.info(f"Analysis report saved to: {output_path}")
        return output_path


def main():
    """Main CLI interface for AD hypergraph repository mapping"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Map AD hypergraph over multiple repositories')
    parser.add_argument('--workspace', '-w', 
                       default='/tmp/ad_hypergraph_workspace',
                       help='Workspace directory for repository clones')
    parser.add_argument('--token', '-t',
                       help='GitHub token for accessing private repositories')
    parser.add_argument('--output', '-o',
                       help='Output path for unified hypergraph')
    parser.add_argument('--report', '-r',
                       help='Output path for analysis report')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create mapper and run analysis
    mapper = ADHypergraphRepoMapper(
        workspace_dir=args.workspace,
        github_token=args.token
    )
    
    # Map all repositories
    analysis = mapper.map_all_repositories()
    
    # Sync unified hypergraph
    mapper.sync_hypergraph(args.output)
    
    # Generate report
    report_path = mapper.generate_analysis_report(analysis, args.report)
    
    print(f"\n🎯 AD Hypergraph Mapping Complete!")
    print(f"📊 Total Entities: {analysis.total_entities}")
    print(f"🔗 Total Relations: {analysis.total_relations}")
    print(f"📈 Completeness: {analysis.completeness_score:.2%}")
    print(f"📋 Report: {report_path}")
    
    if args.output:
        print(f"💾 Unified Hypergraph: {args.output}")


if __name__ == "__main__":
    main()