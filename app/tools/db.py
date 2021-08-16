from collections import namedtuple
from pymongo import MongoClient
from app.common import values

# represents an entry to be inserted into mapping collection
MapEntry = namedtuple('MapEntry', ['hash_a', 'source_a', 'func_a', 'hash_c', 'source_c', 'func_c'])

client = MongoClient(values.MONGODB_HOST, values.MONGODB_PORT)
db = client.testdb
mapping_collection = db.mapping

"""
mapping_collection format (of one document):
{
    orig_hash: "<some hash string>",
    "orig_file_1": {
        "target_hash_a": {
            target_file: "target_file_1",
            "orig_func_1": {
                target_func: "target_func_1",
                "orig_var_1": "target_var_1",
                "orig_var_2": "target_var_2"
            },
            "orig_func_2": {
                ...
            }
        }
        "target_hash_b": {
            target_file: "target_file_1"
            ...
        }
    },
    "orig_file_2": {
        ...
    }
}


"""


def insert_mapping_entry(entry):
    """
    Insert one mapping into the mapping_collection
    :param entry: an entry to be inserted, of type MapEntry
    """
    curr_doc = mapping_collection.find_one({ "orig_hash": entry.hash_a })
    to_insert = dict()
    if curr_doc is None: # doc with this orig_hash was not inserted before
        to_insert["orig_hash"] = entry.hash_a
        to_insert[entry.source_a] = {
            entry.hash_c: {
                "target_file": entry.source_c,
                entry.func_a: {
                    "target_func": entry.func_c
                }
            }
        }
        mapping_collection.insert_one(to_insert)
    else: # doc with this orig_hash already exists
        source_dict = curr_doc.get(entry.source_a)
        if source_dict is None: # this file non-existent
            curr_doc[entry.source_a] = {
                entry.hash_c: {
                    "target_file": entry.source_c,
                    entry.func_a: {
                        "target_func": entry.func_c
                    }
                }
            }
        else:
            target_dict = source_dict.get(entry.hash_c)
            if target_dict is None: # this target hash non-existent
                curr_doc[entry.source_a][entry.hash_c] = {
                    "target_file": entry.source_c,
                    entry.func_a: {
                        "target_func": entry.func_c
                    }
                }
            # TODO: can potentially stop at target hash level, since the very-beginning
            # input is pair of hashes. However, better to do it after getting all mappings
            # (including vars) from training phase, and build up complete hash-level
            # dicts from there.
            else:
                func_dict = target_dict.get(entry.func_a)
                if func_dict is None: # this func non-existent
                    curr_doc[entry.source_a][entry.hash_c][entry.func_a] = {
                        "target_func": entry.func_c
                    }
                else:
                    # TODO: handle vars here
                    pass
        # curr_doc has been updated, replace it in db
        mapping_collection.replace_one({ "orig_hash": entry.hash_a }, curr_doc)
