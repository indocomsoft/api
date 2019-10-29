from apscheduler.events import EVENT_ALL
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.config import APP_CONFIG

scheduler = AsyncIOScheduler(APP_CONFIG)

# See https://github.com/agronholm/apscheduler/blob/3b0d1ce3f3a607125e60cf87e0dc13f9f711cd5e/apscheduler/events.py#L9-L25
EVENTS = {
    2 ** 0: "EVENT_SCHEDULER_STARTED",
    2 ** 1: "EVENT_SCHEDULER_SHUTDOWN",
    2 ** 2: "EVENT_SCHEDULER_PAUSED",
    2 ** 3: "EVENT_SCHEDULER_RESUMED",
    2 ** 4: "EVENT_EXECUTOR_ADDED",
    2 ** 5: "EVENT_EXECUTOR_REMOVED",
    2 ** 6: "EVENT_JOBSTORE_ADDED",
    2 ** 7: "EVENT_JOBSTORE_REMOVED",
    2 ** 8: "EVENT_ALL_JOBS_REMOVED",
    2 ** 9: "EVENT_JOB_ADDED",
    2 ** 10: "EVENT_JOB_REMOVED",
    2 ** 11: "EVENT_JOB_MODIFIED",
    2 ** 12: "EVENT_JOB_EXECUTED",
    2 ** 13: "EVENT_JOB_ERROR",
    2 ** 14: "EVENT_JOB_MISSED",
    2 ** 15: "EVENT_JOB_SUBMITTED",
    2 ** 16: "EVENT_JOB_MAX_INSTANCES",
}


def log_event(event):
    s = ["Scheduler event:"]
    for method in dir(event):
        if method.startswith("_") or method == "traceback":
            continue
        if method == "code":
            s.append(f"code={EVENTS[event.code]}")
        else:
            s.append(f"{method}={getattr(event, method)}")
    print(" ".join(s))


scheduler.add_listener(log_event, EVENT_ALL)
