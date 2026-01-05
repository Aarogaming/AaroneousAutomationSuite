"""
Test suite for Task CLI (AAS-107)

Tests the new task management CLI commands in core/main.py
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent

def run_cli(*args):
    """Run CLI command and return output"""
    result = subprocess.run(
        ["python", "-m", "core.main"] + list(args),
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    return result.stdout + result.stderr, result.returncode

def test_task_available():
    """Test: task available command"""
    print("TEST: task available")
    output, code = run_cli("task", "available")
    assert "AVAILABLE TASKS" in output, "Should show available tasks header"
    assert code == 0, "Should exit successfully"
    print("[OK] PASS: task available\n")

def test_task_list_queued():
    """Test: task list --status queued"""
    print("TEST: task list --status queued")
    output, code = run_cli("task", "list", "--status", "queued")
    assert "TASKS" in output, "Should show tasks header"
    assert "queued" in output.lower() or "No tasks match" in output, "Should filter by queued status"
    assert code == 0, "Should exit successfully"
    print("[OK] PASS: task list --status queued\n")

def test_task_list_in_progress():
    """Test: task list --status 'In Progress'"""
    print("TEST: task list --status 'In Progress'")
    output, code = run_cli("task", "list", "--status", "In Progress")
    assert "TASKS" in output, "Should show tasks header"
    assert code == 0, "Should exit successfully"
    print("[OK] PASS: task list --status 'In Progress'\n")

def test_task_list_high_priority():
    """Test: task list --priority High"""
    print("TEST: task list --priority High")
    output, code = run_cli("task", "list", "--priority", "High")
    assert "TASKS" in output, "Should show tasks header"
    assert code == 0, "Should exit successfully"
    print("[OK] PASS: task list --priority High\n")

def test_task_show():
    """Test: task show AAS-003 (completed task)"""
    print("TEST: task show AAS-003")
    output, code = run_cli("task", "show", "AAS-003")
    assert "TASK DETAILS" in output, "Should show task details header"
    assert "AAS-003" in output, "Should show task ID"
    assert "Pydantic RCS" in output, "Should show task title"
    assert code == 0, "Should exit successfully"
    print("[OK] PASS: task show AAS-003\n")

def test_task_show_nonexistent():
    """Test: task show with non-existent ID"""
    print("TEST: task show AAS-9999 (non-existent)")
    output, code = run_cli("task", "show", "AAS-9999")
    assert "not found" in output.lower(), "Should report task not found"
    assert code == 0, "Should exit gracefully"
    print("[OK] PASS: task show non-existent\n")

def test_legacy_board_command():
    """Test: legacy 'board' command still works"""
    print("TEST: board (legacy)")
    output, code = run_cli("board")
    assert "AAS ACTIVE TASK BOARD" in output, "Should show board header"
    assert "Summary:" in output, "Should show summary statistics"
    assert code == 0, "Should exit successfully"
    print("[OK] PASS: board (legacy)\n")

def test_legacy_blocked_command():
    """Test: legacy 'blocked' command still works"""
    print("TEST: blocked (legacy)")
    output, code = run_cli("blocked")
    assert "BLOCKED" in output or "No blocked tasks" in output, "Should show blocked status"
    assert code == 0, "Should exit successfully"
    print("[OK] PASS: blocked (legacy)\n")

def test_task_create_and_cleanup():
    """Test: task create (with cleanup)"""
    print("TEST: task create")
    
    # Backup ACTIVE_TASKS.md
    backup_path = PROJECT_ROOT / "handoff" / "ACTIVE_TASKS.md.backup"
    original_path = PROJECT_ROOT / "handoff" / "ACTIVE_TASKS.md"
    shutil.copy(original_path, backup_path)
    
    try:
        # Create task
        output, code = run_cli(
            "task", "create", "Test Task for CLI",
            "--priority", "Low",
            "--description", "This is a test task"
        )
        
        assert "Created task AAS-" in output, "Should confirm task creation"
        assert code == 0, "Should exit successfully"
        
        # Verify it appears in list
        output, code = run_cli("task", "list", "--status", "queued")
        assert "Test Task for CLI" in output, "Created task should appear in list"
        
        print("[OK] PASS: task create\n")
    
    finally:
        # Restore backup
        shutil.move(backup_path, original_path)
        print("   (Restored original ACTIVE_TASKS.md)")

def test_task_start_validation():
    """Test: task start with dependency validation"""
    print("TEST: task start validation (blocked task)")
    
    # Try to start AAS-104 which is blocked by AAS-032
    output, code = run_cli("task", "start", "AAS-104", "TestActor")
    
    # Should fail because AAS-032 is not Done
    assert ("blocked" in output.lower() or "AAS-032" in output), "Should report blocking dependency"
    
    print("[OK] PASS: task start validation\n")

def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("TASK CLI TEST SUITE (AAS-107)")
    print("=" * 80 + "\n")
    
    tests = [
        test_task_available,
        test_task_list_queued,
        test_task_list_in_progress,
        test_task_list_high_priority,
        test_task_show,
        test_task_show_nonexistent,
        test_legacy_board_command,
        test_legacy_blocked_command,
        test_task_start_validation,
        test_task_create_and_cleanup,  # Run last (modifies board)
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] FAIL: {test.__name__}")
            print(f"   {e}\n")
            failed += 1
        except Exception as e:
            print(f"[FAIL] ERROR: {test.__name__}")
            print(f"   {e}\n")
            failed += 1
    
    print("=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 80 + "\n")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
