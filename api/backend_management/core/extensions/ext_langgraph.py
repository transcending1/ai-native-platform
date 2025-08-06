import os

from langgraph_sdk import get_sync_client

GRAPH_ID = "agent"
langgraph_client = get_sync_client(url=os.environ['LANGGRAPH_URL'], api_key=None)
