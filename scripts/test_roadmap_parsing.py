#!/usr/bin/env python3
"""
Test script for roadmap parsing functionality in TaskGenerator.

Usage:
    python scripts/test_roadmap_parsing.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.batch_gen import TaskGenerator
from core.config import load_config
from loguru import logger


class MockHandoffManager:
    """Mock handoff manager for testing"""
    pass


class MockLinearSync:
    """Mock Linear sync for testing"""
    pass


def main():
    """Test roadmap parsing"""
    logger.info("Testing roadmap parsing functionality")
    
    # Load config
    config = load_config()
    
    # Create mock dependencies
    handoff = MockHandoffManager()
    linear = MockLinearSync()
    
    # Initialize TaskGenerator
    generator = TaskGenerator(handoff, linear, config)
    
    # Test parsing each roadmap
    roadmap_files = [
        Path("docs/MASTER_ROADMAP.md"),
        Path("docs/AUTOMATION_ROADMAP.md"),
        Path("docs/DESKTOP_GUI_ROADMAP.md"),
        Path("docs/GAME_AUTOMATION_ROADMAP.md")
    ]
    
    total_tasks = 0
    
    for roadmap_path in roadmap_files:
        logger.info(f"\n{'='*60}")
        logger.info(f"Parsing: {roadmap_path}")
        logger.info(f"{'='*60}\n")
        
        tasks = generator.parse_roadmap(roadmap_path)
        total_tasks += len(tasks)
        
        if not tasks:
            logger.warning(f"No unchecked tasks found in {roadmap_path.name}")
            continue
        
        # Display summary
        logger.success(f"Found {len(tasks)} unchecked tasks in {roadmap_path.name}")
        
        # Group by priority
        by_priority = {'urgent': [], 'high': [], 'medium': [], 'low': []}
        for task in tasks:
            by_priority[task['priority']].append(task)
        
        logger.info("\nTasks by priority:")
        for priority in ['urgent', 'high', 'medium', 'low']:
            count = len(by_priority[priority])
            if count > 0:
                logger.info(f"  {priority.upper()}: {count} tasks")
        
        # Show first 3 tasks
        logger.info(f"\nFirst 3 tasks from {roadmap_path.name}:")
        for i, task in enumerate(tasks[:3], 1):
            logger.info(f"\n  {i}. {task['title']}")
            logger.info(f"     Priority: {task['priority']}")
            logger.info(f"     Phase: {task['phase']}")
            logger.info(f"     Task ID: {task.get('task_id', 'None')}")
            desc_preview = task['description'].split('\n')[0][:80]
            logger.info(f"     Description: {desc_preview}...")
    
    # Final summary
    logger.info(f"\n{'='*60}")
    logger.success(f"TOTAL: Found {total_tasks} unchecked tasks across all roadmaps")
    logger.info(f"{'='*60}")
    
    # Show what would happen in review_project_progress
    logger.info("\n\nSimulating low task count scenario:")
    logger.info("If task backlog is low (<5 tasks), these would be suggested:")
    
    all_tasks = []
    for roadmap_path in roadmap_files:
        all_tasks.extend(generator.parse_roadmap(roadmap_path))
    
    priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
    sorted_tasks = sorted(all_tasks, key=lambda t: priority_order.get(t['priority'], 2))
    
    logger.info("\nTop 5 priority tasks from roadmaps:")
    for i, task in enumerate(sorted_tasks[:5], 1):
        logger.info(f"{i}. [{task['priority'].upper()}] {task['title']}")
        logger.info(f"   From: {task['source']}")
        logger.info(f"   Phase: {task['phase']}\n")


if __name__ == "__main__":
    main()
