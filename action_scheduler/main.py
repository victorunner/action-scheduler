import time
from pathlib import Path
from typing import Final, Iterator

from pydantic import parse_obj_as
from sqlalchemy import event, select
from sqlalchemy.orm import Session

from .config import config
from .database import create_db_and_tables, engine
from .models import Action, ActionCreate, ActionORM
from .scheduler import Scheduler
from .utils import read_yaml_file_to_dict

PARENT_DIR_PATH: Final = Path(__file__).parent
SAMPLE_ACTIONS_YAML_FILE_PATH: Final = 'sample_actions.yaml'


def read_actions_from_db() -> Iterator[Action]:
    session = Session(engine)
    return (action.to_pydantic() for action in session.scalars(select(ActionORM)))


def write_sample_actions_to_db():
    actions = parse_obj_as(
        list[ActionCreate],
        read_yaml_file_to_dict(PARENT_DIR_PATH / SAMPLE_ACTIONS_YAML_FILE_PATH),
    )

    with Session(engine) as session:
        for action in actions:
            session.add(ActionORM.from_pydantic(action))

        session.commit()


def cli():
    create_db_and_tables()

    actions = sorted(read_actions_from_db(), key=lambda action: action.id)

    if config.test.write_sample_actions_to_db and not actions:
        write_sample_actions_to_db()
        actions = sorted(read_actions_from_db(), key=lambda action: action.id)

    if config.internal_db:
        internal_db_url = config.internal_db.database_url.render_as_string(
            hide_password=False
        )
    else:
        internal_db_url = None

    scheduler = Scheduler(
        merge_missed_actions=config.action.defaults.merge_missed,
        action_actuality_time=config.action.defaults.actuality_time,
        internal_db_url=internal_db_url,
    )
    scheduler.start()
    # пропущенные экшены будут отработаны согласно настройкам:
    # merge_missed, actuality_time

    scheduler.load_actions(actions, config.action.callback)

    while True:
        if config.test.print_apscheduler_jobs:
            scheduler.print_jobs()

        time.sleep(config.track_changes_period)

        current_actions = sorted(read_actions_from_db(), key=lambda action: action.id)

        # TODO Оптимизировать (events, triggers, last db modification timestamp etc)
        if len(actions) != len(current_actions) or actions != current_actions:
            actions = current_actions
            scheduler.load_actions(actions, config.action.callback)


if __name__ == '__main__':
    cli()
