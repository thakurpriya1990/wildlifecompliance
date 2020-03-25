import localforage from 'localforage';
import Vue from 'vue';

/*
 * Functions below are named after 'Cache' but no cache functionality is used.
 * On the firefox, cache fanctionality doesn't work very well, therefore it has been removed
 */
module.exports = {
    getSetCache: async (store_name, key, url, expiry) => {
        const returnedFromUrl = await Vue.http.get(url);
        return returnedFromUrl.body
    },
    getSetCacheList: async (store_name, url, expiry) => {
        let returned_list = [];  
        const returnedFromUrl = await Vue.http.get(url);
        if (returnedFromUrl.body.results) {
            for (let record of returnedFromUrl.body.results) {
                returned_list.push(record);
            }
        } else if (returnedFromUrl && returnedFromUrl.body && returnedFromUrl.body[0] && returnedFromUrl.body[0].id) {
            for (let record of returnedFromUrl.body) {
                returned_list.push(record);
            }
        } else if (returnedFromUrl.body[0] && returnedFromUrl.body[0].pk) {
            for (let record of returnedFromUrl.body) {
                returned_list.push(record);
            }
        }
        return returned_list
    }
};
