import lmdb

env = lmdb.open('/opt/project/wm-infra'
                '/deploy/local/data/api/westmarches.db/westmarches/oauth_codes.mdb',
                max_dbs=1,
                subdir=False)

db = env.open_db('documents'.encode())

with env.begin() as txn:
    for key, value in txn.cursor(db):
        print(key, str(value))
