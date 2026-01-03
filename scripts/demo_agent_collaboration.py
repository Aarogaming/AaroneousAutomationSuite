
"""
Agent Collaboration Demo

Demonstrates the multi-agent collaboration system:
1. Agents checking in with their capabilities
2. Finding the best agent for a task
3. One agent requesting help from another
4. Accepting and completing help requests
5. Checking out when done

This shows how AI agents (Copilot, ChatGPT, Claude, Sixth, Cline) can
coordinate work without stepping on each other's toes.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
from loguru import logger
from core.managers import ManagerHub


def demo_collaboration():
    """Run a full collaboration demo."""
    
    print("\n" + "="*70)
    print("🤝 AAS Agent Collaboration System Demo")
    print("="*70 + "\n")
    
    # Initialize hub
    hub = ManagerHub.create()
    collab = hub.collaboration
    
    # Step 1: Agents check in
    print("📋 Step 1: Agents Check In\n")
    
    copilot_session = collab.check_in(
        "GitHub Copilot",
        agent_version="1.0"
    )
    
    chatgpt_session = collab.check_in(
        "ChatGPT",
        agent_version="4.0"
    )
    
    sixth_session = collab.check_in(
        "Sixth",
        agent_version="1.0"
    )
    
    time.sleep(1)
    
    # Step 2: Show active roster
    print("\n📋 Step 2: View Active Roster\n")
    
    active = collab.get_active_agents()
    print(f"Active agents: {len(active)}\n")
    for agent in active:
        print(f"  • {agent['agent_name']}")
        print(f"    Best for: {', '.join(agent['capabilities'].get('best_for', []))}")
    
    time.sleep(1)
    
    # Step 3: Find best agent for a complex refactoring task
    print("\n📋 Step 3: Find Best Agent for Task\n")
    
    task_desc = """
    Refactor the TaskManager class to separate concerns:
    - Extract batch processing logic
    - Add comprehensive docstrings
    - Create unit tests for all methods
    This is a large refactoring with 500+ lines of code.
    """
    
    print(f"Task: {task_desc.strip()}\n")
    
    best_agent = collab.find_best_agent_for_task(
        task_desc,
        task_tags=["refactoring", "testing", "documentation"]
    )
    
    if best_agent:
        print(f"✅ Best match: {best_agent['agent_name']}")
        print(f"   Match score: {int(best_agent['match_score']*100)}%")
        print(f"   Why: {', '.join(best_agent['capabilities'].get('best_for', []))}")
    
    time.sleep(1)
    
    # Step 4: Agent acquires task lock
    print("\n📋 Step 4: Agent Acquires Task Lock\n")
    
    # Simulate Sixth claiming a task (use None for demo, or actual task ID)
    # In production, you'd only lock tasks that exist in the database
    task_id = None  # Set to None to skip FK constraint in demo
    
    # For demo purposes, we'll just demonstrate the concept without actual lock
    print(f"💡 In production, Sixth would acquire a lock on a real task")
    print(f"   This prevents other agents from working on the same task")
    print(f"   Lock types: 'active' (full control), 'soft' (intent), 'helper' (read)")
    
    time.sleep(1)
    
    # Step 5: Sixth requests help from Copilot for code review
    print("\n📋 Step 5: Request Help from Another Agent\n")
    
    # For demo, use a conceptual task ID
    demo_task_id = "DEMO-TASK"
    print(f"💡 Simulating help request on conceptual task: {demo_task_id}")
    print(f"   In production, this would be a real task ID from the database\n")
    
    # Skip actual help request to avoid FK constraint
    help_request_id = "help-demo123"
    print(f"🆘 Sixth would request: code_review")
    print(f"   Context: Need review on new TaskManager refactoring before commit")
    print(f"   Urgency: high, Estimated: 15 minutes\n")
    
    time.sleep(2)
    
    # Step 6: Copilot accepts help request
    print("\n📋 Step 6: Another Agent Accepts Help Request\n")
    
    print(f"💡 In production, Copilot would see the help request and accept it")
    print(f"   This creates a 'helper' lock (non-exclusive) so multiple agents")
    print(f"   can assist without blocking the primary owner\n")
    
    print("✅ Copilot would accept with message: 'I'll review the refactoring now!'")
    
    time.sleep(1)
    
    # Step 7: Complete help request
    print("\n📋 Step 7: Complete Help Request\n")
    
    print("✅ Copilot completes review with outcome:")
    print("   'Reviewed code. Suggested minor improvements to error handling. LGTM overall!'\n")
    
    time.sleep(1)
    
    # Step 8: Release lock and check out
    print("\n📋 Step 8: Cleanup - Check Out All Agents\n")
    
    print("💡 In production, agents would release task locks before checking out")
    
    collab.check_out(copilot_session)
    print("👋 GitHub Copilot checked out")
    
    collab.check_out(chatgpt_session)
    print("👋 ChatGPT checked out")
    
    collab.check_out(sixth_session)
    print("👋 Sixth checked out")
    
    time.sleep(1)
    
    # Final roster check
    print("\n📋 Final Check: Active Agents\n")
    
    active = collab.get_active_agents()
    if not active:
        print("✅ All agents checked out successfully")
    else:
        print(f"⚠️  Still {len(active)} active agent(s)")
    
    print("\n" + "="*70)
    print("🎉 Demo Complete!")
    print("="*70 + "\n")
    
    print("Key Takeaways:")
    print("  • Agents can check in with their capabilities")
    print("  • System finds best agent for each task")
    print("  • Agents can request help without losing ownership")
    print("  • Task locks prevent conflicts")
    print("  • Clean check-in/check-out lifecycle")
    print()


if __name__ == "__main__":
    try:
        demo_collaboration()
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise
