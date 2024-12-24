from config.config import settings
import requests
import logging


def get_raw_content(url):
    res = requests.get(url)
    if res.status_code != 200:
        return None
    return res.text


def git_hub_retriever(github_url: str):
    repo_url = github_url.replace("https://github.com/", "")
    github = GitHubData(repo_url)
    summary_data = github.summary_data()
    if not summary_data:
        logging.info(f"出错啦, url={github_url}")
        return None

    # print(summary)
    name = summary_data.get("name", "")
    full_name = summary_data.get("full_name", "")
    star = summary_data.get("stargazers_count", 0)
    fork = summary_data.get("forks_count", 0)
    watch = summary_data.get("subscribers_count", 0)
    homepage = summary_data.get("homepage")
    license_name = "未声明"
    license_ = summary_data.get("license")
    if license_:
        license_name = license_.get("name")
    avatar = summary_data.get("owner").get("avatar_url")
    summary = summary_data.get("description", "")
    tags = summary_data.get("topics", [])

    activity = github.activity_data()
    print(github)
    latest_update = activity[0].get("timestamp")
    releases = github.release_data()
    latest_version = ""
    if releases:
        latest_version = releases[0].get("name")

    read_me_content = github.read_me()
    return (
        name,
        full_name,
        avatar,
        summary,
        read_me_content,
        tags,
        star,
        fork,
        watch,
        homepage,
        license_name,
        latest_update,
        latest_version,
    )


class GitHubData:
    host = "https://api.github.com/repos/"
    repo_path = ""
    token = settings.GITHUB_TOKEN

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    def __init__(self, path):
        self.repo_path = path

    def get_data(self, url):
        res = requests.get(url, headers=self.headers)

        if res.status_code != 200:
            logging.warning(f"{res.status_code},{res.text}")
            return None
        return res.json()

    def summary_data(self):
        url = f"{self.host}{self.repo_path}"
        return self.get_data(url)

    def activity_data(self):
        url = f"{self.host}{self.repo_path}/activity"
        return self.get_data(url)

    def release_data(self):
        url = f"{self.host}{self.repo_path}/releases"
        return self.get_data(url)

    def read_me(self):
        start = f"https://raw.githubusercontent.com/{self.repo_path}"
        prefix = ("main", "master")
        middle = ("", "docs")
        appendix = (
            "README_CN.md",
            "README_ZH.md",
            "README_ZH-CN.md",
            "README-ZH_CN.md",
            "README_CN.md",
            "README_ZH.md",
            "README_zh.md",
            "README-CN.md",
            "README.md",
            "readme.md",
        )
        for a in prefix:
            for b in middle:
                for c in appendix:
                    if b:
                        url = f"{start}/{a}/{b}/{c}"
                    else:
                        url = f"{start}/{a}/{c}"
                    logging.info(url)
                    content = get_raw_content(url)
                    if content:
                        return content

        return None
