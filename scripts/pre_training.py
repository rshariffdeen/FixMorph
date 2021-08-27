#!/usr/bin/env python3

import os
import git
from app.common import definitions
from app.tools import db


def get_changed_files(repo, commit):
    parent = commit + "~1"
    diff_str = repo.git.diff("--name-only", commit, parent)
    return diff_str.split("\n")


def store_pair(repo, from_commit, to_commit):
    try:
        from_files = get_changed_files(repo, from_commit)
        to_files = get_changed_files(repo, to_commit)
        # if len(from_files) != len(to_files): # difficult pairs
        #     return
        db.insert_training_pair_entry(from_commit, to_commit)
    except: # invalid commits
        return


def main():
    txt_file = os.path.join(definitions.DIRECTORY_MAIN, "c_backported.txt")
    repo = git.Repo(definitions.DIRECTORY_LINUX)

    with open(txt_file, "r") as f:
        content = f.readlines()
    
    from_commit = ""
    for line in content:
        if line[0] != ' ': # from commit
            from_commit = line.strip(" \n")
        else: # to commit
            commit_lst = line.strip(" \n").split(",")
            for to_commit in commit_lst:
                if to_commit == from_commit:
                    continue
                store_pair(repo, from_commit, to_commit)


if __name__ == "__main__":
    main()
