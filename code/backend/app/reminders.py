import logging
from datetime import date, timedelta
from app import db

logger = logging.getLogger(__name__)


def send_due_reminders() -> int:
    """
    Find all bookings for tomorrow that haven't had a reminder sent yet,
    log a reminder line for each, mark them as sent, and return the count.
    """
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    bookings = db.get_bookings_needing_reminder(tomorrow)

    count = 0
    for booking in bookings:
        logger.info(
            "REMINDER | phone=%s | name=%s | date=%s | time=%s | booking_id=%s",
            booking["user_phone"],
            booking["user_name"],
            booking["booking_date"],
            booking["start_time"],
            booking["id"],
        )
        db.mark_reminder_sent(booking["id"])
        count += 1

    if count:
        logger.info("Reminders sent: %d for date %s", count, tomorrow)
    else:
        logger.debug("No reminders due for date %s", tomorrow)

    return count
