from ..db import execute


def log_change(
    table_name: str,
    record_id: int,
    action: str,
    field_name: str = None,
    old_value: str = None,
    new_value: str = None,
    changed_by: int = None,
):
    execute(
        "INSERT INTO audit_log "
        "(table_name, record_id, action, field_name, old_value, new_value, changed_by) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (table_name, record_id, action, field_name, old_value, new_value, changed_by),
    )
