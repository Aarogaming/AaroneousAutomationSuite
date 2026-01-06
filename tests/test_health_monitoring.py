"""Test script for enhanced health monitoring system."""
from core.handoff_manager import HandoffManager

# Initialize manager
manager = HandoffManager()

# Get task board health
print("\n" + "="*60)
print("TASK BOARD HEALTH CHECK")
print("="*60)

health = manager.get_task_board_health()

print(f"\n📊 Health Score: {health['summary']['health_score']}")
print(f"   Total Tasks: {health['summary']['total_tasks']}")
print(f"   Stale Tasks: {health['summary']['stale_count']}")
print(f"   Unassigned High Priority: {health['summary']['unassigned_high_priority_count']}")
print(f"   Missing Artifacts: {health['summary']['missing_artifacts_count']}")

if health["stale_tasks"]:
    print("\n⏰ STALE TASKS:")
    for task in health["stale_tasks"]:
        print(f"   - {task['id']}: {task['title']} ({task['days_old']} days old)")

if health["unassigned_high_priority"]:
    print("\n🚨 UNASSIGNED HIGH-PRIORITY TASKS:")
    for task in health["unassigned_high_priority"]:
        print(f"   - {task['id']} [{task['priority'].upper()}]: {task['title']}")

if health["missing_artifacts"]:
    print("\n📁 MISSING ARTIFACT DIRECTORIES:")
    for task in health["missing_artifacts"]:
        print(f"   - {task['id']} [{task['status']}]")

# Generate full health report
print("\n" + "="*60)
print("GENERATING FULL HEALTH REPORT")
print("="*60)

report_path = manager.generate_health_report()
print(f"\n✅ Report generated: {report_path}")

# Display the report
print("\n" + "="*60)
print("HEALTH REPORT CONTENTS")
print("="*60 + "\n")
with open(report_path, 'r', encoding='utf-8') as f:
    print(f.read())
