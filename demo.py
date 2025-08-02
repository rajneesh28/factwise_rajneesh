#!/usr/bin/env python3
"""
Demo script for Team Project Planner API

This script demonstrates the basic functionality of the API by creating
sample users, teams, boards, and tasks. It's useful for testing and
understanding how the API works.

Run this script after starting the API server:
1. python main.py (in one terminal)
2. python demo.py (in another terminal)
"""

import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:8000"

def pretty_print(response):
    """Pretty print JSON response"""
    print(json.dumps(response, indent=2))

def demo_users():
    """Demonstrate user management"""
    print("\n" + "="*50)
    print("DEMO: User Management")
    print("="*50)
    
    # Create users
    users_data = [
        {"name": "john_doe", "display_name": "John Doe"},
        {"name": "jane_smith", "display_name": "Jane Smith"},
        {"name": "bob_wilson", "display_name": "Bob Wilson"},
        {"name": "alice_brown", "display_name": "Alice Brown"}
    ]
    
    user_ids = []
    for user_data in users_data:
        print(f"\nCreating user: {user_data['display_name']}")
        response = requests.post(f"{BASE_URL}/users", json=user_data)
        if response.status_code == 200:
            result = response.json()
            user_ids.append(result['id'])
            print(f"✓ Created user with ID: {result['id']}")
        else:
            print(f"✗ Error: {response.text}")
    
    # List all users
    print(f"\n📋 Listing all users:")
    response = requests.get(f"{BASE_URL}/users")
    if response.status_code == 200:
        users = response.json()
        for user in users:
            print(f"  - {user['name']} ({user['display_name']})")
    
    # Update a user
    if user_ids:
        print(f"\n✏️  Updating user {user_ids[0]}:")
        update_data = {"user": {"display_name": "John Doe (Senior Developer)"}}
        response = requests.put(f"{BASE_URL}/users/{user_ids[0]}", json=update_data)
        if response.status_code == 200:
            print("✓ User updated successfully")
        
        # Show updated user details
        response = requests.get(f"{BASE_URL}/users/{user_ids[0]}")
        if response.status_code == 200:
            user_details = response.json()
            print(f"  Updated display name: {user_details['description']}")
    
    return user_ids

def demo_teams(user_ids):
    """Demonstrate team management"""
    print("\n" + "="*50)
    print("DEMO: Team Management")
    print("="*50)
    
    if not user_ids:
        print("No users available for team demo")
        return []
    
    # Create teams
    teams_data = [
        {
            "name": "Frontend Team", 
            "description": "Responsible for UI/UX development",
            "admin": user_ids[0]
        },
        {
            "name": "Backend Team",
            "description": "Responsible for server-side development", 
            "admin": user_ids[1]
        }
    ]
    
    team_ids = []
    for team_data in teams_data:
        print(f"\nCreating team: {team_data['name']}")
        response = requests.post(f"{BASE_URL}/teams", json=team_data)
        if response.status_code == 200:
            result = response.json()
            team_ids.append(result['id'])
            print(f"✓ Created team with ID: {result['id']}")
        else:
            print(f"✗ Error: {response.text}")
    
    # Add users to teams
    if team_ids and len(user_ids) >= 4:
        print(f"\n👥 Adding users to teams:")
        
        # Add users to first team
        add_users_data = {"users": [user_ids[2], user_ids[3]]}
        response = requests.post(f"{BASE_URL}/teams/{team_ids[0]}/users", json=add_users_data)
        if response.status_code == 200:
            print(f"✓ Added users to {teams_data[0]['name']}")
        
        # List team members
        response = requests.get(f"{BASE_URL}/teams/{team_ids[0]}/users")
        if response.status_code == 200:
            members = response.json()
            print(f"  Members of {teams_data[0]['name']}:")
            for member in members:
                print(f"    - {member['name']} ({member['display_name']})")
    
    # List all teams
    print(f"\n📋 Listing all teams:")
    response = requests.get(f"{BASE_URL}/teams")
    if response.status_code == 200:
        teams = response.json()
        for team in teams:
            print(f"  - {team['name']}: {team['description']}")
    
    return team_ids

def demo_boards_and_tasks(team_ids, user_ids):
    """Demonstrate board and task management"""
    print("\n" + "="*50)
    print("DEMO: Board and Task Management")
    print("="*50)
    
    if not team_ids or not user_ids:
        print("No teams or users available for board demo")
        return
    
    # Create boards
    boards_data = [
        {
            "name": "Website Redesign",
            "description": "Complete redesign of company website"
        },
        {
            "name": "Mobile App MVP",
            "description": "Minimum viable product for mobile application"
        }
    ]
    
    board_ids = []
    for i, board_data in enumerate(boards_data):
        if i < len(team_ids):
            print(f"\nCreating board: {board_data['name']}")
            response = requests.post(f"{BASE_URL}/teams/{team_ids[i]}/boards", json=board_data)
            if response.status_code == 200:
                result = response.json()
                board_ids.append(result['id'])
                print(f"✓ Created board with ID: {result['id']}")
            else:
                print(f"✗ Error: {response.text}")
    
    # Add tasks to boards
    if board_ids and user_ids:
        tasks_data = [
            {"title": "Design mockups", "description": "Create UI mockups for main pages", "user_id": user_ids[0]},
            {"title": "Setup development environment", "description": "Configure local dev environment", "user_id": user_ids[1]},
            {"title": "Implement homepage", "description": "Code the new homepage design", "user_id": user_ids[2]},
            {"title": "User authentication", "description": "Implement user login/register", "user_id": user_ids[1]}
        ]
        
        task_ids = []
        for i, task_data in enumerate(tasks_data):
            board_id = board_ids[i % len(board_ids)]
            print(f"\nAdding task '{task_data['title']}' to board {board_id}")
            response = requests.post(f"{BASE_URL}/boards/{board_id}/tasks", json=task_data)
            if response.status_code == 200:
                result = response.json()
                task_ids.append(result['id'])
                print(f"✓ Created task with ID: {result['id']}")
            else:
                print(f"✗ Error: {response.text}")
        
        # Update task statuses
        if task_ids:
            print(f"\n📝 Updating task statuses:")
            statuses = ["IN_PROGRESS", "COMPLETE", "IN_PROGRESS", "OPEN"]
            for i, task_id in enumerate(task_ids[:len(statuses)]):
                status_data = {"status": statuses[i]}
                response = requests.put(f"{BASE_URL}/tasks/{task_id}/status", json=status_data)
                if response.status_code == 200:
                    print(f"✓ Updated task {task_id} status to {statuses[i]}")
        
        # Export a board
        if board_ids:
            print(f"\n📤 Exporting board {board_ids[0]}:")
            response = requests.post(f"{BASE_URL}/boards/{board_ids[0]}/export")
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Board exported to: {result['out_file']}")
            else:
                print(f"✗ Error: {response.text}")
    
    # List boards for team
    if team_ids:
        print(f"\n📋 Listing boards for team {team_ids[0]}:")
        response = requests.get(f"{BASE_URL}/teams/{team_ids[0]}/boards")
        if response.status_code == 200:
            boards = response.json()
            for board in boards:
                print(f"  - {board['name']} (ID: {board['id']})")

def demo_error_handling():
    """Demonstrate error handling"""
    print("\n" + "="*50)
    print("DEMO: Error Handling")
    print("="*50)
    
    # Try to create user with duplicate name
    print("\n🚫 Testing duplicate user name:")
    user_data = {"name": "john_doe", "display_name": "Another John"}
    response = requests.post(f"{BASE_URL}/users", json=user_data)
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error (expected): {response.json()}")
    
    # Try to access non-existent user
    print("\n🚫 Testing non-existent user:")
    response = requests.get(f"{BASE_URL}/users/99999")
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error (expected): {response.json()}")
    
    # Try invalid JSON
    print("\n🚫 Testing invalid request data:")
    response = requests.post(f"{BASE_URL}/users", json={"name": ""})  # Empty name
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error (expected): {response.json()}")

def main():
    """Run the complete demo"""
    print("🚀 Starting Team Project Planner API Demo")
    print("Make sure the API server is running on http://localhost:8000")
    
    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✓ API server is running")
        else:
            print("✗ API server health check failed")
            return
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to API server. Make sure it's running on port 8000")
        return
    
    # Run demos
    user_ids = demo_users()
    team_ids = demo_teams(user_ids)
    demo_boards_and_tasks(team_ids, user_ids)
    demo_error_handling()
    
    print("\n" + "="*50)
    print("🎉 Demo completed successfully!")
    print("="*50)
    print("\n📚 To explore more:")
    print("  - Visit http://localhost:8000/docs for interactive API documentation")
    print("  - Check the 'out/' directory for exported board files")
    print("  - Use the API endpoints to build your own applications")

if __name__ == "__main__":
    main() 