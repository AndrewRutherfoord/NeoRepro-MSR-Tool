
from driller.util import remove_none_values


def test_remove_none_values():
    result = remove_none_values({"value": 1, "value2": None, "dictionary": { "value3": None }})
    
    assert result.get("value2", "NOPE") == "NOPE"