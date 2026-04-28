from datetime import date, datetime, time, timedelta

from app.core.config import get_settings


class SlotService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def generate_slots(self, for_date: date) -> list[time]:
        if for_date.weekday() >= 5:
            return []

        start = datetime.combine(for_date, time(hour=self.settings.business_day_start_hour))
        end = datetime.combine(for_date, time(hour=self.settings.business_day_end_hour))
        interval = timedelta(minutes=self.settings.appointment_slot_interval_minutes)

        slots: list[time] = []
        current = start
        while current < end:
            slots.append(current.time().replace(second=0, microsecond=0))
            current += interval
        return slots

    def serialize_slots(self, slots: list[time]) -> list[str]:
        return [slot.strftime("%H:%M") for slot in slots]
