import Vue from 'vue';
import {
    api_endpoints,
    helpers
}
from '@/utils/hooks';
import moment from 'moment';

export const documentArtifactStore = {
    namespaced: true,
    state: {
        document_artifact: {
        },
        
    },
    getters: {
        document_artifact: (state) => state.document_artifact,
    },
    mutations: {
        updateDocumentArtifact(state, document_artifact) {
            Vue.set(state, 'document_artifact', {
                ...document_artifact
            });
            console.log('updateDocumentArtifact');
            if (state.document_artifact.artifact_date) {
                state.document_artifact.artifact_date = moment(state.document_artifact.artifact_date, 'YYYY-MM-DD').format('DD/MM/YYYY');
            }
            // default doc implemented in Artifact model/viewset
            let defaultDocumentUrl = helpers.add_endpoint_join(
                api_endpoints.artifact,
                state.document_artifact.id + "/process_default_document/"
                )
            Vue.set(state.document_artifact, 'defaultDocumentUrl', defaultDocumentUrl); 
            // comms log doc implemented in Artifact model/viewset
            let commsLogsDocumentUrl = helpers.add_endpoint_join(
                api_endpoints.artifact,
                state.document_artifact.id + "/process_comms_log_document/"
                )
            Vue.set(state.document_artifact, 'commsLogsDocumentUrl', commsLogsDocumentUrl); 
            /*
            let createLegalCaseProcessCommsLogsDocumentUrl = helpers.add_endpoint_join(
                api_endpoints.legal_case,
                state.legal_case.id + "/create_legal_case_process_comms_log_document/"
                )
            Vue.set(state.legal_case, 'createLegalCaseProcessCommsLogsDocumentUrl', createLegalCaseProcessCommsLogsDocumentUrl);
            */
        },
        updateRelatedItems(state, related_items) {
            Vue.set(state.document_artifact, 'related_items', related_items);
        },
        /*
        updateDocumentArtifactLegalId(state, legal_case_id) {
            console.log(legal_case_id)
            Vue.set(state.document_artifact, 'legal_case_id', legal_case_id);
        },
        */
    },
    actions: {
        async loadDocumentArtifact({ dispatch, commit }, { document_artifact_id }) {
            try {
                const returnedDocumentArtifact = await Vue.http.get(
                    helpers.add_endpoint_json(
                        api_endpoints.document_artifact,
                        document_artifact_id)
                    );

                console.log(returnedDocumentArtifact)
                commit("updateDocumentArtifact", returnedDocumentArtifact.body);

            } catch (err) {
                console.log(err);
            }
        },
        async saveDocumentArtifact({ dispatch, state, rootGetters }, { create, internal, legal_case_id }) {
            let documentArtifactId = null;
            let savedDocumentArtifact = null;
            try {
                let payload = new Object();
                Object.assign(payload, state.document_artifact);
                console.log(payload);
                if (payload.artifact_date) {
                    payload.artifact_date = moment(payload.artifact_date, 'DD/MM/YYYY').format('YYYY-MM-DD');
                } else if (payload.artifact_date === '') {
                    payload.artifact_date = null;
                }
                if (legal_case_id) {
                    payload.legal_case_id = legal_case_id;
                }

                let fetchUrl = null;
                if (create) {
                    fetchUrl = api_endpoints.document_artifact;
                    savedDocumentArtifact = await Vue.http.post(fetchUrl, payload);
                } else {
                    fetchUrl = helpers.add_endpoint_join(
                        api_endpoints.document_artifact,
                        state.document_artifact.id + '/'
                        )
                    console.log(payload);
                    savedDocumentArtifact = await Vue.http.put(fetchUrl, payload);
                }
                await dispatch("setDocumentArtifact", savedDocumentArtifact.body);
                documentArtifactId = savedDocumentArtifact.body.id;

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
        setDocumentArtifact({ commit, }, document_artifact) {
            commit("updateDocumentArtifact", document_artifact);
        },
        /*
        setDocumentArtifactLegalId({ commit, }, legal_case_id) {
            commit("updateDocumentArtifactLegalId", legal_case_id)
        },
        */
        setRelatedItems({ commit }, related_items ) {
            commit("updateRelatedItems", related_items);
        },
    },
};
