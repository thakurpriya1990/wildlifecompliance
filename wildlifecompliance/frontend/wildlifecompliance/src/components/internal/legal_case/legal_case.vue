<template lang="html">
    <div class="container">
      <div class="row">
        <div class="col-md-3">
          <h3>Case: {{ legal_case.number }}</h3>
        </div>
      </div>
          <div class="col-md-3">
            <CommsLogs :comms_url="comms_url" :logs_url="logs_url" :comms_add_url="comms_add_url" :disable_add_entry="false"/>
            <div class="row">
                <div class="panel panel-default">
                    <div class="panel-heading">
                        Workflow
                    </div>
                    <div class="panel-body panel-collapse">
                        <div class="row">
                            <div class="col-sm-12">
                                <strong>Status</strong><br/>
                                {{ statusDisplay }}<br/>
                            </div>
                        </div>

                        <div v-if="legal_case.allocated_group" class="form-group">
                          <div class="row">
                            <div class="col-sm-12 top-buffer-s">
                              <strong>Currently assigned to</strong><br/>
                            </div>
                          </div>
                          <div class="row">
                            <div class="col-sm-12">
                              <select :disabled="!legal_case.user_in_group" class="form-control" v-model="legal_case.assigned_to_id" @change="updateAssignedToId()">
                                <option  v-for="option in legal_case.allocated_group" :value="option.id" v-bind:key="option.id">
                                  {{ option.full_name }} 
                                </option>
                              </select>
                            </div>
                          </div>
                        </div>
                        <div v-if="legal_case.user_in_group">
                            <a @click="updateAssignedToId('current_user')" class="btn pull-right">
                                Assign to me
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="panel panel-default">
                    <div class="panel-heading">
                        Action 
                    </div>
                    <div class="panel-body panel-collapse">
                        <div class="row action-button">
                            <div class="col-sm-12">
                                  <a @click="openInspection()" class="btn btn-primary btn-block" >
                                    Inspection
                                  </a>
                            </div>
                        </div>
                        <div class="row action-button">
                          <div class="col-sm-12">
                                <a @click="addWorkflow('endorse')" class="btn btn-primary btn-block">
                                  Witness Statement
                                </a>
                          </div>
                        </div>
                        <div class="row action-button">
                          <div v-if="offenceVisibility" class="col-sm-12">
                                <a @click="openOffence()" class="btn btn-primary btn-block">
                                  Offence
                                </a>
                          </div>
                        </div>
                        
                        <div class="row action-button">
                          <div class="col-sm-12">
                                <a @click="addWorkflow('request_amendment')" class="btn btn-primary btn-block">
                                  Interview
                                </a>
                          </div>
                        </div>
                        <div class="row action-button">
                          <div class="col-sm-12">
                                <input 
                                :disabled="!sanctionOutcomeVisibility" 
                                type="button" 
                                class="btn btn-primary btn-block" 
                                value="Sanction Outcome" 
                                @click.prevent="openSanctionOutcome()" 
                                />
                                <!--a @click="openSanctionOutcome()" class="btn btn-primary btn-block">
                                  Sanction Outcome
                                </a-->
                          </div>
                        </div>
                        
                        <div  class="row action-button">
                          <div class="col-sm-12">
                                <a @click="open_sanction_outcome()" class="btn btn-primary btn-block">
                                  Brief of Evidence
                                </a>
                          </div>
                        </div>

                        <div  class="row action-button">
                          <div v-if="!readonlyForm" class="col-sm-12">
                                <a @click="addWorkflow('close')" class="btn btn-primary btn-block">
                                  Close
                                </a>
                          </div>
                        </div>

                    </div>
                </div>
            </div>
          </div>
          <div class="col-md-9" id="main-column">
            <div class="row">

                <div class="container-fluid">
                    <ul class="nav nav-pills aho2">
                        <li class="nav-item active"><a data-toggle="tab" :href="'#'+runTab">Running Sheet</a></li>
                        <li class="nav-item"><a data-toggle="tab" :href="'#'+cTab" >Case Details</a></li>
                        <li class="nav-item"><a data-toggle="tab" :href="'#'+rTab">Related Items</a></li>
                    </ul>
                    <div class="tab-content">
                        <div :id="runTab" class="tab-pane fade in active">
                          <FormSection :formCollapse="false" label="Running Sheet" Index="0">
                            <div class="col-sm-12 form-group"><div class="row">
                                <div>
                                    <!--datatable ref="legal_case_table" id="legal-case-table" :dtOptions="dtOptions" :dtHeaders="dtHeaders" /-->
                                </div>
                            </div></div>
                          </FormSection>
                        </div>
                        <div :id="cTab" class="tab-pane fade in">
                            <FormSection :formCollapse="false" label="Case Details">
                                <div class="col-sm-12 form-group"><div class="row">
                                    <label class="col-sm-4">Title</label>
                                    <input type="text" class="form-control" v-model="legal_case.title" />
                                </div></div>
                                <div class="col-sm-12 form-group"><div class="row">
                                    <label class="col-sm-4">Details</label>
                                    <textarea class="form-control location_address_field" v-model="legal_case.details" />
                                </div></div>
                                <div class="col-sm-9">
                                    <filefield 
                                    ref="legal_case_documents" 
                                    name="legal-case-documents" 
                                    :isRepeatable="true" 
                                    :documentActionUrl="legal_case.defaultDocumentUrl" 
                                    :readonly="readonlyForm"/>
                                </div>
                            </FormSection>
                        </div>
                        <div :id="rTab" class="tab-pane fade in">
                            <FormSection :formCollapse="false" label="Related Items">
                                <div class="col-sm-12 form-group"><div class="row">
                                    <div class="col-sm-12" v-if="relatedItemsVisibility">
                                        <RelatedItems v-bind:key="relatedItemsBindId" :parent_update_related_items="setRelatedItems" :readonlyForm="!canUserAction"/>
                                    </div>
                                </div></div>
                            </FormSection>
                        </div>
                    </div>
                </div>
            </div>
          </div>

        <div v-if="legal_case.can_user_action" class="navbar navbar-fixed-bottom" style="background-color: #f5f5f5 ">
            <div class="navbar-inner">
                <div class="container">
                    <p class="pull-right" style="margin-top:5px;">
                        <input type="button" @click.prevent="save('exit')" class="btn btn-primary" value="Save and Exit"/>
                        <input type="button" @click.prevent="save('noexit')" class="btn btn-primary" value="Save and Continue"/>
                    </p>
                </div>
            </div>
        </div>
        <!--div v-if="workflow_type">
          <InspectionWorkflow ref="add_workflow" :workflow_type="workflow_type" v-bind:key="workflowBindId" />
        </div-->
        <div v-if="offenceInitialised">
            <Offence 
            ref="offence" 
            :parent_update_function="loadLegalCase" 
            :region_id="legal_case.region_id" 
            :district_id="legal_case.district_id" 
            :allocated_group_id="legal_case.allocated_group_id" 
            v-bind:key="offenceBindId" 
            />
        </div>
        <div v-if="sanctionOutcomeInitialised">
            <SanctionOutcome 
            ref="sanction_outcome" 
            :parent_update_function="loadLegalCase"
            v-bind:key="sanctionOutcomeBindId" 
            />
        </div>
        <div v-if="inspectionInitialised">
            <Inspection
            ref="inspection" 
            :parent_update_function="loadLegalCase"
            v-bind:key="inspectionBindId" 
            />
        </div>
        <!--InspectionWorkflow ref="inspection_workflow" :workflow_type="workflow_type" v-bind:key="workflowBindId" /-->
    </div>
</template>
<script>
import Vue from "vue";
import FormSection from "@/components/forms/section_toggle.vue";
import CommsLogs from "@common-components/comms_logs.vue";
import datatable from '@vue-utils/datatable.vue'
import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";
import utils from "@/components/external/utils";
import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
import moment from 'moment';
import 'bootstrap/dist/css/bootstrap.css';
import 'eonasdan-bootstrap-datetimepicker';
import Offence from '../offence/offence_modal';
import SanctionOutcome from '../sanction_outcome/sanction_outcome_modal';
import Inspection from '../inspection/create_inspection_modal';
import filefield from '@/components/common/compliance_file.vue';
import RelatedItems from "@common-components/related_items.vue";
require("select2/dist/css/select2.min.css");
require("select2-bootstrap-theme/dist/select2-bootstrap.min.css");
import hash from 'object-hash';


export default {
  name: "ViewLegalCase",
  data: function() {
    return {
      uuid: 0,
      objectHash: null,
      runTab: 'runTab'+this._uid,
      rTab: 'rTab'+this._uid,
      cTab: 'cTab'+this._uid,
      current_schema: [],
      workflowBindId: '',
      workflow_type: '',
      comms_url: helpers.add_endpoint_json(
        api_endpoints.legal_case,
        this.$route.params.legal_case_id + "/comms_log"
      ),
      comms_add_url: helpers.add_endpoint_json(
        api_endpoints.legal_case,
        this.$route.params.legal_case_id + "/add_comms_log"
      ),
      logs_url: helpers.add_endpoint_json(
        api_endpoints.legal_case,
        this.$route.params.legal_case_id + "/action_log"
      ),
      sanctionOutcomeInitialised: false,
      offenceInitialised: false,
      inspectionInitialised: false,
      hashAttributeWhitelist: [],
      //dtOptions: {
      //    serverSide: true,
      //    searchDelay: 1000,
      //    lengthMenu: [ [10, 25, 50, 100, -1], [10, 25, 50, 100, "All"] ],
      //    order: [
      //      [0, 'desc']
      //    ],
      //    autoWidth: false,
      //    rowCallback: function (row, data) {
      //      $(row).addClass('appRecordRow');
      //    },
      //    language: {
      //      processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
      //    },
      //    responsive: true,
      //    processing: true,
      //    ajax: {
      //      'url': '/api/legal_case_paginated/get_paginated_datatable/?format=datatables',
      //      //'url': '/api/legal_case/datatable_list',
      //      //'dataSrc': '',
      //      //'dataSrc': 'data',
      //      //'data': function(d) {
      //      //    d.status_description = vm.filterStatus;
      //      //    d.inspection_description = vm.filterInspectionType;
      //      //    d.date_from = vm.filterPlannedFrom != '' && vm.filterPlannedFrom != null ? moment(vm.filterPlannedFrom, 'DD/MM/YYYY').format('YYYY-MM-DD'): '';
      //      //    d.date_to = vm.filterPlannedTo != '' && vm.filterPlannedTo != null ? moment(vm.filterPlannedTo, 'DD/MM/YYYY').format('YYYY-MM-DD'): '';
      //      //}
      //    },
      //     //dom: 'lBfrtip',
      //     //buttons: [
      //     //    'excel',
      //     //    'csv',
      //     //    ],
      //    columns: [
      //      {
      //          data: 'number',
      //          searchable: false,
      //          //orderable: false
      //      },
      //      {
      //          data: 'title',
      //          searchable: false,
      //          orderable: true
      //      },
      //      {
      //          data: 'status.name',
      //          searchable: false,
      //          orderable: true
      //      },
      //      {
      //          data: 'created_date',
      //          searchable: false,
      //          orderable: true
      //      },
      //      {
      //          data: "assigned_to",
      //          searchable: false,
      //          orderable: false,
      //          mRender: function (data, type, full) {
      //              if (data) {
      //                  return data.full_name;
      //              } else {
      //                  return '';
      //              }
      //          }
      //      },
      //      {
      //          data: 'user_action',
      //          searchable: false,
      //          orderable: false
      //      },
      //    ],
      //},
      //dtHeaders: [
      //  'Number',
      //  'Title',
      //  'Status',
      //  'Created Date',
      //  'Assigned to',
      //  'Action'
      //],
    };
  },
  components: {
    CommsLogs,
    FormSection,
    datatable,
    Offence,
    SanctionOutcome,
    filefield,
    RelatedItems,
    Inspection,
  },
  computed: {
    ...mapGetters('legalCaseStore', {
      legal_case: "legal_case",
    }),
    //...mapGetters({
    //    renderer_form_data: 'renderer_form_data'
    //}),
    csrf_token: function() {
      return helpers.getCookie("csrftoken");
    },
    statusDisplay: function() {
        return this.legal_case.status ? this.legal_case.status.name : '';
    },
    statusId: function() {
        return this.legal_case.status ? this.legal_case.status.id : '';
    },
    readonlyForm: function() {
        //let readonly = true
        //if (this.inspection.status && this.inspection.status.id === 'await_endorsement') {
        //} else if (this.inspection.id) {
        //    readonly = !this.inspection.can_user_action;
        //} else {
        //}
        //console.log(readonly)
        //return readonly
        return false
    },
    canUserAction: function() {
        return this.legal_case.can_user_action;
    },
    offenceExists: function() {
        for (let item of this.legal_case.related_items) {
            if (item.model_name.toLowerCase() === 'offence') {
                return true
            }
        }
        // return false if no related item is an Offence
        return false
    },
    offenceVisibility: function() {
        let offence_visibility = false;
        if (this.legal_case.status && this.legal_case.can_user_action) {
            offence_visibility = this.legal_case.status.id === 'open' ? true : false;
        }
        return offence_visibility;
    },
    sanctionOutcomeVisibility: function() {
        let sanction_outcome_visibility = false;
        if (this.legal_case.status && this.offenceExists && this.legal_case.can_user_action) {
            sanction_outcome_visibility = this.legal_case.status.id === 'open' ? true : false;
        }
        return sanction_outcome_visibility;
    },
    relatedItemsBindId: function() {
        let timeNow = Date.now()
        let bindId = null;
        if (this.legal_case && this.legal_case.id) {
            bindId = 'legal_case_' + this.legal_case.id + '_' + this._uid;
        } else {
            bindId = timeNow.toString();
        }
        return bindId;
    },
    relatedItemsVisibility: function() {
        let related_items_visibility = false;
        if (this.legal_case && this.legal_case.id) {
            related_items_visibility = true;
        }
        return related_items_visibility;
    },
    offenceBindId: function() {
        let offence_bind_id = ''
        //let timeNow = Date.now()
        //this.uuid += 1
        offence_bind_id = 'offence' + parseInt(this.uuid);
        return offence_bind_id;
    },
    sanctionOutcomeBindId: function() {
        let sanction_outcome_bind_id = ''
        //let timeNow = Date.now()
        //this.uuid += 1
        sanction_outcome_bind_id = 'sanction_outcome' + parseInt(this.uuid);
        return sanction_outcome_bind_id;
    },
    inspectionBindId: function() {
        let inspection_bind_id = ''
        //let timeNow = Date.now()
        //this.uuid += 1
        inspection_bind_id = 'inspection' + parseInt(this.uuid);
        return inspection_bind_id;
    },
  },
  filters: {
    formatDate: function(data) {
      return data ? moment(data).format("DD/MM/YYYY HH:mm:ss") : "";
    }
  },
  watch: {
  },
  methods: {
    ...mapActions('legalCaseStore', {
      loadLegalCase: 'loadLegalCase',
      saveLegalCase: 'saveLegalCase',
      setLegalCase: 'setLegalCase',
      setRelatedItems: 'setRelatedItems',
    }),
    //constructInspectionTeamTable: function() {
    //    //console.log('constructInspectionTeamTable');
    //    //console.log(this.inspection.inspection_team);
    //    this.$refs.inspection_team_table.vmDataTable.clear().draw();

    //    if(this.inspection.inspection_team){
    //      for(let i = 0; i< this.inspection.inspection_team.length; i++){
    //        //let already_exists = this.$refs.related_items_table.vmDataTable.columns(0).data()[0].includes(this.displayedEntity.related_items[i].id);

    //        let actionColumn = new Object();
    //        Object.assign(actionColumn, this.inspection.inspection_team[i]);
    //        //actionColumn.can_user_action = this.inspection.can_user_action;
    //        actionColumn.readonlyForm = this.readonlyForm;
    //        // Prevent removal of last team member (plus blank entry)
    //        if (this.inspection.inspection_team.length > 2) {
    //            actionColumn.can_remove = true;
    //        }

    //        //if (!already_exists) {
    //        if (this.inspection.inspection_team[i].id) {
    //        this.$refs.inspection_team_table.vmDataTable.row.add(
    //            {
    //                // 'id': this.inspectionTeam[i].id,
    //                'full_name': this.inspection.inspection_team[i].full_name,
    //                'member_role': this.inspection.inspection_team[i].member_role,
    //                'Action': actionColumn,
    //            }
    //        ).draw();
    //        }
    //      }
    //    }
    //},
    openInspection() {
      this.inspectionInitialised = true;
        this.$nextTick(() => {
          this.$refs.inspection.isModalOpen = true
      });
    },

    openSanctionOutcome(){
      this.uuid += 1;
      this.sanctionOutcomeInitialised = true;
      this.$nextTick(() => {
          this.$refs.sanction_outcome.isModalOpen = true;
      });
    },
    openOffence(){
      this.uuid += 1;
      this.offenceInitialised = true;
      this.$nextTick(() => {
          this.$refs.offence.isModalOpen = true;
      });
    },
    //createNewPersonClicked: function() {
    //  this.newPersonBeingCreated = true;
    //  this.displayCreateNewPerson = !this.displayCreateNewPerson;
    //},
    //addTeamMember: async function() {
    //    await this.modifyInspectionTeam({
    //        user_id: this.teamMemberSelected, 
    //        action: 'add'
    //    });
    //},
    //removeTeamMember: async function(e) {
    //    let memberId = e.target.getAttribute("data-member-id");
    //    await this.modifyInspectionTeam({
    //        user_id: memberId,
    //        action: 'remove'
    //    });
    //},
    //makeTeamLead: async function(e) {
    //    let memberId = e.target.getAttribute("data-member-id");
    //    await this.modifyInspectionTeam({
    //        user_id: memberId, 
    //        action: 'make_team_lead'
    //    });
    //},
    //entitySelected: async function(para) {
    //    console.log(para);
    //    await this.setPartyInspected(para);
    //},
    updateWorkflowBindId: function() {
        //let workflowBindId = ''
        let timeNow = Date.now()
        if (this.workflow_type) {
            this.workflowBindId = this.workflow_type + '_' + timeNow.toString();
        } else {
            this.workflowBindId = timeNow.toString();
        }
    },
    addWorkflow(workflow_type) {
      this.workflow_type = workflow_type;
      this.updateWorkflowBindId();
      this.$nextTick(() => {
        this.$refs.legal_case_workflow.isModalOpen = true;
      });
      // this.$refs.add_workflow.isModalOpen = true;
    },
    save: async function(returnToDash) {
      console.log(returnToDash)
      let savedLegalCase = null;
      //let savedPerson = null;
      if (this.legal_case.id) {
          savedLegalCase = await this.saveLegalCase({ create: false, internal: false });
      } else {
          savedLegalCase = await this.saveLegalCase({ create: true, internal: false });
      }
      this.calculateHash();
      //console.log(savedInspection);
      if (savedLegalCase && savedLegalCase.ok && returnToDash === 'exit') {
        // remove redundant eventListeners
        window.removeEventListener('beforeunload', this.leaving);
        window.removeEventListener('onblur', this.leaving);
        // return to dash
        this.$router.push({ name: 'internal-legal-case-dash' });
      }
    },
    addEventListeners: function() {
      //let vm = this;
      //let el_fr_date = $(vm.$refs.plannedForDatePicker);
      //let el_fr_time = $(vm.$refs.plannedForTimePicker);

      //// "From" field
      //el_fr_date.datetimepicker({
      //  format: "DD/MM/YYYY",
      //  minDate: "now",
      //  showClear: true
      //});
      //el_fr_date.on("dp.change", function(e) {
      //  if (el_fr_date.data("DateTimePicker").date()) {
      //    vm.inspection.planned_for_date = e.date.format("DD/MM/YYYY");
      //  } else if (el_fr_date.data("date") === "") {
      //    vm.inspection.planned_for_date = "";
      //  }
      //});
      //el_fr_time.datetimepicker({ format: "LT", showClear: true });
      //el_fr_time.on("dp.change", function(e) {
      //  if (el_fr_time.data("DateTimePicker").date()) {
      //    vm.inspection.planned_for_time = e.date.format("LT");
      //  } else if (el_fr_time.data("date") === "") {
      //    vm.inspection.planned_for_time = "";
      //  }
      //});
      //$('#inspection-team-table').on(
      //    'click',
      //    '.remove_button',
      //    vm.removeTeamMember,
      //    );
      //$('#inspection-team-table').on(
      //    'click',
      //    '.make_team_lead',
      //    vm.makeTeamLead,
      //    );
      window.addEventListener('beforeunload', this.leaving);
      window.addEventListener('onblur', this.leaving);
    },
    leaving: function(e) {
        let vm = this;
        let dialogText = '';
        if (this.formChanged()){
            e.returnValue = dialogText;
            return dialogText;
        }
    },
    formChanged: function(){
        let changed = false;
        let copiedLegalCase = {};
        Object.getOwnPropertyNames(this.legal_case).forEach(
            (val, idx, array) => {
                if (this.hashAttributeWhitelist.includes(val)) {
                    copiedLegalCase[val] = this.legal_case[val]
                }
            });
        this.addHashAttributes(copiedLegalCase);
        if(this.objectHash !== hash(copiedLegalCase)){
            changed = true;
        }
        return changed;
    },
    calculateHash: function() {
        let copiedLegalCase = {}
        Object.getOwnPropertyNames(this.legal_case).forEach(
            (val, idx, array) => {
                if (this.hashAttributeWhitelist.includes(val)) {
                    copiedLegalCase[val] = this.legal_case[val]
                }
            });
        this.addHashAttributes(copiedLegalCase);
        this.objectHash = hash(copiedLegalCase);
    },
    addHashAttributes: function(obj) {
        let copiedRendererFormData = Object.assign({}, this.renderer_form_data);
        obj.renderer_form_data = copiedRendererFormData;
        return obj;
    },
    updateAssignedToId: async function (user) {
        let url = helpers.add_endpoint_join(
            api_endpoints.legal_case,
            this.legal_case.id + '/update_assigned_to_id/'
            );
        let payload = null;
        if (user === 'current_user' && this.legal_case.user_in_group) {
            payload = {'current_user': true};
        } else if (user === 'blank') {
            payload = {'blank': true};
        } else {
            payload = { 'assigned_to_id': this.legal_case.assigned_to_id };
        }
        let res = await Vue.http.post(
            url,
            payload
        );
        await this.setLegalCase(res.body);
        this.$nextTick(() => {
            this.constructInspectionTeamTable();
        });
    },
  },
  created: async function() {
      if (this.$route.params.legal_case_id) {
          await this.loadLegalCase({ legal_case_id: this.$route.params.legal_case_id });
      }
      console.log(this)

      //// inspection_types
      //let returned_inspection_types = await cache_helper.getSetCacheList(
      //    'InspectionTypes',
      //    api_endpoints.inspection_types
      //    );
      //Object.assign(this.inspectionTypes, returned_inspection_types);
      //// blank entry allows user to clear selection
      //this.inspectionTypes.splice(0, 0,
      //    {
      //      id: "",
      //      description: "",
      //    });
      //// load current Inspection renderer schema
      //this.$nextTick(async () => {
      //    if (this.inspection.inspection_type_id) {
      //        await this.loadSchema();
      //    }
      //});
      // calling modifyInspectionTeam with null parameters returns the current list
      //this.modifyInspectionTeam({user_id: null, action: null});
      // create object hash
      //this.object_hash = hash(this.inspection);
      this.calculateHash();
  },
  destroyed: function() {
      window.removeEventListener('beforeunload', this.leaving);
      window.removeEventListener('onblur', this.leaving);
  },

  mounted: function() {
      //let vm = this;

      //// Time field controls
      //$('#plannedForTimePicker').datetimepicker({
      //        format: 'LT'
      //    });
      //$('#plannedForTimePicker').on('dp.change', function(e) {
      //    vm.setPlannedForTime(e.date.format('LT'));
      //});

      //// Initialise select2 for officer list
      //$(vm.$refs.inspectionteam).select2({
      //    "theme": "bootstrap",
      //    allowClear: true,
      //    placeholder:"Select Team Member"
      //            }).
      //on("select2:select",function (e) {
      //                    let selected = $(e.currentTarget);
      //                    vm.teamMemberSelected = selected.val();
      //                }).
      //on("select2:unselect",function (e) {
      //                    let selected = $(e.currentTarget);
      //                    vm.teamMemberSelected = selected.val();
      //                });
      
      this.$nextTick(async () => {
          this.addEventListeners();
          //this.constructInspectionTeamTable();
      });
  },
};
</script>

<style lang="css">
.action-button {
    margin-top: 5px;
}
#main-column {
  padding-left: 2%;
  padding-right: 0;
  margin-bottom: 50px;
}
.awesomplete {
    width: 100% !important;
}
.nav>li>a:focus, .nav>li>a:hover {
  text-decoration: none;
  background-color: #eee;
}
.nav-item {
  background-color: hsla(0, 0%, 78%, .8) !important;
  margin-bottom: 2px;
}
</style>
