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
        legal_case: {
            
        },
        
    },
    getters: {
        legal_case: (state) => state.legal_case,
        //running_sheet_list: (state) => {
        //    let retList = []
        //    for (let r of state.legal_case.running_sheet_entries) {
        //        retList.push(r.number)
        //    }
        //    return retList
        //},

        running_sheet_set: (state) => state.legal_case.running_sheet_list.map(number => state.legal_case.running_sheet_entries[number])
        
        //running_sheet_set: (state) => {
        //    let rSet = new Set([]);
        //    for (let r of state.legal_case.running_sheet_entries) {
        //        let rKey = r["number"]
        //        console.log(rKey)
        //        rSet.add({rKey: r});

        //        //let rObj = {rKey: r}
        //        //rSet.add(rObj)
        //        //rSet.add({r["number"]: r});
        //    }
        //    return rSet;
        //}
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
            //let runningSheetList = []
            //for (let r of state.legal_case.running_sheet_entries) {
            //    runningSheetList.push(r.number)
            //}
            //Vue.set(state.legal_case, 'running_sheet_list', runningSheetList);
            //let runningSheetObject = {}
            //for (let o of state.legal_case.running_sheet_entries) {
            //    runningSheetObject[o.number] = o
            //}
            //Vue.set(state.legal_case, 'running_sheet_object', runningSheetObject);
            //Vue.set(state.legal_case, 'running_sheet_transform', []);
            //let i = 0
            //for (let r of state.legal_case.running_sheet_entries) {
            //    state.legal_case.running_sheet_transform.push(Object.assign({}, state.legal_case.running_sheet_entries[i]))
            //    state.legal_case.running_sheet_transform[i].description += ' transform'
            //    i += 1;
            //}
        },
        updateRelatedItems(state, related_items) {
            Vue.set(state.legal_case, 'related_items', related_items);
        },
        updateRunningSheetEntries(state, running_sheet_entries) {
            Vue.set(state.legal_case, 'running_sheet_entries', running_sheet_entries);
        },
        updateRunningSheetTransform(state, running_sheet_transform) {
            Vue.set(state.legal_case, 'running_sheet_transform', running_sheet_transform);
        },
        updateRunningSheetEntryDescription(state, { recordNumber, description, userId }) {
            //console.log("updateRunningSheetEntryDescription");
            console.log(recordNumber)
            console.log(description)
            if (state.legal_case.running_sheet_entries && state.legal_case.running_sheet_entries.length > 0) {
                let i = 0;
                for (let r of state.legal_case.running_sheet_entries) {
                    if (r.number === recordNumber) {
                        state.legal_case.running_sheet_entries[i].description = description;
                        state.legal_case.running_sheet_entries[i].user_id = userId;
                    }
                    i += 1
                }
            }
        },
    },
    actions: {
        async loadLegalCase({ dispatch, commit }, { legal_case_id }) {
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
        async saveLegalCase({ dispatch, state, rootGetters }, { create, internal }) {
            let legalCaseId = null;
            let savedLegalCase = null;
            try {
                let payload = new Object();
                Object.assign(payload, state.legal_case);
                console.log(payload);
                if (payload.case_created_date) {
                    payload.case_created_date = moment(payload.planned_for_date, 'DD/MM/YYYY').format('YYYY-MM-DD');
                } else if (payload.case_created_date === '') {
                    payload.case_created_date = null;
                }

                let fetchUrl = null;
                if (create) {
                    fetchUrl = api_endpoints.legal_case;
                    savedLegalCase = await Vue.http.post(fetchUrl, payload);
                } else {
                    // update Inspection
                    fetchUrl = helpers.add_endpoint_join(
                        api_endpoints.legal_case,
                        //state.inspection.id + "/inspection_save/"
                        state.legal_case.id + '/'
                        )
                    savedLegalCase = await Vue.http.put(fetchUrl, payload);
                }
                await dispatch("setLegalCase", savedLegalCase.body);
                legalCaseId = savedLegalCase.body.id;

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
            return savedLegalCase;
        },
        setLegalCase({ commit, }, legal_case) {
            commit("updateLegalCase", legal_case);
        },
        setRelatedItems({ commit }, related_items ) {
            commit("updateRelatedItems", related_items);
        },
        setRunningSheetEntries({ commit }, running_sheet_entries ) {
            commit("updateRunningSheetEntries", running_sheet_entries);
        },
        setRunningSheetTransform({ commit }, running_sheet_transform ) {
            commit("updateRunningSheetTransform", running_sheet_transform);
        },
        setRunningSheetEntryDescription({ commit }, {recordNumber, description, userId}) {
            commit("updateRunningSheetEntryDescription", {recordNumber, description, userId})
        },
    },
};
