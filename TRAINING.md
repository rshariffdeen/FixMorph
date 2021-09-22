# Training related matters

_Note:_ a newer version of git is needed for some of the training mode code. To
install, run:

```
add-apt-repository -y ppa:git-core/ppa
apt-get update
apt-get install -y git
```

## Start up FixMorph and mongodb container

Run `docker-compose up` to start up FixMorph together with mongodb. This will
use the data in `./mongo-volume/` under the project root directory to be the
mongodb data in the container.

To reuse the existing mongo db data (populated training pairs and trained
mappings), unzip `mongo-volume.zip` to be `mongo-volume/` under the project
root before using docker-compose.


## Populate training pairs into mongodb

In order to keep track of what commit pairs (Pb, Pe) have been trained before,
the scipt `pre_training.py` populates a mongo db collection called 
`training_pair` from the `c_backported.txt`.

The `training_pair` collection has fields `hash_b`, `hash_e` and `trained`.
The value of `trained` has three values:

- true: this pair has been trained.
- false: this pair has not been trained.
- error: some error occurred when attempting to train this pair.

(This is already done, and data is reflected in `mongo-volume`.)


## Perform actual training

To start the actual training process, run the script `main_training.py`. This is
a wrapper around FixMorph training mode, which trains the not yet trained pairs
one by one.

This script only builds an index on the trained mappings after all the pairs
have been trained (so as to avoid potential slower insertion with an index in
place). For testing the FixMorph flow with partially trained mappings, it might
be better to manually build an index when only some of the pairs are trained,
but it probably won't matter that much with the current amount of data.

The training process adds new documents to the collection `new_mapping` 
(the `mapping` collection is obsolete). The document format of `new_mapping` 
collection can be found in `app/tools/db.py`. This file also contains functions
related to mongodb operations.

(This is partially done, and the partial data is reflected in `mongo-volume`.)


## Using the trained mapping in FixMorph

Some logic in query db was implemented in `detect_function_clone`. I was trying
the db querying workflow with the following example (but haven't made it 
working yet):

```
cd /FixMorph/experiments/ISSTA21
python3.7 driver.py --data=main-data.json --only-setup --bug-id=20
cd /FixMorph
python3.7 FixMorph.py --conf=/data/backport/linux/20/repair.conf
```
This does not seem to work yet, as the function clone part is still generating 
ast map instead of just querying and return.

_Note:_ There was a bug where I forgot to remove the `func_` prefix for function
names when saving them to db. I am temporarily prepending and removing this
prefix during db querying for now. There can be a db migration to fix this in 
the future.

----

Some other ids in `main-data.json` which **may** have corresponding
trained mappings in db (obtained through manual inspection):

```
id: 5
id: 19
id: 21
id: 22
```
