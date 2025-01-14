from flask import request
from app.services.projects import ProjectService
from app.services.tools import ToolService
from app.utils.jwt_utils import decode_jwt
from app.utils.minio_utils import *

class ToolController:
    @staticmethod
    def get_tools(project_id):
        # Extract JWT from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return {"success": False, "error": "Authorization header is missing or invalid"}, 401
        # Decode the JWT to get the user_id
        token = auth_header.split(" ")[1]
        try:
            payload = decode_jwt(token)
            user_id = payload.get("sub")  # 'sub' contains the user ID
        except Exception as e:
            return {"success": False, "error": str(e)}, 401
        # Verify project ownership
        project = ProjectService.get_project_by_id_and_user(project_id, user_id)
        if not project:
            return {"success": False, "error": "Project not found or not owned by user"}, 404
        # Fetch tools for the project
        try:
            tools = ToolService.get_tools_by_project(project_id)
            return {"success": True, "tools": tools}, 200
        except Exception as e:
            return {"success": False, "error": str(e)}, 500
    
    @staticmethod
    def add_tool(project_id):
        # Extract JWT from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return {"success": False, "error": "Authorization header is missing or invalid"}, 401

        # Decode the JWT to get the user_id
        token = auth_header.split(" ")[1]
        try:
            payload = decode_jwt(token)
            user_id = payload.get("sub")  # 'sub' contains the user ID
        except Exception as e:
            return {"success": False, "error": str(e)}, 401

        # Verify project ownership
        project = ProjectService.get_project_by_id_and_user(project_id, user_id)
        if not project:
            return {"success": False, "error": "Project not found or not owned by user"}, 404

        # Validate request data
        data = request.get_json()
        required_fields = ["position", "procedure", "parameters"]
        if not all(field in data for field in required_fields):
            return {"success": False, "error": f"Missing one of the required fields: {required_fields}"}, 400

        # Call the service to add the tool
        try:
            tool = ToolService.create_tool(
                position=data["position"],
                procedure=data["procedure"],
                parameters=data["parameters"],
                project_id=project_id
            )
            return {"success": True, "tool": tool}, 201
        except Exception as e:
            return {"success": False, "error": str(e)}, 500

    @staticmethod
    def update_tool(project_id, tool_id):
        # Extract JWT from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return {"success": False, "error": "Authorization header is missing or invalid"}, 401

        # Decode the JWT to get the user_id
        token = auth_header.split(" ")[1]
        try:
            payload = decode_jwt(token)
            user_id = payload.get("sub")  # 'sub' contains the user ID
        except Exception as e:
            return {"success": False, "error": str(e)}, 401

        # Verify project ownership
        project = ProjectService.get_project_by_id_and_user(project_id, user_id)
        if not project:
            return {"success": False, "error": "Project not found or not owned by user"}, 404

        # Validate request data
        data = request.get_json()
        if not data:
            return {"success": False, "error": "No data provided"}, 400

        # Update the tool
        try:
            updated_tool = ToolService.update_tool(
                tool_id=tool_id,
                project_id=project_id,
                updates=data
            )
            return {"success": True, "tool": updated_tool}, 200
        except Exception as e:
            return {"success": False, "error": str(e)}, 500


    @staticmethod
    def delete_tool(project_id, tool_id):
        # Extract JWT from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return {"success": False, "error": "Authorization header is missing or invalid"}, 401

        # Decode the JWT to get the user_id
        token = auth_header.split(" ")[1]
        try:
            payload = decode_jwt(token)
            user_id = payload.get("sub")  # 'sub' contains the user ID
        except Exception as e:
            return {"success": False, "error": str(e)}, 401

        # Verify project ownership
        project = ProjectService.get_project_by_id_and_user(project_id, user_id)
        if not project:
            return {"success": False, "error": "Project not found or not owned by user"}, 404

        # Delete the tool
        try:
            ToolService.delete_tool(tool_id, project_id)
            return {"success": True, "message": f"Tool '{tool_id}' deleted successfully"}, 200
        except Exception as e:
            return {"success": False, "error": str(e)}, 500
        
    @staticmethod
    def process_project(project_id):
        # Extract JWT from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return {"success": False, "error": "Authorization header is missing or invalid"}, 401

        # Decode the JWT to get the user_id
        token = auth_header.split(" ")[1]
        try:
            payload = decode_jwt(token)
            user_id = payload.get("sub")  # 'sub' contains the user ID
        except Exception as e:
            return {"success": False, "error": str(e)}, 401

        # Verify project ownership
        project = ProjectService.get_project_by_id_and_user(project_id, user_id)
        if not project:
            return {"success": False, "error": "Project not found or not owned by user"}, 404

        # Get tools for the project
        tools = ToolService.get_tools_by_project(project_id)
        if not tools:
            return {"success": False, "error": "No tools defined for this project"}, 400

        # List images in the src bucket
        src_bucket = f"{project_id}-src"
        try:
            images = list_objects_in_bucket(src_bucket)
        except Exception as e:
            return {"success": False, "error": f"Failed to list images: {str(e)}"}, 500

        # Submit tasks for each image and tool
        try:
            for image in images:
                for tool in tools:
                    submit_task(tool, image, project_id)
            return {"success": True, "message": "Project processing triggered successfully"}, 200
        except Exception as e:
            return {"success": False, "error": f"Failed to submit tasks: {str(e)}"}, 500