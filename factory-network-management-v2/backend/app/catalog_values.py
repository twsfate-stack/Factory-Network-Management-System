def normalize_model_value(value):
    """Normalize lookup keys while preserving human-readable spelling separately."""
    return " ".join(value.split()).casefold()
