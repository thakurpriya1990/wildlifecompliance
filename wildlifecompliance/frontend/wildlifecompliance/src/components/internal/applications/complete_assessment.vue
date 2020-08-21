<template lang="html">
    <div v-if="isApplicationLoaded" class="container" id="internalApplicationAssessment">

        <modal transition="modal fade"
            :showOk="true"
            okClass="btn btn-primary"
            :closeWhenOk="true"
            okText="Mark Complete"
            @ok="completeAssessmentsToMe()"
            cancelClass="btn btn-primary"
            title="Assessment Records" large>

            <div class="container-fluid">
                <div class="row">
                    <div class="panel panel-default">

                        <div class="panel-body panel-collapse collapse in" >
                            <form class="form-horizontal" name="assessment_form" method="put">
                                <div class="col-sm-12">
                                    <div class="form-group">
                                        <div class="row">
                                            <div class="col-sm-12">
                                                <label class="control-label" for="Name">Select licensed activities with assessment for completion</label>
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-sm-12" v-for="(a, index) in activitiesWithAssessment" v-bind:key="`a_${index}`">
                                                <input type="checkbox" name="licence_activity" :value ="a.licence_activity" :id="a.licence_activity" v-model="checkedActivities" > {{a.activity_name_str}}
                                            </div>
                                        </div>
                                    </div>
                                    <div class="form-group">
                                        <div class="row">
                                            <div class="col-sm-3">
                                                <label class="control-label pull-left">Final Comments</label>
                                            </div>
                                            <div class="col-sm-9">
                                                <textarea class="form-control" v-model="final_comment" :readonly="!canCompleteAssessment" style="width: 100%; max-width: 100%;" />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </modal>

        <!-- Application menu -->
        <div class="row" style="padding-bottom: 50px;">
        <h3>{{ headerLabel }}: {{ application.lodgement_number }}</h3>
        <div class="col-md-3">
            <CommsLogs :comms_url="comms_url" :logs_url="logs_url" :comms_add_url="comms_add_url" :disable_add_entry="false"/>
            <div class="row">
                <div class="panel panel-default">
                    <div class="panel-heading">
                       Submission 
                    </div>
                    <div class="panel-body panel-collapse">
                        <div class="row">
                            <div class="col-sm-12">
                                <strong>Submitted by</strong><br/>
                                {{ application.submitter.first_name }} {{ application.submitter.last_name }}
                            </div>
                            <div class="col-sm-12 top-buffer-s">
                                <strong>Lodged on</strong><br/>
                                {{ application.lodgement_date | formatDate}}
                            </div>
                            <div class="col-sm-12 top-buffer-s">
                                <table class="table small-table">
                                    <tr>
                                        <th>Lodgement</th>
                                        <th>Date</th>
                                        <th>Action</th>
                                    </tr>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="panel panel-default">
                    <div class="panel-heading">
                        Workflow 
                    </div>
                    <div class="panel-body panel-collapse">
                        <div class="row">
                            <div class="col-sm-12">
                                <strong>Status</strong><br/>
                                {{ application.processing_status.name }}<br/>
                                <div class ="col-sm-12" v-for="item in licence_type_data">
                                    
                                    <div v-for="item1 in item">
                                        <div v-if="item1.name">
                                            <strong>{{item1.name}}: </strong>{{item1.processing_status.name}}
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="col-sm-12 top-buffer-s" v-show="showAssignToAssessor">
                                <strong>Assigned Assessors</strong><br/>
                            
                                <div v-for="activity_assessment in activeAssessments">
                                    <div v-if="activity_assessment.assessor_group.name">
                                        <div>Assessment for {{activity_assessment.assessor_group.name.split('Wildlife Compliance - Assessors:')[1]}}</div>

                                        <template>
                                            <!-- display selects when Assessor has been allocated -->
                                            <select v-if="activity_assessment.assigned_assessor!=null" ref="assigned_assessor" class="form-control" v-model="activity_assessment.assigned_assessor.id">
                                                <option :value="null"></option>                                                
                                                <option v-for="member in activity_assessment.assessors" :value="member.id" v-bind:key="member.id">{{member.first_name}} {{member.last_name}}</option>
                                            </select>
                                            <!-- display select when no Assessor exist -->
                                            <select v-if="activity_assessment.assigned_assessor==null" ref="assigned_assessor" class="form-control" v-model="activity_assessment.assigned_assessor_id" >
                                                <option :value="null"></option>
                                                <option v-for="member in activity_assessment.assessors" :value="member.id" v-bind:key="member.id">{{member.first_name}} {{member.last_name}}</option>
                                            </select>
                                            <a @click.prevent="makeMeAssessor(activity_assessment)" class="actionBtn pull-right">Assign to me</a>
                                        </template>
                           
                                    </div>
                                </div>

                            </div>

                            <template v-if="isFinalised">
                                <div>
                                    <div class="col-sm-12">
                                        <strong>Application</strong><br/>
                                        <a class="actionBtn" v-if="!showingApplication || !this.unfinishedActivities.length" @click.prevent="toggleApplication({show: true, showFinalised: true})">Show Application</a>
                                        <a class="actionBtn" v-else @click.prevent="toggleApplication({show: false})">Hide Application</a>
                                    </div>
                                    <div class="col-sm-12">
                                        <div class="separator"></div>
                                    </div>
                                </div>
                            </template>
                            <template v-if="isFinalised">
                                <div class="col-sm-12">
                                    <div class="separator"></div>
                                </div>
                            </template>
                              <div class="col-sm-12 top-buffer-s" >
                                <template v-if="showingApplication">
                                    <div class="row">
                                        <div class="col-sm-12">
                                            <strong>Action</strong><br/>
                                        </div>
                                    </div>
                                    <div v-show="showAssessmentConditionButton" class="row">
                                        <div class="col-sm-12">
                                            <button class="btn btn-primary top-buffer-s col-xs-12" @click.prevent="toggleAssessments()">Assessments &amp; Conditions</button><br/>
                                        </div>
                                    </div>   
                                </template>
                                <template v-else>
                                    <div class="row">
                                        <div class="col-sm-12">
                                            <strong>Action</strong><br/>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-sm-12">
                                            <button class="btn btn-primary top-buffer-s col-xs-12" @click.prevent="toggleApplication({show: true})">Back to Application</button><br/>
                                        </div>
                                    </div>
                                    <div class="row" v-show="showRequestInspectionButton">
                                        <div class="col-sm-12">
                                            <button class="btn btn-primary top-buffer-s col-xs-12" @click.prevent="toggleRequestInspection()">Request Inspection</button><br/>
                                        </div>
                                    </div>   
                                    <div class="row" v-show="showCompleteAssessmentsButton">
                                        <div class="col-sm-12">
                                            <button class="btn btn-primary top-buffer-s col-xs-12" @click.prevent="openAssessmentModal()">Complete Assessments</button><br/>
                                        </div>
                                    </div>                                   
                                </template>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <!-- assessment dashboards -->
        <div class="col-md-1"></div>
            <div class="col-md-8">
                <div class="row">

                    <ApplicationAssessments v-if="!applicationDetailsVisible" />

                    <template v-if="applicationDetailsVisible">
                        <a ref="applicantTab" class="nav-link" data-toggle="pill" :href="'#'+applicantTab"></a>
                        <a ref="applicationTab" class="nav-link" data-toggle="pill" :href="'#'+applicationTab"></a>
                        <div :id="applicationTab" class="tab-pane fade in active">
                            <div class="col-md-12">
                                <div class="row">
                                    <form :action="application_form_url" method="post" name="new_application" enctype="multipart/form-data">

                                        <Application form_width="inherit" :withSectionsSelector="false" v-if="isApplicationLoaded">
                                            <input type="hidden" name="csrfmiddlewaretoken" :value="csrf_token"/>
                                            <input type='hidden' name="schema" :value="JSON.stringify(application)" />
                                            <input type='hidden' name="application_id" :value="1" />
                                            <input type='hidden' id="selected_activity_tab_id" v-model="selected_activity_tab_id" />
                                            <div v-if="showNavBarBottom" class="row" style="margin-bottom:50px;">
                                                <div class="navbar navbar-fixed-bottom" style="background-color: #f5f5f5 ">
                                                    <div class="navbar-inner">
                                                        <div class="container">
                                                            <p class="pull-right" style="margin-top:5px;">
                                                                <button v-if="!applicationIsDraft && canSaveApplication" class="btn btn-primary" @click.prevent="save()">Save Changes</button>
                                                            </p>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </Application>

                                    </form>
                                </div>
                            </div>
                        </div>

                    </template>

                    <InspectionRequest ref="inspection"  @inspection-created="requestedInspection"></InspectionRequest>                    

                </div>
            </div>
        </div>

    </div>
</div>
</template>
<script>
import Application from '../../form.vue';
import Vue from 'vue';
import modal from '@vue-utils/bootstrap-modal.vue'
import { mapActions, mapGetters } from 'vuex'
import ApplicationAssessments from './application_assessments.vue';
import datatable from '@vue-utils/datatable.vue';
import CommsLogs from '@common-components/comms_logs.vue';
import ResponsiveDatatablesHelper from "@/utils/responsive_datatable_helper.js";
import InspectionRequest from '../inspection/create_inspection_modal'
import {
    api_endpoints,
    helpers
}
from '@/utils/hooks';
export default {
    name: 'InternalApplicationAssessment',
    data: function() {
        let vm = this;
        return {
            applicantTab: 'applicantTab'+vm._uid,
            applicationTab: 'applicationTab'+vm._uid,
            detailsBody: 'detailsBody'+vm._uid,
            identificationBody: 'identificationBody'+vm._uid,
            addressBody: 'addressBody'+vm._uid,
            checksBody: 'checksBody'+vm._uid,
            isSendingToAssessor: false,
            assessorGroup:{},
            "selectedAssessor":{},
            "loading": [],
            form: null,
            initialisedSelects: false,
            showingApplication:false,
            isOfficerConditions:false,
            isofficerfinalisation:false,
            application_assessor_datatable:vm._uid+'assessment-table',
            assessors_headers:["Assessor Group","Date Sent","Status","Action"],
            assessors_options:{},
            DATE_TIME_FORMAT: 'DD/MM/YYYY HH:mm:ss',
            comms_url: helpers.add_endpoint_json(api_endpoints.applications,vm.$route.params.application_id+'/comms_log'),
            comms_add_url: helpers.add_endpoint_json(api_endpoints.applications,vm.$route.params.application_id+'/add_comms_log'),
            logs_url: helpers.add_endpoint_json(api_endpoints.applications,vm.$route.params.application_id+'/action_log'),
            panelClickersInitialised: false,
            isModalOpen: false,
            assessment: {
                id: "",
                comment: "",
            },
            savingAssessment: false,
            checkedActivities: [],
            final_comment: "",
            isRequestingInspection: false,
            inspection:{
                isModalOpen: false
            },
        }
    },
    components: {
        Application,
        datatable,
        ApplicationAssessments,
        CommsLogs,
        modal,
        InspectionRequest,
    },
    filters: {
        formatDate: function(data){
            return data ? moment(data).format('DD/MM/YYYY HH:mm:ss'): '';
        }
    },
    watch: {
    },
    computed: {
        ...mapGetters([
            'application',
            'original_application',
            'licence_type_data',
            'selected_activity_tab_id',
            'selected_activity_tab_name',
            'hasRole',
            'visibleConditionsFor',
            'checkActivityStatus',
            'isPartiallyFinalised',
            'isFinalised',
            'licenceActivities',
            'isApplicationLoaded',
            'isApplicationActivityVisible',
            'unfinishedActivities',
            'current_user',
            'canEditAssessmentFor',
            'canAssignAssessorFor',
        ]),
        activitiesWithAssessment: function() {
            return this.application.activities.filter(activity => {

                return this.canEditAssessmentFor(activity.licence_activity)
                    && this.canAssignAssessorFor(activity.licence_activity)
            })
        },
        applicationDetailsVisible: function() {
            return this.showingApplication;
        },
        applicationIsDraft: function(){
            return this.application.processing_status.id == 'draft';
        },
        selectedActivity: function(){
            // Function that returns an Application Selected Activity.
            if (this.selected_activity_tab_id == null || this.selected_activity_tab_id<1) {
                this.initTabsAssessor()     // Each Tab is a Licence Activity.
            }
            return this.application.activities.find(activity => {

                return activity.licence_activity === this.selected_activity_tab_id                
            })
        },
        applicantType: function(){
            return this.$store.getters.applicant_type;
        },
        isLoading: function() {
          return this.loading.length > 0
        },
        csrf_token: function() {
          return helpers.getCookie('csrftoken')
        },
        application_form_url: function() {
          return (this.application) ? `/api/application/${this.application.id}/application_officer_save.json` : '';
        },
        userIsAssignedOfficer: function(){
            return this.current_user.id == this.selectedActivity.assigned_officer;
        },
        form_data_comments_url: function() {
            return (this.application) ? `/api/application/${this.application.id}/officer_comments.json` : '';
        },
        headerLabel: function() {
            switch(this.application.application_type.id) {
                case 'amend_activity':
                    return 'Application - Activity Amendment';
                break;
                case 'renew_activity':
                    return 'Application - Activity Renewal';
                break;
                default:
                    return 'Application'
                break;
            }
        },
        showNavBarBottom: function() {
            return !this.applicationIsDraft && this.canSaveApplication
        },
        showCompleteAssessmentsButton: function() {
            return this.isWithAssessor && this.activeAssessments.find(assessment => {
                // Only unassigned or active assessments assigned to user.
                return !assessment.assigned_assessor 
                    || (assessment.assigned_assessor && assessment.assigned_assessor.id === this.current_user.id);               
            });
        },
        showRequestInspectionButton: function() {
            let promptInspection = this.selectedActivity.is_inspection_required && !this.selectedActivity.has_inspection
            return promptInspection && this.showCompleteAssessmentsButton
        },
        showAssignToAssessor: function(){
            return !this.showingApplication && this.canAssignAssessorFor(this.selectedActivity.licence_activity)
        },
        showAssessmentConditionButton: function() {
            return this.showingApplication && this.canAssignAssessorFor(this.selectedActivity.licence_activity)
        },
        isWithAssessor: function() {
            return this.selectedActivity.processing_status.id === 'with_assessor';
        },
        activeAssessments: function() {
            return this.application.assessments.filter(assessment => {

                return assessment.status.id !== 'completed'
                    && assessment.licence_activity === this.selected_activity_tab_id
                    // Only assessor groups associated with user.
                    && assessment.assessors.find(assessor => assessor.id === this.current_user.id);
            });
        },
        form_data_application_url: function() {
            return (this.application) ? `/api/application/${this.application.id}/form_data.json` : '';
        },
    },
    methods: {
        ...mapActions({
            load: 'loadApplication',
            revert: 'revertApplication',
        }),
        ...mapActions([
            'setOriginalApplication',
            'setApplication',
            'setActivityTab',
            'loadCurrentUser',
            'toggleFinalisedTabs',
            'saveFormData',
        ]),
        eventListeners: function(){ // Listens on children components.
            let vm = this;
            let application_tabs = $('#tabs-section li a')[0]
            if (application_tabs==null){ // if doesn't exist then rebuild.
                $("[data-target!=''][data-target]").off("click").on("click", function (e) {
                    vm.setActivityTab({
                        id: parseInt($(this).data('target').replace('#', ''), 10),
                        name: $(this).text()
                    });
                });
            }
            this.initTabsAssessor();
        },
        userHasRole: function(role, activity_id) {
            return this.hasRole(role, activity_id);
        },
        initTabsAssessor: function(force){ // initiate tabs for children components.

            if(this.selected_activity_tab_id && !force) {
                // Non-forced entry to child ApplicationAssessments.
                let application_tabs = $('#tabs-section li a')
                let tab_id = this.selected_activity_tab_id;
                let tab_name = this.selected_activity_tab_name;
                if(application_tabs) {
                    for (let i=0; i < application_tabs.length; i++){

                        if (application_tabs[i].innerText===this.selected_activity_tab_name){
                            // set tab to selected tab.
                            tab = $('#tabs-section li a')[i].click()
                        }
                    }
                }
                return
            }
            // force initiation of tabs on children components.
            let first_tab = this.application.assessments.find(assessment => {
                return assessment.status.id === 'awaiting_assessment'
            })
            if (first_tab) {
                this.licenceActivities().filter(activity => {
                    if (activity.id==first_tab.licence_activity) {

                        this.setActivityTab({ id: activity.id, name: activity.name });
                    }
                })

            }
        },
        close: function () {
            this.isModalOpen = false;
        },
        save: function(props = { showNotification: true }) {
            const { showNotification } = props;
            // this.saveFormData({ url: this.form_data_comments_url }).then(response => {

                this.saveFormData({ url: this.form_data_application_url }).then(response => {   
                    showNotification && swal(
                        'Saved',
                        'Your application has been saved',
                        'success'
                    )     
                }, error => {
                    console.log('Failed to save Application: ', error);
                    swal(
                        'Application Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    )
                });

            // }, error => {
            //     console.log('Failed to save comments: ', error);
            //     swal(
            //         'Application Error',
            //         helpers.apiVueResourceError(error),
            //         'error'
            //     )
            // });
        },
        save_wo: function() {
            return this.save({ showNotification: false });
        },
        canCompleteAssessment: function() {
            if(!this.userHasRole('assessor', this.selected_activity_tab_id)) {
                return false;
            }
            if(this.assessment.status && this.assessment.status.id != 'awaiting_assessment'){
                return false;
            }
            return this.selected_activity_tab_id && this.selectedActivity.processing_status.id == 'with_assessor' ? true : false;
        },
        toggleAssessments:function(){
            this.save_wo();
            $('#tabs-main li').removeClass('active');
            this.isSendingToAssessor = !this.isSendingToAssessor;
            this.showingApplication = false;
        },
        toggleApplication: function({show=false, showFinalised=false}){
            this.showingApplication = show;
            if(this.isSendingToAssessor){
                this.isSendingToAssessor = !show;
            }
            if(this.isOfficerConditions){
                this.isOfficerConditions = !show;
            }
            if(this.isofficerfinalisation){
                this.isofficerfinalisation = !show;
            }
            this.toggleFinalisedTabs(showFinalised);
            setTimeout(() => {
                const firstTab = $('#applicationTab');
                if(firstTab != null) {
                    firstTab.click();
                }
            }, 50);
            !showFinalised && this.load({ url: `/api/application/${this.application.id}/internal_application.json` });
        },
        toggleRequestInspection:function(){
            this.isRequestingInspection = !this.isRequestingInspection;
            this.$nextTick(() => {
                this.$refs.inspection.isModalOpen = true;
            });
        },
        requestedInspection: function(event){
            const data = {
                "licence_activity_id" : this.selected_activity_tab_id,
                "inspection_id": event.inspection,
            }
            this.setOriginalApplication(this.application);
            this.$http.post(helpers.add_endpoint_json(
                    api_endpoints.applications, (this.application.id+'/add_assessment_inspection')
                ), JSON.stringify(data)).then((response) => {
                    this.setApplication(response.body);
                }, (error) => {
                    this.revert();
                       swal(
                        'Application Error',
                        helpers.apiVueResourceError(error),
                        'error'
                        )
                }); 
        },        
        makeMeAssessor: function(assessment){
            let vm = this;
            const data = {
                "assessment_id" : assessment.id,
                "assessor_id": this.current_user.id
            }
            this.setOriginalApplication(this.application);
            this.$http.post(helpers.add_endpoint_json(
                    api_endpoints.applications, (this.application.id+'/assign_application_assessment')
                ), JSON.stringify(data)).then((response) => {
                    this.setApplication(response.body);
                }, (error) => {
                    this.revert();
                       swal(
                        'Application Error',
                        helpers.apiVueResourceError(error),
                        'error'
                        )
                }); 
        },
        onChangeAssessor: function(assessment){
            const data = {
                "assessment_id" : assessment.id,
                "assessor_id": assessment.assigned_assessor==null ? assessment.assigned_assessor_id : assessment.assigned_assessor
            }
            this.setOriginalApplication(this.application);
            this.$http.post(helpers.add_endpoint_json(
                    api_endpoints.applications, (this.application.id+'/assign_application_assessment')
                ), JSON.stringify(data)).then((response) => {
                    this.setApplication(response.body);
                }, (error) => {
                    this.revert();
                       swal(
                        'Application Error',
                        helpers.apiVueResourceError(error),
                        'error'
                        )
                });            
        },
        updateAssignedAssessorSelect:function(assessment){
            let vm = this;
            $(vm.$refs.assigned_assessor).val(assessment.assigned_assessor);
            $(vm.$refs.assigned_assessor).trigger('change');
        },
        completeAssessmentsToMe: function(){
            let vm = this;
            const data = {
                "activity_id" : this.checkedActivities,
                "final_comment" : this.final_comment,
            }
            this.setOriginalApplication(this.application);            
            vm.$http.post(helpers.add_endpoint_json(api_endpoints.applications,(vm.application.id+'/complete_application_assessments')
                ), JSON.stringify(data)).then((response) => {
                    this.setApplication(response.body);
                    this.$router.push({name:"internal-dash"});               
            }, (error) => {
                //console.log(error)
                this.revert();
                let error_msg = '<br/>';
                for (var key in error.body) {
                    error_msg += error.body[key] + '<br/>';
                }
                swal({
                    title: 'Assessment Error',
                    html: 'There was an error completing assessment.<br/>' + error_msg,
                    type: 'error'
                });

            });
        },
        initialiseAssignedAssessorSelect: function(reinit=false){
            let vm = this;
            if (reinit){
                $(vm.$refs.assigned_assessor).data('select2') ? $(vm.$refs.assigned_assessor).select2('destroy'): '';
            }
            $(vm.$refs.assigned_assessor).select2({
                theme: "bootstrap",
                allowClear: true,
                placeholder: "Select Assessor"
            }).
            on("select2:select",function (e) {
                var selected = $(e.currentTarget);
                // Note: currently only one assessment active per licence activity.
                var assessment = vm.activeAssessments[0];
                assessment.assigned_assessor = selected.val();
                vm.onChangeAssessor(assessment)
            }).on("select2:unselecting", function(e) {
                var self = $(this);
                setTimeout(() => {
                    self.select2('close');
                }, 0);
            }).on("select2:unselect",function (e) {
                var selected = $(e.currentTarget);
                // Note: currently only one assessment active per licence activity.
                var assessment = vm.activeAssessments[0];
                assessment.assigned_assessor = null;
                assessment.assigned_assessor_id = null;
                vm.onChangeAssessor(assessment);
            });
        },
        initialiseSelects: function(){
            if (!this.initialisedSelects){
                this.initialisedSelects = true;
                this.initMainTab();
            }
            this.initialiseAssignedAssessorSelect();
        },
        initMainTab: function() {
            if(!this.$refs.applicationTab) {
                return;
            }
            this.$refs.applicationTab.click();
        },
        openAssessmentModal: function() {
            this.isModalOpen = true;
        },
    },
    updated: function(){
        let vm = this;
        if (!vm.panelClickersInitialised){
            $('.panelClicker[data-toggle="collapse"]').on('click', function () {
                var chev = $(this).children()[0];
                window.setTimeout(function () {
                    $(chev).toggleClass("glyphicon-chevron-down glyphicon-chevron-up");
                },100);
            }); 
            vm.panelClickersInitialised = true;
        }
        this.$nextTick(() => {
            vm.initialiseSelects();
            vm.form = document.forms.new_application;
            vm.eventListeners();
        });
    },
    beforeRouteEnter: function(to, from, next) {
        next(vm => {
            vm.load({ url: `/api/application/${to.params.application_id}/internal_application.json` }).then(() => {
            });
            vm.loadCurrentUser({ url: `/api/my_user_details` });
        });
    },
    beforeRouteUpdate: function(to, from, next) {
        next(vm => {
            vm.load({ url: `/api/application/${to.params.application_id}.json` }).then(() => {
            });
        });
    }
}

</script>
<style scoped>
.top-buffer-s {
    margin-top: 10px;
}
.actionBtn {
    cursor: pointer;
}
.hidePopover {
    display: none;
}
.separator {
    border: 1px solid;
    margin-top: 15px;
    margin-bottom: 10px;
    width: 100%;
}
</style>
<style lang="css">
.select2-container {
    width: inherent !important;
}
</style>
