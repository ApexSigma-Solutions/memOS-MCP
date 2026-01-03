"""
Batch Percolation Scheduler for memos.MCP.

This module provides scheduled tasks for percolating conversations from
Obsidian markdown files to the Neo4j knowledge graph.

Features:
- Scheduled percolation every 5 minutes (configurable)
- Scans Obsidian Conversations directory for new files
- Extracts metadata and creates graph nodes/relationships
- Tracks processed files to avoid duplicates
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import re
import yaml

from .config import settings

logger = logging.getLogger(__name__)


class PercolationScheduler:
    """
    Scheduler for batch percolation of conversations to Neo4j.
    
    Monitors the Obsidian vault for new conversation files and
    creates corresponding graph nodes.
    """

    def __init__(
        self,
        vault_path: Optional[Path] = None,
        interval_seconds: int = 300,  # 5 minutes
    ):
        """
        Initialize the percolation scheduler.
        
        Args:
            vault_path: Path to Obsidian vault
            interval_seconds: Interval between percolation runs
        """
        self._vault_path = vault_path or Path(
            os.environ.get("OBSIDIAN_VAULT_PATH", "./vault")
        )
        self._interval = interval_seconds
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._processed_files: Set[str] = set()
        self._stats = {
            "runs": 0,
            "files_processed": 0,
            "errors": 0,
            "last_run": None,
        }

    @property
    def stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        return self._stats.copy()

    async def start(self) -> None:
        """Start the percolation scheduler."""
        if self._running:
            logger.warning("Scheduler already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Started percolation scheduler (every {self._interval}s)")

    async def stop(self) -> None:
        """Stop the percolation scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped percolation scheduler")

    async def _run_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                await self._percolate()
            except Exception as e:
                logger.error(f"Percolation error: {e}")
                self._stats["errors"] += 1
            
            await asyncio.sleep(self._interval)

    async def _percolate(self) -> None:
        """Run a single percolation cycle."""
        logger.debug("Running percolation cycle")
        self._stats["runs"] += 1
        self._stats["last_run"] = datetime.now(timezone.utc).isoformat()
        
        # Scan for conversation files
        conversations_dir = self._vault_path / "Conversations"
        if not conversations_dir.exists():
            logger.debug("No Conversations directory found")
            return
        
        md_files = list(conversations_dir.glob("*.md"))
        new_files = [
            f for f in md_files 
            if str(f) not in self._processed_files
        ]
        
        if not new_files:
            logger.debug("No new conversation files to process")
            return
        
        logger.info(f"Found {len(new_files)} new conversation files")
        
        for file_path in new_files:
            try:
                await self._process_file(file_path)
                self._processed_files.add(str(file_path))
                self._stats["files_processed"] += 1
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                self._stats["errors"] += 1

    async def _process_file(self, file_path: Path) -> None:
        """
        Process a single conversation file.
        
        Extracts frontmatter and creates Neo4j nodes.
        """
        logger.debug(f"Processing {file_path.name}")
        
        content = file_path.read_text(encoding="utf-8")
        
        # Parse frontmatter
        frontmatter = self._parse_frontmatter(content)
        if not frontmatter:
            logger.warning(f"No frontmatter in {file_path.name}")
            return
        
        # Extract key information
        node_data = {
            "file_path": str(file_path),
            "title": frontmatter.get("title", "Untitled"),
            "source": frontmatter.get("source", "unknown"),
            "conversation_id": frontmatter.get("conversation_id"),
            "message_count": frontmatter.get("message_count", 0),
            "created": frontmatter.get("created"),
            "tags": frontmatter.get("tags", []),
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }
        
        # TODO: Create Neo4j node
        # This requires Neo4j connection to be implemented
        # For now, just log the extracted data
        logger.info(
            f"Extracted conversation: {node_data['title']} "
            f"({node_data['message_count']} messages from {node_data['source']})"
        )
        
        # Placeholder for Neo4j integration
        # await self._create_conversation_node(node_data)

    def _parse_frontmatter(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse YAML frontmatter from markdown content."""
        match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if not match:
            return None
        
        try:
            return yaml.safe_load(match.group(1))
        except yaml.YAMLError as e:
            logger.warning(f"YAML parse error: {e}")
            return None

    async def run_once(self) -> Dict[str, Any]:
        """Run a single percolation cycle (for testing/manual trigger)."""
        await self._percolate()
        return self._stats


# Global scheduler instance
_scheduler: Optional[PercolationScheduler] = None


def get_scheduler() -> PercolationScheduler:
    """Get the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = PercolationScheduler()
    return _scheduler


async def start_scheduler() -> None:
    """Start the global scheduler."""
    scheduler = get_scheduler()
    await scheduler.start()


async def stop_scheduler() -> None:
    """Stop the global scheduler."""
    scheduler = get_scheduler()
    await scheduler.stop()
