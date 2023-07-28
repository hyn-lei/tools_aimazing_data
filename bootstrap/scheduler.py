import logging

from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.blocking import BlockingScheduler

from app.jobs.pull_data_from_github import pull_data_from_github
from app.providers import logging_provider


def create_scheduler() -> BlockingScheduler:
    logging_provider.register()

    logging.info("BlockingScheduler initializing")

    scheduler: BlockingScheduler = BlockingScheduler()

    register_job(scheduler)

    return scheduler


def register_job(scheduler):
    """
     注册调度任务
    """
    now = datetime.now()
    scheduler.add_job(pull_data_from_github, 'interval', seconds=3600, next_run_time=now)
