import sqlite3
import os
from typing import List, Dict, Any
from user_base import UserBase
from team_base import TeamBase
from project_board_base import ProjectBoardBase
from database import (
    db, DatabaseError, ValidationError, 
    get_current_timestamp, validate_json_input, format_json_response
)


class UserService(UserBase):
    """Concrete implementation of UserBase using SQLite database"""
    
    def create_user(self, request: str) -> str:
        """Create a new user"""
        try:
            data = validate_json_input(request)
            
            # Validate required fields
            if 'name' not in data or 'display_name' not in data:
                raise ValidationError("Missing required fields: name, display_name")
            
            name = data['name'].strip()
            display_name = data['display_name'].strip()
            
            # Validate constraints
            if len(name) > 64:
                raise ValidationError("Name cannot exceed 64 characters")
            if len(display_name) > 64:
                raise ValidationError("Display name cannot exceed 64 characters")
            if not name:
                raise ValidationError("Name cannot be empty")
            if not display_name:
                raise ValidationError("Display name cannot be empty")
            
            creation_time = get_current_timestamp()
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        "INSERT INTO users (name, display_name, creation_time) VALUES (?, ?, ?)",
                        (name, display_name, creation_time)
                    )
                    user_id = cursor.lastrowid
                    conn.commit()
                    
                    return format_json_response({"id": str(user_id)})
                
                except sqlite3.IntegrityError as e:
                    if "UNIQUE constraint failed" in str(e):
                        raise ValidationError("User name must be unique")
                    raise DatabaseError(f"Database error: {e}")
                    
        except ValidationError as e:
            raise e
        except Exception as e:
            raise DatabaseError(f"Error creating user: {e}")
    
    def list_users(self) -> str:
        """List all users"""
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name, display_name, creation_time FROM users ORDER BY creation_time"
                )
                users = []
                for row in cursor.fetchall():
                    users.append({
                        "name": row['name'],
                        "display_name": row['display_name'],
                        "creation_time": row['creation_time']
                    })
                
                return format_json_response(users)
                
        except Exception as e:
            raise DatabaseError(f"Error listing users: {e}")
    
    def describe_user(self, request: str) -> str:
        """Get user details by ID"""
        try:
            data = validate_json_input(request)
            
            if 'id' not in data:
                raise ValidationError("Missing required field: id")
            
            user_id = data['id']
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name, display_name, creation_time FROM users WHERE id = ?",
                    (user_id,)
                )
                row = cursor.fetchone()
                
                if not row:
                    raise ValidationError("User not found")
                
                user_info = {
                    "name": row['name'],
                    "description": row['display_name'],  # Using display_name as description
                    "creation_time": row['creation_time']
                }
                
                return format_json_response(user_info)
                
        except ValidationError as e:
            raise e
        except Exception as e:
            raise DatabaseError(f"Error describing user: {e}")
    
    def update_user(self, request: str) -> str:
        """Update user details"""
        try:
            data = validate_json_input(request)
            
            if 'id' not in data or 'user' not in data:
                raise ValidationError("Missing required fields: id, user")
            
            user_id = data['id']
            user_data = data['user']
            
            if 'display_name' not in user_data:
                raise ValidationError("Missing required field: display_name in user object")
            
            display_name = user_data['display_name'].strip()
            
            # Validate constraints
            if len(display_name) > 128:
                raise ValidationError("Display name cannot exceed 128 characters")
            if not display_name:
                raise ValidationError("Display name cannot be empty")
            
            # Note: name cannot be updated as per constraint
            if 'name' in user_data:
                raise ValidationError("User name cannot be updated")
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if user exists
                cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
                if not cursor.fetchone():
                    raise ValidationError("User not found")
                
                cursor.execute(
                    "UPDATE users SET display_name = ? WHERE id = ?",
                    (display_name, user_id)
                )
                conn.commit()
                
                return format_json_response({"status": "success"})
                
        except ValidationError as e:
            raise e
        except Exception as e:
            raise DatabaseError(f"Error updating user: {e}")
    
    def get_user_teams(self, request: str) -> str:
        """Get teams for a specific user"""
        try:
            data = validate_json_input(request)
            
            if 'id' not in data:
                raise ValidationError("Missing required field: id")
            
            user_id = data['id']
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if user exists
                cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
                if not cursor.fetchone():
                    raise ValidationError("User not found")
                
                # Get teams where user is a member or admin
                cursor.execute('''
                    SELECT DISTINCT t.name, t.description, t.creation_time
                    FROM teams t
                    LEFT JOIN team_members tm ON t.id = tm.team_id
                    WHERE t.admin_id = ? OR tm.user_id = ?
                    ORDER BY t.creation_time
                ''', (user_id, user_id))
                
                teams = []
                for row in cursor.fetchall():
                    teams.append({
                        "name": row['name'],
                        "description": row['description'] or "",
                        "creation_time": row['creation_time']
                    })
                
                return format_json_response(teams)
                
        except ValidationError as e:
            raise e
        except Exception as e:
            raise DatabaseError(f"Error getting user teams: {e}")


class TeamService(TeamBase):
    """Concrete implementation of TeamBase using SQLite database"""
    
    def create_team(self, request: str) -> str:
        """Create a new team"""
        try:
            data = validate_json_input(request)
            
            # Validate required fields
            if 'name' not in data or 'description' not in data or 'admin' not in data:
                raise ValidationError("Missing required fields: name, description, admin")
            
            name = data['name'].strip()
            description = data['description'].strip()
            admin_id = data['admin']
            
            # Validate constraints
            if len(name) > 64:
                raise ValidationError("Name cannot exceed 64 characters")
            if len(description) > 128:
                raise ValidationError("Description cannot exceed 128 characters")
            if not name:
                raise ValidationError("Name cannot be empty")
            
            creation_time = get_current_timestamp()
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if admin user exists
                cursor.execute("SELECT id FROM users WHERE id = ?", (admin_id,))
                if not cursor.fetchone():
                    raise ValidationError("Admin user not found")
                
                try:
                    cursor.execute(
                        "INSERT INTO teams (name, description, admin_id, creation_time) VALUES (?, ?, ?, ?)",
                        (name, description, admin_id, creation_time)
                    )
                    team_id = cursor.lastrowid
                    
                    # Add admin as team member
                    cursor.execute(
                        "INSERT INTO team_members (team_id, user_id) VALUES (?, ?)",
                        (team_id, admin_id)
                    )
                    
                    conn.commit()
                    return format_json_response({"id": str(team_id)})
                
                except sqlite3.IntegrityError as e:
                    if "UNIQUE constraint failed" in str(e):
                        raise ValidationError("Team name must be unique")
                    raise DatabaseError(f"Database error: {e}")
                    
        except ValidationError as e:
            raise e
        except Exception as e:
            raise DatabaseError(f"Error creating team: {e}")
    
    def list_teams(self) -> str:
        """List all teams"""
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name, description, creation_time, admin_id FROM teams ORDER BY creation_time"
                )
                teams = []
                for row in cursor.fetchall():
                    teams.append({
                        "name": row['name'],
                        "description": row['description'] or "",
                        "creation_time": row['creation_time'],
                        "admin": str(row['admin_id'])
                    })
                
                return format_json_response(teams)
                
        except Exception as e:
            raise DatabaseError(f"Error listing teams: {e}")
    
    def describe_team(self, request: str) -> str:
        """Get team details by ID"""
        try:
            data = validate_json_input(request)
            
            if 'id' not in data:
                raise ValidationError("Missing required field: id")
            
            team_id = data['id']
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name, description, creation_time, admin_id FROM teams WHERE id = ?",
                    (team_id,)
                )
                row = cursor.fetchone()
                
                if not row:
                    raise ValidationError("Team not found")
                
                team_info = {
                    "name": row['name'],
                    "description": row['description'] or "",
                    "creation_time": row['creation_time'],
                    "admin": str(row['admin_id'])
                }
                
                return format_json_response(team_info)
                
        except ValidationError as e:
            raise e
        except Exception as e:
            raise DatabaseError(f"Error describing team: {e}")
    
    def update_team(self, request: str) -> str:
        """Update team details"""
        try:
            data = validate_json_input(request)
            
            if 'id' not in data or 'team' not in data:
                raise ValidationError("Missing required fields: id, team")
            
            team_id = data['id']
            team_data = data['team']
            
            # Build update query dynamically based on provided fields
            update_fields = []
            update_values = []
            
            if 'name' in team_data:
                name = team_data['name'].strip()
                if len(name) > 64:
                    raise ValidationError("Name cannot exceed 64 characters")
                if not name:
                    raise ValidationError("Name cannot be empty")
                update_fields.append("name = ?")
                update_values.append(name)
            
            if 'description' in team_data:
                description = team_data['description'].strip()
                if len(description) > 128:
                    raise ValidationError("Description cannot exceed 128 characters")
                update_fields.append("description = ?")
                update_values.append(description)
            
            if 'admin' in team_data:
                admin_id = team_data['admin']
                update_fields.append("admin_id = ?")
                update_values.append(admin_id)
            
            if not update_fields:
                raise ValidationError("No valid fields to update")
            
            update_values.append(team_id)
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if team exists
                cursor.execute("SELECT id FROM teams WHERE id = ?", (team_id,))
                if not cursor.fetchone():
                    raise ValidationError("Team not found")
                
                # If updating admin, check if user exists
                if 'admin' in team_data:
                    cursor.execute("SELECT id FROM users WHERE id = ?", (team_data['admin'],))
                    if not cursor.fetchone():
                        raise ValidationError("Admin user not found")
                
                try:
                    query = f"UPDATE teams SET {', '.join(update_fields)} WHERE id = ?"
                    cursor.execute(query, update_values)
                    conn.commit()
                    
                    return format_json_response({"status": "success"})
                
                except sqlite3.IntegrityError as e:
                    if "UNIQUE constraint failed" in str(e):
                        raise ValidationError("Team name must be unique")
                    raise DatabaseError(f"Database error: {e}")
                    
        except ValidationError as e:
            raise e
        except Exception as e:
            raise DatabaseError(f"Error updating team: {e}")
    
    def add_users_to_team(self, request: str):
        """Add users to a team"""
        try:
            data = validate_json_input(request)
            
            if 'id' not in data or 'users' not in data:
                raise ValidationError("Missing required fields: id, users")
            
            team_id = data['id']
            user_ids = data['users']
            
            if not isinstance(user_ids, list):
                raise ValidationError("Users must be a list")
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if team exists
                cursor.execute("SELECT id FROM teams WHERE id = ?", (team_id,))
                if not cursor.fetchone():
                    raise ValidationError("Team not found")
                
                # Check current team size
                cursor.execute("SELECT COUNT(*) FROM team_members WHERE team_id = ?", (team_id,))
                current_size = cursor.fetchone()[0]
                
                if current_size + len(user_ids) > 50:
                    raise ValidationError("Cannot exceed maximum team size of 50 users")
                
                # Validate all users exist before adding any
                for user_id in user_ids:
                    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
                    if not cursor.fetchone():
                        raise ValidationError(f"User {user_id} not found")
                
                # Add users to team
                for user_id in user_ids:
                    try:
                        cursor.execute(
                            "INSERT INTO team_members (team_id, user_id) VALUES (?, ?)",
                            (team_id, user_id)
                        )
                    except sqlite3.IntegrityError:
                        # User already in team, skip
                        pass
                
                conn.commit()
                return format_json_response({"status": "success"})
                
        except ValidationError as e:
            raise e
        except Exception as e:
            raise DatabaseError(f"Error adding users to team: {e}")
    
    def remove_users_from_team(self, request: str):
        """Remove users from a team"""
        try:
            data = validate_json_input(request)
            
            if 'id' not in data or 'users' not in data:
                raise ValidationError("Missing required fields: id, users")
            
            team_id = data['id']
            user_ids = data['users']
            
            if not isinstance(user_ids, list):
                raise ValidationError("Users must be a list")
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if team exists
                cursor.execute("SELECT admin_id FROM teams WHERE id = ?", (team_id,))
                team_row = cursor.fetchone()
                if not team_row:
                    raise ValidationError("Team not found")
                
                admin_id = team_row['admin_id']
                
                # Remove users from team (except admin)
                for user_id in user_ids:
                    if str(user_id) == str(admin_id):
                        raise ValidationError("Cannot remove team admin from team")
                    
                    cursor.execute(
                        "DELETE FROM team_members WHERE team_id = ? AND user_id = ?",
                        (team_id, user_id)
                    )
                
                conn.commit()
                return format_json_response({"status": "success"})
                
        except ValidationError as e:
            raise e
        except Exception as e:
            raise DatabaseError(f"Error removing users from team: {e}")
    
    def list_team_users(self, request: str):
        """List all users in a team"""
        try:
            data = validate_json_input(request)
            
            if 'id' not in data:
                raise ValidationError("Missing required field: id")
            
            team_id = data['id']
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if team exists
                cursor.execute("SELECT id FROM teams WHERE id = ?", (team_id,))
                if not cursor.fetchone():
                    raise ValidationError("Team not found")
                
                cursor.execute('''
                    SELECT u.id, u.name, u.display_name
                    FROM users u
                    INNER JOIN team_members tm ON u.id = tm.user_id
                    WHERE tm.team_id = ?
                    ORDER BY u.name
                ''', (team_id,))
                
                users = []
                for row in cursor.fetchall():
                    users.append({
                        "id": str(row['id']),
                        "name": row['name'],
                        "display_name": row['display_name']
                    })
                
                return format_json_response(users)
                
        except ValidationError as e:
            raise e
        except Exception as e:
            raise DatabaseError(f"Error listing team users: {e}")


class ProjectBoardService(ProjectBoardBase):
    """Concrete implementation of ProjectBoardBase using SQLite database"""
    
    def create_board(self, request: str):
        """Create a new board"""
        try:
            data = validate_json_input(request)
            
            # Validate required fields
            if 'name' not in data or 'description' not in data or 'team_id' not in data:
                raise ValidationError("Missing required fields: name, description, team_id")
            
            name = data['name'].strip()
            description = data['description'].strip()
            team_id = data['team_id']
            
            # Validate constraints
            if len(name) > 64:
                raise ValidationError("Board name cannot exceed 64 characters")
            if len(description) > 128:
                raise ValidationError("Description cannot exceed 128 characters")
            if not name:
                raise ValidationError("Board name cannot be empty")
            
            creation_time = data.get('creation_time', get_current_timestamp())
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if team exists
                cursor.execute("SELECT id FROM teams WHERE id = ?", (team_id,))
                if not cursor.fetchone():
                    raise ValidationError("Team not found")
                
                try:
                    cursor.execute(
                        "INSERT INTO boards (name, description, team_id, creation_time) VALUES (?, ?, ?, ?)",
                        (name, description, team_id, creation_time)
                    )
                    board_id = cursor.lastrowid
                    conn.commit()
                    
                    return format_json_response({"id": str(board_id)})
                
                except sqlite3.IntegrityError as e:
                    if "UNIQUE constraint failed" in str(e):
                        raise ValidationError("Board name must be unique for the team")
                    raise DatabaseError(f"Database error: {e}")
                    
        except ValidationError as e:
            raise e
        except Exception as e:
            raise DatabaseError(f"Error creating board: {e}")
    
    def close_board(self, request: str) -> str:
        """Close a board"""
        try:
            data = validate_json_input(request)
            
            if 'id' not in data:
                raise ValidationError("Missing required field: id")
            
            board_id = data['id']
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if board exists and is open
                cursor.execute("SELECT status FROM boards WHERE id = ?", (board_id,))
                board_row = cursor.fetchone()
                
                if not board_row:
                    raise ValidationError("Board not found")
                
                if board_row['status'] == 'CLOSED':
                    raise ValidationError("Board is already closed")
                
                # Check if all tasks are complete
                cursor.execute(
                    "SELECT COUNT(*) FROM tasks WHERE board_id = ? AND status != 'COMPLETE'",
                    (board_id,)
                )
                incomplete_tasks = cursor.fetchone()[0]
                
                if incomplete_tasks > 0:
                    raise ValidationError("Cannot close board with incomplete tasks")
                
                # Close the board
                end_time = get_current_timestamp()
                cursor.execute(
                    "UPDATE boards SET status = 'CLOSED', end_time = ? WHERE id = ?",
                    (end_time, board_id)
                )
                conn.commit()
                
                return format_json_response({"status": "success"})
                
        except ValidationError as e:
            raise e
        except Exception as e:
            raise DatabaseError(f"Error closing board: {e}")
    
    def add_task(self, request: str) -> str:
        """Add a task to a board"""
        try:
            data = validate_json_input(request)
            
            # Validate required fields
            if 'title' not in data or 'description' not in data or 'user_id' not in data:
                raise ValidationError("Missing required fields: title, description, user_id")
            
            title = data['title'].strip()
            description = data['description'].strip()
            user_id = data['user_id']
            board_id = data.get('board_id')  # This should be provided by the API endpoint
            
            if not board_id:
                raise ValidationError("Board ID is required")
            
            # Validate constraints
            if len(title) > 64:
                raise ValidationError("Task title cannot exceed 64 characters")
            if len(description) > 128:
                raise ValidationError("Description cannot exceed 128 characters")
            if not title:
                raise ValidationError("Task title cannot be empty")
            
            creation_time = data.get('creation_time', get_current_timestamp())
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if board exists and is open
                cursor.execute("SELECT status FROM boards WHERE id = ?", (board_id,))
                board_row = cursor.fetchone()
                
                if not board_row:
                    raise ValidationError("Board not found")
                
                if board_row['status'] != 'OPEN':
                    raise ValidationError("Can only add tasks to open boards")
                
                # Check if user exists
                cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
                if not cursor.fetchone():
                    raise ValidationError("User not found")
                
                try:
                    cursor.execute(
                        "INSERT INTO tasks (title, description, board_id, user_id, creation_time) VALUES (?, ?, ?, ?, ?)",
                        (title, description, board_id, user_id, creation_time)
                    )
                    task_id = cursor.lastrowid
                    conn.commit()
                    
                    return format_json_response({"id": str(task_id)})
                
                except sqlite3.IntegrityError as e:
                    if "UNIQUE constraint failed" in str(e):
                        raise ValidationError("Task title must be unique for the board")
                    raise DatabaseError(f"Database error: {e}")
                    
        except ValidationError as e:
            raise e
        except Exception as e:
            raise DatabaseError(f"Error adding task: {e}")
    
    def update_task_status(self, request: str):
        """Update the status of a task"""
        try:
            data = validate_json_input(request)
            
            if 'id' not in data or 'status' not in data:
                raise ValidationError("Missing required fields: id, status")
            
            task_id = data['id']
            status = data['status']
            
            # Validate status
            valid_statuses = ['OPEN', 'IN_PROGRESS', 'COMPLETE']
            if status not in valid_statuses:
                raise ValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if task exists
                cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
                if not cursor.fetchone():
                    raise ValidationError("Task not found")
                
                cursor.execute(
                    "UPDATE tasks SET status = ? WHERE id = ?",
                    (status, task_id)
                )
                conn.commit()
                
                return format_json_response({"status": "success"})
                
        except ValidationError as e:
            raise e
        except Exception as e:
            raise DatabaseError(f"Error updating task status: {e}")
    
    def list_boards(self, request: str) -> str:
        """List all boards for a team"""
        try:
            data = validate_json_input(request)
            
            if 'id' not in data:
                raise ValidationError("Missing required field: id")
            
            team_id = data['id']
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if team exists
                cursor.execute("SELECT id FROM teams WHERE id = ?", (team_id,))
                if not cursor.fetchone():
                    raise ValidationError("Team not found")
                
                cursor.execute(
                    "SELECT id, name FROM boards WHERE team_id = ? AND status = 'OPEN' ORDER BY creation_time",
                    (team_id,)
                )
                
                boards = []
                for row in cursor.fetchall():
                    boards.append({
                        "id": str(row['id']),
                        "name": row['name']
                    })
                
                return format_json_response(boards)
                
        except ValidationError as e:
            raise e
        except Exception as e:
            raise DatabaseError(f"Error listing boards: {e}")
    
    def export_board(self, request: str) -> str:
        """Export a board to a text file"""
        try:
            data = validate_json_input(request)
            
            if 'id' not in data:
                raise ValidationError("Missing required field: id")
            
            board_id = data['id']
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get board details
                cursor.execute('''
                    SELECT b.name, b.description, b.creation_time, b.status, t.name as team_name
                    FROM boards b
                    JOIN teams t ON b.team_id = t.id
                    WHERE b.id = ?
                ''', (board_id,))
                
                board_row = cursor.fetchone()
                if not board_row:
                    raise ValidationError("Board not found")
                
                # Get board tasks
                cursor.execute('''
                    SELECT t.title, t.description, t.status, t.creation_time, u.name as user_name
                    FROM tasks t
                    JOIN users u ON t.user_id = u.id
                    WHERE t.board_id = ?
                    ORDER BY t.creation_time
                ''', (board_id,))
                
                tasks = cursor.fetchall()
                
                # Create output directory if it doesn't exist
                os.makedirs("out", exist_ok=True)
                
                # Generate filename
                safe_board_name = "".join(c for c in board_row['name'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                filename = f"board_{board_id}_{safe_board_name.replace(' ', '_')}.txt"
                filepath = os.path.join("out", filename)
                
                # Generate board export content
                content = []
                content.append("=" * 60)
                content.append(f"BOARD EXPORT: {board_row['name']}")
                content.append("=" * 60)
                content.append(f"Team: {board_row['team_name']}")
                content.append(f"Description: {board_row['description'] or 'No description'}")
                content.append(f"Status: {board_row['status']}")
                content.append(f"Created: {board_row['creation_time']}")
                content.append("")
                
                if tasks:
                    content.append("TASKS:")
                    content.append("-" * 40)
                    
                    for i, task in enumerate(tasks, 1):
                        content.append(f"{i}. {task['title']}")
                        content.append(f"   Status: {task['status']}")
                        content.append(f"   Assigned to: {task['user_name']}")
                        content.append(f"   Description: {task['description'] or 'No description'}")
                        content.append(f"   Created: {task['creation_time']}")
                        content.append("")
                else:
                    content.append("No tasks in this board.")
                
                content.append("=" * 60)
                content.append(f"Export generated on: {get_current_timestamp()}")
                
                # Write to file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(content))
                
                return format_json_response({"out_file": filename})
                
        except ValidationError as e:
            raise e
        except Exception as e:
            raise DatabaseError(f"Error exporting board: {e}") 