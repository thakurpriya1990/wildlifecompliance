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
            // default doc
            let defaultDocumentUrl = helpers.add_endpoint_join(
                api_endpoints.legal_case,
                state.legal_case.id + "/process_default_document/"
                )
            Vue.set(state.legal_case, 'defaultDocumentUrl', defaultDocumentUrl); 
            // prosecution notice
            let prosecutionNoticeDocumentUrl = helpers.add_endpoint_join(
                api_endpoints.legal_case,
                state.legal_case.id + "/process_prosecution_notice_document/"
            )
            Vue.set(state.legal_case, 'prosecutionNoticeDocumentUrl', prosecutionNoticeDocumentUrl); 
            // court hearing notice
            let courtHearingNoticeDocumentUrl = helpers.add_endpoint_join(
                api_endpoints.legal_case,
                state.legal_case.id + "/process_court_hearing_notice_document/"
            )
            Vue.set(state.legal_case, 'courtHearingNoticeDocumentUrl', courtHearingNoticeDocumentUrl); 
            // Brief of evidence
            let briefOfEvidenceDocumentUrl = helpers.add_endpoint_join(
                api_endpoints.legal_case,
                state.legal_case.id + "/process_brief_of_evidence_document/"
                )
            Vue.set(state.legal_case, 'briefOfEvidenceDocumentUrl', briefOfEvidenceDocumentUrl); 
            // Prosecution Brief
            let prosecutionBriefDocumentUrl = helpers.add_endpoint_join(
                api_endpoints.legal_case,
                state.legal_case.id + "/process_prosecution_brief_document/"
                )
            Vue.set(state.legal_case, 'prosecutionBriefDocumentUrl', prosecutionBriefDocumentUrl); 
            // comms logs doc
            let commsLogsDocumentUrl = helpers.add_endpoint_join(
                api_endpoints.legal_case,
                state.legal_case.id + "/process_comms_log_document/"
                )
            Vue.set(state.legal_case, 'commsLogsDocumentUrl', commsLogsDocumentUrl); 
            // createLegalCase comms logs doc - required?
            let createLegalCaseProcessCommsLogsDocumentUrl = helpers.add_endpoint_join(
                api_endpoints.legal_case,
                state.legal_case.id + "/create_legal_case_process_comms_log_document/"
                )
            Vue.set(state.legal_case, 'createLegalCaseProcessCommsLogsDocumentUrl', createLegalCaseProcessCommsLogsDocumentUrl);
            let courtOutcomeDocumentUrl = helpers.add_endpoint_join(
                api_endpoints.legal_case,
                state.legal_case.id + "/process_court_outcome_document/"
                )
            Vue.set(state.legal_case, 'processCourtOutcomeDocumentUrl', courtOutcomeDocumentUrl);
            /*
            let generatedDocumentsUrl = helpers.add_endpoint_join(
                api_endpoints.legal_case,
                state.legal_case.id + "/process_generated_documents/"
                )
            Vue.set(state.legal_case, 'generatedDocumentsUrl', generatedDocumentsUrl);
            */
        },
        updateLegalCaseNoRunningSheet(state, legal_case) {
            // 20200416: current requirement is to only update statement artifacts and related items
            Vue.set(state.legal_case, 'related_items', legal_case.related_items);
            Vue.set(state.legal_case, 'statement_artifacts', legal_case.statement_artifacts);
        },
        updateRelatedItems(state, related_items) {
            Vue.set(state.legal_case, 'related_items', related_items);
        },
        updateRunningSheetEntries(state, running_sheet_entries) {
            Vue.set(state.legal_case, 'running_sheet_entries', running_sheet_entries);
        },
        updateCourtProceedingsJournalEntry(state, journal_entry){
            let i = 0;
            for (let r of state.legal_case.court_proceedings.journal_entries) {
                if (r.number === journal_entry.number) {
                    state.legal_case.court_proceedings.journal_entries.splice(i++, 1, journal_entry);
                }
            }
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
            /*
            if (!state.legal_case.running_sheet_entries) {
                Vue.set(state.legal_case, 'running_sheet_entries', []);
            }
            */
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
        updateCourtProceedingsDate(state, date_entry) {
            if (!state.legal_case.court_proceedings.hasOwnProperty('date_entries_updated')){
                state.legal_case.court_proceedings.date_entries_updated = {};
            }
            state.legal_case.court_proceedings.date_entries_updated[date_entry.id] = date_entry;
        },
        updateBriefOfEvidence(state, brief_of_evidence) {
            Vue.set(state.legal_case, 'brief_of_evidence', brief_of_evidence);
            //Vue.set(state.legal_case.brief_of_evidence, 'legal_case_id', state.legal_case.id);
        },
        updateProsecutionBrief(state, prosecution_brief) {
            Vue.set(state.legal_case, 'prosecution_brief', prosecution_brief);
            //Vue.set(state.legal_case.brief_of_evidence, 'legal_case_id', state.legal_case.id);
        },
        /*
        updateBriefOfEvidencePhysicalArtifactDetailsList(state, physical_artifacts) {
            Vue.set(state.legal_case, 'boe_physical_artifacts_details', physical_artifacts);
        },
        */
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
        updateBoePhysicalArtifactsTicked(state, boePhysicalArtifactsTicked) {
            Vue.set(state.legal_case, 'boe_physical_artifacts_ticked', []);
            for (let r of boePhysicalArtifactsTicked) {
                state.legal_case.boe_physical_artifacts_ticked.push(r)
            }
        },
        updateBoeDocumentArtifactsTicked(state, boeDocumentArtifactsTicked) {
            Vue.set(state.legal_case, 'boe_document_artifacts_ticked', []);
            for (let r of boeDocumentArtifactsTicked) {
                state.legal_case.boe_document_artifacts_ticked.push(r)
            }
        },
        updatePbRoiTicked(state, pbRoiTicked) {
            Vue.set(state.legal_case, 'pb_roi_ticked', []);
            for (let r of pbRoiTicked) {
                state.legal_case.pb_roi_ticked.push(r)
            }
        },
        updatePbOtherStatementsTicked(state, pbOtherStatementsTicked) {
            Vue.set(state.legal_case, 'pb_other_statements_ticked', []);
            for (let r of pbOtherStatementsTicked) {
                state.legal_case.pb_other_statements_ticked.push(r)
            }
        },
        updatePbPhysicalArtifactsTicked(state, pbPhysicalArtifactsTicked) {
            Vue.set(state.legal_case, 'pb_physical_artifacts_ticked', []);
            for (let r of pbPhysicalArtifactsTicked) {
                state.legal_case.pb_physical_artifacts_ticked.push(r)
            }
        },
        updatePbDocumentArtifactsTicked(state, pbDocumentArtifactsTicked) {
            Vue.set(state.legal_case, 'pb_document_artifacts_ticked', []);
            for (let r of pbDocumentArtifactsTicked) {
                state.legal_case.pb_document_artifacts_ticked.push(r)
            }
        },

        /*
        updatePhysicalArtifactSensitiveUnusedReason(state, reasonEvent) {
            let inserted = false;
            let artifactIdStr = reasonEvent.target.id.substring(7)
            let artifactId = parseInt(artifactIdStr)
            // create empty array if it does not exist
            if (!state.legal_case.boe_sensitive_unused_reasons) {
                Vue.set(state.legal_case, 'boe_sensitive_unused_reasons', []);
            }
            // update existing record, if exists
            for (let record of state.legal_case.boe_sensitive_unused_reasons) {
                if (record.id === artifactId) {
                    record.reasons = reasonEvent.target.value;
                    inserted = true;
                }
            }
            // if record does not exist, create it
            if (inserted === false) {
                let newRecord = {
                    "id": artifactId, 
                    "reasons": reasonEvent.target.value
                }
                state.legal_case.boe_sensitive_unused_reasons.push(newRecord);
            }
        },
        */
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
        async saveLegalCase({ dispatch, state, rootGetters }, { 
            create, 
            internal, 
            //createNewRow, 
            createBriefOfEvidence, 
            createProsecutionBrief,
            fullHttpResponse,
            noRunningSheet,
        }) {
            let legalCaseId = null;
            let savedLegalCase = null;
            try {
                let payload = new Object();
                Object.assign(payload, state.legal_case);
                delete payload.running_sheet_entries

                // Remove journal_entries from the payload
                // They seem to be shallow-copied, so you cannot directly delete payload.court_proceedings.journal_entries
                let temp_journal_entries = Object.create(state.legal_case.court_proceedings.journal_entries);
                delete payload.court_proceedings.journal_entries
                state.legal_case.court_proceedings.journal_entries = temp_journal_entries;

                // Remove journal_entries from the payload
                // They seem to be shallow-copied, so you cannot directly delete payload.court_proceedings.journal_entries
                let temp_court_dates = Object.create(state.legal_case.court_proceedings.court_dates);
                delete payload.court_proceedings.court_dates
                state.legal_case.court_proceedings.court_dates = temp_court_dates;

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
                    /*
                    if (createNewRow) {
                        payload.create_new_running_sheet_entry = true;
                    }
                    */
                    if (createBriefOfEvidence) {
                        payload.create_brief_of_evidence = true;
                    }
                    if (createProsecutionBrief) {
                        payload.create_prosecution_brief = true;
                    }
                    if (fullHttpResponse) {
                        payload.full_http_response = true;
                    }
                    if (noRunningSheet) {
                        payload.no_running_sheet = true;
                    }
                    fetchUrl = helpers.add_endpoint_join(
                        api_endpoints.legal_case,
                        state.legal_case.id + '/'
                        )
                    console.log(payload);
                    savedLegalCase = await Vue.http.put(fetchUrl, payload);
                }
                if (fullHttpResponse && savedLegalCase.ok) {
                    console.log(savedLegalCase)
                    await dispatch("setLegalCase", savedLegalCase.body);
                }
                if (noRunningSheet && savedLegalCase.ok) {
                    console.log(savedLegalCase)
                    await dispatch("setLegalCaseNoRunningSheet", savedLegalCase.body);
                }
                legalCaseId = savedLegalCase.body.id;

                delete state.legal_case.court_proceedings.date_entries_updated
                delete state.legal_case.court_proceedings.journal_entries_transform

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
            else if (!create && !internal) {
                await swal("Saved", "The record has been saved", "success");
            }
        },
        setLegalCase({ commit, }, legal_case) {
            commit("updateLegalCase", legal_case);
        },
        setLegalCaseNoRunningSheet({ commit, }, legal_case) {
            commit("updateLegalCaseNoRunningSheet", legal_case);
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
        setCourtProceedingsJournalEntry({ commit }, journal_entry ) {
            commit("updateCourtProceedingsJournalEntry", journal_entry);
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
        setCourtProceedingsDate({ commit }, date_entry ) {
            commit("updateCourtProceedingsDate", date_entry);
        },
        //setBriefOfEvidence({ commit }, {brief_of_evidence, physical_artifacts} ) {
        setBriefOfEvidence({ commit }, brief_of_evidence ) {
            //console.log(brief_of_evidence)
            commit("updateBriefOfEvidence", brief_of_evidence);
            //commit("updateBriefOfEvidencePhysicalArtifactDetailsList", physical_artifacts);
        },
        setProsecutionBrief({ commit }, prosecution_brief ) {
            commit("updateProsecutionBrief", prosecution_brief);
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
        setBoePhysicalArtifactsTicked({ commit }, boePhysicalArtifactsTicked) {
            commit("updateBoePhysicalArtifactsTicked", boePhysicalArtifactsTicked)
        },
        setBoeDocumentArtifactsTicked({ commit }, boeDocumentArtifactsTicked) {
            commit("updateBoeDocumentArtifactsTicked", boeDocumentArtifactsTicked)
        },
        setPbRoiTicked({ commit }, pbRoiTicked) {
            commit("updatePbRoiTicked", pbRoiTicked)
        },
        setPbOtherStatementsTicked({ commit }, pbOtherStatementsTicked) {
            commit("updatePbOtherStatementsTicked", pbOtherStatementsTicked)
        },
        setPbPhysicalArtifactsTicked({ commit }, pbPhysicalArtifactsTicked) {
            commit("updatePbPhysicalArtifactsTicked", pbPhysicalArtifactsTicked)
        },
        setPbDocumentArtifactsTicked({ commit }, pbDocumentArtifactsTicked) {
            commit("updatePbDocumentArtifactsTicked", pbDocumentArtifactsTicked)
        },

        /*
        setPhysicalArtifactSensitiveUnusedReason({ commit }, reasonEvent) {
            commit("updatePhysicalArtifactSensitiveUnusedReason", reasonEvent)
        },
        */
    },
};
