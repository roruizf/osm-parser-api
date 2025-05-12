# In main.py

# --- Standard Library Imports ---
import tempfile
import os
import shutil

# --- FastAPI and Typing Imports ---
from fastapi import FastAPI, UploadFile, File, Query, BackgroundTasks, HTTPException
from typing import List, Optional, Dict, Any

# --- OpenStudio Import ---
import openstudio

# --- Your Toolkit Imports ---
# === Utility function import ===
try:
    from OpenStudio_Toolkit.utils.osm_utils import load_osm_file_as_model
    print("Successfully imported 'load_osm_file_as_model' from toolkit utils.")
except ImportError:
    print(f"ERROR: Could not import 'load_osm_file_as_model' from OpenStudio_Toolkit.utils.osm_utils.")
    load_osm_file_as_model = None

# === Object parsing function imports ===
# Using the exact function names you provided for the initial three object types
try:
    from OpenStudio_Toolkit.osm_objects.spaces import get_all_space_objects_as_dicts
    from OpenStudio_Toolkit.osm_objects.surfaces import get_all_surface_objects_as_dicts
    from OpenStudio_Toolkit.osm_objects.subsurfaces import get_all_subsurface_objects_as_dicts
    print("Core parsing functions (spaces, surfaces, subsurfaces) imported successfully.")
except ImportError as e:
    print(f"ERROR: Could not import one or more core parsing functions. Error: {e}")
    # Define placeholders if imports fail
    get_all_space_objects_as_dicts = None
    get_all_surface_objects_as_dicts = None
    get_all_subsurface_objects_as_dicts = None


# --- FastAPI Application Setup ---

# Initialize the FastAPI application
app = FastAPI(
    title="OpenStudio OSM Parser API",
    description="API to parse OpenStudio (OSM) files and extract building model information.",
    version="0.1.0",
)

# Define the list of object types your parser will support
# (Update this list based on what your OpenStudio-Toolkit can actually parse)
VALID_OBJECT_TYPES = [
    "spaces",
    "surfaces",
    "subsurfaces"
]

# --- Temporary File Handling Functions ---

def save_temp_file(file_content: bytes, filename: str) -> str:
    """
    Saves uploaded file content to a temporary file with its original extension
    and returns the full path to the temporary file.
    """
    try:
        temp_dir = tempfile.mkdtemp() # Create a temporary directory
        
        # Get the file extension from the original filename
        # Default to .osm if no extension is found
        file_ext = os.path.splitext(filename)[1] if os.path.splitext(filename)[1] else ".osm"
        
        # Construct the temporary file path within the created directory
        # Using a fixed name like 'model' + original extension can be good for OpenStudio
        temp_file_path = os.path.join(temp_dir, f"uploaded_model{file_ext}")
        
        with open(temp_file_path, "wb") as f:
            f.write(file_content)
        print(f"Temporary file saved at: {temp_file_path}") # For logging/debugging
        return temp_file_path
    except Exception as e:
        print(f"Error saving temp file: {e}")
        # Clean up directory if file write failed but dir was created
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise HTTPException(status_code=500, detail=f"Could not save uploaded file: {e}")


def cleanup_temp_file(temp_file_path: str):
    """
    Removes the temporary file and its containing directory.
    Designed to be run as a background task.
    """
    if temp_file_path and os.path.exists(temp_file_path):
        temp_dir = os.path.dirname(temp_file_path)
        try:
            shutil.rmtree(temp_dir) # shutil.rmtree removes a directory and all its contents
            print(f"Cleaned up temporary directory: {temp_dir}") # For logging/debugging
        except Exception as e:
            # Log error, but don't let cleanup failure crash the app or stop response
            print(f"Error cleaning up temp directory {temp_dir}: {e}")
    else:
        print(f"Temporary file/directory not found for cleanup: {temp_file_path}")


# --- API Endpoint Definition ---

@app.post("/parse", summary="Parse OSM File", response_model=Dict[str, Any])
async def parse_osm(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="OpenStudio Model (OSM) file to parse."),
    object_types: Optional[List[str]] = Query(
        default=None,
        description=(
            "List of specific object types to parse (e.g., 'spaces', 'surfaces', 'subsurfaces'). "
            "If not provided or empty, all VALID_OBJECT_TYPES will be attempted."
        )
    )
):
    temp_osm_path: Optional[str] = None
    # Initialize results with None for all defined VALID_OBJECT_TYPES.
    results: Dict[str, Any] = {obj_type: None for obj_type in VALID_OBJECT_TYPES}

    try:
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        

        temp_osm_path = save_temp_file(file_content, file.filename or "model.osm")
        background_tasks.add_task(cleanup_temp_file, temp_osm_path)

        types_to_parse: List[str]
        if not object_types: # If list is empty or None from query
            types_to_parse = VALID_OBJECT_TYPES
        else:
            # Validate requested object types against our now smaller VALID_OBJECT_TYPES list
            invalid_types = [ot for ot in object_types if ot not in VALID_OBJECT_TYPES]
            if invalid_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid object type(s) requested: {', '.join(invalid_types)}. Valid types for this version are: {', '.join(VALID_OBJECT_TYPES)}"
                )
            types_to_parse = object_types
        
        print(f"Object types selected for parsing: {types_to_parse}")

        if not load_osm_file_as_model: # Check if the import for model loader worked
            raise HTTPException(status_code=501, detail="Model loading utility from toolkit is not available (import error).")
        
        try:
            model = load_osm_file_as_model(temp_osm_path)
            print("OpenStudio model loaded successfully.")
        except Exception as e_load:
            print(f"Error loading OpenStudio model: {e_load}")
            raise HTTPException(status_code=400, detail=f"Failed to load/translate OpenStudio model: {str(e_load)}")

        # --- Actual Parsing Logic for the defined object types ---
        for obj_type in types_to_parse: # Only loop through types selected for parsing
            data: Any = None
            try:
                print(f"Processing object type: {obj_type}")
                
                if obj_type == "spaces":
                    if get_all_space_objects_as_dicts: # Check if function was imported
                        data = get_all_space_objects_as_dicts(model)
                    else:
                        raise ImportError("Function 'get_all_space_objects_as_dicts' not available.")
                elif obj_type == "surfaces":
                    if get_all_surface_objects_as_dicts: # Check if function was imported
                        data = get_all_surface_objects_as_dicts(model)
                    else:
                        raise ImportError("Function 'get_all_surface_objects_as_dicts' not available.")
                elif obj_type == "subsurfaces":
                    if get_all_subsurface_objects_as_dicts: # Check if function was imported
                        data = get_all_subsurface_objects_as_dicts(model)
                    else:
                        raise ImportError("Function 'get_all_subsurface_objects_as_dicts' not available.")
                # No 'else' needed here, as types_to_parse is already validated.
                # If we add more VALID_OBJECT_TYPES later, we'll need more elif blocks.

                # Data Handling: Assumes your functions return lists of dicts or dicts
                if data is not None:
                    results[obj_type] = data
                else:
                    # Function was called, returned None (e.g., no objects of this type found).
                    # Set to an empty list to distinguish from "not selected" (which remains None from init).
                    results[obj_type] = [] 

            except ImportError as e_imp:
                print(f"ImportError for parsing function for {obj_type}: {e_imp}")
                results[obj_type] = {"error": f"Parsing function for {obj_type} not available: {str(e_imp)}"}
            except Exception as e_parse:
                print(f"Error parsing {obj_type}: {e_parse}")
                results[obj_type] = {"error": f"Error processing {obj_type}: {str(e_parse)}"}
        
        # Non-selected VALID_OBJECT_TYPES will remain as 'None' in the results dict from initialization.
        return results

    except HTTPException:
        raise
    except Exception as e:
        print(f"An unexpected server error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {str(e)}")
