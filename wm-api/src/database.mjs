import lmdb from "lmdb";
import path from "path";
import {ANY, withExtensions} from "lmdb-query";
import sift from "sift";

export class Collection {

    /**
     * {lmdb.Database}
     */
    db;

    /**
     *
     * @param db {lmdb.RootDatabase}
     */
    constructor(db) {
        this.root = db;
        this.db = withExtensions(db.openDB('documents', {}));
    }

    async put(key, value) {
        await this.db.put(key, value);
        return value;
    }

    get(key) {
        return this.db.get(key);
    }

    async remove(key) {
        await this.db.remove(key);
    }

    async pop(key) {
        let result;

        await this.db.transaction(async () => {
            result = this.db.get(key);
            await this.db.remove(key);
        })

        return result;
    }

    find(query = {}) {
        const filter = sift(query)
        return this.db.getRange()
            .filter(({key, value}) => { return filter(value) })
            .asArray
    }
}

export class DatabaseService {

    opened = {}

    constructor(config) {
        this.config = config;
    }

    /**
     *
     * @param collection
     * @returns {Collection}
     */
    open(collection) {
        if(!(collection in this.opened)) {
            return this.opened[collection] = new Collection(lmdb.open({
                path: path.join(this.config.lmdb.root, collection),
                maxDbs: 1
            }));
        }

        return this.opened[collection];
    }

    close(collection) {
        if(collection in this.opened) {
            this.opened[collection].db.close();

        }
    }

}