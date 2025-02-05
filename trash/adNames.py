import json
import re
from trash.test_gdrive import main_downloader as google_downloader

# ✅ Updated Regex to match anywhere in the text
pattern = r"(\d{2}\.\d{2}\.\d{4} (?:F-(?:Video|Static))_N-[\w\+\-()]+(?:_[\w\+\-()]*)*_Co-\d{2,3}.*?(?:_Cm-[A-Z]{2,3})?_De-[A-Z]{2,3})(?:-\d{1,2})?"

# ✅ Load JSON Data
with open("filtered.json", "r", encoding="utf-8") as f:
    json_data = json.load(f)

# print(f"✅ Total JSON Objects: {len(json_data)}")
# print(f"📜 Debugging json_data[1]:\n{json_data[1]}")

matches = []

# ✅ Extract description from json_data[1] only (for debugging)
for item in json_data:
    status = item.get("status", "")
    if status == "MOTION_TODO":
        description = item.get("description", "")
    # print(f"📜 Description Text:\n{description}\n")

    # ✅ Search for matches using regex (ANYWHERE in the text)
        matches_in_desc = re.findall(pattern, description)

        if matches_in_desc:
            # print("✅ Found matches in description:")
            for match in matches_in_desc:
                # print(f"🎯 Matched: {match}")
                matches.append(match)

# ✅ Process the matches
if matches:
    print(f"🚀 Initiating Downloads for {len(matches)}")
    for match in matches:
        google_downloader(match)
else:
    print("❌ No matches found!")
