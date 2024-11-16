import json
import re
import requests
from bs4 import BeautifulSoup
import time
import os

MAX_FILE_SIZE= 500 * 1024 * 1024
# No need to put .jsonl in this function because it will handle it
def save_to_jsonl(filename, data):
    filename = get_next_filename(filename)
    with open(filename, 'a', encoding='utf-8') as f:
        json_line = json.dumps(data, ensure_ascii=False)
        f.write(json_line + '\n')

def replace_jsonl(filename, data):
    with open(f"{filename}.jsonl", 'w', encoding='utf-8') as f:
        for entry in data:
            json.dump(entry, f)
            f.write('\n')

def get_next_filename(base_filename):

    '''
    Generate the next filename based on existing files.
    '''
    i = 1
    while True:
        if i == 1:
            new_filename = f'{base_filename}.jsonl'
        else:
            new_filename = f'{base_filename}_{i}.jsonl'
        if not os.path.exists(new_filename):
            return new_filename
        else:
            file_size = os.path.getsize(new_filename)
            if file_size < MAX_FILE_SIZE:
                return new_filename
        i += 1

def load_jsonl(file_path):
    data = []
    with open(f"{file_path}.jsonl", 'r') as f:
        for line in f:
            data.append(json.loads(line))
    # return jsonl data
    return data

def _get_discussion(soup):
    discussions = soup.find_all('div',class_='relative h-16 w-full overflow-hidden')
    if discussions is None:
        return []
    return discussions

def _get_discussion_href(discussion_list, model_id):
    href_list = []
    for discussion in discussion_list:

        svg = discussion.find('svg')
        svg_classes = svg['class']
        if 'viewbox' in svg.attrs:
            view_box = svg['viewbox']
        else:
            view_box= None
        # class
        # text-green-600 = commit
        # text-blue-600 = issue data
        # text-purple-600 = closed issue data
        # view box attibute 0 0 32 32
        if ('text-blue-600' in svg_classes or 'text-purple-600' in svg_classes) and view_box=='0 0 32 32' :

            title = discussion.find('h4').text.strip()
            href = discussion.find('a')['href']
            discussion_id = href.split('/')[-1]
            author = discussion.find('span',class_='contents').find('a')['href'][1:]
            href_list.append(
                {"ID":f'{model_id}-{discussion_id}',
                '主題':title,
                '来源':author,
                '回复':[],
                '元数据':{'href':href}
                }
            )

    return href_list

def _get_comment(discussion_obj_list):
    for discussion_obj in discussion_obj_list:
        href = discussion_obj['元数据']['href']
        res = requests.get(f"https://huggingface.co{href}")
        soup = BeautifulSoup(res.text,'html.parser')
        conversations = soup.find_all('div',class_=re.compile('scroll-mt-4'))
        
        for i,conversation in enumerate(conversations):
            blockquote = ('\n').join([convs.text for convs in conversation.select('blockquote p')])
            try:
                comment = ('\n').join([convs.text for convs in conversation.select('div > p')])
            except Exception as e:
                comment = conversation.find('span',class_='peer italic text-gray-400').text
            reply_time = conversation.find('time')['datetime']
            try:
                author = conversation.find('div',class_='mr-2 flex flex-shrink-0 items-center').find('a').text
            except Exception as e:
                author = conversation.find('div',class_='mr-2').text
            discussion_obj['回复'].append(
                {
                    "楼ID":str(i),
                    "回复":comment,
                    "扩展字段":{
                        "回复人":author,
                        "引用内容":blockquote,
                        "回复时间":reply_time
                    }
                }
            )
            
    return discussion_obj_list

def download_repo_data(path_type, file_path, output_dir, today_str):
    try:
        repo_list = load_jsonl(file_path)
        for i, repo in enumerate(repo_list):
            if repo['done'] == False:
                repo_id = repo['id']
                res = requests.get(f"https://huggingface.co/datasets/{repo_id}/discussions?status=open")
                time.sleep(0.5)
                soup = BeautifulSoup(res.text,'html.parser')
                discussions = _get_discussion(soup)
                
                res = requests.get(f"https://huggingface.co/datasets/{repo_id}/discussions?status=closed")
                time.sleep(0.5)
                soup = BeautifulSoup(res.text,'html.parser')
                discussions += _get_discussion(soup)
                discussion_obj_list = _get_discussion_href(discussions, repo_id)
                conversations = _get_comment(discussion_obj_list)
                print(f"Downloaded {i+1}/{len(repo_list)} {repo_id}. Total length {len(conversations)}")
                if len(conversations)>0:
                    save_to_jsonl(f"{output_dir}/{path_type}_{today_str}",conversations)
                repo['done'] = True
                repo_list[i] = repo
            else:
                continue
    except Exception as e:
        print(f"An error ocurred: {e}")
    finally:
        replace_jsonl(file_path,repo_list)

