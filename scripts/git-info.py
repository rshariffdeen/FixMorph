import io
import sys
from git import Repo

KEY_COMMIT_ID = "commit-id"
KEY_PARENT_COMMIT = "parent-id"
KEY_FILE_LIST = "file-list"
KEY_VERSION = "version"

repo_path = sys.argv[2]
input_file_path = sys.argv[1]
commit_info_list = list()
commit_list = list()

repo = Repo(repo_path)

with open(input_file_path, 'r') as meta_file:
    commit_list = meta_file.readlines()


for commit_id in commit_list:
    commit_id = commit_id.strip().replace("\n", '')
    commit_info = dict()
    current_commit = repo.commit(commit_id)
    parent_list = current_commit.parents

    if len(parent_list) > 1:
        print("MORE THAN ONE PARENT")

    parent_commit = parent_list[0]
    parent_commit_id = parent_commit.hexsha

    diff_list = parent_commit.diff(current_commit)
    file_list = list()
    for diff in diff_list:
        file_list.append(diff.a_path)

    makefile = current_commit.tree / 'Makefile'
    with io.BytesIO(makefile.data_stream.read()) as f:
        content = f.readlines()

    major_version = content[0].split(" = ")[1].replace("\n", '').strip()
    minor_version = content[1].split(" = ")[1].replace("\n", '').strip()
    sub_verison = content[2].split(" = ")[1].replace("\n", '').strip()
    version = major_version + "." + minor_version + "." + sub_verison

    commit_info[KEY_COMMIT_ID] = commit_id
    commit_info[KEY_PARENT_COMMIT] = parent_commit_id
    commit_info[KEY_FILE_LIST] = file_list
    commit_info[KEY_VERSION] = version
    commit_info_list.append(commit_info)

print(commit_info_list)

