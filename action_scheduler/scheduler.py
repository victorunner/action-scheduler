from typing import Iterable, Literal, Protocol

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .models import Action

# ActionCallback: TypeAlias = Callable[[str], None] | str


class ActionCallback(Protocol):
    def __call__(self, command: str) -> None:
        ...


def build_trigger_from_cron(
    format: Literal['unix', 'apscheduler'], **params: str | int
) -> CronTrigger:
    if format == 'unix':
        # https://www.ibm.com/docs/en/db2/11.5?topic=task-unix-cron-format
        assert isinstance(params['value'], str)
        trigger = CronTrigger.from_crontab(params['value'])
    elif format == 'apscheduler':
        # https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html#module-apscheduler.triggers.cron
        trigger = CronTrigger(**params)

    return trigger


class Scheduler:
    def __init__(
        self,
        *,
        merge_missed_actions: bool,
        action_actuality_time: int,
        internal_db_url: str | None = None,
    ) -> None:
        if action_actuality_time < 0:
            misfire_grace_time = None
        else:
            misfire_grace_time = action_actuality_time  # sec

        config = {
            'apscheduler.executors.default': {
                'class': 'apscheduler.executors.pool:ThreadPoolExecutor',
                'max_workers': 20,
            },
            'apscheduler.job_defaults.coalesce': merge_missed_actions,
            'apscheduler.job_defaults.max_instances': 3,
            'apscheduler.job_defaults.misfire_grace_time': misfire_grace_time,
            'apscheduler.timezone': 'UTC',
        }
        if internal_db_url:
            config['apscheduler.jobstores.default'] = {
                'type': 'sqlalchemy',
                'url': internal_db_url,
            }

        self._apscheduler = BackgroundScheduler(config)

    def start(self):
        self._apscheduler.start()

    def load_actions(
        self, actions: Iterable[Action], callback: ActionCallback | str
    ) -> None:
        used_job_ids = []

        for action in actions:
            cron = action.cron
            trigger = build_trigger_from_cron(cron.format, **cron.params)

            kwargs = {}
            if action.merge_missed is not None:
                kwargs['coalesce'] = action.merge_missed
            # else используется config.action.defaults.merge_missed

            if action.actuality_time is not None:
                if action.actuality_time < 0:
                    # None to allow the job to run no matter how late it is
                    # https://apscheduler.readthedocs.io/en/3.x/modules/schedulers/base.html#apscheduler.schedulers.base.BaseScheduler.add_job
                    kwargs['misfire_grace_time'] = None
                else:
                    kwargs['misfire_grace_time'] = action.actuality_time  # sec
            # else используется config.action.defaults.actuality_time

            job_id = str(action.id)
            used_job_ids.append(job_id)

            self._apscheduler.add_job(
                callback,
                trigger=trigger,
                kwargs={'command': action.command},
                id=str(action.id),
                name=action.name,
                replace_existing=True,
                **kwargs,
            )

        for job in self._apscheduler.get_jobs():
            if job.id not in used_job_ids:
                job.remove()

    def print_jobs(self) -> None:
        self._apscheduler.print_jobs()
