from config.config import settings
import requests
import logging


def get_raw_content(url):
    res = requests.get(url)
    if res.status_code != 200:
        return None
    return res.text


def git_hub_retriever(github_url: str):
    repo_url = github_url.replace('https://github.com', '')
    github = GitHubData(repo_url)
    summary_data = github.summary_data()
    if not summary_data:
        logging.info("出错啦")
        return None

    # print(summary)
    name = summary_data.get("name", "")
    full_name = summary_data.get("full_name", "")
    star = summary_data.get('stargazers_count', 0)
    fork = summary_data.get('forks_count', 0)
    watch = summary_data.get('subscribers_count', 0)
    license_ = summary_data.get('license').get('name')
    avatar = summary_data.get('owner').get('avatar_url')
    summary = summary_data.get('description', '')
    tags = summary_data.get('topics', [])

    activity = github.activity_data()
    # print(activity)
    latest_update = activity[0].get('timestamp')
    releases = github.release_data()
    latest_version = ''
    if releases:
        latest_version = releases[0].get('name')

    read_me_content = github.read_me()
    return name, full_name, avatar, summary, read_me_content, tags, star, fork, watch, license_, latest_update, latest_version


class GitHubData:
    host = 'https://api.github.com/repos'
    repo_path = ''
    token = settings.GITHUB_TOKEN

    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

    def __init__(self, path):
        self.repo_path = path

    def get_data(self, url):
        res = requests.get(url, headers=self.headers)

        if res.status_code != 200:
            logging.warning(f'{res.status_code},{res.text}')
            return None
        return res.json()

    def summary_data(self):
        url = f'{self.host}{self.repo_path}'
        return self.get_data(url)

    def activity_data(self):
        url = f'{self.host}{self.repo_path}/activity'
        return self.get_data(url)

    def release_data(self):
        url = f'{self.host}{self.repo_path}/releases'
        return self.get_data(url)

    def read_me(self):
        url = f'https://raw.githubusercontent.com/{self.repo_path}/main/README_CN.md'

        content = get_raw_content(url)
        if content:
            return content

        logging.info(f"中文版没有数据，获取英文版,repo_path={self.repo_path}")
        #
        url = f'https://raw.githubusercontent.com/{self.repo_path}/main/README.md'
        return get_raw_content(url)
