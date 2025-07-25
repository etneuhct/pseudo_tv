from enum import Enum

from data_types import CategoryCriteria


def serialize_enum_keys(obj):
    if isinstance(obj, dict):
        return {str(k): serialize_enum_keys(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_enum_keys(i) for i in obj]
    elif isinstance(obj, Enum):
        return obj.value
    else:
        return obj

def deserialize_enum_keys(obj):
    if isinstance(obj, dict):
        new_obj = {}
        for k, v in obj.items():
            try:
                enum_key = CategoryCriteria(k)
            except ValueError:
                enum_key = k  # Garde la clé si ce n'est pas une enum
            new_obj[enum_key] = deserialize_enum_keys(v)
        return new_obj
    elif isinstance(obj, list):
        return [deserialize_enum_keys(i) for i in obj]
    else:
        return obj