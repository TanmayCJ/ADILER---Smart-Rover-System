Mars Rover Agentic Simulation (mars-rover-agentic-sim)

Quick commands (from repo root):

Sequential workflow:
	C:/Users/tanny/AppData/Local/Programs/Python/Python314/python.exe mars-rover-agentic-sim/scripts/run_agent_workflow.py --data-dir scripts/synthetic_data_full --scenario easy_navigation

LangGraph workflow:
	C:/Users/tanny/AppData/Local/Programs/Python/Python314/python.exe -m pip install -r mars-rover-agentic-sim/ai_brain/requirements.txt
	C:/Users/tanny/AppData/Local/Programs/Python/Python314/python.exe mars-rover-agentic-sim/scripts/run_langgraph_workflow.py --data-dir scripts/synthetic_data_full --scenario easy_navigation

Tests (after pytest install):
	C:/Users/tanny/AppData/Local/Programs/Python/Python314/python.exe -m pip install pytest
	C:/Users/tanny/AppData/Local/Programs/Python/Python314/python.exe -m pytest mars-rover-agentic-sim
