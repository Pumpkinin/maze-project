from editor.tools.wall_tools import WallVTool, WallHTool, EraseTool
from editor.tools.entity_tools import SpawnPlayerTool, PlaceExitTool
from editor.tools.select_tool import SelectTool

TOOLS = {
    "select": SelectTool(),
    "wall_v": WallVTool(),
    "wall_h": WallHTool(),
    "erase":  EraseTool(),
    "spawn":  SpawnPlayerTool(),
    "exit":   PlaceExitTool(),
}
