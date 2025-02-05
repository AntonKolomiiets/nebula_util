import json
from typing import List
from models import Task

class TaskStore:
    def __init__(self, filename: str):
        self.filename = filename
        self.tasks: List[Task] = []
    
    def load_tasks(self) -> None:
        """Load tasks from a JSON file and parse them into Task objects."""
        with open(self.filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            # assuming data is a list of tasks; if not, adjust accordingly
            self.tasks = [Task(**task_dict) for task_dict in data]
    
    def filter_tasks_by_motioner(self, user_id: str) -> List[Task]:
        """Return all tasks where at least one motioner has the given userId."""
        return [
            task for task in self.tasks
            if any(motioner.userId == user_id for motioner in task.motioners)
        ]
    
    
