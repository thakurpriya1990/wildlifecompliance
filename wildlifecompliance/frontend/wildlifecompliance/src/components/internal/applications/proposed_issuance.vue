<template lang="html">
    <div id="proposedIssuanceLicence">
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" :title="title" large>
            <div class="container-fluid">
                <div class="row">
                    <form class="form-horizontal" name="licenceForm">
                        <alert :show.sync="showError" type="danger"><strong>{{errorString}}</strong></alert>
                        <div class="col-sm-12">
                            <div class="form-group">
                                <div class="row">
                                    <div class="col-sm-12">
                                        <label class="control-label" for="Name">Select licensed activities to Propose Issue</label>
                                        <div v-for="activity in visibleLicenceActivities">
                                            <div v-for="p in activity.purpose">
                                                <input type="checkbox" :value ="p.id" :id="p.id" v-model="propose_issue.purposes">{{p.name}}                                                
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="form-group" v-if="canEditLicenceDates">
                                <div class="row">
                                    <div class="col-sm-3">
                                        
                                        <label class="control-label pull-left" for="Name">Proposed Start Date</label>
                                    </div>
                                    <div class="col-sm-9">
                                        <div class="input-group date" ref="start_date" style="width: 70%;">
                                            <input type="text" class="form-control" name="start_date" placeholder="DD/MM/YYYY" v-model="propose_issue.start_date">
                                            <span class="input-group-addon">
                                                <span class="glyphicon glyphicon-calendar"></span>
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="form-group" v-if="canEditLicenceDates">
                                <div class="row">
                                    <div class="col-sm-3">
                                        <label class="control-label pull-left" for="Name">Proposed Expiry Date</label>
                                    </div>
                                    <div class="col-sm-9">
                                        <div class="input-group date" ref="due_date" style="width: 70%;">
                                            <input type="text" class="form-control" name="due_date" placeholder="DD/MM/YYYY" v-model="propose_issue.expiry_date">
                                            <span class="input-group-addon">
                                                <span class="glyphicon glyphicon-calendar"></span>
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="form-group">
                                <div class="row">
                                    <div class="col-sm-3">
                                        <label class="control-label pull-left" for="Name">Proposed Details</label>
                                    </div>
                                    <div class="col-sm-9">
                                        <textarea name="licence_details" class="form-control" style="width:70%;" v-model="propose_issue.reason"></textarea>
                                    </div>
                                </div>
                            </div>
                            <div class="form-group">
                                <div class="row">
                                    <div class="col-sm-3">
                                        <label class="control-label pull-left" for="Name">Proposed CC email</label>
                                    </div>
                                    <div class="col-sm-9">
                                            <input type="text" class="form-control" name="licence_cc" style="width:70%;" v-model="propose_issue.cc_email">
                                    </div>
                                </div>
                            </div>
                            <div class="form-group">
                                <div class="row">
                                    <div class="col-sm-3">
                                        <label class="control-label pull-left" for="Name">Proposed Attachments</label>
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
                            <div class="form-group">
                                <div class="row">
                                    <div class="col-sm-3">
                                        <label class="control-label pull-left" for="Name">Email Attachments</label>
                                    </div>
            			            <div class="col-sm-9">
                                        <filefield 
                                            ref="comms_log_file" 
                                            name="comms-log-file" 
                                            :isRepeatable="true" 
                                            documentActionUrl="temporary_document" 
                                            @update-temp-doc-coll-id="setTemporaryEmailCollectionId"/>
                                    </div>                                                              
                                </div>
                            </div>   
                        </div>
                    </form>
                </div>
            </div>
            <div slot="footer">
                <button type="button" v-if="issuingLicence" disabled class="btn btn-default" @click="ok"><i class="fa fa-spinner fa-spin"></i>Proposing Issue</button>
                <button type="button" v-else class="btn btn-success" @click="ok">Propose Issue</button>
                <button type="button" class="btn btn-default" @click="cancel">Cancel</button>
            </div>
        </modal>
    </div>
</template>

<script>
//import $ from 'jquery'
import modal from '@vue-utils/bootstrap-modal.vue'
import alert from '@vue-utils/alert.vue'
import {helpers,api_endpoints} from "@/utils/hooks.js"
import { mapGetters } from 'vuex'
import filefield from '@/components/common/compliance_file.vue'
export default {
    name:'Proposed-Licence',
    components:{
        modal,
        alert,
        filefield,
    },
    props:{
    },
    data:function () {
        let vm = this;
        return {
            isModalOpen:false,
            form:null,
            propose_issue:{
                activity:[],
                purposes:[],
                cc_email:null,
                reason:null,
                expiry_date:null,
                start_date:null,
            },
            issuingLicence: false,
            validation_form: null,
            errors: false,
            errorString: '',
            successString: '',
            success:false,
            datepickerOptions:{
                format: 'DD/MM/YYYY',
                showClear:true,
                useCurrent:false,
                keepInvalid:true,
                allowInputToggle:true
            },
            temporary_document_colection_id: null,
            temporary_document_email_id: null,
        }
    },
    computed: {
        ...mapGetters([
            'application',
            'application_id',
            'licence_type_data',
            'hasRole',
            'licenceActivities',
            'canAssignOfficerFor',
        ]),
        canEditLicenceDates: function() {
            return this.application.application_type && this.application.application_type.id !== 'amend_activity';
        },
        showError: function() {
            var vm = this;
            return vm.errors;
        },
        title: function(){
        // TODO: application processing_status doesnt have a "with approver" status (disturbance legacy), need to fix
            return this.application.processing_status.id == 'with_approver' ? 'Issue Licence' : 'Propose to issue licence';
        },
        visibleLicenceActivities: function() {
            console.log('visibleLicenceActivities')
            console.log(this.licenceActivities())
            var activities = this.licenceActivities().filter(
                // filter on activity user has perms for.
                activity => { return this.canAssignOfficerFor(activity.id) }                
            );
            console.log(activities)
            return activities;
        },
        applicationIssuanceDocumentUrl: function() {
            let url = '';
            if (this.selected_activity_tab_id) {
                url = helpers.add_endpoint_join(
                    api_endpoints.application_selected_activity,
                    this.selected_activity_tab_id + "/process_issuance_document/"
                )
            }
            return url;
        },
    },
    methods:{
        ok:function () {
            let vm =this;
            if($(vm.form).valid()){
                vm.sendData();
            }
        },
        cancel:function () {
            this.close()
        },
        close:function () {
            this.isModalOpen = false;
            this.propose_issue = {
                activity:[],
                cc_email:null,
                reason:null,
                expiry_date:null,
                start_date:null
            };
            this.errors = false;
            $('.has-error').removeClass('has-error');
            this.validation_form.resetForm();
        },
        fetchContact: function(id){
            let vm = this;
            vm.$http.get(api_endpoints.contact(id)).then((response) => {
                vm.contact = response.body; vm.isModalOpen = true;
            },(error) => {
                console.log(error);
            } );
        },
        setTemporaryDocumentCollectionId: function(val) {
            this.temporary_document_collection_id = val;
        },
        setTemporaryEmailCollectionId: function(val) {
            this.temporary_document_email_id = val;
        },
        sendData:function(){
            let vm = this;
            vm.errors = false;
            vm.propose_issue.proposed_attachments_id = this.temporary_document_collection_id;
            vm.propose_issue.email_attachments_id = this.temporary_document_email_id;
            let propose_issue = JSON.parse(JSON.stringify(vm.propose_issue));
            vm.issuingLicence = true;
            if (propose_issue.purposes.length > 0){
                vm.$http.post(helpers.add_endpoint_json(api_endpoints.applications,vm.application_id+'/proposed_licence'),JSON.stringify(vm.propose_issue),{
                        emulateJSON:true,
                    }).then((response)=>{
                        //swal(
                        //        'Propose Issue',
                        //        'The selected licenced activities have been proposed for Issue.',
                        //        'success'
                        //)
                        //vm.issuingLicence = false;
                        //vm.close();
                        //vm.$emit('refreshFromResponse',response);
                        vm.$router.push({
                            name:"internal-dash",
                        });     
                    },(error)=>{
                        vm.errors = true;
                        vm.issuingLicence = false;
                        vm.errorString = helpers.apiVueResourceError(error);
                    });
            } else {
                vm.issuingLicence = false;
                swal(
                     'Propose Issue',
                     'Please select at least once licenced purpose to Propose Issue.',
                     'error'
                )
            }
            
        },
        addFormValidations: function() {
            let vm = this;
            vm.validation_form = $(vm.form).validate({
                rules:  {
                    start_date: { required: this.canEditLicenceDates },
                    due_date: { required: this.canEditLicenceDates },
                    licence_details: "required",
                },
                messages: {
                },
                showErrors: function(errorMap, errorList) {
                    $.each(this.validElements(), function(index, element) {
                        var $element = $(element);
                        $element.attr("data-original-title", "").parents('.form-group').removeClass('has-error');
                    });
                    // destroy tooltips on valid elements
                    $("." + this.settings.validClass).tooltip("destroy");
                    // add or update tooltips
                    for (var i = 0; i < errorList.length; i++) {
                        var error = errorList[i];
                        $(error.element)
                            .tooltip({
                                trigger: "focus"
                            })
                            .attr("data-original-title", error.message)
                            .parents('.form-group').addClass('has-error');
                    }
                }
            });
       },
       eventListeners:function () {
            let vm = this;
            // Initialise Date Picker
            $(vm.$refs.due_date).datetimepicker(vm.datepickerOptions);
            $(vm.$refs.due_date).on('dp.change', function(e){
                if ($(vm.$refs.due_date).data('DateTimePicker').date()) {
                    vm.propose_issue.expiry_date =  e.date.format('DD/MM/YYYY');
                }
                else if ($(vm.$refs.due_date).data('date') === "") {
                    vm.propose_issue.expiry_date = "";
                }
             });
            $(vm.$refs.start_date).datetimepicker(vm.datepickerOptions);
            $(vm.$refs.start_date).on('dp.change', function(e){
                if ($(vm.$refs.start_date).data('DateTimePicker').date()) {
                    vm.propose_issue.start_date =  e.date.format('DD/MM/YYYY');
                }
                else if ($(vm.$refs.start_date).data('date') === "") {
                    vm.propose_issue.start_date = "";
                }
             });
        },
        preloadLastActivity: function() {
            this.$http.get(
                helpers.add_endpoint_json(api_endpoints.applications, this.application_id+'/last_current_activity')
            ).then((response) => {
                if(response.body.activity) {
                    const start_date = response.body.activity.start_date;
                    const expiry_date = response.body.activity.expiry_date;
                    this.propose_issue.start_date = moment(start_date, 'YYYY-MM-DD').format('DD/MM/YYYY');
                    this.propose_issue.expiry_date = moment(expiry_date, 'YYYY-MM-DD').format('DD/MM/YYYY');
                }
            },(error) => {
                console.log(error);
            } );
        },
   },
   mounted:function () {
        this.form = document.forms.licenceForm;
        this.addFormValidations();
        this.$nextTick(()=>{
            this.eventListeners();
        });
   }
}
</script>

<style lang="css">
</style>
