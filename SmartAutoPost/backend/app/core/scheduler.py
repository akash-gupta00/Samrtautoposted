# Background scheduler import kar rahe hain.
from apscheduler.schedulers.background import BackgroundScheduler

# Interval trigger import kar rahe hain.
from apscheduler.triggers.interval import IntervalTrigger

# Scheduler object create kar rahe hain.
scheduler = BackgroundScheduler()


# Scheduler start karne wala function.
def start_scheduler():

    # Agar scheduler already chal raha hai to dubara start nahi karenge.
    if scheduler.running:
        return

    # Scheduler start kar rahe hain.
    scheduler.start()


# Scheduler stop karne wala function.
def stop_scheduler():

    # Agar scheduler chal raha hai tabhi stop karenge.
    if scheduler.running:
        scheduler.shutdown()