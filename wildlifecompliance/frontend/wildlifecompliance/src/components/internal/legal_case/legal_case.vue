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
                            <div v-if="canUserAction" class="col-sm-12">
                                  <a @click="openInspection()" class="btn btn-primary btn-block" >
                                    Inspection
                                  </a>
                            </div>
                        </div>
                        <div class="row action-button">
                          <div v-if="canUserAction && offenceVisibility" class="col-sm-12">
                                <a @click="openOffence()" class="btn btn-primary btn-block">
                                  Offence
                                </a>
                          </div>
                        </div>
                        <div class="row action-button">
                          <div v-if="canUserAction" class="col-sm-12">
                                <input 
                                :disabled="!sanctionOutcomeVisibility" 
                                type="button" 
                                class="btn btn-primary btn-block" 
                                value="Sanction Outcome" 
                                @click.prevent="openSanctionOutcome()" 
                                />
                          </div>
                        </div>
                        
                        <div  class="row action-button">
                          <div v-if="canUserAction" class="col-sm-12">
                                <a @click="open_sanction_outcome()" class="btn btn-primary btn-block">
                                  Brief of Evidence
                                </a>
                          </div>
                        </div>

                        <div id="close-button" class="row action-button">
                          <div v-if="canUserAction" class="col-sm-12">
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
                                    <div class="row action-button">
                                        <!--div v-if="canUserAction" class="col-sm-12"-->
                                        <!--div class="col-sm-1 pull-right" /-->
                                        <div v-if="canUserAction">
                                              <!--a @click="createNewRunningSheetEntry()" class="btn btn-primary btn-block" -->
                                              <a @click="createNewRunningSheetEntry()" class="btn btn-primary pull-right new-row-button" >
                                                New Row
                                              </a>
                                        </div>
                                    </div>
                                    <datatable 
                                    ref="running_sheet_table" 
                                    id="running-sheet-table" 
                                    :dtOptions="dtOptionsRunningSheet" 
                                    :dtHeaders="dtHeadersRunningSheet"
                                    parentStyle=" "
                                    />
                                </div>
                            </div></div>
                          </FormSection>
                        </div>
                        <div :id="cTab" class="tab-pane fade in">
                            <FormSection :formCollapse="false" label="Case Details">
                                <div class="col-sm-12 form-group"><div class="row">
                                    <label class="col-sm-10">Title
                                        <input :readonly="readonlyForm" type="text" class="form-control" v-model="legal_case.title" />
                                    </label>
                                </div></div>
                                <div class="col-sm-12 form-group"><div class="row">
                                    <label class="col-sm-10">Details
                                        <textarea :readonly="readonlyForm" class="form-control location_address_field" v-model="legal_case.details" />
                                    </label>
                                </div></div>
                                <div class="col-sm-12 form-group"><div class="row">
                                    <div v-if="legal_case.defaultDocumentUrl">
                                        <label class="col-sm-10">Documents
                                            <filefield 
                                            ref="legal_case_documents" 
                                            name="legal-case-documents" 
                                            :isRepeatable="true" 
                                            :documentActionUrl="legal_case.defaultDocumentUrl" 
                                            :readonly="readonlyForm"
                                            />
                                        </label>
                                    </div>
                                </div></div>
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

        <div v-if="canUserAction" class="navbar navbar-fixed-bottom" style="background-color: #f5f5f5 ">
            <div class="navbar-inner">
                <div class="container">
                    <p class="pull-right" style="margin-top:5px;">
                        <button v-if="showSpinner && showExit" disabled type="button" @click.prevent="save('exit')" class="btn btn-primary">
                            <i class="fa fa-spinner fa-spin"/> Saving</button>
                        <button v-else type="button" @click.prevent="save('exit')" class="btn btn-primary" >Save and Exit</button>
                        <button v-if="showSpinner && !showExit" disabled type="button" @click.prevent="save('noexit')" class="btn btn-primary" >
                            <i class="fa fa-spinner fa-spin"/> Saving</button>
                        <button v-else type="button" @click.prevent="save('noexit')" class="btn btn-primary">Save and Continue</button>
                    </p>
                </div>
            </div>
        </div>
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
        <Magic ref="magic" />
        <SearchPersonOrganisationModal 
        ref="search_person_or_organisation_modal"
        :readonlyForm="readonlyForm"
        v-bind:key="searchPersonOrganisationBindId"
        @person-selected="insertPersonModalUrl"
        :rowNumberSelected="rowNumberSelected"
        />
        <div v-if="runningSheetHistoryEntryBindId">
            <RunningSheetHistory 
            ref="running_sheet_history"
            :runningSheetHistoryEntryInstance="runningSheetHistoryEntryInstance"
            v-bind:key="runningSheetHistoryEntryBindId"
            />
        </div>
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
import Magic from './magic';
import SearchPersonOrganisationModal from '@/components/common/search_person_or_organisation_modal';
import _ from 'lodash';
import RunningSheetHistory from './running_sheet_history'


export default {
    name: "ViewLegalCase",
    data: function() {
        return {
            uuid: 0,
            showSpinner: false,
            showExit: false,
            rowNumberSelected: '',
            runningSheetUrl: [],
            runningSheetEntriesUpdated: [],
            runningSheetHistoryEntryBindId: '',
            runningSheetHistoryEntryInstance: '',
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
            searchPersonOrganisationInitialised: false,
            offenceInitialised: false,
            inspectionInitialised: false,
            hashAttributeWhitelist: [
              'allocated_group_id',
              'case_created_date',
              'case_created_time',
              'details',
              'title',
              'legal_case_priority_id',
              'region_id',
              'district_id',
            ],
            searchPersonKeyPressed: false,
            searchObjectKeyPressed: false,
            //magicValue: null,
            magic: true,
            dtHeadersRunningSheet: [
                "id",
                "Number",
                "Date",
                "Time",
                "User",
                "Description",
                "deleted",
                "Action",
            ],
            dtOptionsRunningSheet: {
                columns: [
                    {
                        visible: false,
                        mRender: function(data, type, row) {
                            return row.id;
                        }
                    },
                    {
                        mRender: function(data, type, row) {
                            let retStr = row.number;
                            return retStr;
                        }
                    },
                    {
                        mRender: function(data, type, row) {
                            let retStr = row.date_mod;
                            return retStr;
                        }
                    },
                    {
                        mRender: function(data, type, row) {
                            let retStr = row.time_mod;
                            return retStr;
                        }
                    },
                    {
                        mRender: function(data, type, row) {
                            let retStr = row.user_full_name;
                            return retStr;
                        }
                    },
                    {
                        mRender: function(data, type, row) {
                            let retStr = '';
                            retStr = `<div id=${row.number} style="min-height:20px" contenteditable="true">${row.description}</div>`
                            if (row.deleted) {
                                retStr = '<strike>' + 
                                    `<div id=${row.number} style="min-height:20px" contenteditable="false">${row.description}</div>`
                                    '</strike>';
                            }
                            return retStr;

                        }
                    },
                    {
                        visible: false,
                        mRender: function(data, type, row) {
                            return row.deleted;
                        }
                    },
                    {
                        mRender: function(data, type, row) {
                            let retStr = '';
                            let rowIdDel = row.number.replace('-', 'D')
                            let rowIdHist = row.number.replace('-', 'H')
                            let rowIdReinstate = row.number.replace('-', 'R')
                            if (row.action) {
                                retStr += `<a id=${rowIdHist} class="row_history" href="#">History</a><br/><br/>`
                                if (!row.deleted) {
                                    retStr += `<a id=${rowIdDel} class="row_delete" href="#">Delete</a><br/>`
                                } else {
                                    retStr += `<a id=${rowIdReinstate} class="row_reinstate" href="#">Reinstate</a><br/>`
                                }

                            }
                            return retStr;

                        }
                    },
                ]
            }
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
    Magic,
    SearchPersonOrganisationModal,
    RunningSheetHistory,
  },
  computed: {
    ...mapGetters('legalCaseStore', {
      legal_case: "legal_case",
    }),
    ...mapGetters({
        current_user: 'current_user'
    }),
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
        let readonly = true
        if (this.legal_case && this.legal_case.id) {
            readonly = !this.legal_case.can_user_action;
        }
        return readonly
    },
    canUserAction: function() {
        let return_val = false
        if (this.legal_case && this.legal_case.id) {
            return_val = this.legal_case.can_user_action;
        }
        return return_val
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
    searchPersonOrganisationBindId: function() {
        let search_person_organisation_id = ''
        search_person_organisation_id = 'search_person_organisation_' + parseInt(this.uuid);
        return search_person_organisation_id;
    },
    offenceBindId: function() {
        let offence_bind_id = ''
        offence_bind_id = 'offence' + parseInt(this.uuid);
        return offence_bind_id;
    },
    sanctionOutcomeBindId: function() {
        let sanction_outcome_bind_id = ''
        sanction_outcome_bind_id = 'sanction_outcome' + parseInt(this.uuid);
        return sanction_outcome_bind_id;
    },
    inspectionBindId: function() {
        let inspection_bind_id = ''
        inspection_bind_id = 'inspection' + parseInt(this.uuid);
        return inspection_bind_id;
    },
  },
  filters: {
    formatDate: function(data) {
      return data ? moment(data).format("DD/MM/YYYY HH:mm:ss") : "";
    }
  },
  methods: {
    ...mapActions('legalCaseStore', {
      loadLegalCase: 'loadLegalCase',
      saveLegalCase: 'saveLegalCase',
      setLegalCase: 'setLegalCase',
      setRelatedItems: 'setRelatedItems',
      setRunningSheetEntries: 'setRunningSheetEntries',
      setRunningSheetEntryDescription: 'setRunningSheetEntryDescription',
      setRunningSheetTransform: 'setRunningSheetTransform',
      setAddRunningSheetEntry: 'setAddRunningSheetEntry',
      setRunningSheetEntry: 'setRunningSheetEntry',
    }),
    ...mapActions({
        loadCurrentUser: 'loadCurrentUser',
    }),
    setRunningSheetHistoryEntryBindId: function() {
        if (this.runningSheetHistoryEntryInstance) {
            this.uuid += 1;
            this.runningSheetHistoryEntryBindId = this.runningSheetHistoryEntryInstance + '_' + this.uuid;
        }
    },
    runningSheetTransformWrapper: async function() {
        let runningSheet = []
        let i = 0;
        for (let r of this.runningSheetUrl) {
            if (this.runningSheetEntriesUpdated.includes(r.number)) {
                r.description = this.urlToToken(r.description)
                r.user_id = this.current_user.id;
                runningSheet.push(r);
            }
            i += 1;
        }
        await this.setRunningSheetTransform(runningSheet)
    },
    insertPersonModalUrl: function(entity) {
        let recordNumber = entity.row_number_selected;
        let recordNumberElement = $('#' + recordNumber)
        let replacementVal = ''
        if (entity.full_name) {
            replacementVal = `<a contenteditable="false" target="_blank" href="/internal/users/${entity.id}">${entity.full_name}</a>`
        }
        let recordDescriptionHtml = recordNumberElement[0].innerHTML.replace('@@', replacementVal).replace(/&nbsp\;/g, ' ');
        this.updateRunningSheetUrlEntry({
            "recordNumber": recordNumber,
            "recordDescription": recordDescriptionHtml,
            "redraw": true,
        })
    },
    constructRunningSheetTable: function(pk){
        console.log("constructRunningSheetTable")
        if (!pk) {
            this.$refs.running_sheet_table.vmDataTable.clear().draw();
        }
        let actionColumn = !this.readonlyForm;
        if (this.runningSheetUrl){
            for(let i = 0;i < this.runningSheetUrl.length; i++){
                if (!pk || this.runningSheetUrl[i].id === pk) {
                    this.$refs.running_sheet_table.vmDataTable.row.add({ 
                        "id": this.runningSheetUrl[i].id,
                        "number": this.runningSheetUrl[i].number,
                        "date_mod": this.runningSheetUrl[i].date_mod,
                        "time_mod": this.runningSheetUrl[i].time_mod,
                        "user_full_name": this.runningSheetUrl[i].user_full_name,
                        "description": this.runningSheetUrl[i].description,
                        "deleted": this.runningSheetUrl[i].deleted,
                        "action": actionColumn,
                    }).draw();
                }
            }
        }
        console.log("constructRunningSheetTable - end")
    },
    constructRunningSheetTableEntry: function( rowNumber ){
        let actionColumn = !this.readonlyForm;
        if (this.$refs.running_sheet_table && this.$refs.running_sheet_table.vmDataTable) {
            console.log("constructRunningSheetTableEntry");
            this.$refs.running_sheet_table.vmDataTable.rows().every((rowIdx, tableLoop, rowLoop) => {
                let rowData = this.$refs.running_sheet_table.vmDataTable.row(rowIdx).data()
                console.log(rowIdx)
                console.log(rowData)
                if (rowData.number === rowNumber) {
                    let i = 0;
                    for (let r of this.runningSheetUrl) {
                        if (r.number === rowNumber) {
                            rowData.date_mod = this.runningSheetUrl[rowIdx].date_mod;
                            rowData.time_mod = this.runningSheetUrl[rowIdx].time_mod;
                            rowData.user_full_name = this.runningSheetUrl[rowIdx].user_full_name;
                            rowData.description = this.runningSheetUrl[rowIdx].description;
                            rowData.deleted = this.runningSheetUrl[rowIdx].deleted;
                            rowData.action = actionColumn;
                            this.$refs.running_sheet_table.vmDataTable.row(rowIdx).invalidate().draw();
                        }
                        i += 1;
                    }
                }
            });
        }
    },
    createNewRunningSheetEntry: async function() {
        let payload = {
            "legal_case_id": this.legal_case.id,
            "user_id": this.current_user.id,
        }
        let fetchUrl = helpers.add_endpoint_join(
            api_endpoints.legal_case,
            this.legal_case.id + '/create_running_sheet_entry/'
            )
        let updatedRunningSheet = await Vue.http.post(fetchUrl, payload);
        console.log(updatedRunningSheet)
        if (updatedRunningSheet.ok) {
            await this.setAddRunningSheetEntry(updatedRunningSheet.body);
            let returnPayload = _.cloneDeep(updatedRunningSheet.body);
            returnPayload.description = this.tokenToUrl(returnPayload.description);
            this.runningSheetUrl.push(returnPayload);
            this.constructRunningSheetTable(returnPayload.id);
        }
    },
    openInspection() {
      this.uuid += 1;
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
    openSearchPersonOrganisation(rowNumber){
      this.uuid += 1;
      this.rowNumberSelected = rowNumber;
      this.searchPersonOrganisationInitialised = true;
      this.$nextTick(() => {
          this.$refs.search_person_or_organisation_modal.isModalOpen = true;
      });
    },
    updateWorkflowBindId: function() {
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
    },
    save: async function(returnToDash) {
      this.showSpinner = true;
      if (returnToDash === 'exit') {
          this.showExit = true;
      }      
      console.log(returnToDash)
      await this.runningSheetTransformWrapper();
      if (this.legal_case.id) {
          await this.saveLegalCase({ create: false, internal: false });
      } else {
          await this.saveLegalCase({ create: true, internal: false });
      }
      // TODO: add hash list etc
      this.calculateHash();
      if (returnToDash === 'exit') {
        // remove redundant eventListeners
        window.removeEventListener('beforeunload', this.leaving);
        window.removeEventListener('onblur', this.leaving);
        // return to dash
        this.$router.push({ name: 'internal-legal-case-dash' });
      } else {
          this.runningSheetEntriesUpdated = [];
          this.constructRunningSheetTableWrapper();
      }
      this.showSpinner = false;
      this.showExit = false;
    },
    magicMethod: function() {
        console.log("magic method");
        this.$refs.magic.isModalOpen = true;
        this.magic = false;
    },
    updateRunningSheetUrlEntry: function({
          recordNumber,
          recordDescription,
          redraw
    }) {
        console.log("updateRunningSheetUrl")
        if (this.magic && recordDescription && recordDescription.toLowerCase().includes('shibaken')) {
            this.magicMethod()
        }
        console.log(recordNumber)
        console.log(recordDescription)
        console.log(redraw)
        let i = 0;
        for (let r of this.runningSheetUrl) {
            console.log(r.deleted)
            if (r.number === recordNumber) {
                if (recordDescription) {
                    r.description = recordDescription
                }
                if (redraw) {
                    this.constructRunningSheetTableEntry( recordNumber );
                }
            }
            i += 1;
        }
    },
    runningSheetKeyup: function(e) {
        let rowObj = {}
        let recordNumber = e.target.id
        let recordDescriptionText = e.target.textContent
        let recordDescriptionHtml = e.target.innerHTML.replace(/\&nbsp\;/g, ' ');
        // add recordNumber to runningSheetEntriesUpdated
        for (let r of this.runningSheetUrl) {
            if (!(recordNumber === r.number)) {
                this.runningSheetEntriesUpdated.push(recordNumber);
            }
        }
        const ignoreArray = [49, 50, 16]
        if (ignoreArray.includes(e.which)) {
            //pass
        } else {
            let i = 0;
            for (let r of this.runningSheetUrl) {
                if (r.number === recordNumber) {
                    this.updateRunningSheetUrlEntry({
                        "recordNumber": recordNumber,
                        "recordDescription": recordDescriptionHtml, 
                        "redraw": false
                    })
                    this.searchPersonKeyPressed = false;
                    this.searchObjectKeyPressed = false;
                }
                i += 1;
            }
        }
    },
    runningSheetKeydown: async function(e) {

        // keycode 49 = !
        if (e.which === 49 && this.searchObjectKeyPressed) {
            // TODO: replace with modal_open call
            console.log("open modal")
            this.openInspection()
            this.searchObjectKeyPressed = false;
        } else if (e.which === 49) {
            this.searchObjectKeyPressed = true;
        } else if (e.which === 50 && this.searchPersonKeyPressed) {
            // TODO: replace with modal_open call
            console.log("open modal")
            console.log(e.target.id)
            let rowElement = $('#' + e.target.id);
            this.openSearchPersonOrganisation(e.target.id)
            this.searchPersonKeyPressed = false;
        } else if (e.which === 50) {
            console.log(e);
            this.searchPersonKeyPressed = true;
        // keycode 16 = Shift (must be pressed to access !)
        //} else if (e.which === 16 || e.which === 32) {
        } else if (e.which === 16) {
            // pass
        } else {
            this.searchPersonKeyPressed = false;
            this.searchObjectKeyPressed = false;
        }
    },
    urlToToken: function(description) {
        let parsedText = description;
        const personUrlRegex = /<a contenteditable\=\"false\" target\=\"\_blank\" href\=\"\/internal\/users\/\d+\"\>\w+(\s\w+)*\<\/a\>/g
        const personIdRegex = /\/internal\/users\/\d+/g
        const personNameRegex = /\/internal\/users\/\d+\"\>\w+(\s\w+)*/g
        let matchArray = [...description.matchAll(personUrlRegex)];
        if (matchArray && matchArray.length > 0) {
            for (let match of matchArray) {
                let idArray = [...match[0].matchAll(personIdRegex)];
                console.log(idArray)
                let idStr = idArray[0][0]
                let id = idStr.substring(16)
                let personArray = [...match[0].matchAll(personNameRegex)];
                console.log(personArray)
                let personFound = personArray[0][0]
                let person = personFound.replace(/\/internal\/users\/\d+\"\>/g, String(''));
                let replacementVal = `{{ "person_id": "${id}", "full_name": "${person}" }}`
                parsedText = parsedText.replace(match[0], replacementVal).replace(/\&nbsp\;/g, ' ');
                console.log(parsedText);
            }
        }
        return parsedText;
    },
    tokenToUrl: function(description) {
        console.log("tokenToUrl")
        let parsedText = description;
        const personTokenRegex = /\{\{ \"person\_id\"\: \"\d+\"\, \"full\_name\"\: \"\w+(\s\w+)*\" \}\}/g;
        const personIdRegex = /\{\{ \"person\_id\"\: \"\d+/g;
        const personNameRegex = /\"full\_name\"\: \"\w+ \w+/g;
        let personTokenArray = [...description.matchAll(personTokenRegex)];
        for (let personToken of personTokenArray) {
            console.log(personToken)
            let idArray = [...personToken[0].matchAll(personIdRegex)];
            console.log(idArray)
            let idStr = idArray[0][0]
            let id = idStr.substring(17)
            console.log(id)
            let nameArray = [...personToken[0].matchAll(personNameRegex)];
            console.log(nameArray)
            let nameStr = nameArray[0][0]
            let fullName = nameStr.substring(14)
            console.log(id)
            parsedText = parsedText.replace(
                personToken[0],
                `<a contenteditable="false" target="_blank" href="/internal/users/${id}">${fullName}</a>`
            );
            console.log(parsedText)
        }
        return parsedText
    },
    addEventListeners: function() {
      let vm = this;
      let runningSheetTable = $('#running-sheet-table');
      console.log(runningSheetTable)
      runningSheetTable.on(
          'keydown',
          (e) => {
              this.runningSheetKeydown(e)
          });
      runningSheetTable.on(
          'keyup',
          (e) => {
              this.runningSheetKeyup(e)
          });
      runningSheetTable.on(
          'click',
          '.row_delete',
          (e) => {
              this.runningSheetRowDelete(e)
          });
      
      runningSheetTable.on(
          'click',
          '.row_history',
          (e) => {
              this.runningSheetRowHistory(e)
          });
      runningSheetTable.on(
          'click',
          '.row_reinstate',
          (e) => {
              this.runningSheetRowReinstate(e)
          });
      
      window.addEventListener('beforeunload', this.leaving);
      window.addEventListener('onblur', this.leaving);
    },
    runningSheetRowDelete: async function(e) {
        this.showSpinner = true;
        console.log(e)
        let rowNumber = e.target.id.replace('D', '-');
        console.log(rowNumber)
        console.log("runningSheetRowDelete")
        let running_sheet_id = null;
        for (let r of this.legal_case.running_sheet_entries) {
            if (r.number === rowNumber) {
                running_sheet_id = r.id
            }
        }
        let returnedEntry = await Vue.http.post(
            helpers.add_endpoint_join(
                api_endpoints.legal_case,
                this.legal_case.id + '/delete_running_sheet_entry/',
            ),
            {
                "running_sheet_id": running_sheet_id,
                "deleted": true,
            }
            );
        if (returnedEntry.ok) {
            // required for running_sheet_history
            await this.setRunningSheetEntry(returnedEntry.body);
            let i = 0;
            for (let r of this.runningSheetUrl) {
                if (r.number === rowNumber) {
                    this.runningSheetUrl.splice(i, 1, returnedEntry.body);
                    this.runningSheetUrl[i].description = this.tokenToUrl(this.runningSheetUrl[i].description);
                }
                i += 1
            }
            this.constructRunningSheetTableEntry(rowNumber);
            
        }
        this.showSpinner = false;
    },
    runningSheetRowReinstate: async function(e) {
        this.showSpinner = true;
        console.log(e)
        let rowNumber = e.target.id.replace('R', '-');
        console.log(rowNumber)
        console.log("runningSheetRowReinstate")
        let running_sheet_id = null;
        for (let r of this.legal_case.running_sheet_entries) {
            if (r.number === rowNumber) {
                running_sheet_id = r.id
            }
        }
        let returnedEntry = await Vue.http.post(
            helpers.add_endpoint_join(
                api_endpoints.legal_case,
                this.legal_case.id + '/reinstate_running_sheet_entry/',
            ),
            {
                "running_sheet_id": running_sheet_id,
                "deleted": false,
            }
            );
        if (returnedEntry.ok) {
            // required for running_sheet_history
            await this.setRunningSheetEntry(returnedEntry.body);
            let i = 0;
            for (let r of this.runningSheetUrl) {
                if (r.number === rowNumber) {
                    this.runningSheetUrl.splice(i, 1, returnedEntry.body);
                    this.runningSheetUrl[i].description = this.tokenToUrl(this.runningSheetUrl[i].description);
                }
                i += 1
            }
            this.constructRunningSheetTableEntry(rowNumber);
        }
        this.showSpinner = false;
    },
    runningSheetRowHistory: function(e) {
        console.log(e)
        let rowNumber = e.target.id.replace('H', '-');
        console.log(rowNumber)
        console.log("runningSheetRowHistory")
        this.runningSheetHistoryEntryInstance = rowNumber;
        this.setRunningSheetHistoryEntryBindId()
        this.$nextTick(() => {
            this.$refs.running_sheet_history.isModalOpen = true;
        });
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
        if (this.runningSheetEntriesUpdated.length > 0) {
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
        this.constructRunningSheetTableWrapper();
    },
    constructRunningSheetTableWrapper: function() {
        this.runningSheetUrl = _.cloneDeep(this.legal_case.running_sheet_entries);
        let i = 0;
        for (let r of this.legal_case.running_sheet_entries) {
            let description = this.tokenToUrl(r.description)
            this.runningSheetUrl[i].description = description;
            i += 1;
        }
        this.$nextTick(() => {
            this.constructRunningSheetTable();
        });
    },
  },
  created: async function() {
      if (this.$route.params.legal_case_id) {
          await this.loadLegalCase({ legal_case_id: this.$route.params.legal_case_id });
      }
      await this.loadCurrentUser({ url: `/api/my_compliance_user_details` });
      console.log(this)

      this.calculateHash();
      this.constructRunningSheetTableWrapper();
  },
  destroyed: function() {
      window.removeEventListener('beforeunload', this.leaving);
      window.removeEventListener('onblur', this.leaving);
  },

  mounted: function() {
      this.$nextTick(() => {
          this.addEventListeners();
      });
  },
};
</script>

<style lang="css">
.action-button {
    margin-top: 5px;
}
.new-row-button {
    margin-bottom: 5px;
    margin-right: 13px;
}
#close-button {
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
.inline-datatable {
  overflow-wrap: break-word;
}
</style>
