"""Autonomous Knowledge Adapter for AI Mega Agents Atlas

This module provides the core autonomous knowledge adapter that enables all 49 agents
to automatically train, learn, and adapt from engineering and developer resources.
Designed for plug-and-play enterprise deployment with minimal-modular architecture.
"""

import asyncio
import hashlib
import json
import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
from urllib.parse import urljoin, urlparse
import uuid

try:
    import httpx
    import aiofiles
    ASYNC_HTTP_AVAILABLE = True
except ImportError:
    ASYNC_HTTP_AVAILABLE = False
    import urllib.request
    import urllib.error
    # Create dummy httpx for type hints
    class httpx:
        class AsyncClient:
            pass


class KnowledgeSourceType(Enum):
    """Types of knowledge sources"""
    GITHUB_REPO = "github_repo"
    DOCUMENTATION = "documentation" 
    TUTORIAL = "tutorial"
    BEST_PRACTICES = "best_practices"
    CODE_EXAMPLES = "code_examples"
    TECH_TRENDS = "tech_trends"


class LearningStatus(Enum):
    """Learning operation status"""
    IDLE = "idle"
    CRAWLING = "crawling"
    PROCESSING = "processing"
    LEARNING = "learning"
    ADAPTING = "adapting"
    ERROR = "error"


@dataclass
class KnowledgeSource:
    """Represents a knowledge source for learning"""
    id: str
    name: str
    url: str
    source_type: KnowledgeSourceType
    domain_tags: Set[str] = field(default_factory=set)
    priority: int = 1
    last_updated: Optional[datetime] = None
    crawl_frequency: timedelta = field(default_factory=lambda: timedelta(hours=24))
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeItem:
    """Individual piece of knowledge extracted from sources"""
    id: str 
    source_id: str
    title: str
    content: str
    content_type: str  # code, documentation, tutorial, etc.
    domain_tags: Set[str] = field(default_factory=set)
    difficulty_level: int = 1  # 1-5 scale
    relevance_score: float = 0.0
    extracted_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningMetrics:
    """Metrics for knowledge adapter performance"""
    total_sources: int = 0
    active_sources: int = 0
    knowledge_items_learned: int = 0
    successful_adaptations: int = 0
    profit_improvements: float = 0.0
    last_learning_session: Optional[datetime] = None
    learning_efficiency: float = 0.0
    adaptation_success_rate: float = 0.0


class KnowledgeExtractor(ABC):
    """Abstract base class for knowledge extractors"""
    
    @abstractmethod
    async def extract(self, source: KnowledgeSource) -> List[KnowledgeItem]:
        """Extract knowledge items from a source"""
        pass
    
    @abstractmethod
    def can_handle(self, source: KnowledgeSource) -> bool:
        """Check if this extractor can handle the source"""
        pass


class GitHubKnowledgeExtractor(KnowledgeExtractor):
    """Extractor for GitHub repositories"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.GitHubExtractor")
        
    async def extract(self, source: KnowledgeSource) -> List[KnowledgeItem]:
        """Extract knowledge from GitHub repository"""
        items = []
        
        try:
            if not ASYNC_HTTP_AVAILABLE:
                return await self._extract_fallback(source)
                
            async with httpx.AsyncClient() as client:
                # Extract repository structure and content
                repo_info = await self._get_repo_info(client, source.url)
                if not repo_info:
                    return items
                
                # Get README and documentation
                readme_content = await self._get_readme(client, repo_info)
                if readme_content:
                    items.append(self._create_knowledge_item(
                        source, "README", readme_content, "documentation"
                    ))
                
                # Get code examples and tutorials
                code_items = await self._extract_code_examples(client, repo_info)
                items.extend(code_items)
                
                # Get project structure insights
                structure_items = await self._extract_project_structure(client, repo_info)
                items.extend(structure_items)
                
        except Exception as e:
            self.logger.error(f"Error extracting from {source.url}: {e}")
            
        return items
    
    def can_handle(self, source: KnowledgeSource) -> bool:
        """Check if this is a GitHub source"""
        return "github.com" in source.url.lower()
    
    async def _extract_fallback(self, source: KnowledgeSource) -> List[KnowledgeItem]:
        """Fallback extraction without async HTTP"""
        items = []
        try:
            # Simple URL-based extraction
            content = self._fetch_url_content(source.url)
            if content:
                items.append(self._create_knowledge_item(
                    source, "Content", content[:1000], "documentation"
                ))
        except Exception as e:
            self.logger.error(f"Fallback extraction failed for {source.url}: {e}")
        return items
    
    def _fetch_url_content(self, url: str) -> str:
        """Fetch content using urllib (fallback)"""
        try:
            with urllib.request.urlopen(url) as response:
                return response.read().decode('utf-8')
        except Exception:
            return ""
    
    async def _get_repo_info(self, client: httpx.AsyncClient, url: str) -> Optional[Dict]:
        """Get repository information"""
        try:
            # Extract owner/repo from URL
            parts = url.replace("https://github.com/", "").split("/")
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
                api_url = f"https://api.github.com/repos/{owner}/{repo}"
                response = await client.get(api_url)
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            self.logger.error(f"Error getting repo info: {e}")
        return None
    
    async def _get_readme(self, client: httpx.AsyncClient, repo_info: Dict) -> Optional[str]:
        """Get README content"""
        try:
            readme_url = f"{repo_info['url']}/readme"
            response = await client.get(readme_url)
            if response.status_code == 200:
                readme_data = response.json()
                import base64
                return base64.b64decode(readme_data['content']).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Error getting README: {e}")
        return None
    
    async def _extract_code_examples(self, client: httpx.AsyncClient, repo_info: Dict) -> List[KnowledgeItem]:
        """Extract code examples from repository"""
        items = []
        try:
            # Get repository contents
            contents_url = f"{repo_info['url']}/contents"
            response = await client.get(contents_url)
            if response.status_code == 200:
                contents = response.json()
                for item in contents[:10]:  # Limit to avoid rate limits
                    if item['type'] == 'file' and item['name'].endswith(('.py', '.js', '.md')):
                        file_content = await self._get_file_content(client, item['download_url'])
                        if file_content:
                            items.append(self._create_knowledge_item(
                                KnowledgeSource(id="", name="", url=repo_info['html_url'], 
                                              source_type=KnowledgeSourceType.GITHUB_REPO),
                                item['name'], file_content[:2000], "code_examples"
                            ))
        except Exception as e:
            self.logger.error(f"Error extracting code examples: {e}")
        return items
    
    async def _get_file_content(self, client: httpx.AsyncClient, url: str) -> Optional[str]:
        """Get file content from URL"""
        try:
            response = await client.get(url)
            if response.status_code == 200:
                return response.text
        except Exception:
            pass
        return None
    
    async def _extract_project_structure(self, client: httpx.AsyncClient, repo_info: Dict) -> List[KnowledgeItem]:
        """Extract project structure insights"""
        items = []
        try:
            # Create structure knowledge item
            structure_info = {
                "language": repo_info.get('language', 'Unknown'),
                "size": repo_info.get('size', 0),
                "topics": repo_info.get('topics', []),
                "description": repo_info.get('description', ''),
                "stargazers_count": repo_info.get('stargazers_count', 0)
            }
            
            items.append(self._create_knowledge_item(
                KnowledgeSource(id="", name="", url=repo_info['html_url'], 
                              source_type=KnowledgeSourceType.GITHUB_REPO),
                "Project Structure", json.dumps(structure_info), "best_practices"
            ))
        except Exception as e:
            self.logger.error(f"Error extracting project structure: {e}")
        return items
    
    def _create_knowledge_item(self, source: KnowledgeSource, title: str, 
                             content: str, content_type: str) -> KnowledgeItem:
        """Create a knowledge item"""
        item_id = hashlib.md5(f"{source.url}_{title}_{content[:100]}".encode()).hexdigest()
        return KnowledgeItem(
            id=item_id,
            source_id=source.id,
            title=title,
            content=content,
            content_type=content_type,
            domain_tags=source.domain_tags.copy(),
            relevance_score=0.5,  # Default relevance
            metadata={"source_url": source.url}
        )


class AutonomousKnowledgeAdapter:
    """Core autonomous knowledge adapter for AI agents"""
    
    def __init__(self, agent_domain: str = "general"):
        """Initialize the knowledge adapter
        
        Args:
            agent_domain: Domain specialization for the agent (analytics, content, etc.)
        """
        self.agent_domain = agent_domain
        self.logger = logging.getLogger(f"{__name__}.{agent_domain}")
        
        # Internal state
        self._sources: Dict[str, KnowledgeSource] = {}
        self._knowledge_base: Dict[str, KnowledgeItem] = {}
        self._extractors: List[KnowledgeExtractor] = []
        self._metrics = LearningMetrics()
        self._status = LearningStatus.IDLE
        self._learning_task: Optional[asyncio.Task] = None
        
        # Configuration
        self._max_knowledge_items = 1000
        self._learning_frequency = timedelta(hours=6)
        self._profit_optimization_enabled = True
        
        # Initialize extractors
        self._initialize_extractors()
        
        # Add default knowledge sources
        self._add_default_sources()
    
    def _initialize_extractors(self):
        """Initialize knowledge extractors"""
        self._extractors = [
            GitHubKnowledgeExtractor(),
        ]
    
    def _add_default_sources(self):
        """Add default knowledge sources including build-your-own-x"""
        default_sources = [
            KnowledgeSource(
                id="build-your-own-x",
                name="Build Your Own X",
                url="https://github.com/codecrafters-io/build-your-own-x",
                source_type=KnowledgeSourceType.GITHUB_REPO,
                domain_tags={"engineering", "tutorials", "implementation"},
                priority=10,
                crawl_frequency=timedelta(hours=12)
            ),
            KnowledgeSource(
                id="awesome-lists",
                name="Awesome Lists",
                url="https://github.com/sindresorhus/awesome",
                source_type=KnowledgeSourceType.GITHUB_REPO,
                domain_tags={"resources", "curated", "best_practices"},
                priority=8,
                crawl_frequency=timedelta(days=1)
            ),
            KnowledgeSource(
                id="free-programming-books",
                name="Free Programming Books",
                url="https://github.com/EbookFoundation/free-programming-books",
                source_type=KnowledgeSourceType.GITHUB_REPO,
                domain_tags={"learning", "books", "programming"},
                priority=7,
                crawl_frequency=timedelta(days=2)
            )
        ]
        
        # Add domain-specific sources based on agent domain
        domain_sources = self._get_domain_specific_sources()
        default_sources.extend(domain_sources)
        
        # Actually store the sources
        for source in default_sources:
            self._sources[source.id] = source
            
        # Update metrics immediately
        self._metrics.total_sources = len(self._sources)
        self._metrics.active_sources = sum(1 for s in self._sources.values() if s.is_active)
    
    def _get_domain_specific_sources(self) -> List[KnowledgeSource]:
        """Get domain-specific knowledge sources"""
        sources = []
        
        domain_mappings = {
            "analytics": [
                ("data-science-resources", "https://github.com/academic/awesome-datascience", 
                 {"data_science", "analytics", "machine_learning"}),
                ("python-data-analysis", "https://github.com/wesm/pydata-book",
                 {"python", "data_analysis", "pandas"})
            ],
            "content": [
                ("content-marketing", "https://github.com/marketingtechguru/awesome-marketing",
                 {"marketing", "content", "seo"}),
                ("writing-tools", "https://github.com/writing-resources/awesome-writing",
                 {"writing", "content_creation", "copywriting"})
            ],
            "cybersecurity": [
                ("security-resources", "https://github.com/sbilly/awesome-security",
                 {"security", "cybersecurity", "penetration_testing"}),
                ("hacking-tools", "https://github.com/vitalysim/Awesome-Hacking-Resources",
                 {"hacking", "tools", "security_assessment"})
            ],
            "financial": [
                ("fintech-resources", "https://github.com/moov-io/awesome-fintech",
                 {"fintech", "financial", "trading"}),
                ("crypto-resources", "https://github.com/sobolevn/awesome-cryptography",
                 {"cryptocurrency", "blockchain", "cryptography"})
            ]
        }
        
        if self.agent_domain in domain_mappings:
            for source_id, url, tags in domain_mappings[self.agent_domain]:
                sources.append(KnowledgeSource(
                    id=f"{self.agent_domain}_{source_id}",
                    name=source_id.replace("-", " ").title(),
                    url=url,
                    source_type=KnowledgeSourceType.GITHUB_REPO,
                    domain_tags=set(tags),
                    priority=9,
                    crawl_frequency=timedelta(hours=18)
                ))
        
        return sources
    
    async def start_autonomous_learning(self) -> bool:
        """Start autonomous learning process"""
        try:
            if self._learning_task and not self._learning_task.done():
                return True  # Already running
            
            self.logger.info(f"Starting autonomous learning for {self.agent_domain} domain")
            self._learning_task = asyncio.create_task(self._learning_loop())
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start autonomous learning: {e}")
            return False
    
    async def stop_autonomous_learning(self):
        """Stop autonomous learning process"""
        if self._learning_task and not self._learning_task.done():
            self._learning_task.cancel()
            try:
                await self._learning_task
            except asyncio.CancelledError:
                pass
        
        self._status = LearningStatus.IDLE
        self.logger.info(f"Stopped autonomous learning for {self.agent_domain} domain")
    
    async def _learning_loop(self):
        """Main autonomous learning loop"""
        while True:
            try:
                # Perform learning cycle
                await self._perform_learning_cycle()
                
                # Wait for next learning cycle
                await asyncio.sleep(self._learning_frequency.total_seconds())
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in learning loop: {e}")
                self._status = LearningStatus.ERROR
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    async def _perform_learning_cycle(self):
        """Perform a complete learning cycle"""
        self.logger.info(f"Starting learning cycle for {self.agent_domain}")
        
        try:
            # Phase 1: Crawl knowledge sources
            self._status = LearningStatus.CRAWLING
            new_knowledge = await self._crawl_knowledge_sources()
            
            # Phase 2: Process and filter knowledge
            self._status = LearningStatus.PROCESSING
            processed_knowledge = await self._process_knowledge(new_knowledge)
            
            # Phase 3: Learn and integrate knowledge
            self._status = LearningStatus.LEARNING
            await self._integrate_knowledge(processed_knowledge)
            
            # Phase 4: Adapt and optimize
            self._status = LearningStatus.ADAPTING
            await self._optimize_for_profit()
            
            # Update metrics
            self._update_learning_metrics()
            
            self._status = LearningStatus.IDLE
            self.logger.info(f"Learning cycle completed for {self.agent_domain}")
            
        except Exception as e:
            self.logger.error(f"Error in learning cycle: {e}")
            self._status = LearningStatus.ERROR
    
    async def _crawl_knowledge_sources(self) -> List[KnowledgeItem]:
        """Crawl all active knowledge sources"""
        new_knowledge = []
        
        for source in self._sources.values():
            if not source.is_active:
                continue
                
            # Check if source needs updating
            if (source.last_updated and 
                datetime.utcnow() - source.last_updated < source.crawl_frequency):
                continue
            
            # Find appropriate extractor
            extractor = next((e for e in self._extractors if e.can_handle(source)), None)
            if not extractor:
                continue
            
            try:
                self.logger.info(f"Crawling knowledge source: {source.name}")
                items = await extractor.extract(source)
                new_knowledge.extend(items)
                source.last_updated = datetime.utcnow()
                
            except Exception as e:
                self.logger.error(f"Error crawling {source.name}: {e}")
        
        self.logger.info(f"Crawled {len(new_knowledge)} knowledge items")
        return new_knowledge
    
    async def _process_knowledge(self, knowledge_items: List[KnowledgeItem]) -> List[KnowledgeItem]:
        """Process and filter knowledge items"""
        processed = []
        
        for item in knowledge_items:
            # Calculate relevance score
            relevance = self._calculate_relevance(item)
            item.relevance_score = relevance
            
            # Filter by relevance threshold
            if relevance >= 0.3:  # Only keep relevant items
                processed.append(item)
        
        # Sort by relevance and limit
        processed.sort(key=lambda x: x.relevance_score, reverse=True)
        processed = processed[:100]  # Limit per cycle
        
        self.logger.info(f"Processed {len(processed)} relevant knowledge items")
        return processed
    
    def _calculate_relevance(self, item: KnowledgeItem) -> float:
        """Calculate relevance score for knowledge item"""
        score = 0.0
        
        # Domain tag matching
        agent_domain_tags = {self.agent_domain, "general", "business", "profit"}
        matching_tags = item.domain_tags.intersection(agent_domain_tags)
        score += len(matching_tags) * 0.3
        
        # Content type weighting
        content_weights = {
            "code_examples": 0.8,
            "best_practices": 0.9,
            "tutorial": 0.7,
            "documentation": 0.6
        }
        score += content_weights.get(item.content_type, 0.5)
        
        # Content quality indicators
        if len(item.content) > 500:  # Substantial content
            score += 0.2
        if any(keyword in item.content.lower() for keyword in 
               ["implementation", "example", "best practice", "tutorial"]):
            score += 0.3
        
        return min(score, 1.0)
    
    async def _integrate_knowledge(self, knowledge_items: List[KnowledgeItem]):
        """Integrate new knowledge into the knowledge base"""
        integrated = 0
        
        for item in knowledge_items:
            if item.id not in self._knowledge_base:
                self._knowledge_base[item.id] = item
                integrated += 1
        
        # Maintain knowledge base size
        if len(self._knowledge_base) > self._max_knowledge_items:
            # Remove lowest relevance items
            sorted_items = sorted(self._knowledge_base.values(), 
                                key=lambda x: x.relevance_score)
            items_to_remove = len(self._knowledge_base) - self._max_knowledge_items
            for item in sorted_items[:items_to_remove]:
                del self._knowledge_base[item.id]
        
        self.logger.info(f"Integrated {integrated} new knowledge items")
    
    async def _optimize_for_profit(self):
        """Optimize agent capabilities for profit based on learned knowledge"""
        if not self._profit_optimization_enabled:
            return
        
        # Analyze knowledge for profit opportunities
        profit_insights = self._analyze_profit_opportunities()
        
        # Apply optimizations (placeholder for agent-specific implementation)
        optimizations_applied = 0
        for insight in profit_insights:
            if await self._apply_profit_optimization(insight):
                optimizations_applied += 1
        
        self.logger.info(f"Applied {optimizations_applied} profit optimizations")
    
    def _analyze_profit_opportunities(self) -> List[Dict[str, Any]]:
        """Analyze knowledge base for profit opportunities"""
        opportunities = []
        
        # Look for trending technologies and practices
        tech_trends = self._extract_tech_trends()
        for trend in tech_trends:
            opportunities.append({
                "type": "tech_trend",
                "data": trend,
                "potential_impact": self._estimate_profit_impact(trend)
            })
        
        # Look for efficiency improvements
        efficiency_patterns = self._extract_efficiency_patterns()
        for pattern in efficiency_patterns:
            opportunities.append({
                "type": "efficiency",
                "data": pattern,
                "potential_impact": self._estimate_profit_impact(pattern)
            })
        
        return opportunities
    
    def _extract_tech_trends(self) -> List[Dict[str, Any]]:
        """Extract technology trends from knowledge base"""
        trends = []
        
        # Analyze content for trending topics
        tech_keywords = {}
        for item in self._knowledge_base.values():
            content_lower = item.content.lower()
            for keyword in ["ai", "machine learning", "blockchain", "cloud", "api", 
                          "microservices", "docker", "kubernetes", "automation"]:
                if keyword in content_lower:
                    tech_keywords[keyword] = tech_keywords.get(keyword, 0) + 1
        
        # Convert to trends
        for keyword, count in tech_keywords.items():
            if count >= 3:  # Minimum threshold
                trends.append({
                    "technology": keyword,
                    "frequency": count,
                    "confidence": min(count / 10.0, 1.0)
                })
        
        return trends
    
    def _extract_efficiency_patterns(self) -> List[Dict[str, Any]]:
        """Extract efficiency improvement patterns"""
        patterns = []
        
        # Look for optimization patterns in code examples
        for item in self._knowledge_base.values():
            if item.content_type == "code_examples":
                content_lower = item.content.lower()
                if any(keyword in content_lower for keyword in 
                      ["optimize", "performance", "efficient", "fast", "scalable"]):
                    patterns.append({
                        "source": item.title,
                        "pattern_type": "performance_optimization",
                        "content_snippet": item.content[:200]
                    })
        
        return patterns
    
    def _estimate_profit_impact(self, opportunity: Dict[str, Any]) -> float:
        """Estimate potential profit impact of an opportunity"""
        # Simple heuristic-based estimation
        base_impact = 0.1
        
        if opportunity.get("frequency", 0) > 5:
            base_impact += 0.2
        if opportunity.get("confidence", 0) > 0.7:
            base_impact += 0.3
        
        return min(base_impact, 1.0)
    
    async def _apply_profit_optimization(self, insight: Dict[str, Any]) -> bool:
        """Apply a profit optimization insight"""
        # Placeholder for agent-specific optimization logic
        # This would be implemented by individual agents
        self.logger.info(f"Applying optimization: {insight['type']}")
        return True
    
    def _update_learning_metrics(self):
        """Update learning performance metrics"""
        self._metrics.total_sources = len(self._sources)
        self._metrics.active_sources = sum(1 for s in self._sources.values() if s.is_active)
        self._metrics.knowledge_items_learned = len(self._knowledge_base)
        self._metrics.last_learning_session = datetime.utcnow()
        
        # Calculate learning efficiency
        if self._metrics.total_sources > 0:
            self._metrics.learning_efficiency = (
                self._metrics.knowledge_items_learned / self._metrics.total_sources
            )
    
    # Public API methods
    
    def add_knowledge_source(self, source: KnowledgeSource) -> bool:
        """Add a new knowledge source"""
        try:
            self._sources[source.id] = source
            self.logger.info(f"Added knowledge source: {source.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add knowledge source: {e}")
            return False
    
    def remove_knowledge_source(self, source_id: str) -> bool:
        """Remove a knowledge source"""
        try:
            if source_id in self._sources:
                del self._sources[source_id]
                self.logger.info(f"Removed knowledge source: {source_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to remove knowledge source: {e}")
            return False
    
    def query_knowledge(self, query: str, limit: int = 10) -> List[KnowledgeItem]:
        """Query the knowledge base"""
        query_lower = query.lower()
        matches = []
        
        for item in self._knowledge_base.values():
            # Simple text matching
            if (query_lower in item.title.lower() or 
                query_lower in item.content.lower() or
                any(tag in query_lower for tag in item.domain_tags)):
                matches.append(item)
        
        # Sort by relevance
        matches.sort(key=lambda x: x.relevance_score, reverse=True)
        return matches[:limit]
    
    def get_knowledge_summary(self) -> Dict[str, Any]:
        """Get summary of current knowledge state"""
        return {
            "agent_domain": self.agent_domain,
            "status": self._status.value,
            "metrics": {
                "total_sources": self._metrics.total_sources,
                "active_sources": self._metrics.active_sources,
                "knowledge_items": self._metrics.knowledge_items_learned,
                "learning_efficiency": self._metrics.learning_efficiency,
                "last_learning_session": (
                    self._metrics.last_learning_session.isoformat() 
                    if self._metrics.last_learning_session else None
                )
            },
            "knowledge_categories": self._get_knowledge_categories(),
            "top_knowledge_sources": self._get_top_sources()
        }
    
    def _get_knowledge_categories(self) -> Dict[str, int]:
        """Get categories of knowledge items"""
        categories = {}
        for item in self._knowledge_base.values():
            categories[item.content_type] = categories.get(item.content_type, 0) + 1
        return categories
    
    def _get_top_sources(self) -> List[Dict[str, Any]]:
        """Get top knowledge sources by priority"""
        sources = sorted(self._sources.values(), key=lambda x: x.priority, reverse=True)
        return [
            {
                "id": s.id,
                "name": s.name,
                "url": s.url,
                "priority": s.priority,
                "is_active": s.is_active,
                "last_updated": s.last_updated.isoformat() if s.last_updated else None
            }
            for s in sources[:5]
        ]
    
    # Integration methods for BaseAgent
    
    async def enhance_agent_capabilities(self, current_capabilities: List[str]) -> List[str]:
        """Enhance agent capabilities based on learned knowledge"""
        enhanced_capabilities = current_capabilities.copy()
        
        # Analyze knowledge for new capability opportunities
        for item in self._knowledge_base.values():
            if item.relevance_score > 0.7:  # High relevance items
                # Extract potential capabilities from content
                potential_caps = self._extract_capabilities_from_content(item.content)
                for cap in potential_caps:
                    if cap not in enhanced_capabilities:
                        enhanced_capabilities.append(cap)
        
        return enhanced_capabilities
    
    def _extract_capabilities_from_content(self, content: str) -> List[str]:
        """Extract potential capabilities from content"""
        capabilities = []
        content_lower = content.lower()
        
        capability_patterns = {
            "data analysis": ["analyze", "data", "statistics", "insights"],
            "automation": ["automate", "script", "workflow", "process"],
            "api integration": ["api", "integration", "webhook", "endpoint"],
            "machine learning": ["ml", "predict", "model", "algorithm"],
            "optimization": ["optimize", "improve", "efficiency", "performance"]
        }
        
        for capability, keywords in capability_patterns.items():
            if all(keyword in content_lower for keyword in keywords[:2]):  # At least 2 keywords
                capabilities.append(capability)
        
        return capabilities
    
    async def get_profit_recommendations(self) -> List[Dict[str, Any]]:
        """Get profit optimization recommendations based on knowledge"""
        recommendations = []
        
        # Analyze recent high-value knowledge
        recent_items = [
            item for item in self._knowledge_base.values()
            if (datetime.utcnow() - item.extracted_at).days <= 7
            and item.relevance_score > 0.6
        ]
        
        for item in recent_items:
            if "profit" in item.content.lower() or "revenue" in item.content.lower():
                recommendations.append({
                    "type": "revenue_opportunity",
                    "source": item.title,
                    "description": item.content[:200],
                    "confidence": item.relevance_score,
                    "implementation_priority": "high" if item.relevance_score > 0.8 else "medium"
                })
        
        return recommendations[:10]  # Top 10 recommendations


# Global knowledge adapter registry for agents
_knowledge_adapters: Dict[str, AutonomousKnowledgeAdapter] = {}


def get_knowledge_adapter(agent_domain: str) -> AutonomousKnowledgeAdapter:
    """Get or create knowledge adapter for agent domain"""
    if agent_domain not in _knowledge_adapters:
        _knowledge_adapters[agent_domain] = AutonomousKnowledgeAdapter(agent_domain)
    return _knowledge_adapters[agent_domain]


async def shutdown_all_adapters():
    """Shutdown all knowledge adapters"""
    for adapter in _knowledge_adapters.values():
        await adapter.stop_autonomous_learning()
    _knowledge_adapters.clear()