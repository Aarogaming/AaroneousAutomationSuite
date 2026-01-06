"""
Test suite for FCFS (First-Come-First-Served) task claiming system.
Tests HandoffManager's claim_next_task, complete_task, and dependency logic.

Run with: python scripts/test_fcfs_claiming.py
"""
import os
import sys
import shutil
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.handoff_manager import HandoffManager


class TestFCFSClaiming:
    """Test suite for FCFS claiming system."""
    
    def setup_method(self, method):
        self.tests_passed = 0
        self.tests_failed = 0
        self.temp_dir = None
        self.setup()

    def teardown_method(self, method):
        self.teardown()
        
    def setup(self):
        """Create temporary task board for testing."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        self.temp_dir = tempfile.mkdtemp(prefix="aas_test_")
        self.task_board_path = os.path.join(self.temp_dir, "ACTIVE_TASKS.md")
        self.artifact_dir = os.path.join(self.temp_dir, "artifacts")
        os.makedirs(self.artifact_dir, exist_ok=True)
        
        # Create test task board
        test_board = """# AAS Active Task Board

| ID | Priority | Title | Depends On | Status | Assignee | Created | Updated |
|:---|:---|:---|:---|:---|:---|:---|:---|
 | TEST-001 | Urgent | Critical Bug Fix | - | queued | - | 2026-01-02 | 2026-01-02 | 
 | TEST-002 | High | Important Feature | - | queued | - | 2026-01-02 | 2026-01-02 | 
 | TEST-003 | Medium | Normal Task | TEST-001 | queued | - | 2026-01-02 | 2026-01-02 | 
 | TEST-004 | Low | Minor Enhancement | TEST-002, TEST-003 | queued | - | 2026-01-02 | 2026-01-02 | 
 | TEST-005 | High | Already Done | - | Done | TestBot | 2026-01-02 | 2026-01-02 | 
 | TEST-006 | Urgent | In Progress Task | - | In Progress | Alice | 2026-01-02 | 2026-01-02 | 
 | TEST-007 | Medium | Blocked Task | TEST-999 | queued | - | 2026-01-02 | 2026-01-02 | 
 | TEST-008 | Low | Another Low Priority | - | queued | - | 2026-01-02 | 2026-01-02 | 
"""
        with open(self.task_board_path, "w", encoding="utf-8") as f:
            f.write(test_board)
            
        # Create manager and override task_board_path
        self.manager = HandoffManager(artifact_dir=self.artifact_dir)
        self.manager.task_board_path = self.task_board_path
        
    def teardown(self):
        """Clean up temporary files."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            
    def assert_true(self, condition: bool, test_name: str, message: str = ""):
        """Assert helper with test tracking."""
        if condition:
            print(f"✅ PASS: {test_name}")
            self.tests_passed += 1
        else:
            print(f"❌ FAIL: {test_name}")
            if message:
                print(f"   {message}")
            self.tests_failed += 1
            
    def assert_equals(self, actual, expected, test_name: str):
        """Assert equality with test tracking."""
        if actual == expected:
            print(f"✅ PASS: {test_name}")
            self.tests_passed += 1
        else:
            print(f"❌ FAIL: {test_name}")
            print(f"   Expected: {expected}")
            print(f"   Got: {actual}")
            self.tests_failed += 1
            
    # Test 1: Priority-based claiming
    def test_priority_based_claiming(self):
        """Test that highest priority queued tasks are claimed first."""
        print("\n--- Test 1: Priority-Based Claiming ---")
        
        # Should claim TEST-001 (Urgent, no dependencies)
        claimed = self.manager.claim_next_task("Actor1")
        
        self.assert_true(claimed is not None, "Task was claimed")
        self.assert_equals(claimed.get("id"), "TEST-001", "Claimed highest priority task (Urgent)")
        
        # Verify it's marked In Progress
        lines, tasks, _ = self.manager.parse_board()
        test001 = next((t for t in tasks if t["id"] == "TEST-001"), None)
        self.assert_equals(test001["status"], "In Progress", "Task status updated to In Progress")
        self.assert_equals(test001["assignee"], "Actor1", "Assignee set correctly")
        
    # Test 2: Dependency blocking
    def test_dependency_blocking(self):
        """Test that tasks with incomplete dependencies are not claimed."""
        print("\n--- Test 2: Dependency Blocking ---")
        
        # TEST-003 depends on TEST-001 (which is now In Progress from test 1)
        # So it should skip TEST-003 and claim TEST-002 (High priority, no deps)
        claimed = self.manager.claim_next_task("Actor2")
        
        self.assert_true(claimed is not None, "Task was claimed")
        self.assert_equals(claimed.get("id"), "TEST-002", "Skipped blocked task, claimed next eligible")
        
    # Test 3: Complete task and unblock dependents
    def test_complete_task_unblocking(self):
        """Test that completing a task allows dependents to be claimed."""
        print("\n--- Test 3: Complete Task and Unblock ---")
        
        # Complete TEST-001 (which TEST-003 depends on)
        success = self.manager.complete_task("TEST-001")
        self.assert_true(success, "Task marked as Done")
        
        # Now TEST-003 should be claimable (Medium priority)
        # But TEST-002 is still In Progress, so TEST-003 is highest eligible
        claimed = self.manager.claim_next_task("Actor3")
        
        self.assert_true(claimed is not None, "Task was claimed")
        self.assert_equals(claimed.get("id"), "TEST-003", "Previously blocked task now claimable")
        
    # Test 4: Multiple dependencies
    def test_multiple_dependencies(self):
        """Test task with multiple dependencies waits for all."""
        print("\n--- Test 4: Multiple Dependencies ---")
        
        # TEST-004 depends on both TEST-002 and TEST-003
        # TEST-003 is now In Progress, TEST-002 is In Progress
        # So TEST-004 should not be claimed yet
        
        # Only TEST-008 (Low priority, no deps) should be available
        claimed = self.manager.claim_next_task("Actor4")
        
        self.assert_true(claimed is not None, "Task was claimed")
        self.assert_equals(claimed.get("id"), "TEST-008", "Correctly skipped task with incomplete multi-deps")
        
        # Now complete both TEST-002 and TEST-003
        self.manager.complete_task("TEST-002")
        self.manager.complete_task("TEST-003")
        
        # TEST-004 should now be claimable
        claimed = self.manager.claim_next_task("Actor5")
        self.assert_equals(claimed.get("id"), "TEST-004", "Task with multiple deps claimable after all complete")
        
    # Test 5: No eligible tasks
    def test_no_eligible_tasks(self):
        """Test behavior when no eligible tasks are available."""
        print("\n--- Test 5: No Eligible Tasks ---")
        
        # All queued tasks should now be claimed or blocked
        claimed = self.manager.claim_next_task("Actor6")
        
        self.assert_true(claimed is None, "Returns None when no eligible tasks")
        
    # Test 6: Blocked tasks list
    def test_blocked_tasks_list(self):
        """Test get_blocked_tasks returns correct blocked tasks."""
        print("\n--- Test 6: Blocked Tasks List ---")
        
        # Reset for this test
        self.setup()
        
        blocked = self.manager.get_blocked_tasks()
        
        # Should find TEST-003 (depends on TEST-001 which is queued)
        # and TEST-004 (depends on TEST-002, TEST-003)
        # and TEST-007 (depends on TEST-999 which doesn't exist)
        
        blocked_ids = [t["id"] for t in blocked]
        self.assert_true("TEST-003" in blocked_ids, "TEST-003 is blocked")
        self.assert_true("TEST-004" in blocked_ids, "TEST-004 is blocked")
        self.assert_true("TEST-007" in blocked_ids, "TEST-007 is blocked by missing dep")
        
        print(f"   Found {len(blocked)} blocked tasks: {blocked_ids}")
        
    # Test 7: Artifact scaffolding
    def test_artifact_scaffolding(self):
        """Test that claiming creates artifact directory."""
        print("\n--- Test 7: Artifact Scaffolding ---")
        
        claimed = self.manager.claim_next_task("ArtifactTester")
        
        if claimed:
            task_id = claimed["id"]
            artifact_path = os.path.join(self.artifact_dir, task_id)
            readme_path = os.path.join(artifact_path, "README.md")
            
            self.assert_true(os.path.exists(artifact_path), f"Artifact directory created: {artifact_path}")
            self.assert_true(os.path.exists(readme_path), "README.md created in artifact directory")
            
            # Check README contains task info
            with open(readme_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assert_true(task_id in content, "README contains task ID")
                self.assert_true("ArtifactTester" in content, "README contains assignee")
        
    # Test 8: FCFS fairness (same priority)
    def test_fcfs_fairness(self):
        """Test that among same priority, first in board is claimed first."""
        print("\n--- Test 8: FCFS Fairness (Same Priority) ---")
        
        # Create board with multiple High priority tasks
        test_board = """# AAS Active Task Board

| ID | Priority | Title | Depends On | Status | Assignee | Created | Updated |
|:---|:---|:---|:---|:---|:---|:---|:---|
 | FAIR-001 | High | First High Priority | - | queued | - | 2026-01-02 | 2026-01-02 | 
 | FAIR-002 | High | Second High Priority | - | queued | - | 2026-01-02 | 2026-01-02 | 
 | FAIR-003 | High | Third High Priority | - | queued | - | 2026-01-02 | 2026-01-02 | 
"""
        with open(self.task_board_path, "w", encoding="utf-8") as f:
            f.write(test_board)
            
        # First claim should get FAIR-001
        claimed1 = self.manager.claim_next_task("Actor1")
        self.assert_equals(claimed1.get("id"), "FAIR-001", "First task claimed among same priority")
        
        # Second claim should get FAIR-002
        claimed2 = self.manager.claim_next_task("Actor2")
        self.assert_equals(claimed2.get("id"), "FAIR-002", "Second task claimed in order")
        
        # Third claim should get FAIR-003
        claimed3 = self.manager.claim_next_task("Actor3")
        self.assert_equals(claimed3.get("id"), "FAIR-003", "Third task claimed in order")
        
    # Test 9: Parse board with different statuses
    def test_parse_board_status_map(self):
        """Test that parse_board correctly builds status map."""
        print("\n--- Test 9: Parse Board Status Map ---")
        
        self.setup()
        lines, tasks, status_map = self.manager.parse_board()
        
        self.assert_equals(status_map.get("TEST-001"), "queued", "Queued task in status map")
        self.assert_equals(status_map.get("TEST-005"), "Done", "Done task in status map")
        self.assert_equals(status_map.get("TEST-006"), "In Progress", "In Progress task in status map")
        
        print(f"   Status map: {dict(list(status_map.items())[:3])}...")
        
    # Test 10: Edge case - circular dependencies (should not deadlock)
    def test_circular_dependencies(self):
        """Test handling of circular dependencies."""
        print("\n--- Test 10: Circular Dependencies (Edge Case) ---")
        
        # Create board with circular deps
        test_board = """# AAS Active Task Board

| ID | Priority | Title | Depends On | Status | Assignee | Created | Updated |
|:---|:---|:---|:---|:---|:---|:---|:---|
 | CIRC-001 | High | Task A | CIRC-002 | queued | - | 2026-01-02 | 2026-01-02 | 
 | CIRC-002 | High | Task B | CIRC-001 | queued | - | 2026-01-02 | 2026-01-02 | 
 | CIRC-003 | Medium | Independent Task | - | queued | - | 2026-01-02 | 2026-01-02 | 
"""
        with open(self.task_board_path, "w", encoding="utf-8") as f:
            f.write(test_board)
            
        # Should skip both circular tasks and claim CIRC-003
        claimed = self.manager.claim_next_task("CircTester")
        
        self.assert_true(claimed is not None, "Doesn't deadlock on circular deps")
        self.assert_equals(claimed.get("id"), "CIRC-003", "Claims non-circular task instead")
        
        blocked = self.manager.get_blocked_tasks()
        blocked_ids = [t["id"] for t in blocked]
        self.assert_true("CIRC-001" in blocked_ids and "CIRC-002" in blocked_ids, 
                        "Both circular tasks marked as blocked")
        
    def run_all_tests(self):
        """Run all tests and report results."""
        print("=" * 60)
        print("FCFS CLAIMING TEST SUITE")
        print("=" * 60)
        
        try:
            self.setup()
            
            # Run tests in sequence (some depend on previous state)
            self.test_priority_based_claiming()
            self.test_dependency_blocking()
            self.test_complete_task_unblocking()
            self.test_multiple_dependencies()
            self.test_no_eligible_tasks()
            
            # These tests reset state
            self.teardown()
            self.setup()
            self.test_blocked_tasks_list()
            
            self.teardown()
            self.setup()
            self.test_artifact_scaffolding()
            
            self.teardown()
            self.setup()
            self.test_fcfs_fairness()
            
            self.teardown()
            self.setup()
            self.test_parse_board_status_map()
            
            self.teardown()
            self.setup()
            self.test_circular_dependencies()
            
        finally:
            self.teardown()
            
        # Summary
        print("\n" + "=" * 60)
        print(f"TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_failed}")
        print(f"📊 Total:  {self.tests_passed + self.tests_failed}")
        
        if self.tests_failed == 0:
            print("\n🎉 ALL TESTS PASSED! FCFS claiming system is working correctly.")
            return 0
        else:
            print(f"\n⚠️  {self.tests_failed} test(s) failed. Please review.")
            return 1


if __name__ == "__main__":
    tester = TestFCFSClaiming()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)
