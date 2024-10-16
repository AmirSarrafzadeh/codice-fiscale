import json

# read the ISTAT.json file
istat = json.load(open("ISTAT.json"))
istat_it = json.load(open("ISTAT_it.json", encoding='utf-8'))

# merge the two dictionaries
istat.update(istat_it)

# write the merged dictionary to a new file
with open("all_ISTAT.json", "w") as f:
    json.dump(istat, f)