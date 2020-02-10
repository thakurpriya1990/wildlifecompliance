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
            running_sheet_entries: [],
            //runningSheetArtifactList: [],
            //runningSheetPersonList: [],
        },
        
    },
    getters: {
        legal_case: (state) => state.legal_case,
        running_sheet_set: (state) => state.legal_case.running_sheet_list.map(number => state.legal_case.running_sheet_entries[number])
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
        },
        updateRelatedItems(state, related_items) {
            Vue.set(state.legal_case, 'related_items', related_items);
        },
        updateRunningSheetEntries(state, running_sheet_entries) {
            Vue.set(state.legal_case, 'running_sheet_entries', running_sheet_entries);
        },
        updateRunningSheetEntry(state, running_sheet_entry) {
            console.log(running_sheet_entry)
            let i = 0;
            for (let r of state.legal_case.running_sheet_entries) {
                if (r.number === running_sheet_entry.number) {
                    state.legal_case.running_sheet_entries.splice(i, 1, running_sheet_entry);
                }
                i += 1;
            }
        },
        updateAddRunningSheetEntry(state, running_sheet_entry) {
            state.legal_case.running_sheet_entries.push(running_sheet_entry)
        },
        updateAddCourtProceedingsEntry(state, court_proceedings_entry) {
            state.legal_case.court_proceedings.journal_entries.push(court_proceedings_entry)
        },
        updateRunningSheetTransform(state, running_sheet_transform) {
            Vue.set(state.legal_case, 'running_sheet_transform', running_sheet_transform);
        },
        updateCourtProceedingsTransform(state, journal_entry_transform) {
            if (!state.legal_case.court_proceedings.hasOwnProperty('journal_entries_transform')){
                state.legal_case.court_proceedings.journal_entries_transform = {};
            }
            state.legal_case.court_proceedings.journal_entries_transform[journal_entry_transform.number] = journal_entry_transform;
        },
        updateBriefOfEvidence(state, brief_of_evidence) {
            Vue.set(state.legal_case, 'brief_of_evidence', brief_of_evidence);
            //Vue.set(state.legal_case.brief_of_evidence, 'legal_case_id', state.legal_case.id);
        },
        updateRunningSheetEntryDescription(state, { recordNumber, description, userId }) {
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
        updateRunningSheetPersonList(state, entity) {
            if (!state.legal_case.running_sheet_person_list) {
                Vue.set(state.legal_case, 'running_sheet_person_list', []);
            }
            state.legal_case.running_sheet_person_list.push(entity)
        },
        updateBoeRoiTicked(state, boeRoiTicked) {
            Vue.set(state.legal_case, 'boe_roi_ticked', []);
            for (let r of boeRoiTicked) {
                state.legal_case.boe_roi_ticked.push(r)
            }
        },
        updateBoeOtherStatementsTicked(state, boeOtherStatementsTicked) {
            Vue.set(state.legal_case, 'boe_other_statements_ticked', []);
            for (let r of boeOtherStatementsTicked) {
                state.legal_case.boe_other_statements_ticked.push(r)
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

                console.log(returnedLegalCase)
                commit("updateLegalCase", returnedLegalCase.body);

            } catch (err) {
                console.log(err);
            }
        },
        async saveLegalCase({ dispatch, state, rootGetters }, { create, internal, createNewRow }) {
            let legalCaseId = null;
            let savedLegalCase = null;
            try {
                let payload = new Object();
                Object.assign(payload, state.legal_case);
                delete payload.running_sheet_entries
                delete payload.court_proceedings.journal_entries;  // Instead, send 'journal_entries_transform', which holds only updated data.
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
                    if (createNewRow) {
                        payload.create_new_running_sheet_entry = true;
                    }
                    fetchUrl = helpers.add_endpoint_join(
                        api_endpoints.legal_case,
                        state.legal_case.id + '/'
                        )
                    console.log(payload);
                    savedLegalCase = await Vue.http.put(fetchUrl, payload);
                }
                //await dispatch("setLegalCase", savedLegalCase.body);
                legalCaseId = savedLegalCase.body.id;

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
        setLegalCase({ commit, }, legal_case) {
            commit("updateLegalCase", legal_case);
        },
        setRelatedItems({ commit }, related_items ) {
            commit("updateRelatedItems", related_items);
        },
        setRunningSheetEntries({ commit }, running_sheet_entries ) {
            commit("updateRunningSheetEntries", running_sheet_entries);
        },
        setRunningSheetEntry({ commit }, running_sheet_entry ) {
            commit("updateRunningSheetEntry", running_sheet_entry);
        },
        setAddRunningSheetEntry({ commit }, running_sheet_entry ) {
            commit("updateAddRunningSheetEntry", running_sheet_entry);
        },
        setAddCourtProceedingsEntry({ commit }, court_proceedings_entry ) {
            commit("updateAddCourtProceedingsEntry", court_proceedings_entry);
        },
        setRunningSheetTransform({ commit }, running_sheet_transform ) {
            commit("updateRunningSheetTransform", running_sheet_transform);
        },
        setCourtProceedingsTransform({ commit }, journal_entry_transform) {
            commit("updateCourtProceedingsTransform", journal_entry_transform);
        },
        setBriefOfEvidence({ commit }, brief_of_evidence ) {
            console.log(brief_of_evidence)
            commit("updateBriefOfEvidence", brief_of_evidence);
        },
        setRunningSheetEntryDescription({ commit }, {recordNumber, description, userId}) {
            commit("updateRunningSheetEntryDescription", {recordNumber, description, userId})
        },
        addToRunningSheetPersonList({ commit }, entity) {
            commit("updateRunningSheetPersonList", entity)
        },
        setBoeRoiTicked({ commit }, boeRoiTicked) {
            commit("updateBoeRoiTicked", boeRoiTicked)
        },
        setBoeOtherStatementsTicked({ commit }, boeOtherStatementsTicked) {
            commit("updateBoeOtherStatementsTicked", boeOtherStatementsTicked)
        },
    },
};
