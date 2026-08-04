import os
from langgraph.checkpoint.memory import MemorySaver

def get_checkpointer():
    """
    Returns an in-memory or SQLite checkpointer for session persistence.
    """
    try:
        import sqlite3
        from langgraph.checkpoint.sqlite import SqliteSaver
        os.makedirs("data", exist_ok=True)
        db_path = "data/memory.sqlite"
        conn = sqlite3.connect(db_path, check_same_thread=False)
        return SqliteSaver(conn)
    except Exception as e:
        print(f"Warning: SqliteSaver not available ({e}), falling back to MemorySaver.")
        return MemorySaver()

def get_graph_with_memory(compiled_graph):
    """
    Attaches conversation memory checkpointer to the LangGraph workflow.
    """
    checkpointer = get_checkpointer()
    return compiled_graph
