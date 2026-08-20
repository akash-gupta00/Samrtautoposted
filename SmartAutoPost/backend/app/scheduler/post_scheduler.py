from apscheduler.schedulers.background import BackgroundScheduler

from app.database.session import SessionLocal
from app.services.post_schedule_service import PostScheduleService


scheduler = BackgroundScheduler(
    timezone="Asia/Kolkata",
)

schedule_service = PostScheduleService()


def process_scheduled_posts():

    db = SessionLocal()

    try:
        result = schedule_service.process_pending_schedules(db)

        if result.get("processed", 0) > 0:
            print(
                f"✅ Scheduled posts processed: "
                f"{result['processed']}"
            )

    except Exception as error:
        db.rollback()
        print(f"❌ Scheduler error: {error}")

    finally:
        db.close()


def start_scheduler():

    if scheduler.running:
        return

    scheduler.add_job(
        process_scheduled_posts,
        trigger="interval",
        seconds=30,
        id="post_scheduler",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()

    print("✅ APiScheduler Started")


def stop_scheduler():

    if scheduler.running:
        scheduler.shutdown(wait=False)

        print("🛑 APiScheduler Stopped")