"""Quick script to verify recycled tasks"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db_manager import DatabaseManager
from core.db_models import Task

db = DatabaseManager('artifacts/aas.db')

with db.get_session() as s:
    tasks = s.query(Task).filter(Task.id.in_(['AAS-114', 'AAS-115', 'AAS-116', 'AAS-117', 'AAS-118'])).all()
    
    print(f"\n✅ Found {len(tasks)} recycled tasks:\n")
    for t in tasks:
        print(f"  {t.id}: {t.title}")
        print(f"    Status: {t.status.value}")
        print(f"    Priority: {t.priority.value}")
        print(f"    Dependencies: {t.dependencies}")
        print()
