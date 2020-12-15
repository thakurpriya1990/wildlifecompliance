<template lang='html'>

<div id="access-menu">
    <CommsLogs :comms_url="comms_url" :logs_url="logs_url" :comms_add_url="comms_add_url" :disable_add_entry="false"/>

    <div class="row">
        <div class="panel panel-default">
            <div class="panel-heading">Submission</div>
            <div class="panel-body panel-collapse">
                <div class="row">
                    <div class="col-sm-12">
                        <strong>Submitted by</strong><br/>
                        {{ returns.submitter.first_name}} {{ returns.submitter.last_name}}
                    </div>
                    <div class="col-sm-12"><br/></div>
                    <div class="col-sm-12 top-buffer-s">
                        <strong>Lodged on</strong><br/>
                        {{ returns.lodgement_date | formatDate}}
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
            <div class="panel-heading">Workflow</div>
            <div class="panel-body panel-collapse">
                <div class="row">
                    <div class="col-sm-12">
                        <strong>Status</strong><br/>
                        {{ returns.processing_status }}
                    </div>
                    <div class="col-sm-12"><br/></div>
                    <div v-show="showAssignToList" class="col-sm-12 top-buffer-s">
                        <strong>Assigned Officer</strong><br/>
                        <div class="form-group">
                            <template>
                                <select ref="assigned_to" class="form-control" v-model="returns.assigned_to">
                                    <option v-for="member in returns.activity_curators" :value="member.id" v-bind:key="member.id">{{member.first_name}} {{member.last_name}}</option>
                                </select>
                                <a @click.prevent="assignToMe()" class="actionBtn pull-right">Assign to me</a>
                            </template>
                        </div>
                    </div>
                    <div v-show="!showAssignToList" class="col-sm-12 top-buffer-s">
                        <strong>Assigned Officer</strong><br/>
                        <div class="form-group"> {{ returns.assigned_to }} </div>
                    </div>

                    <!-- Workflow Actions -->
                    <div v-show="showActionButtons" class="col-sm-12 top-buffer-s">
                        <strong>Action</strong><br/><br/>
                        <button style="width:255px;" class="btn btn-primary btn-md" @click.prevent="acceptReturn()">Accept</button><br/><br/>
                        <button style="width:255px;" class="btn btn-primary btn-md" @click.prevent="amendmentRequest()">Request Amendment</button>
                        <br/><br/>
                    </div>

                </div>
            </div>
        </div>
    </div>

    <AmendmentRequest ref="amendment_request" ></AmendmentRequest>

</div>

</template>
<script>
import $ from 'jquery'
import Vue from 'vue'
import { mapActions, mapGetters } from 'vuex';
import datatable from '@vue-utils/datatable.vue'
import CommsLogs from '@common-components/comms_logs.vue'
import AmendmentRequest from './amendment_request.vue';
import ResponsiveDatatablesHelper from "@/utils/responsive_datatable_helper.js"
import '@/scss/forms/form.scss';
import {
    api_endpoints,
    helpers
}
from '@/utils/hooks'
export default {
    name: 'ReturnAccess',
    components: {
        CommsLogs,
        AmendmentRequest,
    },
    filters: {
        formatDate: function(data){
            return data ? moment(data).format('DD/MM/YYYY HH:mm:ss'): '';
        }
    },
    data() {
        let vm = this;
        return {
            spinner : false,

            // Filters
            logs_url: helpers.add_endpoint_json(api_endpoints.returns,vm.$route.params.return_id+'/action_log'),
            comms_url: helpers.add_endpoint_json(api_endpoints.returns,vm.$route.params.return_id+'/comms_log'),
            comms_add_url: helpers.add_endpoint_json(api_endpoints.returns,vm.$route.params.return_id+'/add_comms_log'),
            
        }
    },
    props:{
        form_width: {
            type: String,
            default: 'col-md-9'
        },
    },
    computed: {
        ...mapGetters([
            'returns',
            'returns_tabs',
            'selected_returns_tab_id',
            'species_list',
            'is_external',
            'current_user',
            'canAssignOfficerFor',
        ]),
        showActionButtons: function(){
            return this.returns.can_be_processed && this.returns.user_in_officers
        },
        showAssignToList: function(){
            return this.canAssignOfficerFor(this.returns.condition.licence_activity_id) && !this.returns.is_accepted && !this.returns.is_draft
        },
    },
    methods: {
        ...mapActions([
            'setReturnsTabId',
            'setReturnsSpecies',
            'setReturnsExternal',
            'setReturns',
            'loadCurrentUser',
        ]),
        eventListeners: function(){
        // none.
        },
        initMainTab: function() {
        // none.
        },
        initSelects: function(){
            const vm = this
            if (!vm.initSelects){
                vm.initSelects = true;
                vm.initMainTab();
            }
            vm.initAssignedOfficerSelect();            
        },
        initAssignedOfficerSelect: function(reinit=false){
            const vm = this
            if (reinit){
                $(vm.$refs.assigned_to).data('select2') ? $(vm.$refs.assigned_to).select2('destroy'): '';
            }
            // Assigned officer select
            $(vm.$refs.assigned_to).select2({
                "theme": "bootstrap",
                allowClear: true,
                placeholder:"Select Officer"
            }).
            on("select2:select",function (e) {
                e.stopImmediatePropagation();
                e.preventDefault();
                var selected = $(e.currentTarget);
                vm.returns.assigned_to = selected.val();
                vm.assignOfficer();
            }).on("select2:unselecting", function(e) {
                var vm = $(this);
                setTimeout(() => {
                    vm.select2('close');
                }, 0);
            }).on("select2:unselect",function (e) {
                e.stopImmediatePropagation();
                e.preventDefault();
                var selected = $(e.currentTarget);
                vm.returns.assigned_to = null;
                vm.assignOfficer();
            });
        },
        refreshFromResponse:function(response){
            this.setReturns(response.body);
            this.$nextTick(() => {
                this.initAssignedOfficerSelect(true);
                this.updateAssignedOfficerSelect();
            });
        },
        updateAssignedOfficerSelect:function(){
            $(this.$refs.assigned_to).val(this.returns.assigned_to);
            $(this.$refs.assigned_to).trigger('change');
        },
        assignToMe: async function(){
            await this.save_wo();
            const data = {
                // none.
            }
            this.$http.post(helpers.add_endpoint_json(api_endpoints.returns,(this.returns.id+'/assign_to_me')),JSON.stringify(data),{
                emulateJSON:true

            }).then((response) => {
                this.refreshFromResponse(response);
                this.updateAssignedOfficerSelect();

            }, (error) => {
                // this.revert();
                // this.updateAssignedOfficerSelect();
                console.log(error)
                swal(
                    'Application Error',
                    helpers.apiVueResourceError(error),
                    'error'
                )
            });
        },
        assignOfficer: async function(){
            await this.save_wo();
            let unassign = true;
            let data = {};
            unassign = this.returns.assigned_to == null ? true : false;
            data = {
                'officer_id': this.returns.assigned_to,
            };
            if (!unassign){
                this.$http.post(helpers.add_endpoint_json(api_endpoints.returns,(this.returns.id+'/assign_officer')),JSON.stringify(data),{
                    emulateJSON:true

                }).then((response) => {
                    this.refreshFromResponse(response);
                    this.updateAssignedOfficerSelect();

                }, (error) => {
                    // this.revert();
                    // this.updateAssignedOfficerSelect();
                    console.log(error)
                    swal(
                        'Returns Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    )
                });
            }
            else{
                this.$http.post(helpers.add_endpoint_json(api_endpoints.returns,(this.returns.id+'/unassign_officer')),JSON.stringify(data),{
                    emulateJSON:true

                }).then((response) => {
                    this.refreshFromResponse(response);
                    this.updateAssignedOfficerSelect();
    
                }, (error) => {
                    console.log(error)
                    // this.revert();
                    // this.updateAssignedOfficerSelect();
                    swal(
                        'Returns Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    )
                });
            }
        },
        save_wo: async function(props = { showNotification: true }) {
            const { showNotification } = props;
            this.form=document.forms.external_returns_form;
            var data = new FormData(this.form);

            this.$http.post(helpers.add_endpoint_json(api_endpoints.returns,this.returns.id+'/officer_comments'),data,{
                        emulateJSON:true,

            }).then((response)=>{

                return true // continue.
            
            },(error)=>{
                console.log(error);
                swal('Error',
                    'There was an error saving your return details.<br/>' + error.body,
                    'error'
                )
            });
        },
        amendmentRequest: async function(){
            await this.save_wo();
            this.$refs.amendment_request.amendment.text = '';
            this.$refs.amendment_request.isModalOpen = true;
        },
        acceptReturn: async function(){
            await this.save_wo();
            this.form=document.forms.internal_returns_form;

            this.$http.post(helpers.add_endpoint_json(api_endpoints.returns,this.returns.id+'/accept'),{
                            emulateJSON:true,

            }).then((response)=>{

                // Return to dashboard.
                this.$router.push({name:"internal-dash"});

            },(error)=>{
                console.log(error);
                swal('Error',
                        'There was an error accepting the return.<br/>' + error.body,
                        'error'
                )
            });
        }
    },
    updated: function(){
        this.$nextTick(() => {
            this.form = document.forms.internal_returns_form;
            this.initSelects();
            this.eventListeners();
        });
    },
    created: function(){
        // none.
    },
    mounted: function(){
        // none.
    },
}
</script>
