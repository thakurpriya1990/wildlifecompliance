import Vue from 'vue';
import {
    api_endpoints,
    helpers
}
from '@/utils/hooks';

export const utilsStore = {
    namespaced: true,
    state: {
        mapboxAccessToken: '',
    },
    getters: {
        mapboxAccessToken: state => state.mapboxAccessToken,
    },
    mutations: {
        updateMapboxAccessToken(state, token) {
            state.mapboxAccessToken = token;
        },
    },
    actions: {
        async loadMapboxAccessToken({ commit }) {
            console.log("loadMapboxAccessToken");
            try {
                const returnedMapboxAccessToken = await Vue.http.get(api_endpoints.geocoding_address_search_token);
                const returnedMapboxAccessTokenBody = await returnedMapboxAccessToken.json();
                commit('updateMapboxAccessToken', returnedMapboxAccessTokenBody.access_token);

            } catch (err) {
                console.log(err);
            }
        },
    },
};
