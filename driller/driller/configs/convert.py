import yaml
import requests


def check(url):
    return True
    headers = {"content-type": "application/json", "Accept-Charset": "UTF-8"}
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(f"Not found: {url}")
    return r.status_code == 200


data = None
with open("./mining-cost-awareness.yaml", "r") as file:
    data = yaml.load(file, Loader=yaml.Loader)
    # print(data)

NUM = 10

repos = []
for line in data[:NUM]:
    name = line["name"].split("/")[-1]
    url = f"https://github.com/{line['name']}.git"

    repos.append(
        {
            "project_id": name,
            "url": url,
            "repo": name,
            "index_code": False,
            "index_developer_email": True,
            "start_date": "1 April, 2019 00:00",
            "end_date": "20 April, 2024 00:00",
        }
    )

with open(f"./output_{NUM}.yaml", "w") as file:
    file.writelines(
        yaml.dump(
            {
                "repositories": {
                    "defaults": {
                        "index_code": False,
                        "index_developer_email": True,
                        "start_date": "1 April, 2019 00:00",
                        "end_date": "20 April, 2024 00:00",
                    },
                    "projects": repos,
                }
            }
        )
    )
