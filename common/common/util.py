from datetime import datetime
import json


class DateTimeEncoder(json.JSONEncoder):
    date_format = "%Y-%m-%d %H:%M:%S"

    def default(self, obj):
        if isinstance(obj, datetime):
            # Convert datetime object to a string
            return obj.strftime(self.date_format)
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)
