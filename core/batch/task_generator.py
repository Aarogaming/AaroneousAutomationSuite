"""
Autonomous Task Generator

Automatically creates tasks based on:
- Project progress reviews
- Known issues and errors
- Development opportunities
- Code quality improvements
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger


class TaskGenerator:
    """Generates tasks from various sources"""
    
    def __init__(self, handoff_manager, linear_sync, config):
        self.handoff = handoff_manager
        self.linear = linear_sync
        self.config = config
        self.team_id = getattr(config, 'linear_team_id', None)
        self.task_board = Path("handoff/ACTIVE_TASKS.md")
        self.issues_log = Path("artifacts/issues/known_issues.json")
        self.issues_log.parent.mkdir(parents=True, exist_ok=True)
    
    def get_total_task_count(self) -> int:
        """Count total tasks on the board (excluding archived ones)"""
        if not self.task_board.exists():
            return 0
        
        content = self.task_board.read_text(encoding='utf-8')
        count = 0
        for line in content.split('\n'):
            if line.strip().startswith('|') and 'AAS-' in line and '---' not in line and '| ID |' not in line:
                count += 1
        return count

    async def review_project_progress(self) -> List[Dict[str, Any]]:
        """
        Review project progress and identify needed tasks.
        
        Analyzes:
        - Completed tasks and their outcomes
        - Blocked tasks and dependencies
        - Overdue tasks
        - Task velocity and bottlenecks
        
        Returns list of suggested tasks.
        """
        logger.info("Reviewing project progress...")
        
        suggestions = []
        
        # Parse current task board
        if not self.task_board.exists():
            logger.warning("Task board not found")
            return suggestions
        
        content = self.task_board.read_text(encoding='utf-8')
        
        # Analyze task statuses
        task_stats = {
            'todo': 0,
            'queued': 0,
            'in_progress': 0,
            'in_review': 0,
            'done': 0,
            'blocked': 0
        }
        
        blocked_tasks = []
        overdue_tasks = []
        
        for line in content.split('\n'):
            if not line.strip().startswith('|') or '---' in line:
                continue
            
            parts = [p.strip() for p in line.split('|')]
            if len(parts) < 6:
                continue
            
            task_id = parts[1]
            if not task_id or not task_id.startswith('AAS-'):
                continue
            
            status = parts[5].lower() if len(parts) > 5 else ''
            dependencies = parts[4] if len(parts) > 4 else '-'
            
            # Count statuses
            for key in task_stats:
                if key in status:
                    task_stats[key] += 1
                    break
            
            # Check for blocked tasks
            if dependencies and dependencies != '-' and status in ['queued', 'todo']:
                blocked_tasks.append({
                    'id': task_id,
                    'title': parts[3] if len(parts) > 3 else '',
                    'dependencies': dependencies
                })
        
        logger.info(f"Project stats: {task_stats}")
        
        # Generate suggestions based on analysis
        
        # 1. Too many blocked tasks?
        if len(blocked_tasks) > 3:
            suggestions.append({
                'title': 'Resolve Dependency Bottlenecks',
                'description': f"We have {len(blocked_tasks)} blocked tasks. Review and prioritize completing: {', '.join([t['dependencies'] for t in blocked_tasks[:3]])}",
                'priority': 'high',
                'type': 'process_improvement',
                'auto_generated': True,
                'source': 'progress_review'
            })
        
        # 2. Low task velocity?
        if task_stats['in_progress'] > 5 and task_stats['done'] < 10:
            suggestions.append({
                'title': 'Review In-Progress Tasks',
                'description': f"We have {task_stats['in_progress']} tasks in progress but only {task_stats['done']} completed. Review WIP limits and task complexity.",
                'priority': 'medium',
                'type': 'process_improvement',
                'auto_generated': True,
                'source': 'progress_review'
            })
        
        # 3. No queued work?
        if task_stats['queued'] + task_stats['todo'] < 3:
            suggestions.append({
                'title': 'Plan Next Sprint Tasks',
                'description': "Task backlog is low. Review roadmap and create new tasks for upcoming features.",
                'priority': 'medium',
                'type': 'planning',
                'auto_generated': True,
                'source': 'progress_review'
            })
        
        logger.success(f"Generated {len(suggestions)} suggestions from progress review")
        return suggestions
    
    async def scan_for_issues(self) -> List[Dict[str, Any]]:
        """
        Scan codebase and logs for known issues.
        
        Sources:
        - Exception logs
        - TODO/FIXME comments
        - Health reports
        - Git issues (if integrated)
        
        Returns list of issue-based tasks.
        """
        logger.info("Scanning for issues...")
        
        issues = []
        
        # 1. Scan health reports
        health_report = Path("artifacts/handoff/reports/HEALTH_REPORT.md")
        if health_report.exists():
            content = health_report.read_text(encoding='utf-8')
            
            # Look for error/warning sections
            if '## Errors' in content or '## Warnings' in content:
                error_lines = [
                    line for line in content.split('\n')
                    if line.startswith('- ') and ('error' in line.lower() or 'failed' in line.lower())
                ]
                
                for error_line in error_lines[:5]:  # Limit to top 5
                    issues.append({
                        'title': f"Fix: {error_line[2:60]}...",
                        'description': f"Health report shows: {error_line}\n\nSource: HEALTH_REPORT.md",
                        'priority': 'high',
                        'type': 'bugfix',
                        'auto_generated': True,
                        'source': 'health_report'
                    })
        
        # 2. Scan code for TODO/FIXME
        todo_file = Path("artifacts/issues/todos.json")
        if todo_file.exists():
            try:
                todos = json.loads(todo_file.read_text())
                for todo in todos[:3]:  # Top 3 TODOs
                    issues.append({
                        'title': f"TODO: {todo.get('title', 'Unnamed')}",
                        'description': f"```\n{todo.get('code', '')}\n```\n\nFile: {todo.get('file', 'unknown')}\nLine: {todo.get('line', '?')}",
                        'priority': 'low',
                        'type': 'improvement',
                        'auto_generated': True,
                        'source': 'code_todos'
                    })
            except Exception as e:
                logger.debug(f"Could not parse TODOs: {e}")
        
        # 3. Load known issues log
        if self.issues_log.exists():
            try:
                known_issues = json.loads(self.issues_log.read_text())
                for issue in known_issues.get('open', [])[:3]:
                    if not issue.get('has_task'):
                        issues.append({
                            'title': issue.get('title', 'Unknown Issue'),
                            'description': issue.get('description', '') + f"\n\nFirst seen: {issue.get('first_seen', 'unknown')}",
                            'priority': issue.get('priority', 'medium'),
                            'type': 'bugfix',
                            'auto_generated': True,
                            'source': 'issues_log'
                        })
            except Exception as e:
                logger.debug(f"Could not load issues log: {e}")
        
        logger.success(f"Found {len(issues)} issues to convert to tasks")
        return issues
    
    async def suggest_improvements(self) -> List[Dict[str, Any]]:
        """
        Suggest development improvements based on:
        - Code complexity
        - Test coverage
        - Documentation gaps
        - Performance opportunities
        
        Returns list of improvement tasks.
        """
        logger.info("Analyzing improvement opportunities...")
        
        improvements = []
        
        # 1. Check for missing tests
        test_files = list(Path("scripts").glob("test_*.py"))
        core_modules = list(Path("core").rglob("*.py"))
        
        tested_modules = set()
        for test_file in test_files:
            # Extract module name from test_xxx.py
            module = test_file.stem.replace('test_', '')
            tested_modules.add(module)
        
        untested = []
        for module_file in core_modules:
            if module_file.stem != '__init__' and module_file.stem not in tested_modules:
                untested.append(module_file.stem)
        
        if len(untested) > 3:
            improvements.append({
                'title': 'Increase Test Coverage',
                'description': f"Found {len(untested)} core modules without tests: {', '.join(untested[:5])}\n\nAdd test files to improve code reliability.",
                'priority': 'medium',
                'type': 'testing',
                'auto_generated': True,
                'source': 'code_analysis'
            })
        
        # 2. Check for missing documentation
        docs_dir = Path("docs")
        if docs_dir.exists():
            doc_files = list(docs_dir.glob("*.md"))
            if len(doc_files) < 5:
                improvements.append({
                    'title': 'Expand Documentation',
                    'description': f"Only {len(doc_files)} documentation files found. Consider adding:\n- Architecture overview\n- API reference\n- Deployment guide\n- Troubleshooting FAQ",
                    'priority': 'low',
                    'type': 'documentation',
                    'auto_generated': True,
                    'source': 'docs_analysis'
                })
        
        # 3. Check for large files (potential refactoring targets)
        large_files = []
        for py_file in Path(".").rglob("*.py"):
            if py_file.stat().st_size > 15000:  # >15KB
                lines = len(py_file.read_text(encoding='utf-8', errors='ignore').split('\n'))
                if lines > 500:
                    large_files.append((py_file, lines))
        
        if large_files:
            largest = sorted(large_files, key=lambda x: x[1], reverse=True)[0]
            improvements.append({
                'title': f'Refactor Large Module: {largest[0].stem}',
                'description': f"{largest[0]} has {largest[1]} lines. Consider breaking into smaller, focused modules for better maintainability.",
                'priority': 'low',
                'type': 'refactoring',
                'auto_generated': True,
                'source': 'code_complexity'
            })
        
        logger.success(f"Identified {len(improvements)} improvement opportunities")
        return improvements
    
    async def create_tasks(self, suggestions: List[Dict[str, Any]], dry_run: bool = False) -> List[str]:
        """
        Create tasks from suggestions.
        
        Args:
            suggestions: List of task dicts (title, description, priority, etc.)
            dry_run: If True, only log what would be created
            
        Returns:
            List of created task IDs
        """
        # Safety check: stop creating tasks if board has too many
        total_tasks = self.get_total_task_count()
        if total_tasks >= 500:
            logger.warning(f"🛑 Task creation suspended: {total_tasks} tasks on board (max: 500)")
            logger.info("Task creation will resume when count drops below 100")
            return []
        elif total_tasks >= 400:
            logger.warning(f"⚠️ Approaching task limit: {total_tasks}/500 tasks")
        
        created_tasks = []
        
        for suggestion in suggestions:
            try:
                title = suggestion['title']
                description = suggestion.get('description', '')
                priority = suggestion.get('priority', 'medium')
                task_type = suggestion.get('type', 'improvement')
                source = suggestion.get('source', 'auto_generated')
                
                if dry_run:
                    logger.info(f"[DRY RUN] Would create: {title} (priority: {priority})")
                    continue
                
                # Create in Linear if available
                if self.linear and self.team_id:
                    full_description = f"{description}\n\n---\n**Auto-generated task**\nType: {task_type}\nSource: {source}\nCreated: {datetime.now().isoformat()}"
                    
                    issue_id = self.linear.create_issue(
                        self.team_id,
                        title,
                        full_description
                    )
                    
                    if issue_id:
                        logger.success(f"Created Linear task: {title}")
                        created_tasks.append(issue_id)
                else:
                    logger.warning("Linear not available, skipping task creation")
            
            except Exception as e:
                logger.error(f"Failed to create task '{suggestion.get('title', 'unknown')}': {e}")
        
        logger.info(f"Created {len(created_tasks)} new tasks")
        return created_tasks
    
    async def log_issue(
        self,
        title: str,
        description: str,
        priority: str = 'medium',
        error_type: str = 'unknown',
        create_task: bool = True
    ) -> Optional[str]:
        """
        Log an issue and optionally create a task for it.
        
        Args:
            title: Issue title
            description: Detailed description
            priority: Priority level
            error_type: Type of error (exception, warning, etc.)
            create_task: Whether to create a Linear task
            
        Returns:
            Task ID if created, None otherwise
        """
        try:
            # Load or create issues log
            if self.issues_log.exists():
                issues_data = json.loads(self.issues_log.read_text())
            else:
                issues_data = {'open': [], 'resolved': []}
            
            # Add new issue
            issue = {
                'title': title,
                'description': description,
                'priority': priority,
                'type': error_type,
                'first_seen': datetime.now().isoformat(),
                'occurrences': 1,
                'has_task': False
            }
            
            # Check if already logged
            existing = next((i for i in issues_data['open'] if i['title'] == title), None)
            if existing:
                existing['occurrences'] += 1
                existing['last_seen'] = datetime.now().isoformat()
                logger.debug(f"Updated existing issue: {title} (occurrences: {existing['occurrences']})")
            else:
                issues_data['open'].append(issue)
                logger.info(f"Logged new issue: {title}")
            
            # Save issues log
            self.issues_log.write_text(json.dumps(issues_data, indent=2))
            
            # Create task if requested
            if create_task and not (existing and existing.get('has_task')):
                task_id = await self.create_tasks([{
                    'title': f"Fix: {title}",
                    'description': description,
                    'priority': priority,
                    'type': 'bugfix',
                    'source': 'logged_issue'
                }])
                
                if task_id:
                    if existing:
                        existing['has_task'] = True
                    else:
                        issue['has_task'] = True
                    self.issues_log.write_text(json.dumps(issues_data, indent=2))
                    return task_id[0] if task_id else None
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to log issue: {e}")
            return None
