"""
Linear Integration Verification Tool

Verifies Linear API connectivity and configuration for AAS.
Run this after setting up Linear integration to ensure everything works.

Usage: python scripts/verify_linear.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config.manager import AASConfig
from core.handoff.linear import LinearSync
from loguru import logger
import requests


def verify_api_key(api_key: str) -> bool:
    """Test if API key is valid."""
    print("🔑 Verifying Linear API key...")
    
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    
    query = """
    query {
      viewer {
        id
        name
        email
      }
    }
    """
    
    try:
        response = requests.post(
            "https://api.linear.app/graphql",
            headers=headers,
            json={"query": query},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "viewer" in data["data"]:
                viewer = data["data"]["viewer"]
                print(f"   ✅ API key valid")
                print(f"   👤 User: {viewer.get('name')} ({viewer.get('email')})")
                print(f"   🆔 ID: {viewer.get('id')}")
                return True
            else:
                print(f"   ❌ Unexpected response: {data}")
                return False
        else:
            print(f"   ❌ HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def get_teams(api_key: str) -> list:
    """Get available teams."""
    print("\n📋 Fetching teams...")
    
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    
    query = """
    query {
      teams {
        nodes {
          id
          name
          key
        }
      }
    }
    """
    
    try:
        response = requests.post(
            "https://api.linear.app/graphql",
            headers=headers,
            json={"query": query},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            teams = data.get("data", {}).get("teams", {}).get("nodes", [])
            
            if teams:
                print(f"   ✅ Found {len(teams)} team(s):")
                for team in teams:
                    print(f"      • {team['name']} (ID: {team['id']}, Key: {team['key']})")
                return teams
            else:
                print("   ⚠️  No teams found")
                return []
        else:
            print(f"   ❌ HTTP {response.status_code}: {response.text}")
            return []
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []


def test_issue_creation(api_key: str, team_id: str) -> bool:
    """Test creating and closing an issue."""
    print(f"\n🧪 Testing issue creation (Team: {team_id})...")
    
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    
    # Create test issue
    create_mutation = """
    mutation CreateIssue($teamId: String!, $title: String!, $description: String!) {
      issueCreate(input: {
        teamId: $teamId
        title: $title
        description: $description
      }) {
        success
        issue {
          id
          identifier
          url
        }
      }
    }
    """
    
    try:
        response = requests.post(
            "https://api.linear.app/graphql",
            headers=headers,
            json={
                "query": create_mutation,
                "variables": {
                    "teamId": team_id,
                    "title": "[TEST] AAS Linear Integration Verification",
                    "description": "This is a test issue created by scripts/verify_linear.py. Safe to delete."
                }
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("data", {}).get("issueCreate", {}).get("success"):
                issue = data["data"]["issueCreate"]["issue"]
                issue_id = issue["id"]
                issue_identifier = issue["identifier"]
                issue_url = issue["url"]
                
                print(f"   ✅ Created test issue: {issue_identifier}")
                print(f"   🔗 URL: {issue_url}")
                
                # Archive the test issue
                archive_mutation = """
                mutation ArchiveIssue($issueId: String!) {
                  issueArchive(id: $issueId) {
                    success
                  }
                }
                """
                
                archive_response = requests.post(
                    "https://api.linear.app/graphql",
                    headers=headers,
                    json={
                        "query": archive_mutation,
                        "variables": {"issueId": issue_id}
                    },
                    timeout=10
                )
                
                if archive_response.status_code == 200:
                    print(f"   ✅ Archived test issue (cleanup)")
                else:
                    print(f"   ⚠️  Couldn't archive test issue (manual cleanup needed)")
                
                return True
            else:
                print(f"   ❌ Failed to create issue: {data}")
                return False
        else:
            print(f"   ❌ HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def verify_linear_integration():
    """Main verification flow."""
    print("=" * 60)
    print("LINEAR INTEGRATION VERIFICATION")
    print("=" * 60)
    
    # Load config
    print("\n📄 Loading configuration...")
    try:
        config = AASConfig()
        
        if not config.linear_api_key:
            print("   ❌ LINEAR_API_KEY not set in .env")
            print("\n💡 Add to .env:")
            print("   LINEAR_API_KEY=lin_api_your-key-here")
            print("   LINEAR_TEAM_ID=your-team-id")
            return 1
        
        print("   ✅ Configuration loaded")
        
    except Exception as e:
        print(f"   ❌ Config error: {e}")
        return 1
    
    # Verify API key
    api_key = config.linear_api_key.get_secret_value()
    if not verify_api_key(api_key):
        print("\n❌ API key verification failed")
        print("💡 Get a new key: https://linear.app/settings/api")
        return 1
    
    # Get teams
    teams = get_teams(api_key)
    if not teams:
        print("\n❌ No teams found or error fetching teams")
        return 1
    
    # Use configured team or first available
    if config.linear_team_id and config.linear_team_id != "your-team-id-here":
        team_id = config.linear_team_id
    else:
        team_id = teams[0]["id"]
    
    team_name = next((t["name"] for t in teams if t["id"] == team_id), "Unknown")
    
    if not config.linear_team_id or config.linear_team_id == "your-team-id-here":
        print(f"\n⚠️  LINEAR_TEAM_ID not configured, using detected team: {team_name}")
        print(f"💡 Add to .env: LINEAR_TEAM_ID={team_id}")
    else:
        print(f"\n✅ Using configured team: {team_name} ({team_id})")
    
    # Test issue creation/archival
    if not test_issue_creation(api_key, team_id):
        print("\n❌ Issue operations failed")
        return 1
    
    # Test LinearSync class
    print("\n🔧 Testing LinearSync class...")
    try:
        linear_sync = LinearSync(config.linear_api_key)
        print("   ✅ LinearSync initialized")
        
        # Try fetching active tasks
        tasks = linear_sync.get_active_tasks(team_id)
        print(f"   ✅ Fetched active tasks: {len(tasks)} task(s)")
        
    except Exception as e:
        print(f"   ❌ LinearSync error: {e}")
        return 1
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)
    print("✅ Linear integration is working correctly!")
    print("\n📚 Next steps:")
    print("   1. Install Linear GitHub App (see .github/LINEAR_INTEGRATION.md)")
    print("   2. Configure bidirectional sync in Linear settings")
    print("   3. Test by creating a commit with 'AAS-XXX: Description'")
    print("   4. Verify sync with: python scripts/test_gitkraken.py")
    
    return 0


if __name__ == "__main__":
    exit_code = verify_linear_integration()
    sys.exit(exit_code)
