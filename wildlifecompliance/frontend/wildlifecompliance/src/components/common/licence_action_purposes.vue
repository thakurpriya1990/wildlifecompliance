<template lang="html">
    <div id="actionLicencePurpose">
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" :title="title" large>
            <div class="container-fluid">
                <div class="row">
                    <form class="form-horizontal" name="actionPurposeForm">
                        <alert :show.sync="showError" type="danger"><strong>{{errorString}}</strong></alert>
                        <div class="col-sm-12">
                            <div class="form-group">
                                <div class="row">
                                    <div v-if=hasActionableLicencePurposes class="col-sm-12">
                                        <div v-for="(purpose, index) in actionableLicencePurposes" v-bind:key="`purpose_${index}`">
                                            <div>
                                                <input type="checkbox" :value ="purpose.purpose.id" :id="purpose.purpose.id" v-model="action_licence.purpose_ids_list"> {{purpose.name}}
                                            </div>
                                        </div>
                                    </div>
                                    <div v-else class="col-sm-12">
                                        <span>You cannot apply this action to any purposes. This may be due to open applications that have yet to be processed.</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
            <div slot="footer">
                <button type="button" v-if="actioningPurposes" disabled class="btn btn-default" @click="ok"><i class="fa fa-spinner fa-spin"></i>{{actioning_text}} Purpose(s)</button>
                <button type="button" v-if="hasActionableLicencePurposes && !actioningPurposes" class="btn btn-primary" @click="ok">{{action_text}} Purpose(s)</button>
                <button type="button" class="btn btn-default" @click="cancel">Close</button>
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
export default {
    name:'LicenceActionPurposes',
    components:{
        modal,
        alert
    },
    props:{
        licence_id: String,
        licence_activity_purposes: Array,
        action: String
    },
    data:function () {
        let vm = this;
        return {
            isModalOpen:false,
            form:null,
            action_licence:{
                purpose_ids_list:[],
            },
            actioningPurposes: false,
            validation_form: null,
            errors: false,
            errorString: '',
            successString: '',
            success:false,
            checkbox_list: {
                application: 0,
                purpose_ids: [],
            },
            selectedActivityId: 0,
        }
    },
    computed: {
        ...mapGetters([
            'application_id',
        ]),
        showError: function() {
            var vm = this;
            return vm.errors;
        },
        title: function(){
            if (this.action == 'cancel'){
                return 'Select purpose(s) to cancel';
            } else if (this.action == 'suspend'){
                return 'Select purpose(s) to suspend';
            } else if (this.action == 'surrender'){
                return 'Select purpose(s) to surrender';
            } else if (this.action == 'reactivate-renew'){
                return 'Select purpose(s) to reactivate renew';
            } else if (this.action == 'reissue'){
                return 'Select purpose(s) to reissue';
            } else if (this.action == 'reinstate'){
                return 'Select purpose(s) to reinstate';
            }
        },
        action_text: function(){
            if (this.action == 'cancel'){
                return 'Cancel';
            } else if (this.action == 'suspend'){
                return 'Suspend';
            } else if (this.action == 'surrender'){
                return 'Surrender';
            } else if (this.action == 'reactivate-renew'){
                return 'Reactivate Renew';
            } else if (this.action == 'reissue'){
                return 'Reissue';
            } else if (this.action == 'reinstate'){
                return 'Reinstate';
            }
        },
        actioning_text: function(){
            if (this.action == 'cancel'){
                return 'Cancelling';
            } else if (this.action == 'suspend'){
                return 'Suspending';
            } else if (this.action == 'surrender'){
                return 'Surrendering';
            } else if (this.action == 'reactivate-renew'){
                return 'Reactivating Renew';
            } else if (this.action == 'reissue'){
                return 'Reissue';
            } else if (this.action == 'reinstate'){
                return 'Reinstating';
            }
        },
        actionableLicencePurposesByAppId: function(appId) {
            return this.licence_activity_purposes.filter(activity => {
                return activity.application===appId;
            });
        },
        actionableLicencePurposes: function() {
            return this.licence_activity_purposes;
        },
        hasActionableLicencePurposes: function() {
            return this.licence_activity_purposes.length > 0;
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
            this.action_licence = {
                purpose_ids_list:[]
            };
            this.errors = false;
            $('.has-error').removeClass('has-error');
            this.validation_form.resetForm();
        },
        close_back_to_application:function (app_id) {
            this.isModalOpen = false;
            this.action_licence = {
                purpose_ids_list:[]
            };
            this.errors = false;
            $('.has-error').removeClass('has-error');
            this.validation_form.resetForm();
            // route back to application for reissue.
            this.$router.push({name:"internal-application", params:{application_id: app_id}});
        },
        sendData:function(){
            let vm = this;
            let data = new FormData()
            vm.errors = false;
            vm.actioningPurposes = true;
            if (vm.action == 'cancel'){
                if (vm.action_licence.purpose_ids_list.length > 0){
                    data.purpose_ids_list = vm.action_licence.purpose_ids_list
                    data.selected_activity_id = vm.selectedActivityId;
                    vm.$http.post(helpers.add_endpoint_json(api_endpoints.licences,vm.licence_id+'/cancel_purposes'),JSON.stringify(data),{
                            emulateJSON:true,
                        }).then((response)=>{
                            swal(
                                    'Cancel Purposes',
                                    'The selected licenced purposes have been Cancelled.',
                                    'success'
                            )
                            vm.actioningPurposes = false;
                            vm.close();
                            vm.$emit('refreshFromResponse',response);
                        },(error)=>{
                            vm.errors = true;
                            vm.actioningPurposes = false;
                            vm.errorString = helpers.apiVueResourceError(error);
                        });
                } else {
                    vm.actioningPurposes = false;
                    swal(
                         'Cancel Purpose',
                         'Please select at least once licenced purpose to Cancel.',
                         'error'
                    )
                }
            } else if (vm.action == 'suspend'){
                if (vm.action_licence.purpose_ids_list.length > 0){
                    data.purpose_ids_list = vm.action_licence.purpose_ids_list
                    data.selected_activity_id = vm.selectedActivityId;
                    vm.$http.post(helpers.add_endpoint_json(api_endpoints.licences,vm.licence_id+'/suspend_purposes'),JSON.stringify(data),{
                            emulateJSON:true,
                        }).then((response)=>{
                            swal(
                                    'Suspend Purposes',
                                    'The selected licenced purposes have been Suspended.',
                                    'success'
                            )
                            vm.actioningPurposes = false;
                            vm.close();
                            vm.$emit('refreshFromResponse',response);
                        },(error)=>{
                            vm.errors = true;
                            vm.actioningPurposes = false;
                            vm.errorString = helpers.apiVueResourceError(error);
                        });
                } else {
                    vm.actioningPurposes = false;
                    swal(
                         'Suspend Purpose',
                         'Please select at least once licenced purpose to Suspend.',
                         'error'
                    )
                }
            } else if (vm.action == 'surrender'){
                if (vm.action_licence.purpose_ids_list.length > 0){
                    data.purpose_ids_list = vm.action_licence.purpose_ids_list
                    data.selected_activity_id = vm.selectedActivityId;
                    vm.$http.post(helpers.add_endpoint_json(api_endpoints.licences,vm.licence_id+'/surrender_purposes'),JSON.stringify(data),{
                            emulateJSON:true,
                        }).then((response)=>{
                            swal(
                                    'Surrender Purposes',
                                    'The selected licenced purposes have been Surrendered.',
                                    'success'
                            )
                            vm.actioningPurposes = false;
                            vm.close();
                            vm.$emit('refreshFromResponse',response);
                        },(error)=>{
                            vm.errors = true;
                            vm.actioningPurposes = false;
                            vm.errorString = helpers.apiVueResourceError(error);
                        });
                } else {
                    vm.actioningPurposes = false;
                    swal(
                         'Surrender Purpose',
                         'Please select at least once licenced purpose to Surrender.',
                         'error'
                    )
                }
            } else if (vm.action == 'reactivate-renew'){
                if (vm.action_licence.purpose_ids_list.length > 0){
                    data.purpose_ids_list = vm.action_licence.purpose_ids_list
                    data.selected_activity_id = vm.selectedActivityId;
                    vm.$http.post(helpers.add_endpoint_json(api_endpoints.licences,vm.licence_id+'/reactivate_renew_purposes'),JSON.stringify(data),{
                            emulateJSON:true,
                        }).then((response)=>{
                            swal(
                                    'Reactivate Renew Purposes',
                                    'Renew for the selected licenced purposes has been Reactivated.',
                                    'success'
                            )
                            vm.actioningPurposes = false;
                            vm.close();
                            vm.$emit('refreshFromResponse',response);
                        },(error)=>{
                            vm.errors = true;
                            vm.actioningPurposes = false;
                            vm.errorString = helpers.apiVueResourceError(error);
                        });
                } else {
                    vm.actioningPurposes = false;
                    swal(
                         'Reactivate Renew Purpose',
                         'Please select at least once licenced purpose to Reactivate Renew.',
                         'error'
                    )
                }
            } else if (vm.action == 'reissue'){
                if (vm.action_licence.purpose_ids_list.length > 0){
                    data.purpose_ids_list = vm.action_licence.purpose_ids_list
                    data.selected_activity_id = vm.selectedActivityId;
                    vm.$http.post(helpers.add_endpoint_json(api_endpoints.licences,vm.licence_id+'/reissue_purposes'),JSON.stringify(data),{
                            emulateJSON:true,
                        }).then((response)=>{
                            vm.actioningPurposes = false;
                            let p1 = this.licence_activity_purposes.filter(pur => {
                                return pur.purpose.id===this.action_licence.purpose_ids_list[0];
                            })
                            vm.close_back_to_application(p1[0].application);
                            vm.$emit('refreshFromResponse',response);
                        },(error)=>{
                            vm.errors = true;
                            vm.actioningPurposes = false;
                            vm.errorString = helpers.apiVueResourceError(error);
                        });
                } else {
                    vm.actioningPurposes = false;
                    swal(
                         'Reissue Purpose',
                         'Please select at least once licenced purpose to Reissue.',
                         'error'
                    )
                }
            } else if (vm.action == 'reinstate'){
                if (vm.action_licence.purpose_ids_list.length > 0){
                    data.purpose_ids_list = vm.action_licence.purpose_ids_list
                    data.selected_activity_id = vm.selectedActivityId;
                    vm.$http.post(helpers.add_endpoint_json(api_endpoints.licences,vm.licence_id+'/reinstate_purposes'),JSON.stringify(data),{
                            emulateJSON:true,
                        }).then((response)=>{
                            swal(
                                    'Reinstate Purposes',
                                    'The selected licenced purposes have been Reinstated.',
                                    'success'
                            )
                            vm.actioningPurposes = false;
                            vm.close();
                            vm.$emit('refreshFromResponse',response);
                        },(error)=>{
                            vm.errors = true;
                            vm.actioningPurposes = false;
                            vm.errorString = helpers.apiVueResourceError(error);
                        });
                } else {
                    vm.actioningPurposes = false;
                    swal(
                         'Reinstate Purpose',
                         'Please select at least once licenced purpose to Reinstate.',
                         'error'
                    )
                }
            }
        },
        addFormValidations: function() {
            let vm = this;
            vm.validation_form = $(vm.form).validate({
                rules:  {
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
        updateCheckboxList: function() {
            // TODO: filtered purpose checkbox list per application.

            let last_id = this.action_licence.purpose_ids_list.length-1
            let p1 = this.licence_activity_purposes.filter(pur => {
                return pur.purpose.id===this.action_licence.purpose_ids_list[last_id];
            })

            //var p1 = this.action_licence.purpose_ids_list[0];
            if (p1[0] && this.checkbox_list.application!==p1[0].application){
                // not the same application
                this.checkbox_list.application = p1[0].application;
                this.checkbox_list.purpose_ids = [];
                for (let i=0; i<this.licence_activity_purposes.length; i++){
                    // go through all purposes available
                    let p = this.licence_activity_purposes[i]

                    if (p.application===p1[0].application && this.action_licence.purpose_ids_list.find(id => id === p.purpose.id)){
                        // match on application and selected
                        this.checkbox_list.purpose_ids.push(p.purpose.id);
                    }
                }
            } else if (p1[0] && this.checkbox_list.application===p1[0].application){
                // same application
                this.checkbox_list.purpose_ids = [];
                for (let i=0; i<this.licence_activity_purposes.length; i++){
                    let p = this.licence_activity_purposes[i]
                    if (p.application===p1[0].application && this.action_licence.purpose_ids_list.find(id => id === p.purpose.id)){
                        // match on application and selected
                        this.checkbox_list.purpose_ids.push(p.purpose.id)
                    }
                }
            }
            if (!p1[0]){
                this.checkbox_list.application = 0;
                this.checkbox_list.purpose_ids = [];
            }
            //this.action_licence.purpose_ids_list = []

        },
   },
   mounted:function () {
        this.form = document.forms.actionPurposeForm;
        this.addFormValidations();
   }
}
</script>
<style lang="css">
</style>
