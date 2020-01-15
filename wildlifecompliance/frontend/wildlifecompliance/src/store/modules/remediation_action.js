import Vue from 'vue';
import {
    api_endpoints,
    helpers
}
from '@/utils/hooks';

export const remediationActionStore = {
    namespaced: true,
    state: {
        remediation_action: { },
    },
    getters: {
        remediation_action: state => state.remediation_action,
    },
    mutations: {
        updateRemediationAction(state, remediation_action) {
            console.log('updateRemediationAction');
            Vue.set(state, 'remediation_action', {
                ...remediation_action
            });
            if (state.remediation_action.due_date) {
                state.remediation_action.due_date = moment(state.remediation_action.due_date, 'YYYY-MM-DD').format('DD/MM/YYYY');
            }

            let remediationActionDocumentUrl = helpers.add_endpoint_join(
                api_endpoints.remediation_action,
                state.remediation_action.id + "/process_default_document/"
                )
            console.log(remediationActionDocumentUrl);
            Vue.set(state.remediation_action, 'remediationActionDocumentUrl', remediationActionDocumentUrl); 

            let commsLogsDocumentUrl = helpers.add_endpoint_join(
                api_endpoints.remediation_action,
                state.remediation_action.id + "/process_comms_log_document/"
                )
            Vue.set(state.remediation_action, 'commsLogsDocumentUrl', commsLogsDocumentUrl); 
        },
        updateCanUserAction(state, can_user_action) {
            Vue.set(state.remediation_action, 'can_user_action', can_user_action);
        },
    },
    actions: {
        async loadRemediationAction({ dispatch, }, { remediation_action_id }) {
            console.log("loadRemediationAction");
            const returnedRemediationAction = await Vue.http.get(
                    helpers.add_endpoint_json(
                        api_endpoints.remediation_action, 
                        remediation_action_id)
                    );

            await dispatch("setRemediationAction", returnedRemediationAction.body);
        },
        async saveRemediationAction({ dispatch, state }) {
            console.log('saveRemediationAction');
            // Construct url endpoint
            let putUrl = helpers.add_endpoint_join(api_endpoints.remediation_action, state.remediation_action.id + '/');

            // Construct payload to store data to be sent
            let payload = {};
            Object.assign(payload, state.remediation_action);

            let savedRemediationAction = await Vue.http.put(putUrl, payload);
        },
        async submitRemediationAction({ dispatch, state }) {
            console.log('submitRemediationAction1');

            // Construct url endpoint
            let submitUrl = helpers.add_endpoint_join(api_endpoints.remediation_action, state.remediation_action.id + '/submit/');

            // Construct payload to store data to be sent
            let payload = {};
            Object.assign(payload, state.remediation_action);

            let submittedRemediationAction = await Vue.http.post(submitUrl, payload);
        },
        setRemediationAction({ commit, }, remediation_action) {
            commit("updateRemediationAction", remediation_action);
        },
        setCanUserAction({ commit, }, can_user_action) {
            commit("updateCanUserAction", can_user_action);
        },
    },
}
