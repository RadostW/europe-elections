import requests
import json
import time

all_results = []

# Loop through levels 0 to 5
for level in range(6):
    print(f"\n Fetching data for level {level}...")
    url = f"https://bdl.stat.gov.pl/api/v1/units?format=json&level={level}&page-size=100&page=0"

    while url:
        print(f"  Fetching: {url}")
        response = requests.get(url)
        data = response.json()

        # Append results from this page
        all_results.extend(data.get("results", []))

        # Sleep for 1 second before the next request
        time.sleep(1)

        # Move to the next page if available
        url = data.get("links", {}).get("next")

# Save all results to a JSON file
with open("../../data/poland/raw_datasets/poland__region_id__all_units_levels_0_to_5.json", "w", encoding="utf-8") as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)

print(f"Done! Downloaded {len(all_results)} records across levels 0 to 5.")
