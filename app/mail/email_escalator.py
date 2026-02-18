def determine_escalation(reminder_count: int):
    if reminder_count <= 2:
        return "mild"
    elif reminder_count > 2 and reminder_count <= 4:
        return "medium"
    elif reminder_count > 4:
        return "stern"