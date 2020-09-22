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
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-12" v-for="(a, index) in applicationSelectedActivitiesForPurposes" v-bind:key="`a_${index}`">
                                        <input type="checkbox" name="licence_activity" :value ="a.id" :id="a.id" v-model="checkedActivities" > <b>{{a.activity_name_str}}</b>
                                        <div v-show="checkedActivities.find(checked => checked===a.id)">
                                            <div v-for="(p, p_idx) in a.proposed_purposes" v-bind:key="`p_${p_idx}`">
                                
                                                <div class="panel panel-primary">
                                                    <div class="panel-heading">
                                                        <h4 class="panel-title">{{p.purpose.short_name}}
                                                            <a class="panelClicker" :href="`#${p_idx}${index}`+purposeBody" data-toggle="collapse"  data-parent="#userInfo" expanded="true" :aria-controls="purposeBody">
                                                                <span class="glyphicon glyphicon-chevron-down pull-right "></span>
                                                            </a>
                                                        </h4>
                                                    </div>
                                                    <div class="panel-body panel-collapse collapse" :id="`${p_idx}${index}`+purposeBody">
                                                        <div class="row">
                                                            <div class="col-sm-3">
                                                                <input type="radio" :value ="true" :id="p.purpose.id" v-model="getPickedPurpose(p.purpose.id).isProposed" /> Issue &nbsp;
                                                                <input type="radio" :value ="false" :id="p.purpose.id" v-model="getPickedPurpose(p.purpose.id).isProposed" /> Decline &nbsp;
                                                            </div>
                                                            <div class="col-sm-3">
                                                                <div class="input-group date" v-if="getPickedPurpose(p.purpose.id).isProposed" :ref="`start_date_${p.id}`" style="width: 100%;">
                                                                    <input :readonly="!canEditLicenceDates && p.proposed_start_date" type="text" class="form-control" :name="`start_date_${p.id}`" placeholder="DD/MM/YYYY" v-model="p.proposed_start_date">
                                                                    <span class="input-group-addon">
                                                                        <span class="glyphicon glyphicon-calendar"></span>
                                                                    </span>
                                                                </div>
                                                            </div>
                                                            <div class="col-sm-3">                                                        
                                                                <div class="input-group date" v-if="getPickedPurpose(p.purpose.id).isProposed" :ref="`end_date_${p.id}`" style="width: 100%;">
                                                                    <input :readonly="!canEditLicenceDates && p.proposed_end_date" type="text" class="form-control" :name="`end_date_${p.id}`" placeholder="DD/MM/YYYY" v-model="p.proposed_end_date">
                                                                    <span class="input-group-addon">
                                                                        <span class="glyphicon glyphicon-calendar"></span>
                                                                    </span>
                                                                </div>
                                                            </div>
                                                            <div class="col-sm-12" v-if="getPickedPurpose(p.purpose.id).isProposed">
                                                                <div class="col-sm-3">
                                                                    <label class="control-label pull-left" for="Name">Additional Fee</label>
                                                                </div>
                                                                <div class="col-sm-6">
                                                                    <input type="text" ref="licence_fee" class="form-control" style="width:20%;" v-model="p.additional_fee" />
                                                                </div>
                                                            </div>
                                                            <div class="col-sm-12" v-if="getPickedPurpose(p.purpose.id).isProposed">
                                                                <div class="col-sm-3">
                                                                    <label class="control-label pull-left" for="Name">Fee Description 1</label>
                                                                </div>
                                                                <div class="col-sm-6">
                                                                    <input type="text" ref="licence_fee_text" class="form-control" style="width:70%;" v-model="p.additional_fee_text" />
                                                                </div>
                                                            </div>
                                                            <!-- Activity Purpose Free Text -->        
                                                            <div v-for="(free_text, pt_idx) in p.purpose_species_json" v-bind:key="`pt_${pt_idx}`">

                                                                <!--
                                                                <div class="col-sm-12">
                                                                    <div class="col-sm-3">
                                                                        <label class="control-label pull-left" for="Name">Header</label>
                                                                    </div>
                                                                    <div class="col-sm-6">
                                                                        <input type="text" ref="ap_text_header" class="form-control" style="width:70%;" v-model="free_text.header" />
                                                                    </div>
                                                                    <div v-show="free_text.is_additional_info" class="col-sm-3">
                                                                        <input type="checkbox" checked disabled/>
                                                                        <label>Is additional info</label>
                                                                    </div>
                                                                </div>
                                                                -->
                                                                <div class="col-sm-12">
                                                                    <div class="col-sm-3">
                                                                        <label class="control-label pull-left" for="Name">Details</label>
                                                                    </div>
                                                                    <div class="col-sm-6">
                                                                        <textarea ref="ap_text_detail" class="form-control" style="width:100%;" v-model="free_text.details" />
                                                                    </div>
                                                                    <div v-show="free_text.is_additional_info" class="col-sm-3">
                                                                        <input type="checkbox" checked disabled/>
                                                                        <label>Is additional info</label>
                                                                    </div>
                                                                </div>

                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>

                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="form-group">
                                <div class="row">
                                    <div class="col-sm-3">
                                        <label class="control-label pull-left" for="Name">Details for Applicant</label>
                                    </div>
                                    <div class="col-sm-9">
                                        <textarea name="licence_details" class="form-control" style="width:70%;" v-model="propose_issue.reason"></textarea>
                                    </div>
                                </div>
                            </div>
                            <div class="form-group">
                                <div class="row">
                                    <div class="col-sm-3">
                                        <label class="control-label pull-left" for="Name">Copy email</label>
                                    </div>
                                    <div class="col-sm-9">
                                            <input type="text" class="form-control" name="licence_cc" style="width:70%;" v-model="propose_issue.cc_email">
                                    </div>
                                </div>
                            </div>
                            <div class="form-group">
                                <div class="row">
                                    <div class="col-sm-3">
                                        <label class="control-label pull-left" for="Name">Documents for Applicant</label>
                                    </div>
            			            <div class="col-sm-9">
                                        <filefield 
                                            ref="issuance_documents" 
                                            name="issuance-documents" 
                                            :isRepeatable="true" 
                                            documentActionUrl="temporary_document" 
                                            @update-temp-doc-coll-id="setTemporaryIssuanceDocumentsCollectionId"/>
                                    </div>                                                              
                                </div>
                            </div>
                            <div class="form-group">
                                <div class="row">
                                    <div class="col-sm-3">
                                        <label class="control-label pull-left" for="Name">Details for Approver</label>
                                    </div>
                                    <div class="col-sm-9">
                                        <textarea name="licence_details" class="form-control" style="width:70%;" v-model="propose_issue.approver_detail"></textarea>
                                    </div>
                                </div>
                            </div>   
                            <div class="form-group">
                                <div class="row">
                                    <div class="col-sm-3">
                                        <label class="control-label pull-left" for="Name">Documents for Approver</label>
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
                            <div v-for="a, idx in checkedActivities">
                                <div class="form-group">
                                    <!-- <div class="row">
                                        <div class="col-sm-12">
                                            <label class="control-label pull-left" >Additional Fees for {{ getCheckedActivity(a).activity_name_str }}</label>
                                        </div>
                                    </div> -->
                                </div>                                 
                                <div class="form-group">
                                    <div class="row">
                                        <!-- <div class="col-sm-3">
                                            <label class="control-label pull-left" for="Name">Description</label>
                                        </div>
                                        <div class="col-sm-9">
                                            <input type="text" :name='"licence_fee_text_" + idx' class="form-control" style="width:70%;" v-model="getCheckedActivity(a).additional_fee_text" />
                                        </div> -->
                                    </div>
                                </div>  
                                <div class="form-group">
                                    <div class="row">
                                        <!-- <div class="col-sm-3">
                                            <label class="control-label pull-left" for="Name">Fee</label>
                                        </div>
                                        <div class="col-sm-9">
                                            <input type="text" ref="licence_fee" class="form-control" style="width:20%;" v-model="getCheckedActivity(a).additional_fee" />
                                        </div> -->
                                    </div>
                                </div>
                            </div>  
                        </div>
                    </form>
                </div>
            </div>
            <div slot="footer">
                <button type="button" v-if="issuingLicence" disabled class="btn btn-primary" @click="ok"><i class="fa fa-spinner fa-spin"></i>Proposing Issue</button>
                <button type="button" v-else class="btn btn-primary" @click="ok">Propose Issue</button>
                <button type="button" class="btn btn-primary" @click="cancel">Cancel</button>
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
            purposeBody: `purposeBody${vm._uid}`,
            isModalOpen:false,
            form:null,
            propose_issue:{
                activity: [],
                purposes: [],
                cc_email:null,
                reason:null,
                approver_detail:null,
                // additional_fee_text:null,
                // additional_fee:0,
                temporary_document_email_id: null,
                activities: null,
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
            pickedPurposes: [],
            checkedActivities: [],
            additionalFees: []
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
            'selected_activity_tab_id',
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
        applicationSelectedActivitiesForPurposes: function() {
            return this.application.activities.filter( activity => { 
                // if (activity.additional_fee==null){
                //     activity.additional_fee = '0.00'
                // }
                return activity.processing_status.name.match(/with officer/gi) 
                } // only non-processed activities.
            );
        },
        applicationSelectedActivity: function() {
            let val = this.application.activities.find(
                activity => { return activity.licence_activity === this.selected_activity_tab_id } 
            );
            return val
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
                purposes:[],
            };
            this.errors = false;
            $('.has-error').removeClass('has-error');
            this.validation_form.resetForm();

            // this.application.activities.forEach(a => {
            //     a.additional_fee = '0.00'
            //     a.additional_fee_text = null
            // });
            this.checkedActivities = [];
            this.pickedPurposes = [];
        },
        fetchContact: function(id){
            let vm = this;
            vm.$http.get(api_endpoints.contact(id)).then((response) => {
                vm.contact = response.body; vm.isModalOpen = true;
            },(error) => {
                console.log(error);
            } );
        },
        getCheckedActivity: function(_id){
            return this.applicationSelectedActivitiesForPurposes.find(a => {
                return a.id===_id
            });
        },
        getPickedPurpose: function(_id){
            let picked = this.pickedPurposes.find(p => {return p.id===_id})
            if (!picked) {
                picked = {
                    id: _id, 
                    isProposed: true,
                    additional_fee: 0,
                    additional_fee_text: '',
                    species_header: '',
                    species_text: '',
                }
                this.pickedPurposes.push(picked)
            }
            return picked
        },
        isPickedPurpose: function(_id){
            let activities = this.applicationSelectedActivitiesForPurposes.filter( a => {return this.checkedActivities.includes(a.id)})
            return activities.find(a => { 
                return a.purposes.find(p => p.id === _id)
            })
        },
        setTemporaryIssuanceDocumentsCollectionId: function(val) {
            this.propose_issue.issuance_documents_id = val;
        },
        setTemporaryEmailCollectionId: function(val) {
            this.propose_issue.email_attachments_id = val;
        },
        sendData:function(){
            let vm = this;
            vm.errors = false;
            vm.propose_issue.purposes = vm.pickedPurposes.filter(p => { return this.isPickedPurpose(p.id)} );
            vm.propose_issue.activity = vm.checkedActivities;
            vm.propose_issue.activities = vm.applicationSelectedActivitiesForPurposes.filter( a => {return vm.checkedActivities.includes(a.id)});
            let propose_issue = JSON.parse(JSON.stringify(vm.propose_issue));
            vm.issuingLicence = true;
            vm.$http.post(helpers.add_endpoint_json(api_endpoints.applications,vm.application_id+'/proposed_licence'),JSON.stringify(vm.propose_issue),{
                    emulateJSON:true,
                }).then((response)=>{

                    vm.$router.push({name:"internal-dash",});     

                },(error)=>{
                    vm.errors = true;
                    vm.issuingLicence = false;
                    vm.errorString = helpers.apiVueResourceError(error);
                });

            
        },
        addFormValidations: function() {
            let vm = this;
            vm.validation_form = $(vm.form).validate({
                rules:  {
                    start_date: { required: this.canEditLicenceDates },
                    due_date: { required: this.canEditLicenceDates },
                    licence_details: "required",
                    licence_activity: { required: true},
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
       initialiseAttributes: function() {
           //this.preloadProposedPurpose()

       },
       eventListeners:function () {
            let vm = this;
            // Initialise Date Picker
            for (let i=0; i<vm.applicationSelectedActivitiesForPurposes.length; i++){
                let act = vm.applicationSelectedActivitiesForPurposes[i]
                for (let p=0; p<act.proposed_purposes.length; p++){
                    let purpose = act.proposed_purposes[p]
                    let start_date = 'start_date_' + purpose.id
                    $(`[name='${start_date}']`).datetimepicker(vm.datepickerOptions);
                    $(`[name='${start_date}']`).on('dp.change', function(e){
                        if ($(`[name='${start_date}']`).data('DateTimePicker').date()) {
                            purpose.proposed_start_date =  e.date.format('DD/MM/YYYY');
                        }
                        else if ($(`[name='${start_date}']`).data('date') === "") {
                            purpose.proposed_start_date = "";
                        }
                    });
                    let end_date = 'end_date_' + purpose.id
                    $(`[name='${end_date}']`).datetimepicker(vm.datepickerOptions);
                    $(`[name='${end_date}']`).on('dp.change', function(e){
                        if ($(`[name='${end_date}']`).data('DateTimePicker').date()) {
                            purpose.proposed_end_date =  e.date.format('DD/MM/YYYY');
                        }
                        else if ($(`[name='${end_date}']`).data('date') === "") {
                            purpose.proposed_end_date = "";
                        }
                    });
                }
            }
         },
         preloadProposedPurpose: function() {
            for (let i=0; i<this.applicationSelectedActivitiesForPurposes.length; i++){
                let act = this.applicationSelectedActivitiesForPurposes[i]
                for (let p=0; p<act.proposed_purposes.length; p++){
                    let proposed = act.proposed_purposes[p]
                    proposed.species_header_1 = proposed.purpose.species_header_1
                    proposed.species_header_2 = proposed.purpose.species_header_2
                    proposed.species_header_3 = proposed.purpose.species_header_3
                    proposed.species_header_4 = proposed.purpose.species_header_4
                    proposed.species_header_5 = proposed.purpose.species_header_5
                    proposed.species_header_6 = proposed.purpose.species_header_6
                    proposed.species_text_1 = proposed.purpose.species_text_1
                    proposed.species_text_2 = proposed.purpose.species_text_2
                    proposed.species_text_3 = proposed.purpose.species_text_3
                    proposed.species_text_4 = proposed.purpose.species_text_4
                    proposed.species_text_5 = proposed.purpose.species_text_5
                    proposed.species_text_6 = proposed.purpose.species_text_6
                }
            }             
         },
        preloadLastActivity: function() {
            let activities = this.applicationSelectedActivitiesForPurposes
            for(let a=0; a<activities.length; a++){
                let activity = activities[a]

                for(let p=0; p<activity.proposed_purposes.length; p++){
                    let purpose = activity.proposed_purposes[p]
                    if (purpose.proposed_start_date == null || purpose.proposed_start_date.charAt(2)==='/'){
                        continue
                    }
                    let date1 = moment(purpose.proposed_start_date, 'YYYY-MM-DD').format('DD/MM/YYYY')
                    let date2 = moment(purpose.proposed_end_date, 'YYYY-MM-DD').format('DD/MM/YYYY')
                    purpose.proposed_start_date = date1
                    purpose.proposed_end_date = date2
                }
            }
        },
   },
   updated:function () {
        this.$nextTick(()=>{
            this.eventListeners();
        });
   },
   mounted:function () {
        this.form = document.forms.licenceForm;
        this.addFormValidations();
        this.$nextTick(()=>{
            this.eventListeners();
        });
        this.initialiseAttributes();
   }
}
</script>

<style lang="css">
</style>
