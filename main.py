import requests
import argparse
import os
from datetime import datetime
import json
from utils import *
from bs4 import BeautifulSoup
# types = ['datasets', 'models']
today_str = datetime.now().strftime('%Y%m%d')
repo_types = {
    'datasets':{"endpoint":"https://huggingface.co/datasets/"},
    'models':{"endpoint":"https://huggingface.co/models"}
}
base_url = 'https://huggingface.co/api/'


def get_repo_list(repo_types):
    for repo_type in repo_types:
        res = requests.get(base_url+repo_type)
        records = res.json()
        for record in records:
            record['done'] = False
            save_to_jsonl(f'temp/{repo_type}_repo_{today_str}',record)

def create_dir(output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Directory {output_dir} created.")
    else:
        print(f"Directory {output_dir} already exists. Skipping creation.")

def get_existing_local_repo_list():
    directory = 'temp'
    files = os.listdir(directory)
    if 'datasets' in repo_types:
        datasets = [f for f in files if f.startswith("datasets_") and f.endswith(".jsonl")]
    if 'models' in repo_types:
        models = [f for f in files if f.startswith("models_") and f.endswith(".jsonl")]

    # 这里假设都爬datasets 和 models, 需要单独爬, 可以自己修改代码
    if not datasets or not models:
        print("No existing repo list found")
        return False, None

    latest_dataset = max(datasets)
    latest_model = max(models)
    path_list = [
        {'type':'datasets', 'path':os.path.join(directory, latest_dataset)},
        {'type':'models', 'path':os.path.join(directory, latest_model)},
    ]
    return True, path_list

def main():
    parser = argparse.ArgumentParser(description="HuggingFace discussion scrapper.")
    parser.add_argument('-o', '--output', type=str, help='Output directory', required=True)
    parser.add_argument('-r', '--refresh', action='store_true', help='Refresh Repo List', required=False)

    args = parser.parse_args()
    output_dir = args.output
    refresh = args.refresh

    create_dir(output_dir=output_dir)
    create_dir('temp')

    existing_repo, path_list = get_existing_local_repo_list()
    if refresh or not existing_repo:
        get_repo_list(repo_types)
        _ ,path_list = get_existing_local_repo_list()

    #### handle datasets
    for path_obj in path_list:

        path_type = path_obj['type']
        path = path_obj['path'].replace('.jsonl','')

        download_repo_data(path_type, path, output_dir, today_str)
if __name__== '__main__':

    main()