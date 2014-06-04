from datetime import datetime


def timestamp():
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')