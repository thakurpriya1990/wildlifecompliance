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
                          <div v-if="canUserAction" class="col-sm-12">
                                <a @click="addWorkflow('endorse')" class="btn btn-primary btn-block">
                                  Witness Statement
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
                                <a @click="addWorkflow('request_amendment')" class="btn btn-primary btn-block">
                                  Interview
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
                                <!--a @click="openSanctionOutcome()" class="btn btn-primary btn-block">
                                  Sanction Outcome
                                </a-->
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
                                    <!--div class="col-sm-6"-->
                                        <label class="col-sm-10">Type !! to open Inspection or @@ to open SearchPerson</label>
                                        <!--input id="test1" type="text" class="form-control" v-model="magicValue" /-->
                                    <div class="row action-button">
                                        <div v-if="canUserAction" class="col-sm-12">
                                              <a @click="createNewRunningSheetEntry()" class="btn btn-primary btn-block" >
                                                New Row
                                              </a>
                                        </div>
                                    </div>
                                    <!--div class="col-sm-3 inline-datatable" contenteditable="true">this <a contenteditable="false" href="www.google.com">google</a> this2</div>
                                    <div v-model="runningSheetObj[`CS000018-1`].description" contenteditable="true">this <a contenteditable="false" href="www.google.com">google</a> this2</div-->

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
        <Magic ref="magic" />
        <SearchPersonOrganisationModal 
        ref="search_person_or_organisation_modal"
        :readonlyForm="readonlyForm"
        v-bind:key="searchPersonOrganisationBindId"
        @person-selected="insertPersonModalToken"
        :rowNumberSelected="rowNumberSelected"
        />
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
import Magic from './magic';
import SearchPersonOrganisationModal from '@/components/common/search_person_or_organisation_modal';
import _ from 'lodash';


export default {
    name: "ViewLegalCase",
    data: function() {
        return {
            //tempRunningSheet: [],
            uuid: 0,
            rowNumberSelected: '',
            runningSheet: [],
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
                "Date Created",
                "User",
                "Description",
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
                            let ret_str = row.number;
                            if (row.deleted) {
                                ret_str = '<strike>' + ret_str + '</strike>';
                            }
                            return ret_str;
                        }
                    },
                    {
                        mRender: function(data, type, row) {
                            let ret_str = row.date_created;
                            if (row.deleted) {
                                ret_str = '<strike>' + ret_str + '</strike>';
                            }
                            return ret_str;
                        }
                    },
                    {
                        mRender: function(data, type, row) {
                            let ret_str = row.user_full_name;
                            if (row.deleted) {
                                ret_str = '<strike>' + ret_str + '</strike>';
                            }
                            return ret_str;
                        }
                    },
                    {
                        mRender: function(data, type, row) {
                            let ret_str = '';

                            //let num_chars = 1000;
                            //if (row.allegedOffence.removed){
                            //    if(row.allegedOffence.reason_for_removal){
                            //        let name = row.allegedOffence.reason_for_removal;
                            //        let shortText = (name.length > num_chars) ?
                            //            '<span title="' + name + '">' + $.trim(name).substring(0, num_chars).split(" ").slice(0, -1).join(" ") + '...</span>' :
                            //            name;
                            //        ret_str = ret_str + shortText;

                            //    } else {
                            //        ret_str = ret_str + '<textarea class="reason_element" data-alleged-offence-uuid="' + row.allegedOffence.uuid + '">' + row.allegedOffence.reason_for_removal + '</textarea>';
                            //    }
                            //}
                            //ret_str = '<div><input type="text" /><link href="www.google.com>google</link><input type="text" /></div>'
                            //ret_str = '<div><input type="text">this</input><a href="www.google.com">google</a><input type="text">this2</input></div>'
                            //ret_str = '<div contenteditable="true">this <a contenteditable="false" href="www.google.com">google</a> this2</div>'
                            //ret_str = '<div v-model="legal_case.running_sheet_object[' + row.number + '] contenteditable="true">this <a contenteditable="false" href="www.google.com">google</a> this2</div>'
                            //ret_str = '<div v-model="runningSheetObj[' + String.fromCharCode(34) + row.number + String.fromCharCode(34) + '].description" contenteditable="true">this <a contenteditable="false" href="www.google.com">google</a> this2</div>'
                            //ret_str = '<div id=' + row.number + ' contenteditable="true">this <a contenteditable="false" href="www.google.com">google</a> this2</div>'
                            ret_str = '<div id=' + row.number + ' contenteditable="true">' + row.description + '</div>'
                            //ret_str = '<div contenteditable="true">this <a contenteditable="false" href="www.google.com">google</a> this2</div>'
                            return ret_str;

                        }
                    },
                    {
                        mRender: function(data, type, row) {
                            let ret_str = '';
                            //let ret_str = row.allegedOffence.number_linked_sanction_outcomes_active + '(' + row.allegedOffence.number_linked_sanction_outcomes_total + ')';
                            //if (row.offence.in_editable_status && row.offence.can_user_action){
                            //    if (row.allegedOffence.removed){
                            //        ret_str = ret_str + '<a href="#" class="restore_button" data-alleged-offence-uuid="' + row.allegedOffence.uuid + '">Restore</a>';
                            //    } else {
                            //        if (!row.allegedOffence.number_linked_sanction_outcomes_active){
                            //            ret_str = ret_str + '<a href="#" class="remove_button" data-alleged-offence-uuid="' + row.allegedOffence.uuid + '">Remove</a>';
                            //        }
                            //    }
                            //}
                            return ret_str;

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
  },
  computed: {
    ...mapGetters('legalCaseStore', {
      legal_case: "legal_case",
      //running_sheet_list: "running_sheet_list",
      //running_sheet_obj: "running_sheet_obj",
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
        //return false
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
        //let timeNow = Date.now()
        //this.uuid += 1
        search_person_organisation_id = 'search_person_organisation_' + parseInt(this.uuid);
        return search_person_organisation_id;
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
    runningSheetVuex: function() {
        let retRunningSheet = [];
        if (this.legal_case && this.legal_case.running_sheet_entries) {
            retRunningSheet = _.cloneDeep(this.legal_case.running_sheet_entries)
        }
        return retRunningSheet;
    },
  },
  watch: {
      runningSheetVuex: {
          immediate: true,
          handler: function(newValue, oldValue) {
              //console.log(newValue)
              //console.log(oldValue)
              let i = 0;
              for (let r of newValue) {
                  if (oldValue && oldValue.length > 0 && r.description !== oldValue[i].description) {
                      this.updateRunningSheetEntry({
                          "rowId": i, 
                          "recordNumber": r.number, 
                          "description": r.description,
                          'redraw': true,
                      });
                  }
                  i += 1;
              }
          },
          deep: true
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
    }),
    ...mapActions({
        loadCurrentUser: 'loadCurrentUser',
    }),
      insertPersonModalToken: function(entity) {
        console.log(entity)
        let recordNumber = entity.row_number_selected;
        let recordNumberElement = $('#' + recordNumber)
        let recordDescription = recordNumberElement[0].textContent;
        //let replacementVal = String('{{ ' + '"person_id": ' + entity.id + ' }}')
        let replacementVal = ''
        if (entity.full_name) {
            replacementVal = `{{ "person_id": ${entity.id}, "full_name": ${entity.full_name} }}`
        }
        //let replacementIdx = recordDescription.indexOf('@@')
        let recordDescriptionText = recordDescription.replace('@@', replacementVal);
        let recordDescriptionHtml = recordNumberElement[0].innerHTML.replace(/\&nbsp\;/g, ' ');
        console.log(recordDescriptionText)
        console.log(recordDescriptionHtml)

        this.updateRunningSheetVuexWrapper({
            recordNumber,
            recordDescriptionText,
            recordDescriptionHtml,
        })


    },
    findStringDiff(str1, str2) { 
          let diff= "";
          str2.split('').forEach(function(val, i){
                  if (val != str1.charAt(i))
                        diff += val ;
                });
          return diff;
    },
    updateRunningSheetEntry: function({rowId, recordNumber, description, redraw}) {
        if (this.magic && redraw && description.toLowerCase().includes('shibaken')) {
            this.magicMethod()
        }
        let i = 0;
        for (let r of this.runningSheet) {
            if (rowId === i && recordNumber === r.number) {
                //const personTokenRegex = /\{\{ \"person\_id\"\: \d+ \}\}/g;
                const personTokenRegex = /\{\{ \"person\_id\"\: \d+\, \"full\_name\"\: \"\w+ \w+\" \}\}/g;
                let personTokenArray = [...description.matchAll(personTokenRegex)];
                const personUrlRegex = /<a contenteditable\=\"false\" target\=\"\_blank\" href\=\"\/internal\/users\/\d+\"\>\w+\s\w+\<\/a\>/g
                let personUrlArray = [...r.description.matchAll(personUrlRegex)];
                if (personTokenArray.length > personUrlArray.length) {
                    for (let personToken of personTokenArray) {
                        r.description = description.replace(
                            personTokenRegex,
                            `<a contenteditable="false" target="_blank" href="/internal/users/${7822}">Mark bloke</a>`
                        );
                        this.runningSheet.splice(i, 1, r);
                        console.log(r.description)
                        if (redraw) {
                            this.constructRunningSheetTableEntry({"rowNum": i, "description": r.description});
                        }
                    }
                }
            }
            i += 1;
        }

    },

    constructRunningSheetTable: function(){
        this.$refs.running_sheet_table.vmDataTable.clear().draw();
        if (this.runningSheet && this.runningSheetVuex){
            for(let i = 0;i < this.runningSheet.length; i++){
                this.updateRunningSheetEntry({
                    "rowId": i,
                    "recordNumber": this.runningSheetVuex[i].number,
                    "description":  this.runningSheetVuex[i].description
                });
                //this.addRunningSheetEntryToTable(this.offence.alleged_offences[i]);
                this.$refs.running_sheet_table.vmDataTable.row.add({ 
                    "id": this.runningSheet[i].id,
                    "number": this.runningSheet[i].number,
                    "date_created": this.runningSheet[i].date_created,
                    "user_full_name": this.runningSheet[i].user_full_name,
                    "description": this.runningSheet[i].description,
                    "action": this.runningSheet[i].action,
                }).draw();
                //let actionColumn
            }
        }
    },
    constructRunningSheetTableEntry: function({rowNum, description}){
        console.log(description)
        if (this.$refs.running_sheet_table && this.$refs.running_sheet_table.vmDataTable) {
            console.log("constructRunningSheetTableEntry");
            let tableRow = this.$refs.running_sheet_table.vmDataTable.row(rowNum).data()
            tableRow.description = description
            this.$refs.running_sheet_table.vmDataTable.row(rowNum).data(tableRow).draw()
        }
    },
    createNewRunningSheetEntry: async function() {
        let payload = {
            "legal_case_id": this.legal_case.id,
            "user_id": this.current_user.id,
        }
        let fetchUrl = helpers.add_endpoint_join(
            api_endpoints.legal_case,
            //state.inspection.id + "/inspection_save/"
            this.legal_case.id + '/create_running_sheet_entry/'
            )
        let updatedRunningSheet = await Vue.http.post(fetchUrl, payload);
        if (updatedRunningSheet.body && updatedRunningSheet.body.running_sheet_entries){
            await this.setRunningSheetEntries(updatedRunningSheet.body.running_sheet_entries);
            //this.runningSheetEventListeners();
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
    },
    save: function(returnToDash) {
      console.log(returnToDash)
      let savedLegalCase = null;
      //let savedPerson = null;
      this.$nextTick(async () => {
          if (this.legal_case.id) {
              savedLegalCase = await this.saveLegalCase({ create: false, internal: false });
          } else {
              savedLegalCase = await this.saveLegalCase({ create: true, internal: false });
          }
      })
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
    magicMethod: function() {
        console.log("magic method");
        this.$refs.magic.isModalOpen = true;
        this.magic = false;
    },
    updateRunningSheetVuexWrapper: async function({
          recordNumber,
          recordDescriptionText,
          recordDescriptionHtml
    }) {
        console.log("wrapper")
        console.log(recordNumber)
        console.log(recordDescriptionText)
        console.log(recordDescriptionHtml)
        let recordDescription = this.parseStringInput({
            "recordDescriptionHtml": recordDescriptionHtml,
            "recordDescriptionText": recordDescriptionText,
        });
        console.log(recordDescription)
        await this.setRunningSheetEntryDescription(
            {
                "recordNumber": recordNumber, 
                "description": recordDescription,
                "userId": this.current_user.id,
            })
    },
    runningSheetKeyup: async function(e) {
        let rowObj = {}
        let recordNumber = e.target.id
        let recordDescriptionText = e.target.textContent
        let recordDescriptionHtml = e.target.innerHTML.replace(/\&nbsp\;/g, ' ');
        const ignoreArray = [49, 50, 16]
        if (ignoreArray.includes(e.which)) {
            //pass
        } else {
            let i = 0;
            for (let r of this.runningSheet) {
                if (r.number === recordNumber) {
                    this.updateRunningSheetVuexWrapper({
                        recordNumber,
                        recordDescriptionHtml, 
                        recordDescriptionText
                    })
                    //let recordDescription = this.parseStringInput({
                    //    "recordDescriptionHtml": recordDescriptionHtml,
                    //    "recordDescriptionText": recordDescriptionText,
                    //    "rowId": i
                    //});
                    //await this.setRunningSheetEntryDescription(
                    //    {
                    //        "recordNumber": recordNumber, 
                    //        "description": recordDescription,
                    //        "userId": this.current_user.id,
                    //    })
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
            //console.log(e);

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
      parseStringInput: function({recordDescriptionHtml, recordDescriptionText}) {
        //console.log(recordDescriptionText)
        //console.log(recordDescriptionHtml)
        //let parsedText = this.legal_case.running_sheet_entries[rowId].description;
        let parsedText = String(recordDescriptionText);
        //Object.assign(parsedText, str);
        //let selectedRowId = null;
        //let i = 0;
        //for (r of this.runningSheet) {
        //    if (r.number === rowNumber) {
        //        selectedRowId = i
        //    }
        //}


        const personUrlRegex = /<a contenteditable\=\"false\" target\=\"\_blank\" href\=\"\/internal\/users\/\d+\"\>\w+\s\w+\<\/a\>/g
        const personIdRegex = /\/internal\/users\/\d+/g
        const personNameRegex = /\/internal\/users\/\d+\"\>\w+\s\w+/g
        //console.log(personUrlRegex)
        //console.log(str)
        //let re = /\{\{ \"person\_id\"\: \d+ \}\}/g;
        //let matchArray = personUrlRegex.exec(recordDescriptionHtml)
        let matchArray = [...recordDescriptionHtml.matchAll(personUrlRegex)];
        console.log(typeof(matchArray))
        console.log(matchArray)
        if (matchArray && matchArray.length > 0) {
            for (let match of matchArray) {
                console.log("match")
                console.log(typeof(match))
                console.log(match)
                console.log(typeof(match[0]))
                console.log(match[0])
                
                //let idArray = personIdRegex.exec(match[0])
                let idArray = [...match[0].matchAll(personIdRegex)];
                console.log(idArray)
                let idStr = idArray[0][0]
                let id = idStr.substring(16)
                //let replacementVal = String('{{ ' + '"person_id": ' + id + ', "full_name":  }}')
                console.log(replacementVal)
                //let personArray = personNameRegex.exec(match[0])
                let personArray = [...match[0].matchAll(personNameRegex)];
                console.log(personArray)
                let personFound = personArray[0][0]
                let person = personFound.replace(/\/internal\/users\/\d+\"\>/g, String(''));
                let replacementVal = `{{ "person_id": ${id}, "full_name": ${person} }}`
                console.log(person)
                parsedText = parsedText.replace(person, String(replacementVal)).replace(/\&nbsp\;/g, ' ');
                //Object.assign(this.runningSheet[i].description, r.description);
            }
        }
        console.log(parsedText)
        console.log(typeof(parsedText))
        return parsedText;
    },
    addEventListeners: function() {
      //let vm = this;
      let runningSheetTable = $('#running-sheet-table');
      
      runningSheetTable.on(
          'keydown',
          (e) => {
              console.log(runningSheetTable)
              this.runningSheetKeydown(
                  e, 
                  runningSheetTable[0].selectionStart, 
                  runningSheetTable[0].selectionEnd)
          });
      runningSheetTable.on(
          'keyup',
          (e) => {
              //console.log(runningSheetTable.text())
              this.runningSheetKeyup(e)
          });
      //console.log(runningSheetTable);
      //runningSheetTable.addEventListener("keydown", this.runningSheetEvents);
      

      //let runningSheetDataTable = $('running-sheet-table').DataTable();
      //runningSheetTable.on( 'click', 'td', function() {
      //        var rowIdx = runningSheetDataTable
      //            .cell( vm )
      //            .index().row;
      //     
      //        runningSheetDataTable
      //            .rows( rowIdx )
      //            .nodes()
      //            .to$()
      //            .addClass( 'clicked' );
      //} );

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
    },
  },
  created: async function() {
      if (this.$route.params.legal_case_id) {
          await this.loadLegalCase({ legal_case_id: this.$route.params.legal_case_id });
      }
      await this.loadCurrentUser({ url: `/api/my_compliance_user_details` });
      console.log(this)

      this.calculateHash();
      //Object.assign(this.runningSheet, this.legal_case.running_sheet_entries);
      this.runningSheet = _.cloneDeep(this.legal_case.running_sheet_entries);
      this.$nextTick(() => {
          this.constructRunningSheetTable();
      });
  },
  destroyed: function() {
      window.removeEventListener('beforeunload', this.leaving);
      window.removeEventListener('onblur', this.leaving);
  },

  mounted: function() {
      this.$nextTick(async () => {
          this.addEventListeners();
          //this.runningSheetEventListeners();
          //this.constructRunningSheetTable();
      });
  },
};
</script>

<style lang="css">
.action-button {
    margin-top: 5px;
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
