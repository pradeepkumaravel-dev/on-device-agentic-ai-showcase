import os 


from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

SUMMARY_THRESHOLD_PERCENT = 75  # % of MAX_CONTEXT_TOKENS that reveals the Summarize button
# MAX_CONTEXT_TOKENS = 32768 
MAX_CONTEXT_TOKENS = 4028 

DB_FILE_PATH = "state_checkpoints.sqlite"

ROLE_MAP = {
    "system": SystemMessage,
    "user": HumanMessage,
    "assistant": AIMessage,
}