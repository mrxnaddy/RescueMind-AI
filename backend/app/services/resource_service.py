def derive_status(requested_status: str, available_quantity: int) -> str:
    """Resource status rules.

    - 'unavailable' is set by a human (maintenance, offline) and is kept.
    - Otherwise: no free units -> 'busy', free units -> 'available'.
    """

    if requested_status == "unavailable":
        return "unavailable"

    return "busy" if available_quantity <= 0 else "available"