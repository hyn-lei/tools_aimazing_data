import logging
import time

from app.models.data_card import DataCard
from app.providers.github_data import git_hub_retriever


def pull_data_from_github():
    pull_data()


def pull_data():
    """
    获取所有 data_cards 的数据
    """

    all_list = DataCard.list_all()
    error_count = 0
    for model in all_list:
        try:
            # print(type(model))
            url = model['url']
            if not url:
                continue

            id_ = model['id']
            data = git_hub_retriever(url)
            if not data:
                continue

            name, full_name, avatar, author_name, summary, read_me_content, tags, star, fork, watch, homepage, \
                license_, latest_update, latest_version = data

            DataCard.update_or_create(url, data, False)
            logging.info(
                f'summary data, {id_}, {url}, {avatar},{author_name}, {star}, {fork}, {watch}, {homepage}, {license_},{latest_update},'
                f' {latest_version}')
        except Exception as e:
            logging.error(f"Error processing data card {model.get('id')}: {e}", exc_info=True)
            error_count += 1
            time.sleep(30)
            if error_count >= 10:
                logging.error("Error count reached 10, stopping job function.")
                raise e

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
        # update = DataCard.update(author_avatar=avatar, stars=star, forks=fork, watches=watch,
        #                         license=license_, latest_update=latest_update,
        #                         latest_version=latest_version).where(DataCard.id == id_)


#
# print(update.sql())
# result = update.execute()
# logging.info(f'update summary data end, {url}, result:{result}')


if __name__ == '__main__':
    pull_data_from_github()
