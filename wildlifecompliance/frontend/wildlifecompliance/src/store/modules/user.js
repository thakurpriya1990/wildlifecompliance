import Vue from 'vue';
import {
    api_endpoints,
    helpers
}
from '@/utils/hooks';
import {
    UPDATE_SELECTED_TAB_ID,
    UPDATE_SELECTED_TAB_NAME,
    UPDATE_CURRENT_USER,
    UPDATE_SELECTED_APPLY_ORG_ID,
    UPDATE_SELECTED_APPLY_PROXY_ID,
    UPDATE_SELECTED_APPLY_LICENCE_SELECT,
    UPDATE_APPLICATION_WORKFLOW_STATE,
    UPDATE_RECEPTION_METHOD_ID,
} from '@/store/mutation-types';

export const userStore = {
    state: {
        selected_activity_tab_id: 0,
        selected_activity_tab_name: '',
        selected_apply_org_id: null,
        selected_apply_proxy_id: null,
        selected_apply_licence_select: null,
        application_workflow_state: false,
        current_user: {},
        reception_method_id: null,
        
    },
    getters: {
        current_user: state => state.current_user,
        compliance_allocated_group: state => state.compliance_allocated_group,
        selected_activity_tab_id: state => state.selected_activity_tab_id,
        selected_activity_tab_name: state => state.selected_activity_tab_name,
        selected_apply_org_id: state => state.selected_apply_org_id,
        selected_apply_proxy_id: state => state.selected_apply_proxy_id,
        selected_apply_licence_select: state => state.selected_apply_licence_select,
        application_workflow_state: state => state.application_workflow_state,
        reception_method_id: state => state.reception_method_id,
        hasRole: (state, getters, rootState, rootGetters) => (role, activity_id) => {
            if(rootGetters.application.user_roles == null) {
                return false;
            }
            return rootGetters.application.user_roles.find(
                role_record =>
                (role.constructor === Array ? role : [role]
                    ).includes(role_record.role) && (!activity_id || activity_id == role_record.activity_id)
            );
        },
        visibleConditionsFor: (state, getters, rootState, rootGetters) => (for_role, processing_status, tab_id) => {
            return rootGetters.licence_type_data.activity.filter(activity =>
                activity.name && activity.processing_status.id == processing_status && getters.hasRole(for_role, activity.id) &&
                (!tab_id || tab_id == activity.id)
            );
        },
        canViewDeficiencies: (state, getters) => {
            if (getters.isApplicationLoaded){

                return getters.hasRole('licensing_officer') || getters.application.can_current_user_edit;
            }
            if (getters.isReturnsLoaded){

                return getters.returns.activity_curators.find(curator => curator.id === getters.current_user.id);
            }
            return false
        },
        canEditDeficiencies: (state, getters) => {
            if (getters.isApplicationLoaded){

                return getters.application.activities.find(activity => {

                    return activity.licence_activity === getters.selected_activity_tab_id
                        // verify role exist for selected activity.
                        && getters.hasRole('licensing_officer', activity.licence_activity)
                        // verify activity status.
                        && ['with_officer', 'with_officer_conditions'].includes(activity.processing_status.id)
                        // verify current user is associated.
                        // && activity.licensing_officers.find(officer => officer.id === getters.current_user.id);
                        // verify user is assigned or activity is not allocated.
                        && (!activity.assigned_officer || activity.assigned_officer===getters.current_user.id)
                });   
            }
            if (getters.isReturnsLoaded){

                return getters.returns.activity_curators.find(curator => curator.id === getters.current_user.id);
            }
            return false
        },
        canViewComments: (state, getters) => {
            return getters.hasRole('licensing_officer') || getters.hasRole('assessor');
        },
        canViewPayments: (state, getters) => {
            return getters.current_user.is_payment_officer;
        },
        canAssignApproverFor: (state, getters, rootState, rootGetters) => (activity_id) => {
            // This function also checks authorisation.
            return rootGetters.application.activities.find(activity => {

                return activity.licence_activity === activity_id 
                    && ['with_officer_finalisation', 'awaiting_licence_fee_payment'].includes(activity.processing_status.id) 
                    && getters.hasRole('issuing_officer', activity_id)
                    // verify current user is associated.
                    && activity.issuing_officers.find(officer => officer.id === getters.current_user.id);
            })                    
        },
        canEditAssessmentFor: (state, getters, rootState, rootGetters) => (activity_id) => {
            return rootGetters.application.assessments.find(assessment => {

                return (assessment.licence_activity===activity_id)
                    // verify user is authorised for activity.
                    && (getters.hasRole('assessor', assessment.licence_activity))
                    // verify user is assigned or assessment is not allocated.
                    && (!assessment.assigned_assessor || assessment.assigned_assessor.id===getters.current_user.id)
            });          
        },
        canRequestAmendmentFor: (state, getters, rootState, rootGetters) => (activity_id) => {
            return rootGetters.application.activities.find(activity => {

                return activity.licence_activity === activity_id
                    // verify user is authorised for activity.
                    && getters.hasRole('licensing_officer', activity_id)
                    // verify activity status
                    && ['with_officer', 'with_officer_conditions'].includes(activity.processing_status.id)
                    // verify current user is associated.
                    && activity.licensing_officers.find(officer => officer.id === getters.current_user.id);
            });          
        },
        canAssignOfficerFor: (state, getters, rootState, rootGetters) => (activity_id) => {
            if (getters.isApplicationLoaded){

                return rootGetters.application.activities.find(activity => {

                    return activity.licence_activity === activity_id
                        // verify role exist for activity.
                        && getters.hasRole('licensing_officer', activity_id)
                        // verify activity status.
                        && ['with_officer', 'with_officer_conditions'].includes(activity.processing_status.id)
                        // verify current user is associated.
                        && activity.licensing_officers.find(officer => officer.id === getters.current_user.id);
                });  

            }
            if (getters.isReturnsLoaded){

                return getters.returns.activity_curators.find(curator => {
                    // verify current user is associated.
                    return getters.returns.activity_curators.find(officer => officer.id === getters.current_user.id);
                });
            }
                  
        },
        canAssignAssessorFor: (state, getters, rootState, rootGetters) => (activity_id) => {
            return rootGetters.application.activities.find(activity => {

                return activity.licence_activity === activity_id
                    // verify user is authorised for activity.
                    && getters.hasRole('assessor', activity_id)
                    // verify activity status.
                    && ['with_assessor'].includes(activity.processing_status.id)
                    // verify user belongs to assessor group.
                    && rootGetters.application.assessments.find(assessment => {

                        return assessment.licence_activity === activity_id
                            && assessment.assessors.find(assessor => assessor.id === getters.current_user.id);
                    });
            });                    
        },
    },
    mutations: {
        [UPDATE_SELECTED_TAB_ID] (state, tab_id) {
            state.selected_activity_tab_id = tab_id;
        },
        [UPDATE_SELECTED_TAB_NAME] (state, tab_name) {
            state.selected_activity_tab_name = tab_name;
        },
        [UPDATE_CURRENT_USER] (state, user) {
            Vue.set(state, 'current_user', {...user});
        },
        [UPDATE_SELECTED_APPLY_ORG_ID] (state, org_id) {
            state.selected_apply_org_id = org_id;
        },
        [UPDATE_SELECTED_APPLY_PROXY_ID] (state, proxy_id) {
            state.selected_apply_proxy_id = proxy_id;
        },
        [UPDATE_SELECTED_APPLY_LICENCE_SELECT] (state, licence_select) {
            state.selected_apply_licence_select = licence_select;
        },
        [UPDATE_APPLICATION_WORKFLOW_STATE] (state, bool) {
            state.application_workflow_state = bool;
        },
        [UPDATE_RECEPTION_METHOD_ID] (state, pay_method) {
            state.reception_method_id = pay_method;
        },
    },
    actions: {
        setActivityTab({ commit }, { id, name }) {
            commit(UPDATE_SELECTED_TAB_ID, id);
            commit(UPDATE_SELECTED_TAB_NAME, name);
        },
        setApplyOrgId({ commit }, { id }) {
            commit(UPDATE_SELECTED_APPLY_ORG_ID, id);
        },
        setApplyProxyId({ commit }, { id }) {
            commit(UPDATE_SELECTED_APPLY_PROXY_ID, id);
        },
        setApplyLicenceSelect({ commit }, { licence_select }) {
            commit(UPDATE_SELECTED_APPLY_LICENCE_SELECT, licence_select);
        },
        setApplicationWorkflowState({ commit }, { bool }) {
            commit(UPDATE_APPLICATION_WORKFLOW_STATE, bool);
        },
        setReceptionMethodId({ commit }, { pay_method }) {
            commit(UPDATE_RECEPTION_METHOD_ID, pay_method);
        },
        loadCurrentUser({ dispatch, commit }, { url }) {
            return new Promise((resolve, reject) => {
                Vue.http.get(url).then(res => {
                    dispatch('setCurrentUser', res.body);
                    resolve();
                },
                err => {
                    console.log(err);
                    reject();
                });
            })
        },
        
        setCurrentUser({ dispatch, commit }, user) {
            commit(UPDATE_CURRENT_USER, user);
        },
        async loadAllocatedGroup({}, {region_district_id, group_permission}) {
            let url = helpers.add_endpoint_join(
                api_endpoints.region_district,
                region_district_id + '/get_compliance_group_by_region_district/'
                );
            let returned = await Vue.http.post(
                url,
                { 'group_permission': group_permission
                });
            return returned;
        },
    }
}
