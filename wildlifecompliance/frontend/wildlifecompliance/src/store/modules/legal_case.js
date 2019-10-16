import Vue from 'vue';
import {
    api_endpoints,
    helpers
}
from '@/utils/hooks';
import moment from 'moment';

export const legalCaseStore = {
    namespaced: true,
    state: {
        legalCase: {
            
        },
        
    },
    getters: {
        legal_case: state => state.legal_case,
    },
    mutations: {
        updateLegalCase(state, legal_case) {
            Vue.set(state, 'legal_case', {
                ...legal_case
            });
            console.log('updateLegalCase');
            if (state.legal_case.case_created_date) {
                state.legal_case.case_created_date = moment(state.legal_case.case_created_date, 'YYYY-MM-DD').format('DD/MM/YYYY');
            }
            //let inspectionReportDocumentUrl = helpers.add_endpoint_join(
            //    api_endpoints.inspection,
            //    state.inspection.id + "/process_inspection_report_document/"
            //    )
            //Vue.set(state.inspection, 'inspectionReportDocumentUrl', inspectionReportDocumentUrl); 
            //let rendererDocumentUrl = helpers.add_endpoint_join(
            //    api_endpoints.inspection,
            //    state.inspection.id + "/process_renderer_document/"
            //    )
            //Vue.set(state.inspection, 'rendererDocumentUrl', rendererDocumentUrl); 
            //let commsLogsDocumentUrl = helpers.add_endpoint_join(
            //    api_endpoints.inspection,
            //    state.inspection.id + "/process_comms_log_document/"
            //    )
            //Vue.set(state.inspection, 'commsLogsDocumentUrl', commsLogsDocumentUrl); 
            //let createInspectionProcessCommsLogsDocumentUrl = helpers.add_endpoint_join(
            //    api_endpoints.inspection,
            //    state.inspection.id + "/create_inspection_process_comms_log_document/"
            //    )
            //Vue.set(state.inspection, 'createInspectionProcessCommsLogsDocumentUrl', createInspectionProcessCommsLogsDocumentUrl); 
        },
        updateRelatedItems(state, related_items) {
            Vue.set(state.legal_case, 'related_items', related_items);
        },
    },
    actions: {
        async loadlegalCase({ dispatch, commit }, { legal_case_id }) {
            try {
                const returnedLegalCase = await Vue.http.get(
                    helpers.add_endpoint_json(
                        api_endpoints.legal_case, 
                        legal_case_id)
                    );

                /* Set Inspection object */
                //await dispatch("setInspection", returnedInspection.body);
                await dispatch("setLegalCase", returnedLegalCase.body);

            } catch (err) {
                console.log(err);
            }
        },
        // async modifyInspectionTeam({ dispatch, state}, { user_id, action }) {
        //     console.log("modifyInspectionTeam");
        //     try {
        //         const returnedInspection = await Vue.http.post(
        //             helpers.add_endpoint_join(
        //                 api_endpoints.inspection,
        //                 state.inspection.id + '/modify_inspection_team/',
        //             ),
        //             { user_id, action }
        //             );

        //         /* Set Inspection object */
        //         await dispatch("setInspection", returnedInspection.body);

        //     } catch (err) {
        //         console.log(err);
        //     }
        // },
        // TODO: convert to legal_case
        async saveInspection({ dispatch, state, rootGetters }, { create, internal }) {
            let inspectionId = null;
            let savedInspection = null;
            try {
                let payload = new Object();
                Object.assign(payload, state.inspection);
                console.log(payload);
                if (payload.planned_for_date) {
                    payload.planned_for_date = moment(payload.planned_for_date, 'DD/MM/YYYY').format('YYYY-MM-DD');
                } else if (payload.planned_for_date === '') {
                    payload.planned_for_date = null;
                }
                // Renderer data
                if (state.inspection.schema) {
                if (state.inspection.schema.length > 0) {
                    payload.renderer_data = rootGetters.renderer_form_data;
                    }
                }

                let fetchUrl = null;
                if (create) {
                    fetchUrl = api_endpoints.inspection;
                    savedInspection = await Vue.http.post(fetchUrl, payload);
                } else {
                    // update Inspection
                    fetchUrl = helpers.add_endpoint_join(
                        api_endpoints.inspection,
                        //state.inspection.id + "/inspection_save/"
                        state.inspection.id + '/'
                        )
                    savedInspection = await Vue.http.put(fetchUrl, payload);
                }
                await dispatch("setInspection", savedInspection.body);
                inspectionId = savedInspection.body.id;

            } catch (err) {
                console.log(err);
                if (internal) {
                    // return "There was an error saving the record";
                    return err;
                } else {
                    await swal("Error", "There was an error saving the record", "error");
                }
                //return window.location.href = "/internal/inspection/";
                //console.log(savedInspection);
            }
            // internal arg used when file upload triggers record creation
            if (internal) {
                console.log("modal file create")
            }
            // update inspection
            else if (!create) {
                await swal("Saved", "The record has been saved", "success");
            }
            return savedInspection;
        },
        
        setLegalCase({ commit, }, legal_case) {
            commit("updateLegalCase", legal_case);
        },
        setRelatedItems({ commit }, related_items ) {
            commit("updateRelatedItems", related_items);
        },
    },
};
