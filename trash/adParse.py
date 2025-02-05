import json
import re

USER_ID = "dea0621e-879a-4850-a283-d3217416cb6d"

# Load JSON data safely
with open("data.json", "r", encoding="utf-8", errors="ignore") as f:
    raw_data = f.read()

# Remove control characters that could break parsing
clean_data = re.sub(r'[\x00-\x1F\x7F]', '', raw_data)

# Parse JSON
try:
    json_data = json.loads(clean_data)
    print("JSON loaded successfully!")
except json.JSONDecodeError as e:
    print(f"Failed to parse JSON: {e}")
    exit()

# Filter objects where motioners contain the USER_ID
filtered_tasks = [
    task for task in json_data
    if "motioners" in task and any(motioner.get("userId") == USER_ID for motioner in task["motioners"])
]

# Save filtered results to 'filtered.json'
with open("filtered.json", "w", encoding="utf-8") as f:
    json.dump(filtered_tasks, f, indent=4, ensure_ascii=False)

print(f"Filtered {len(filtered_tasks)} tasks containing user ID {USER_ID}. Saved to 'filtered.json'.")