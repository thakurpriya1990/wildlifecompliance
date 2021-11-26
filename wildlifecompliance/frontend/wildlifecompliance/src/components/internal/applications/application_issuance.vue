<template id="application_issuance">
                <div class="col-md-12">

                    <div class="row">
                    <ul class="nav nav-pills mb-3" id="tabs-main" data-tabs="tabs">
                        <li class="nav-item"><a class="nav-link" data-toggle="pill" v-on:click="selectApplicantTab()">Applicant</a></li>
                        <li class="nav-item" v-for="(activity, index) in visibleLicenceActivities" v-bind:key="`issue_activity_tab_${index}`">
                            <a class="nav-link" data-toggle="pill" v-on:click="selectTab(activity)">{{activity.name}}</a>
                        </li>
                    </ul>
                    </div>
                    <div class="tab-content">
                        <div class="row" v-for="(item, index) in selectedActivity" v-bind:key="`issue_activity_content_${index}`">
                            <div class="panel panel-default">
                                <div class="panel-heading">
                                    <h3 class="panel-title">Issue/Decline - {{item.name}}
                                        <a class="panelClicker" :href="'#'+panelBody" data-toggle="collapse"  data-parent="#userInfo" expanded="false" :aria-controls="panelBody">
                                            <span class="glyphicon glyphicon-chevron-down pull-right "></span>
                                        </a>
                                    </h3>
                                </div>
                                <div class="panel-body panel-collapse collapse in" :id="panelBody">
                                    <form class="form-horizontal" action="index.html" method="post">
                                        <div class="col-sm-12">
                                            <div class="form-group">

                                                <div class="row">
                                                    <div class="col-sm-12"><label class="control-label pull-left">Proposed Purposes:</label></div>
                                                    <div class="col-sm-12"><label class="control-label pull-left">&nbsp;</label></div>
                                                    <div class="col-sm-12">
                                                        <div v-for="(p, index) in applicationSelectedActivitiesForPurposes" v-bind:key="`p_${index}`">
                                
                                                            <div class="panel panel-primary">
                                                                <div class="panel-heading">
                                                                    <h4 class="panel-title">{{p.purpose.short_name}}
                                                                        <a class="panelClicker" :href="`#${index}`+purposeBody" data-toggle="collapse"  data-parent="#userInfo" expanded="true" :aria-controls="purposeBody">
                                                                            <span class="glyphicon glyphicon-chevron-down pull-right "></span>
                                                                        </a>
                                                                    </h4>
                                                                </div>
                                                                <div class="panel-body panel-collapse collapse" :id="`${index}`+purposeBody">
                                                                    <div class="row">
                                                                        <div class="col-sm-12">
                                                                            <div class="col-sm-3">
                                                                                <input type="radio" :value ="true" :id="p.purpose.id" v-model="getPickedPurpose(p.purpose.id).isProposed" /> Issue &nbsp;
                                                                                <input type="radio" :value ="false" :id="p.purpose.id" v-model="getPickedPurpose(p.purpose.id).isProposed" /> Decline &nbsp;
                                                                            </div>
                                                                            <div class="col-sm-3">
                                                                                <div class="input-group date" v-if="getPickedPurpose(p.purpose.id).isProposed" :ref="`start_date_${p.id}`" style="width: 100%;">
                                                                                    <input :readonly="p.processing_status!=='reissue' && (!canEditLicenceDates && p.proposed_end_date)" type="text" class="form-control" :name="`start_date_${p.id}`" placeholder="DD/MM/YYYY" v-model="p.proposed_start_date">
                                                                                    <span class="input-group-addon">
                                                                                        <span class="glyphicon glyphicon-calendar"></span>
                                                                                    </span>
                                                                                </div>
                                                                            </div>                                                                                                                                                 
                                                                            <div class="col-sm-3">                                                        
                                                                                <div class="input-group date" v-if="getPickedPurpose(p.purpose.id).isProposed" :ref="`end_date_${p.id}`" style="width: 100%;">
                                                                                    <input :readonly="p.processing_status!=='reissue' && (!canEditLicenceDates && p.proposed_end_date)" type="text" class="form-control" :name="`end_date_${p.id}`" placeholder="DD/MM/YYYY" v-model="p.proposed_end_date">
                                                                                    <span class="input-group-addon">
                                                                                        <span class="glyphicon glyphicon-calendar"></span>
                                                                                    </span>
                                                                                </div>
                                                                            </div>
                                                                        </div>
                                                                        <div class="col-sm-12">
                                                                            <div class="col-sm-3" v-if="getPickedPurpose(p.purpose.id).isProposed">
                                                                                <label class="control-label pull-left" for="Name">Additional Fee</label>
                                                                            </div>
                                                                            <div class="col-sm-6" v-if="getPickedPurpose(p.purpose.id).isProposed">
                                                                                <input type="text" ref="licence_fee" class="form-control" style="width:50%;" v-model="p.additional_fee" />
                                                                            </div>
                                                                        </div>
                                                                        <div class="col-sm-12">
                                                                            <div class="col-sm-3" v-if="getPickedPurpose(p.purpose.id).isProposed">
                                                                                <label class="control-label pull-left" for="Name">Fee Description</label>
                                                                            </div>
                                                                            <div class="col-sm-6" v-if="getPickedPurpose(p.purpose.id).isProposed">
                                                                                <input type="text" :name='"licence_fee_text_" + index' class="form-control" style="width:100%;" v-model="p.additional_fee_text" />
                                                                            </div>
                                                                        </div>

                                                                        <!-- Activity Purpose Free Text -->        
                                                                        <div v-for="(free_text, pt_idx) in p.purpose_species_json" v-bind:key="`pt_${pt_idx}`">
                                                                            <br/>


                                                                            <div class="col-sm-12">
                                                                                <div class="col-sm-3">
                                                                                    <label class="control-label pull-left" for="Name">Details</label>
                                                                                    <div v-show="free_text.is_additional_info" ><br/><br/>
                                                                                        <input type="checkbox" checked disabled/>
                                                                                        <label>Is additional info</label>
                                                                                    </div>
                                                                                </div>
                                                                                <div class="col-sm-9">

                                                                                    <ckeditor ref="ap_text_detail" v-model="free_text.details" :config="editorConfig"></ckeditor>
                                                                                </div>

                                                                            </div>

                                                                        </div>

                                                                        <div class="col-sm-12" v-if="!getPickedPurpose(p.purpose.id).isProposed">                                                        
                                                                            &nbsp;
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div class="row">
                                                    <div class="col-sm-12" />
                                                </div><br/>                                          
                                                <div class="row">
                                                </div><br/>
                                                <div class="row">
                                                </div>
                                            </div>
                                        </div>
                                        
                                    </form>
                                </div>
                            </div>
                            <div class="panel panel-default">
                                <div class="panel-heading">
                                    <h3 class="panel-title">Emailing
                                        <a class="panelClicker" :href="'#'+emailPanelBody" data-toggle="collapse"  data-parent="#userInfo" expanded="false" :aria-controls="emailPanelBody">
                                            <span class="glyphicon glyphicon-chevron-down pull-right "></span>
                                        </a>
                                    </h3>
                                </div>
                                <div class="panel-body panel-collapse collapse in" :id="emailPanelBody">
                                    <div class="row">
                                        <div class="col-sm-3">
                                            
                                            <label class="control-label pull-left"  for="details">Details</label>
                                        </div>
                                        <div class="col-sm-9">
                                            <div class="input-group date" ref="details" style="width: 70%;">
                                                <input type="text" class="form-control" name="details" v-model="getActivity(item.id).reason">
                                            </div>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-sm-3">
                                            <label class="control-label pull-left"  for="details">CC Email</label>
                                        </div>
                                        <div class="col-sm-9">
                                            <div class="input-group date" ref="cc_email" style="width: 70%;">
                                                <input type="text" class="form-control" name="cc_email" v-model="getActivity(item.id).cc_email">
                                            </div>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-sm-3">
                                            <label class="control-label pull-left"  for="details">Files to be attached to email</label>
                                        </div>
                                        <div class="col-sm-9">
                                            <filefield 
                                                ref="issuance_documents" 
                                                name="issuance-documents" 
                                                :isRepeatable="true" 
                                                :documentActionUrl="applicationIssuanceDocumentUrl" />
                                        </div>                                    
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div> <!-- end of tab content -->

                    <div class="row" v-if="licence.activity.some(activity => activity.final_status === 'issued')">
                        <div class="panel panel-default">
                            <div class="panel-heading">
                                <h3 class="panel-title">Issue
                                    <a class="panelClicker" :href="'#'+issuePanelBody" data-toggle="collapse"  data-parent="#userInfo" expanded="false" :aria-controls="issuePanelBody">
                                        <span class="glyphicon glyphicon-chevron-down pull-right "></span>
                                    </a>
                                </h3>
                            </div>
                            <div class="panel-body panel-collapse collapse in" :id="issuePanelBody">
                                <div class="row">
                                    <div class="col-sm-3">
                                        <label class="control-label pull-left"  for="details">ID Check</label>
                                    </div>
                                    <div class="col-sm-9">

                                        <button v-if="isIdCheckAccepted" disabled class="btn btn-success">Accepted</button>
                                        <label v-if="isIdCheckAwaitingUpdate">Awaiting update. Override to Issue: &nbsp;</label>
                                        <label v-if="isIdNotChecked">Has not been accepted. Override to Issue: &nbsp;</label>
                                        <input v-if="isIdNotChecked || isIdCheckAwaitingUpdate" type="checkbox" :value="true" v-model="getCheckedItem('id_check').isChecked" />

                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-3">
                                        <label class="control-label pull-left"  for="details">Character Check</label>
                                    </div>
                                    <div class="col-sm-9">

                                        <button v-if="isCharacterCheckAccepted" disabled class="btn btn-success">Accepted</button>
                                        <label v-if="isCharacterNotChecked">Has not been accepted. Override to Issue: &nbsp;</label>
                                        <input v-if="isCharacterNotChecked" type="checkbox" :value="true" v-model="getCheckedItem('character_check').isChecked" />

                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-3">
                                        <label class="control-label pull-left"  for="details">Return Check</label>
                                    </div>
                                    <div class="col-sm-9">

                                        <button v-if="isReturnCheckAccepted" disabled class="btn btn-success">Accepted</button>
                                        <label v-if="isReturnCheckAwaitingReturns">Awaiting return. Override to Issue: &nbsp;</label>
                                        <label v-if="isReturnNotChecked">Has not been accepted. Override to Issue: &nbsp;</label>
                                        <input v-if="isReturnNotChecked || isReturnCheckAwaitingReturns" type="checkbox" :value="true" v-model="getCheckedItem('return_check').isChecked" />

                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <p>Click <a href="#" @click.prevent="preview()">here</a> to preview the licence document.</p>

                    <div class="row" style="margin-bottom:50px;">
                        <div class="navbar navbar-fixed-bottom" style="background-color: #f5f5f5 ">
                            <div class="navbar-inner">
                                <div class="container" v-if="canIssueOrDecline">
                                    <p class="pull-right" style="margin-top:5px;">
                                        <button v-if="showSpinner" type="button" class="btn btn-primary pull-right" ><i class="fa fa-spinner fa-spin"/>Issue/Decline</button>
                                        <button v-else class="btn btn-primary pull-right" @click.prevent="ok()">Issue/Decline</button>
                                    </p>
                                </div>
                                <div class="container" v-else>
                                    <p class="pull-right" style="margin-top:5px;">
                                        <button disabled class="btn btn-primary pull-right" @click.prevent="ok()">Issue/Decline</button>
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                </div>

            
</template>
<script>
import {
    api_endpoints,
    helpers
}
from '@/utils/hooks'
import { mapGetters, mapActions } from 'vuex'
import filefield from '@/components/common/compliance_file.vue'

export default {
    name: 'InternalApplicationIssuance',
    components:{
        filefield,
    },    
    props: {
        application: Object,
        licence_activity_tab:Number,
        final_view_conditions: {
            type: Boolean,
            default: false,
        },        
    },
    data: function() {
        let vm = this;
        if (vm.application.can_view_richtext_src) {
            var toolbar_options = [
                [ 'Source' ],
                [ '-', 'Bold', 'Italic' ],
                [ 'Format' ],
                [ 'NumberedList', 'BulletedList' ],
                //[ 'Indent', 'Outdent' ],
                [ 'Table' ],
            ]
	} else {
            var toolbar_options = [
                [ '-', 'Bold', 'Italic' ],
                [ 'Format' ],
                [ 'NumberedList', 'BulletedList' ],
                [ 'Table' ],
            ]
	}

        return {
            panelBody: "application-issuance-"+vm._uid,
            issuePanelBody: "app-issuance-check-"+vm._uid,
            emailPanelBody: "app-issuance-email-"+vm._uid,
            purposeBody: `purposeBody${vm._uid}`,
            proposed_licence:{},
            licence:{
                activity: [],
                checked_items: [{
                    id: null,
                    isChecked: false,
                }],

                current_application: vm.application.id,
                purposes: [],
                selected_purpose_ids: [],
                },
            datepickerOptions:{
                format: 'DD/MM/YYYY',
                showClear:true,
                useCurrent:false,
                keepInvalid:true,
                allowInputToggle:true
            },
            pickedPurposes: [],
            spinner:false,

            editorConfig: {
                // The configuration of the editor.
                toolbar: toolbar_options,
                format_tags: 'p;h1;h2;h3;h4;h5;h6;div',

                // remove bottom bar
                removePlugins: 'elementspath',
                resize_enabled: false, 
            },
        }
    },
    watch:{
    },
    computed:{
        ...mapGetters([
            'selected_activity_tab_id',
            'licenceActivities',
            'filterActivityList',
            'isApplicationActivityVisible',
            'application_workflow_state',
        ]),
        csrf_token: function() {
            return helpers.getCookie('csrftoken')
        },
        applicationIssuanceDocumentUrl: function() {
            let url = '';
            if (this.selectedApplicationActivityId) {
                url = helpers.add_endpoint_join(
                    api_endpoints.application_selected_activity,
                    this.selectedApplicationActivityId + "/process_issuance_document/"
                )
            }
            return url;
        },
        applicationSelectedActivitiesForPurposes: function() {
            var proposed = this.selectedApplicationActivity.proposed_purposes.filter(purpose => {
                if (purpose.processing_status === 'reissue'){
                    purpose.proposed_start_date = purpose.start_date
                    purpose.proposed_end_date = purpose.expiry_date              
                }
                return ['reissue','propose','selected'].includes(purpose.processing_status)
            });
            return proposed;
        },
        canIssueOrDecline: function() {

            let is_checked = this.getCheckedItem('id_check').isChecked && this.getCheckedItem('character_check').isChecked  && this.getCheckedItem('return_check').isChecked;
            let is_accepted = this.isIdCheckAccepted && this.isCharacterCheckAccepted && this.isReturnCheckAccepted;
            return (this.allActivitiesDeclined || is_checked || is_accepted) && this.visibleLicenceActivities.length;
        },
        selectedActivity: function() {
            return this.visibleLicenceActivities.filter(
                activity => activity.id == this.selected_activity_tab_id
            );
        },
        visibleLicenceActivities: function() {

            return this.licenceActivities();
        },
        isActivityVisible: function(activity_id) {
            return this.isApplicationActivityVisible({ activity_id: activity_id });
        },
        selectedApplicationActivity: function() {       
            let selected_activity = this.application.activities.find(
                activity => { return activity.licence_activity == this.selected_activity_tab_id }
            );
            return selected_activity
        },
        selectedApplicationActivityId: function() {     
            let activity_id = null;
            if (this.selectedApplicationActivity) {
                activity_id = this.selectedApplicationActivity.id;
            }
            return activity_id
        },
        isIdCheckAccepted: function(){
            return this.application.id_check_status.id == 'accepted';
        },
        isIdCheckAwaitingUpdate: function(){
            return this.application.id_check_status.id == 'awaiting_update';
        },
        isIdNotChecked: function(){
            return this.application.id_check_status.id == 'not_checked'
                || this.application.id_check_status.id == 'updated' ;
        },
        isCharacterCheckAccepted: function(){
            return this.application.character_check_status.id == 'accepted';
        },
        isCharacterNotChecked: function(){
            return this.application.character_check_status.id == 'not_checked';
        },
        isReturnCheckAccepted: function(){
            return this.application.return_check_status.id == 'accepted';
        },
        isReturnCheckAwaitingReturns: function(){
            return this.application.return_check_status.id == 'awaiting_returns';
        },
        isReturnNotChecked: function(){
            return this.application.return_check_status.id == 'not_checked'
                || this.application.return_check_status.id == 'updated' ;
        },
        finalStatus: function() {
            return (id) => {
                return this.getActivity(id).final_status;
            }
        },
        allActivitiesDeclined: function() {
            return this.licence && !this.licence.activity.filter(
                activity => activity.final_status !== 'declined'
            ).length;
        },
        canSubmit: function() {

            let required_confirmations = this.application.activities.find(activity => {
 
                return activity.licence_activity === this.selected_activity_tab_id
                
            });
            let confirmations = this.licence.activity.filter(activity => {

                return activity.id === required_confirmations.licence_activity && activity.confirmed;

            }).length;

            return confirmations;
        },
        canEditLicenceDates: function() {
            return this.application.application_type && this.application.application_type.id !== 'amend_activity';
        },
        showSpinner: function() {
            return this.spinner
        },
        preview_licence_url: function() {
            this.initialiseLicenceDetails();
            return (this.application.id) ? `/preview/licence-pdf/${this.application.id}` : ''
        },
    },
    methods:{
        ...mapActions({
            load: 'loadApplication',
            revert: 'revertApplication',
        }),
        ...mapActions([
            'setActivityTab',
            'finalDecisionData',
            'setApplicationWorkflowState',
        ]),
        selectTab: function(component) {
            this.setActivityTab({id: component.id, name: component.name});
            this.$emit('action-tab', {tab: component})
        },
        selectApplicantTab: function() {
            this.$emit('action-tab', {tab: 'IssueApplicant'})
        },
       preview: async function () {
            let vm = this;

            this.setApplicationWorkflowState({bool: true});

            this.spinner = true;
            let selected = []
            let activity_pickedPurposes = []
            let confirmations = []
            for (let a=0; a<this.application.activities.length; a++){
                let activity = this.application.activities[a]

                if (activity.licence_activity === this.selected_activity_tab_id){

                    let confirmation = this.licence.activity.filter(a => {

                        return a.id === activity.licence_activity;

                    })[0]
                    confirmation.confirmed=true;
                    confirmations.push(confirmation);

                    let proposed = activity.proposed_purposes
                    for (let p=0; p<proposed.length; p++){
                        let purpose = proposed[p]
                        if (['reissue','propose','selected'].includes(purpose.processing_status)){
                            selected.push(purpose)

                            let picked_purpose = this.pickedPurposes.filter(picked => {
                                return picked.id === purpose.purpose.id;
                            })[0]
                            activity_pickedPurposes.push(picked_purpose)
                        }
                    }
                }
            }

            vm.licence.purposes = selected;
            vm.licence.activity = confirmations;
            vm.licence.selected_purpose_ids = activity_pickedPurposes;
            let licence = JSON.parse(JSON.stringify(vm.licence));
            licence.purposes = vm.licence.purposes.map(purpose => {
                const date_formats = ["DD/MM/YYYY", "YYYY-MM-DD"];
                return {
                    ...purpose,
                    proposed_start_date: purpose.proposed_start_date ?
                        moment(purpose.proposed_start_date, date_formats).format('YYYY-MM-DD') : null,
                    proposed_end_date: purpose.proposed_end_date ?
                        moment(purpose.proposed_end_date, date_formats).format('YYYY-MM-DD') : null,
                }
            });

            vm.post_and_redirect(
                vm.preview_licence_url,
                {'csrfmiddlewaretoken' : vm.csrf_token, 'formData': JSON.stringify(licence)}
            );

            this.setApplicationWorkflowState({bool: false});

        },

        post_and_redirect: function(url, postData) {
            /* http.post and ajax do not allow redirect from Django View (post method),
               this function allows redirect by mimicking a form submit.

               usage:  vm.post_and_redirect(vm.application_fee_url, {'csrfmiddlewaretoken' : vm.csrf_token});
            */
            var postFormStr = "<form method='POST' target='_blank' name='Preview Licence' action='" + url + "'>";

            for (var key in postData) {
                if (postData.hasOwnProperty(key)) {
                    postFormStr += "<input type='hidden' name='" + key + "' value='" + postData[key] + "'>";
                }
            }
            postFormStr += "</form>";
            var formElement = $(postFormStr);
            $('body').append(formElement);
            $(formElement).submit();
            this.spinner = false;
        },

        ok: async function () {
            let vm = this;

            this.spinner = true;
            let selected = []
            let activity_pickedPurposes = []
            let confirmations = []
            for (let a=0; a<this.application.activities.length; a++){
                let activity = this.application.activities[a]

                if (activity.licence_activity === this.selected_activity_tab_id){

                    let confirmation = this.licence.activity.filter(a => {

                        return a.id === activity.licence_activity;

                    })[0]
                    confirmation.confirmed=true;
                    confirmations.push(confirmation);

                    let proposed = activity.proposed_purposes
                    for (let p=0; p<proposed.length; p++){
                        let purpose = proposed[p]
                        if (['reissue','propose','selected'].includes(purpose.processing_status)){
                            selected.push(purpose)

                            let picked_purpose = this.pickedPurposes.filter(picked => {
                                return picked.id === purpose.purpose.id;
                            })[0]
                            activity_pickedPurposes.push(picked_purpose)
                        }
                    }
                }
            }

            vm.licence.purposes = selected;
            vm.licence.activity = confirmations;
            vm.licence.selected_purpose_ids = activity_pickedPurposes;

            let licence = JSON.parse(JSON.stringify(vm.licence));
            licence.purposes = vm.licence.purposes.map(purpose => {
                const date_formats = ["DD/MM/YYYY", "YYYY-MM-DD"];
                return {
                    ...purpose,
                    proposed_start_date: purpose.proposed_start_date ?
                        moment(purpose.proposed_start_date, date_formats).format('YYYY-MM-DD') : null,
                    proposed_end_date: purpose.proposed_end_date ?
                        moment(purpose.proposed_end_date, date_formats).format('YYYY-MM-DD') : null,
                }
            });

            this.setApplicationWorkflowState({bool: true});
            await this.finalDecisionData({ url: `/api/application/${this.application.id}/final_decision_data.json` }).then( async response => {

                await vm.$http.post(helpers.add_endpoint_json(api_endpoints.applications,vm.application.id+'/final_decision'),JSON.stringify(licence),{
                            emulateJSON:true,

                        }).then((response)=>{
                            this.spinner = false
                            this.setApplicationWorkflowState({bool: false});
                            vm.$router.push({ name:"internal-dash", });

                        },(error)=>{
                            this.spinner = false
                            this.setApplicationWorkflowState({bool: false});
                            swal(
                                'Application Error',
                                helpers.apiVueResourceError(error),
                                'error'
                            )

                        });

            },(error)=>{
                this.spinner = false
                this.setApplicationWorkflowState({bool: false});
                swal(
                    'Application Error',
                    helpers.apiVueResourceError(error),
                    'error'
                )

            });

        },
        getActivity: function(id) {
            const activity = this.licence.activity.find(activity => activity.id == id);
            return activity ? activity : {};
        },
        getPickedPurpose: function(_id){
            let picked = this.pickedPurposes.find(p => {return p.id===_id})
            if (!picked) {
                picked = {id: _id, isProposed: true}
                this.pickedPurposes.push(picked)
            }
            return picked
        },
        getCheckedItem: function(_id){
            let checked = this.licence.checked_items.find(c => {return c.id===_id})
            if (!checked) {
                checked = {
                    id: _id, 
                    isChecked: false,
                }
                this.licence.checked_items.push(checked)
            }
            return checked;
        },
        initialiseLicenceDetails() {
            var final_status = null;
            for(let proposal of this.proposed_licence){
                if (proposal.proposed_action.id =='propose_issue'){
                    final_status="issued"
                }
                if (proposal.proposed_action.id =='propose_decline'){
                    final_status="declined"
                }
                const processing_status = proposal.processing_status;
                if(!['with_officer_finalisation', 'awaiting_licence_fee_payment'].includes(processing_status)) {
                    continue;
                }
                const activity_id = proposal.licence_activity.id;
                this.licence.activity.push({
                    id: activity_id,
                    name: proposal.licence_activity.name,
                    start_date: proposal.proposed_start_date,
                    end_date: proposal.proposed_end_date,
                    reason: proposal.reason,
                    cc_email: proposal.cc_email,
                    final_status: final_status,
                    confirmed: false,
                    purposes: proposal.issued_purposes_id,
                });
            }
            if(this.application.id_check_status.id == 'accepted'){
                this.licence.id_check = true;
            }
            if(this.application.id_check_status.id == 'not_checked'){
                this.licence.id_check = false;
            }
            if(this.application.character_check_status.id == 'accepted'){
                this.licence.character_check = true;
            }
            if(this.application.character_check_status.id == 'not_checked'){
                this.licence.character_check = false;
            }
            if(this.application.return_check_status.id == 'accepted'){
                this.licence.return_check=true;
            }
            if(this.application.return_check_status.id == 'not_checked'){
                this.licence.return_check=false;
            }

            for (let a=0; a<this.application.activities.length; a++){
                let activity = this.application.activities[a];
                for(let p=0; p<activity.proposed_purposes.length; p++){
                    let purpose = activity.proposed_purposes[p]
                    let picked = this.pickedPurposes.find(p => {return p.id===purpose.purpose.id})
                    if (picked == null){
                        picked = {id: purpose.purpose.id, isProposed: false}
                        this.pickedPurposes.push(picked)
                    }
                    if (['reissue','propose'].includes(purpose.processing_status)) {
                        picked.isProposed = true

                    } else {
                        picked.isProposed = false
                    }
                    if (purpose.proposed_start_date != null && purpose.proposed_start_date.charAt(2)==='/'){
                        continue
                    }
                    let date1 = moment(purpose.proposed_start_date, 'YYYY-MM-DD').format('DD/MM/YYYY')
                    let date2 = moment(purpose.proposed_end_date, 'YYYY-MM-DD').format('DD/MM/YYYY')
                    if (purpose.proposed_start_date == null){
                        date1 = '';
                        date2 = ''
                    }
                    purpose.proposed_start_date = date1
                    purpose.proposed_end_date = date2
                }
            }
        },
        
        fetchProposeIssue(){
            let vm = this;
            
           vm.$http.get(helpers.add_endpoint_join(api_endpoints.applications,(vm.application.id+'/get_proposed_decisions/')))
            .then((response) => {
                vm.proposed_licence = response.body;
                this.initialiseLicenceDetails();
                
            }, (error) => {
               
                swal(
                    'Application Error',
                    helpers.apiVueResourceError(error),
                    'error'
                )
            });
        },
       
        eventListeners(){
            this.initDatePicker();
        },

        initFirstTab: function(force){
            const tab = $('#tabs-main li:first-child a')[0];
            var first_tab = this.application.activities[0].licence_activity

            if(tab) {
                tab.click();
            }
            else { // force first tab selection attributes.
                this.licenceActivities().filter(activity => {
                    if (activity.id==first_tab) {

                        this.setActivityTab({ id: activity.id, name: activity.name });
                    }
                })
            }
        },

        setTemporaryDocumentCollectionId: function(val) {
            this.temporary_document_collection_id = val;
        },

        userHasRole: function(role, activity_id) {
            return this.application.user_roles.filter(
                role_record => role_record.role == role && (!activity_id || activity_id == role_record.activity_id)
            ).length;
        },

        //Initialise Date Picker
        initDatePicker: function() {
            for (let a=0; a<this.application.activities.length; a++){
                let activity = this.application.activities[a];
                for (let p=0; p<activity.proposed_purposes.length; p++){
                    let purpose = activity.proposed_purposes[p]
                    let start_date = 'start_date_' + purpose.id
                    $(`[name='${start_date}']`).datetimepicker(this.datepickerOptions);
                    $(`[name='${start_date}']`).on('dp.change', function(e){
                        if ($(`[name='${start_date}']`).data('DateTimePicker') && $(`[name='${start_date}']`).data('DateTimePicker').date()) {
                            purpose.proposed_start_date =  e.date.format('DD/MM/YYYY');
                        }
                        else if ($(`[name='${start_date}']`).data('date') === "") {
                            purpose.proposed_start_date = "";
                        }
                        else {
                            purpose.proposed_start_date = "";
                        }
                    });
                    let end_date = 'end_date_' + purpose.id
                    $(`[name='${end_date}']`).datetimepicker(this.datepickerOptions);
                    $(`[name='${end_date}']`).on('dp.change', function(e){
                        if ($(`[name='${end_date}']`).data('DateTimePicker') && $(`[name='${end_date}']`).data('DateTimePicker').date()) {
                            purpose.proposed_end_date =  e.date.format('DD/MM/YYYY');
                        }
                        else if ($(`[name='${end_date}']`).data('date') === "") {
                            purpose.proposed_end_date = "";
                        }
                        else {
                            purpose.proposed_end_date = "";
                        }
                    });
                }
            }
        }
    },
    updated: function(){
        this.eventListeners();
    },
    mounted: function(){
        let vm = this;
        this.fetchProposeIssue();

        this.$nextTick(() => {
            vm.eventListeners();

        });

    },
    
}
</script>
<style scoped>
    .confirmation-checkbox {
        margin-top: 10px;
    }
    br {
        padding-bottom: 5px;
    }
</style>
