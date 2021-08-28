#!/usr/bin/env python3

import sys
from app import main
from app.tools import db

def wrap_main():
    # set argv here so don't need to pass in training flags
    sys.argv.append("--training")

    total_untrained_pairs = db.num_untrained_pairs()

    print("\n[TRAINING] Training begins. Found {} commit pairs in total."
        .format(total_untrained_pairs))

    current_pair = 1
    while current_pair <= total_untrained_pairs:
        print("[TRAINING] Start training the {}/{} commit pair."
            .format(current_pair, total_untrained_pairs))
        main.main()
        current_pair += 1

    print("[TRAINING] Building database indexes...\n")
    db.create_index_mapping()
    print("[TRAINING] Finished training all commit pairs!\n")


if __name__ == "__main__":
    wrap_main()
