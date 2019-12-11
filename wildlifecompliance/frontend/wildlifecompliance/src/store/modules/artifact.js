import Vue from 'vue';
import {
    api_endpoints,
    helpers
}
from '@/utils/hooks';
import moment from 'moment';

export const artifactStore = {
    namespaced: true,
    state: {
        artifact: {
        },
        
    },
    getters: {
        artifact: (state) => state.artifact,
    },
    mutations: {
        updateArtifact(state, artifact) {
            Vue.set(state, 'artifact', {
                ...artifact
            });
            console.log('updateArtifact');
            /*
            if (state.legal_case.case_created_date) {
                state.legal_case.case_created_date = moment(state.legal_case.case_created_date, 'YYYY-MM-DD').format('DD/MM/YYYY');
            }
            let defaultDocumentUrl = helpers.add_endpoint_join(
                api_endpoints.legal_case,
                state.legal_case.id + "/process_default_document/"
                )
            Vue.set(state.legal_case, 'defaultDocumentUrl', defaultDocumentUrl); 
            let commsLogsDocumentUrl = helpers.add_endpoint_join(
                api_endpoints.legal_case,
                state.legal_case.id + "/process_comms_log_document/"
                )
            Vue.set(state.legal_case, 'commsLogsDocumentUrl', commsLogsDocumentUrl); 
            let createLegalCaseProcessCommsLogsDocumentUrl = helpers.add_endpoint_join(
                api_endpoints.legal_case,
                state.legal_case.id + "/create_legal_case_process_comms_log_document/"
                )
            Vue.set(state.legal_case, 'createLegalCaseProcessCommsLogsDocumentUrl', createLegalCaseProcessCommsLogsDocumentUrl);
            */
        },
        updateRelatedItems(state, related_items) {
            Vue.set(state.legal_case, 'related_items', related_items);
        },
    },
    actions: {
        async loadArtifact({ dispatch, commit }, { artifact_id }) {
            try {
                const returnedArtifact = await Vue.http.get(
                    helpers.add_endpoint_json(
                        api_endpoints.artifact,
                        artifact_id)
                    );

                console.log(returnedArtifact)
                commit("updateArtifact", returnedArtifact.body);

            } catch (err) {
                console.log(err);
            }
        },
        async saveArtifact({ dispatch, state, rootGetters }, { create, internal }) {
            let artifactId = null;
            let savedArtifact = null;
            try {
                let payload = new Object();
                Object.assign(payload, state.artifact);
                console.log(payload);
                /*
                if (payload.case_created_date) {
                    payload.case_created_date = moment(payload.planned_for_date, 'DD/MM/YYYY').format('YYYY-MM-DD');
                } else if (payload.case_created_date === '') {
                    payload.case_created_date = null;
                }
                */

                let fetchUrl = null;
                if (create) {
                    fetchUrl = api_endpoints.artifact;
                    savedLegalCase = await Vue.http.post(fetchUrl, payload);
                } else {
                    fetchUrl = helpers.add_endpoint_join(
                        api_endpoints.artifact,
                        state.artifact.id + '/'
                        )
                    console.log(payload);
                    savedArtifact = await Vue.http.put(fetchUrl, payload);
                }
                //await dispatch("setLegalCase", savedLegalCase.body);
                artifactId = savedArtifact.body.id;

            } catch (err) {
                console.log(err);
                if (internal) {
                    // return "There was an error saving the record";
                    return err;
                } else {
                    await swal("Error", "There was an error saving the record", "error");
                }
            }
            // internal arg used when file upload triggers record creation
            if (internal) {
                // pass
            }
            // update legal_case
            else if (!create) {
                await swal("Saved", "The record has been saved", "success");
            }
        },
        setArtifact({ commit, }, artifact) {
            commit("updateArtifact", artifact);
        },
        setRelatedItems({ commit }, related_items ) {
            commit("updateRelatedItems", related_items);
        },
    },
};
