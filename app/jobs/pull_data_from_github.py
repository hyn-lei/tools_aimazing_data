import logging

import requests

from app.models import data_card
from app.models.data_card import DataCard
from app.providers.database import db


def pull_data_from_github():
    pull_data = PullData(db)
    pull_data.start()


class GitHubData:
    host = 'https://api.github.com/repos'
    repo_path = ''
    token = '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'

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


class PullData:
    _db = None

    def __init__(self, db):
        self._db = db
        pass

    def start(self):
        """
        获取所有 data_cards 的数据
        """
        all_list = DataCard.list_all()
        for model in all_list:
            # print(type(model))
            url = model['url']
            if not url:
                continue

            id_ = model['id']
            repo_url = url.replace('https://github.com', '')
            github = GitHubData(repo_url)
            summary = github.summary_data()
            if not summary:
                logging.info("出错啦")
                continue
            star = summary.get('stargazers_count', 0)
            fork = summary.get('forks_count', 0)
            watch = summary.get('watchers_count', 0)
            license_ = summary.get('license').get('name')
            avatar = summary.get('owner').get('avatar_url')

            activity = github.activity_data()
            # print(activity)
            latest_update = activity[0].get('timestamp')
            releases = github.release_data()
            latest_version = ''
            if releases:
                latest_version = releases[0].get('name')

            logging.info(
                f'summary data, {id_}, {repo_url}, {avatar}, {star}, {fork}, {watch}, {license_},{latest_update},'
                f' {latest_version}')

            # update db
            # model.author_avatar = avatar
            # model.stars = star
            # model.forks = fork
            # model.watches = watch
            # model.license = license_
            # model.latest_update = latest_update
            # model.latest_version = latest_version
            # result = model.save()
            # update = DataCard.update(model)
            update = DataCard.update(author_avatar=avatar, stars=star, forks=fork, watches=watch,
                                     license=license_, latest_update=latest_update,
                                     latest_version=latest_version).where(DataCard.id == id_)

            # print(update.sql())
            result = update.execute()
            logging.info(f'update summary data end, {repo_url}, result:{result}')


if __name__ == '__main__':
    pull_data_from_github()
