# Team Project Planner API

A REST API for managing team project planning with users, teams, and project boards built with FastAPI and SQLite.

## Overview

This project implements a comprehensive team project planner tool that provides APIs for:
- **User Management**: Create, update, list, and describe users
- **Team Management**: Create teams, manage team membership, and handle team operations
- **Project Board Management**: Create boards, manage tasks, track progress, and export board data

## Architecture & Design Decisions

### Technology Stack
- **FastAPI**: Modern, fast web framework for building APIs with Python
- **SQLite**: Lightweight, file-based database for data persistence
- **Pydantic**: Data validation and serialization using Python type annotations
- **Uvicorn**: ASGI server for running the FastAPI application

### Design Principles
1. **Clean Architecture**: Separation of concerns with distinct layers (database, services, API)
2. **Extensibility**: Abstract base classes allow for easy extension and testing
3. **Type Safety**: Full type annotations and Pydantic models for request/response validation
4. **Error Handling**: Comprehensive exception handling with appropriate HTTP status codes
5. **Data Integrity**: SQLite constraints ensure data consistency and referential integrity

### Database Schema
- **Users**: Store user information with unique names and display names
- **Teams**: Manage teams with admins and descriptions
- **Team Members**: Many-to-many relationship between users and teams
- **Boards**: Project boards associated with teams
- **Tasks**: Individual tasks assigned to users within boards

### Key Implementation Choices

#### File-based SQLite Database
- **Rationale**: Provides ACID compliance and relational data integrity while maintaining simplicity
- **Location**: All data stored in `db/factwise.db`
- **Benefits**: No external database setup required, supports complex queries, built-in constraint checking

#### Service Layer Pattern
- **Rationale**: Separates business logic from API endpoints for better testability and maintainability
- **Implementation**: Concrete service classes inherit from provided base classes
- **Benefits**: Clear separation of concerns, easy to unit test, follows SOLID principles

#### FastAPI with Automatic Documentation
- **Rationale**: Provides automatic OpenAPI documentation and request validation
- **Benefits**: Self-documenting API, built-in validation, excellent performance
- **Documentation**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)

#### Comprehensive Error Handling
- **Validation Errors**: Return 400 status with detailed error messages
- **Database Errors**: Return 500 status with appropriate error handling
- **Business Logic Constraints**: Enforced at both database and application levels

## Features

### User Management
- Create users with unique names (max 64 chars) and display names (max 64 chars)
- List all users with creation timestamps
- Get detailed user information
- Update user display names (names are immutable)
- View teams associated with a user

### Team Management
- Create teams with unique names, descriptions, and admin users
- List all teams with admin information
- Update team details including changing admins
- Add/remove users from teams (max 50 users per team)
- Prevent removal of team admins
- List all users in a team

### Project Board Management
- Create boards with unique names per team
- Add tasks to open boards with user assignments
- Update task status (OPEN → IN_PROGRESS → COMPLETE)
- Close boards only when all tasks are complete
- List open boards for a team
- Export board data to formatted text files

### Data Export
- Creative board export feature generates human-readable reports
- Includes board metadata, task details, and user assignments
- Files saved to `out/` directory with timestamps

## API Endpoints

### Users
- `POST /users` - Create a new user
- `GET /users` - List all users
- `GET /users/{user_id}` - Get user details
- `PUT /users/{user_id}` - Update user
- `GET /users/{user_id}/teams` - Get user's teams

### Teams
- `POST /teams` - Create a new team
- `GET /teams` - List all teams
- `GET /teams/{team_id}` - Get team details
- `PUT /teams/{team_id}` - Update team
- `POST /teams/{team_id}/users` - Add users to team
- `DELETE /teams/{team_id}/users` - Remove users from team
- `GET /teams/{team_id}/users` - List team users

### Boards & Tasks
- `POST /teams/{team_id}/boards` - Create a board
- `GET /teams/{team_id}/boards` - List team boards
- `PUT /boards/{board_id}/close` - Close a board
- `POST /boards/{board_id}/tasks` - Add task to board
- `PUT /tasks/{task_id}/status` - Update task status
- `POST /boards/{board_id}/export` - Export board

### Utility
- `GET /health` - Health check
- `GET /` - API information

## Installation & Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**:
   ```bash
   python main.py
   ```
   or
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

3. **Access the API**:
   - API Base URL: `http://localhost:8000`
   - Interactive Documentation: `http://localhost:8000/docs`
   - Alternative Documentation: `http://localhost:8000/redoc`

## Data Constraints & Validation

### User Constraints
- Names must be unique and ≤ 64 characters
- Display names ≤ 64 characters (≤ 128 for updates)
- Names cannot be updated after creation

### Team Constraints
- Team names must be unique and ≤ 64 characters
- Descriptions ≤ 128 characters
- Maximum 50 users per team
- Team admins cannot be removed from teams

### Board & Task Constraints
- Board names must be unique per team and ≤ 64 characters
- Task titles must be unique per board and ≤ 64 characters
- Tasks can only be added to open boards
- Boards can only be closed when all tasks are complete
- Valid task statuses: OPEN, IN_PROGRESS, COMPLETE

## Project Structure

```
factwise-python/
├── __init__.py
├── main.py                 # FastAPI application with REST endpoints
├── services.py             # Concrete service implementations
├── database.py             # SQLite database setup and utilities
├── user_base.py           # User management base class
├── team_base.py           # Team management base class
├── project_board_base.py  # Board management base class
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── db/                   # Database files (auto-created)
│   └── project_planner.db      # SQLite database
└── out/                 # Board export files (auto-created)
```

## Error Handling

The application implements comprehensive error handling:
- **Input Validation**: Pydantic models validate request data structure
- **Business Rules**: Service layer enforces business constraints
- **Database Integrity**: SQLite constraints ensure data consistency
- **HTTP Status Codes**: Appropriate codes for different error types (400, 500)
- **Error Messages**: Detailed, user-friendly error descriptions

## Performance Considerations

- **Database Indexing**: Unique constraints on critical fields provide automatic indexing
- **Connection Management**: Context managers ensure proper connection cleanup
- **JSON Processing**: Efficient JSON serialization/deserialization
- **Query Optimization**: Minimal database queries with proper JOIN operations

## Assumptions & Design Decisions

1. **Team-Board Relationship**: One team manages one project board (simplified model)
2. **User IDs**: Auto-incrementing integer IDs for simplicity
3. **Timestamp Format**: ISO 8601 format for cross-platform compatibility
4. **File Export**: Text format chosen for maximum compatibility and readability
5. **Admin Privileges**: Team admins are automatically team members
6. **Task Assignment**: Tasks must be assigned to specific users (no unassigned tasks)

