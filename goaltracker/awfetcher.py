
import json
from datetime import datetime, timezone, timedelta
import requests

AW_QUERY_URL = "http://localhost:5600/api/0/query/"

def fetch_hours(filters : list, begin_date : datetime, end_date : datetime):
    data = {
        "query": [
            "events = flood(query_bucket(find_bucket(\"aw-watcher-window\")));",
            "not_afk = flood(query_bucket(find_bucket(\"aw-watcher-afk\")));",
            "not_afk = filter_keyvals(not_afk, \"status\", [\"not-afk\"]);",
            "browser_events = [];",
            "audible_events = filter_keyvals(browser_events, \"audible\", [true]);",
            "not_afk = period_union(not_afk, audible_events);",
            "events = filter_period_intersect(events, not_afk);",
            "events = categorize(events, {});".format(json.dumps(filters)),
            "cat_events   = sort_by_duration(merge_events_by_keys(events, [\"$category\"]));",
            "duration = sum_durations(events);",
            "RETURN = {}".format(
                 json.dumps(
                    {
                        "cat_events": "__cat_events__"
                    }, indent=4
                ).replace("\"__cat_events__\"", "cat_events"))
        #{\n        \"window\": {\n            \"app_events\": app_events,\n            \"title_events\": title_events,\n            \"cat_events\": cat_events,\n            \"active_events\": not_afk,\n            \"duration\": duration\n        },\n        \"browser\": {\n            \"domains\": browser_domains,\n            \"urls\": browser_urls,\n            \"duration\": browser_duration\n        }\n    };"
        ],
        "timeperiods": [
            "{}/{}".format(begin_date.isoformat(), end_date.isoformat())
            #"2024-10-17T04:00:00+03:00/2024-10-18T04:00:00+03:00"
        ]
    }
    data_json = json.dumps(data)
    headers = {'Content-type': 'application/json'}

    response = requests.post(AW_QUERY_URL, data=data_json, headers=headers)
    total_secs = 0
    
    if response.status_code == 200:
            results = json.loads(response.content)
            for res in results:
                if "cat_events" not in res.keys():
                     continue
                
                for cat in res['cat_events']:
                     if cat['data']['$category'] != "Uncategorized":
                          total_secs += cat['duration']
            
    return total_secs / 60 / 60

def main():
    filter = [[['Work'], {'type': 'regex', 'ignore_case': True, 'regex': 'code'}]]

    begin_date = datetime.now(timezone(timedelta(hours=3)))
    begin_date = begin_date.replace(hour=0, minute=0, second=0, microsecond=0)

    end_date = datetime.now(timezone(timedelta(hours=3)))
    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=0)
    print(fetch_hours(filter, begin_date=begin_date, end_date=end_date))

    pass

if __name__ == "__main__":
    main()