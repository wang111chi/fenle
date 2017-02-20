import importme

from task import Task, TaskIdent, RunType


class TestTask(Task):

    u"""仅供测试和示范."""

    IDENT = TaskIdent.TEST

    def _run(self):
        print("test task runned")
        self.run_success = True


if __name__ == "__main__":
    TestTask(RunType.MANUAL).run()
