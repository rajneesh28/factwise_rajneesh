from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Dict
import json
import uvicorn

from services import UserService, TeamService, ProjectBoardService
from database import ValidationError, DatabaseError

# Initialize FastAPI app
app = FastAPI(
    title="Team Project Planner API",
    description="A REST API for managing team project planning with users, teams, and project boards",
    version="1.0.0"
)

# Initialize service instances
user_service = UserService()
team_service = TeamService()
board_service = ProjectBoardService()


# Exception handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=400,
        content={"error": "Validation Error", "detail": str(exc)}
    )


@app.exception_handler(DatabaseError)
async def database_exception_handler(request: Request, exc: DatabaseError):
    return JSONResponse(
        status_code=500,
        content={"error": "Database Error", "detail": str(exc)}
    )


# Helper function to handle JSON string responses
def parse_service_response(response: str) -> Dict[Any, Any]:
    """Parse JSON string response from services"""
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid response format from service")


# Pydantic models for request validation
class CreateUserRequest(BaseModel):
    name: str
    display_name: str


class UpdateUserRequest(BaseModel):
    user: Dict[str, str]


class CreateTeamRequest(BaseModel):
    name: str
    description: str
    admin: str


class UpdateTeamRequest(BaseModel):
    team: Dict[str, Any]


class AddUsersToTeamRequest(BaseModel):
    users: list


class CreateBoardRequest(BaseModel):
    name: str
    description: str
    creation_time: str = None


class AddTaskRequest(BaseModel):
    title: str
    description: str
    user_id: str
    creation_time: str = None


class UpdateTaskStatusRequest(BaseModel):
    status: str


# User endpoints
@app.post("/users", summary="Create a new user")
async def create_user(request: CreateUserRequest):
    """Create a new user with name and display_name"""
    request_json = request.json()
    response = user_service.create_user(request_json)
    return parse_service_response(response)


@app.get("/users", summary="List all users")
async def list_users():
    """Get a list of all users"""
    response = user_service.list_users()
    return parse_service_response(response)


@app.get("/users/{user_id}", summary="Get user details")
async def describe_user(user_id: str):
    """Get detailed information about a specific user"""
    request_json = json.dumps({"id": user_id})
    response = user_service.describe_user(request_json)
    return parse_service_response(response)


@app.put("/users/{user_id}", summary="Update user")
async def update_user(user_id: str, request: UpdateUserRequest):
    """Update user information (only display_name can be updated)"""
    request_data = {"id": user_id, "user": request.user}
    request_json = json.dumps(request_data)
    response = user_service.update_user(request_json)
    return parse_service_response(response)


@app.get("/users/{user_id}/teams", summary="Get user's teams")
async def get_user_teams(user_id: str):
    """Get all teams that a user belongs to"""
    request_json = json.dumps({"id": user_id})
    response = user_service.get_user_teams(request_json)
    return parse_service_response(response)


# Team endpoints
@app.post("/teams", summary="Create a new team")
async def create_team(request: CreateTeamRequest):
    """Create a new team with name, description, and admin"""
    request_json = request.json()
    response = team_service.create_team(request_json)
    return parse_service_response(response)


@app.get("/teams", summary="List all teams")
async def list_teams():
    """Get a list of all teams"""
    response = team_service.list_teams()
    return parse_service_response(response)


@app.get("/teams/{team_id}", summary="Get team details")
async def describe_team(team_id: str):
    """Get detailed information about a specific team"""
    request_json = json.dumps({"id": team_id})
    response = team_service.describe_team(request_json)
    return parse_service_response(response)


@app.put("/teams/{team_id}", summary="Update team")
async def update_team(team_id: str, request: UpdateTeamRequest):
    """Update team information"""
    request_data = {"id": team_id, "team": request.team}
    request_json = json.dumps(request_data)
    response = team_service.update_team(request_json)
    return parse_service_response(response)


@app.post("/teams/{team_id}/users", summary="Add users to team")
async def add_users_to_team(team_id: str, request: AddUsersToTeamRequest):
    """Add users to a team"""
    request_data = {"id": team_id, "users": request.users}
    request_json = json.dumps(request_data)
    response = team_service.add_users_to_team(request_json)
    return parse_service_response(response)


@app.delete("/teams/{team_id}/users", summary="Remove users from team")
async def remove_users_from_team(team_id: str, request: AddUsersToTeamRequest):
    """Remove users from a team"""
    request_data = {"id": team_id, "users": request.users}
    request_json = json.dumps(request_data)
    response = team_service.remove_users_from_team(request_json)
    return parse_service_response(response)


@app.get("/teams/{team_id}/users", summary="List team users")
async def list_team_users(team_id: str):
    """Get all users in a team"""
    request_json = json.dumps({"id": team_id})
    response = team_service.list_team_users(request_json)
    return parse_service_response(response)


# Board endpoints
@app.post("/teams/{team_id}/boards", summary="Create a new board")
async def create_board(team_id: str, request: CreateBoardRequest):
    """Create a new board for a team"""
    request_data = {
        "name": request.name,
        "description": request.description,
        "team_id": team_id
    }
    # Only include creation_time if it's provided
    if request.creation_time:
        request_data["creation_time"] = request.creation_time
    
    request_json = json.dumps(request_data)
    response = board_service.create_board(request_json)
    return parse_service_response(response)


@app.get("/teams/{team_id}/boards", summary="List team boards")
async def list_boards(team_id: str):
    """Get all open boards for a team"""
    request_json = json.dumps({"id": team_id})
    response = board_service.list_boards(request_json)
    return parse_service_response(response)


@app.put("/boards/{board_id}/close", summary="Close a board")
async def close_board(board_id: str):
    """Close a board (only possible if all tasks are complete)"""
    request_json = json.dumps({"id": board_id})
    response = board_service.close_board(request_json)
    return parse_service_response(response)


@app.post("/boards/{board_id}/tasks", summary="Add task to board")
async def add_task(board_id: str, request: AddTaskRequest):
    """Add a new task to a board"""
    request_data = {
        "title": request.title,
        "description": request.description,
        "user_id": request.user_id,
        "board_id": board_id
    }
    # Only include creation_time if it's provided
    if request.creation_time:
        request_data["creation_time"] = request.creation_time
    
    request_json = json.dumps(request_data)
    response = board_service.add_task(request_json)
    return parse_service_response(response)


@app.put("/tasks/{task_id}/status", summary="Update task status")
async def update_task_status(task_id: str, request: UpdateTaskStatusRequest):
    """Update the status of a task (OPEN, IN_PROGRESS, COMPLETE)"""
    request_data = {"id": task_id, "status": request.status}
    request_json = json.dumps(request_data)
    response = board_service.update_task_status(request_json)
    return parse_service_response(response)


@app.post("/boards/{board_id}/export", summary="Export board")
async def export_board(board_id: str):
    """Export a board to a text file"""
    request_json = json.dumps({"id": board_id})
    response = board_service.export_board(request_json)
    return parse_service_response(response)


# Health check endpoint
@app.get("/health", summary="Health check")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "message": "Team Project Planner API is running"}


# Root endpoint
@app.get("/", summary="API Information")
async def root():
    """Get API information"""
    return {
        "message": "Welcome to Team Project Planner API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 