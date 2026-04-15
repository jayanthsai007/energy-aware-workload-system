import asyncio
from collections import deque

task_queue = deque()


def add_task(task):
    task_queue.append(task)


def get_task():
    if task_queue:
        return task_queue.popleft()
    return None
