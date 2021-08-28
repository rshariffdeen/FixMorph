import sys
import pymongo
from collections import namedtuple
from app.common import values

# represents an entry to be inserted into mapping collection
MapEntry = namedtuple('MapEntry', ['version_a', 'source_a', 'func_a', 'version_c', 'source_c', 'func_c'])

client = pymongo.MongoClient(values.MONGODB_HOST, values.MONGODB_PORT)
db = client.fm
training_pair_collection = db.training_pair
mapping_collection = db.mapping


"""
mapping_collection format (of one document):
{
    orig_version: "4.19",
    target_version: "4.18",
    orig_file: "drivers/spi/spi-dw.c",
    orig_func: "func_dw_spi_add_host",
    target_file: "drivers/spi/spi-dw.c",
    target_func: "func_dw_spi_add_host",
    var_mapping: {
        "orig_foo": "target_foo",
        "orig_bar": "target_bar"
    }
}
"""

def insert_mapping_entry(entry):
    to_insert = {
        "orig_version": entry.version_a,
        "target_version": entry.version_c,
        "orig_file": entry.source_a,
        "orig_func": entry.func_a,
        "target_file": entry.source_c,
        "target_func": entry.func_c,
        "var_mapping": {}
    }
    mapping_collection.insert_one(to_insert)


def insert_training_pair_entry(hash_b, hash_e):
    to_insert = {
        "hash_b": hash_b,
        "hash_e": hash_e,
        "trained": False
    }
    training_pair_collection.insert_one(to_insert)


def num_untrained_pairs():
    return training_pair_collection.count_documents({ "trained": False })


def get_one_untrained_pair():
    untrained_pair = training_pair_collection.find_one({ "trained": False },
        sort=[("hash_b", pymongo.ASCENDING)])
    if untrained_pair:
        return (untrained_pair["hash_b"], untrained_pair["hash_e"])
    else:
        sys.exit("No more untrained pairs. Training done!")


def mark_pair_as_trained(hash_b, hash_e):
    training_pair_collection.update_one({ "hash_b": hash_b, "hash_e": hash_e },
                                        { "$set": {"trained": True} })


def create_index_mapping():
    """
    Build compound index on `orig_version`, `target_version`,
    `orig_file` and `orig_func`
    """
    mapping_collection.create_index([("orig_version", pymongo.ASCENDING),
                                     ("target_version", pymongo.ASCENDING),
                                     ("orig_file", pymongo.ASCENDING), 
                                     ("orig_func", pymongo.ASCENDING)])


def create_index_training_pair():
    """
    Build two compound indexes:
        (1) `trained` and `hash_b`
        (2) `hash_b` and `hash_e`
    """
    training_pair_collection.create_index([("trained", pymongo.ASCENDING), 
                                           ("hash_b", pymongo.ASCENDING)])
    training_pair_collection.create_index([("hash_b", pymongo.ASCENDING), 
                                           ("hash_e", pymongo.ASCENDING)])


"""
!!!!!deprecated
mapping_collection format (of one document):
{
    orig_version: "<some version string>",
    "orig_file_1": {
        "target_version_a": {
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
        "target_version_b": {
            target_file: "target_file_1"
            ...
        }
    },
    "orig_file_2": {
        ...
    }
}
"""

# def insert_mapping_entry(entry):
#     """
#     Insert one mapping into the mapping_collection
#     :param entry: an entry to be inserted, of type MapEntry
#     """
#     curr_doc = mapping_collection.find_one({ "orig_version": entry.version_a })
#     to_insert = dict()
#     if curr_doc is None: # doc with this orig_version was not inserted before
#         to_insert["orig_version"] = entry.version_a
#         to_insert[entry.source_a] = {
#             entry.version_c: {
#                 "target_file": entry.source_c,
#                 entry.func_a: {
#                     "target_func": entry.func_c
#                 }
#             }
#         }
#         mapping_collection.insert_one(to_insert)
#     else: # doc with this orig_version already exists
#         source_dict = curr_doc.get(entry.source_a)
#         if source_dict is None: # this file non-existent
#             curr_doc[entry.source_a] = {
#                 entry.version_c: {
#                     "target_file": entry.source_c,
#                     entry.func_a: {
#                         "target_func": entry.func_c
#                     }
#                 }
#             }
#         else:
#             target_dict = source_dict.get(entry.version_c)
#             if target_dict is None: # this target hash non-existent
#                 curr_doc[entry.source_a][entry.version_c] = {
#                     "target_file": entry.source_c,
#                     entry.func_a: {
#                         "target_func": entry.func_c
#                     }
#                 }
#             # TODO: can potentially stop at target hash level, since the very-beginning
#             # input is pair of hashes. However, better to do it after getting all mappings
#             # (including vars) from training phase, and build up complete hash-level
#             # dicts from there.
#             else:
#                 func_dict = target_dict.get(entry.func_a)
#                 if func_dict is None: # this func non-existent
#                     curr_doc[entry.source_a][entry.version_c][entry.func_a] = {
#                         "target_func": entry.func_c
#                     }
#                 else:
#                     # TODO: handle vars here
#                     pass
#         # curr_doc has been updated, replace it in db
#         mapping_collection.replace_one({ "orig_version": entry.version_a }, curr_doc)
