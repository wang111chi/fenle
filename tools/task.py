#!/usr/bin/env python3

import importme

import os
from enum import Enum
import datetime

from base.db import engine, t_task_log, t_task_footprint
from base import logger
from base import util


class TaskIdent(Enum):
    BASE = 0

    TEST = 1001


class RunType(Enum):
    MANUAL = 0            # 手动运行
    AUTO = 1              # 自动运行(比如定时任务)


class TaskStatus(Enum):
    RUNNING = 0           # 任务开始跑
    DONE = 1              # 任务跑成功(没出异常，且主动设置了run_success为True)


class Task:
    SIMULTANEOUSLY = False  # 是否可以同时跑同一个任务的多个实例，默认为否
    IDENT = TaskIdent.BASE  # 任务ID，为TaskIdent枚举值，每个任务类应该提供此值

    def __init__(self, run_type):
        self.run_type = run_type
        self.run_success = False
        self._db = None
        self.logger = logger.get("task-log")

    def run(self):
        if not self._check():
            return

        logstring = "{} start, run_type = {}".format(
            self.whoami, self.run_type.name)
        self.logger.info(logstring)

        self._set_running()
        self._run()
        self._end()

    def _check(self):
        if not self.SIMULTANEOUSLY:
            self._file_lock = util.FileLock(
                "{}.lock".format(self.IDENT.name.lower()),
                os.path.join(os.path.split(os.path.realpath(__file__))[0],
                             "locks"))
            if not self._file_lock.lock():
                self.logger.warn(
                    "do not repeat run {} "
                    "at the same time".format(self.whoami))
                return False
        return True

    def _run(self):
        pass

    def _end(self):
        logstring = "{} end, run_type = {}".format(
            self.whoami, self.run_type.name)
        self.logger.info(logstring)

        if self.run_success:
            self._set_runned()

    def _set_running(self):
        self.db.execute(t_task_footprint.delete().where(
            t_task_footprint.c.task_id == self.IDENT.value))

        self.db.execute(t_task_footprint.insert().values(
            task_id=self.IDENT.value,
            task_name=self.IDENT.name,
            status=TaskStatus.RUNNING.value,
            modify_time=datetime.datetime.now(),
        ))

    def _set_runned(self):
        self.db.execute(t_task_log.insert().values(
            task_id=self.IDENT.value,
            task_name=self.IDENT.name,
            run_type=self.run_type.value,
            create_time=datetime.datetime.now(),
        ))

        self.db.execute(t_task_footprint.update().where(
            t_task_footprint.c.task_id == self.IDENT.value
        ).values(
            status=TaskStatus.DONE.value,
            modify_time=datetime.datetime.now(),
        ))

    @property
    def whoami(self):
        return "task {}<ident{}>".format(self.IDENT.name, self.IDENT.value)

    @property
    def db(self):
        if not self._db:
            self._db = engine.connect()
        return self._db
