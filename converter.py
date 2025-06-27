import json

# with open("leetcode_contest_raw.json", "r") as infile:
#     data = json.load(infile)

# with open("leetcode_contest.jsonl", "w") as outfile:
#     for row in data["rows"]:
#         json.dump(row["row"], outfile)
#         outfile.write("\n")


import json

with open("leetcode_contest_raw.json", "r") as infile:
    data = json.load(infile)

with open("leetcode_contest2.jsonl", "w") as outfile:
    # Only process the first 3 rows
    for row in data["rows"][:3]:
        json.dump(row["row"], outfile)
        outfile.write("\n")