"""
Test Agent Collaboration System

Demonstrates multi-agent coordination features:
- Check-in/check-out
- Task locking
- Help requests
- Capability matching
"""

import sys
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.managers import ManagerHub
from loguru import logger


@pytest.fixture
def sessions(hub):
    """Fixture for agent sessions."""
    collab = hub.collaboration
    session_copilot = collab.check_in("GitHub Copilot", agent_version="1.0")
    session_chatgpt = collab.check_in("ChatGPT", agent_version="4.0")
    session_sixth = collab.check_in("Sixth", agent_version="3.5")
    
    # Create tasks for locking tests
    with hub.db.get_session() as session:
        from core.db_models import Task, TaskPriority, TaskStatus
        for tid in ["AAS-105", "AAS-106"]:
            if not session.query(Task).filter_by(id=tid).first():
                task = Task(id=tid, title=f"Test Task {tid}", priority=TaskPriority.MEDIUM, status=TaskStatus.QUEUED)
                session.add(task)
    
    yield {
        "copilot": session_copilot,
        "chatgpt": session_chatgpt,
        "sixth": session_sixth
    }
    
    # Cleanup
    collab.check_out(session_copilot)
    collab.check_out(session_chatgpt)
    collab.check_out(session_sixth)
    
    # Cleanup
    collab.check_out(session_copilot)
    collab.check_out(session_chatgpt)
    collab.check_out(session_sixth)

def test_agent_checkin(hub):
    """Test agent check-in and roster display."""
    print("\n" + "="*60)
    print("TEST 1: Agent Check-In and Roster")
    print("="*60)
    
    collab = hub.collaboration
    
    # Multiple agents check in
    session_copilot = collab.check_in("GitHub Copilot", agent_version="1.0")
    
    # View active agents
    agents = collab.get_active_agents()
    print(f"\nActive agents: {len(agents)}")
    found = False
    for agent in agents:
        print(f"  • {agent['agent_name']} ({agent['session_id'][:12]}...)")
        if agent['agent_name'] == "GitHub Copilot":
            found = True
    
    assert found
    collab.check_out(session_copilot)


def test_task_locking(hub, sessions):
    """Test task locking to prevent conflicts."""
    print("\n" + "="*60)
    print("TEST 2: Task Locking (Conflict Prevention)")
    print("="*60)
    
    collab = hub.collaboration
    
    # Agent 1 acquires lock
    print("\n1. GitHub Copilot tries to lock AAS-105...")
    success = collab.acquire_task_lock("AAS-105", sessions["copilot"], "active")
    print(f"   Result: {'✅ Acquired' if success else '❌ Failed'}")
    
    # Agent 2 tries to acquire same lock (should fail)
    print("\n2. ChatGPT tries to lock AAS-105 (should fail)...")
    success = collab.acquire_task_lock("AAS-105", sessions["chatgpt"], "active")
    print(f"   Result: {'✅ Acquired' if success else '❌ Failed (expected)'}")
    
    # Agent 2 can acquire helper lock
    print("\n3. ChatGPT tries helper lock on AAS-105...")
    success = collab.acquire_task_lock("AAS-105", sessions["chatgpt"], "helper")
    print(f"   Result: {'✅ Acquired' if success else '❌ Failed'}")
    
    # Agent 3 locks different task
    print("\n4. Sixth locks AAS-106...")
    success = collab.acquire_task_lock("AAS-106", sessions["sixth"], "active")
    print(f"   Result: {'✅ Acquired' if success else '❌ Failed'}")


def test_help_requests(hub, sessions):
    """Test help request protocol."""
    print("\n" + "="*60)
    print("TEST 3: Help Request Protocol")
    print("="*60)
    
    collab = hub.collaboration
    
    # Agent requests help
    print("\n1. GitHub Copilot requests architecture help...")
    help_id = collab.request_help(
        task_id="AAS-105",
        requester_session_id=sessions["copilot"],
        help_type="architecture",
        context="Need advice on gRPC service design patterns for async streaming",
        urgency="medium",
        estimated_time=20
    )
    print(f"   Help request created: {help_id}")
    
    # View open requests
    print("\n2. Viewing open help requests...")
    requests = collab.get_open_help_requests()
    for req in requests:
        print(f"   • {req['id'][:12]}... - {req['help_type']} ({req['urgency']})")
        print(f"     Task: {req['task_id']}")
        print(f"     Context: {req['context'][:60]}...")
    
    # Agent accepts help request
    print("\n3. Sixth accepts help request...")
    success = collab.accept_help_request(
        request_id=help_id,
        helper_session_id=sessions["sixth"],
        response_message="I can help! I have experience with gRPC streaming patterns."
    )
    print(f"   Result: {'✅ Accepted' if success else '❌ Failed'}")
    
    # Complete help
    print("\n4. Marking help as completed...")
    collab.complete_help_request(
        request_id=help_id,
        outcome="Suggested repository pattern with bidirectional streaming. Provided proto examples."
    )
    print("   ✅ Help completed")
    
    return help_id


def test_capability_matching(hub):
    """Test capability-based task matching."""
    print("\n" + "="*60)
    print("TEST 4: Capability-Based Task Matching")
    print("="*60)
    
    collab = hub.collaboration
    
    # Test different task types
    test_cases = [
        {
            "description": "Refactor large Python module with complex async patterns",
            "tags": ["refactoring", "python", "async"]
        },
        {
            "description": "Design system architecture for distributed task queue",
            "tags": ["architecture", "system_design"]
        },
        {
            "description": "Write comprehensive test suite for gRPC services",
            "tags": ["testing", "grpc"]
        },
        {
            "description": "Quick bug fix in TypeScript React component",
            "tags": ["debugging", "quick_fix", "typescript"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Task: {test_case['description'][:50]}...")
        best_agent = collab.find_best_agent_for_task(
            task_description=test_case["description"],
            task_tags=test_case["tags"]
        )
        
        if best_agent:
            print(f"   ✓ Best match: {best_agent['agent_name']} (score: {best_agent['match_score']:.0%})")
            caps = best_agent['capabilities']
            print(f"     Strengths: {', '.join(caps.get('strengths', [])[:3])}")
        else:
            print("   ✗ No suitable agent available")


def test_cleanup(hub, sessions):
    """Cleanup: check out all agents."""
    print("\n" + "="*60)
    print("CLEANUP: Check-Out All Agents")
    print("="*60)
    
    collab = hub.collaboration
    
    for name, session_id in sessions.items():
        collab.check_out(session_id)
        print(f"  ✓ {name.capitalize()} checked out")
    
    print("\n✅ All tests completed!")


def main():
    """Run all collaboration tests."""
    logger.info("Starting Agent Collaboration System Tests")
    
    try:
        # Test 1: Check-in
        hub, sessions = test_agent_checkin()
        
        # Test 2: Task Locking
        test_task_locking(hub, sessions)
        
        # Test 3: Help Requests
        test_help_requests(hub, sessions)
        
        # Test 4: Capability Matching
        test_capability_matching(hub)
        
        # Cleanup
        test_cleanup(hub, sessions)
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
