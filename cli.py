#cli.py
import time
import json
from trash.old_client import AdbrazeClient
# from api_client import AdbrazeClient
from task_store import TaskStore
from task_manager import setup_new_task

def main():
    client = AdbrazeClient()
    # Ensure we have a valid token
    if not client.session.cookies.get("AuthenticationToken"):
        if not client.login():
            return

    while True:
        tasks = client.get_tasks()
        if tasks:
            with open("data.json", "w", encoding="utf-8") as f:
                json.dump(tasks, f, indent=4, ensure_ascii=False)
            print(f"Cached {len(tasks)} tasks.")

            store = TaskStore("data.json")
            store.load_tasks()

            target_user_id = client.user_id
            matching_tasks = store.filter_tasks_by_motioner(target_user_id)

            print(f"Found {len(matching_tasks)} tasks for motioner {target_user_id}")
            for task in matching_tasks:
                if task.status == "MOTION_TODO" or task.status == "MOTION_IN_PROCESS":
                    print(f"💥 {task.name}")
                    setup_new_task(task=task)

        # Wait a minute before next check
        time.sleep(60)

if __name__ == "__main__":
    main()