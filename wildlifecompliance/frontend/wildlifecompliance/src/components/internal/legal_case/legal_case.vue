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
            magicKeyPressed: false,
            magicKey2Pressed: false,
            magicValue: null,
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

    runningSheetDeprecated: function() {
        let retRunningSheet = [];
        if (this.legal_case && this.legal_case.running_sheet_entries) {
            let i = 0
            for (let r of this.legal_case.running_sheet_entries) {
                retRunningSheet.push(Object.assign({}, this.legal_case.running_sheet_entries[i]))
                //retRunningSheet[i].description += ' transform'
                let re = /\{\{ \"person\_id\"\: \d+ \}\}/g;
                let matchArray = re.exec(retRunningSheet[i].description)
                //console.log(matchArray)
                if (matchArray && matchArray.length > 0) {
                    for (let match of matchArray) {
                        //if (match.index) {
                        //    console.log("match.index")
                        //    console.log(match.index)
                        //    //state.legal_case.running_sheet_transform[i].description =  description + ' transform';
                        //    state.legal_case.running_sheet_transform[i].description.replace(match, 'blah transform');
                        //}
                        console.log("match")
                        console.log(typeof(match))
                        console.log(match)
                        //state.legal_case.running_sheet_transform[i].description =  description;
                        retRunningSheet[i].description = retRunningSheet[i].description.replace(
                            match, //'blah transform'
                            '<a contenteditable="false" target="_blank"  href="/internal/users/7822">Mark</a>'
                        );
                        this.constructRunningSheetTableEntry({"rowNum": i, "description": retRunningSheet[i].description});
                    }
                }
                i += 1;
            }
        }
        return retRunningSheet;
    },
    //runningSheetEntries: function() {
    //    let retRunningSheet = null;
    //    if (this.legal_case && this.legal_case.running_sheet_entries) {
    //        //Object.assign(ret_running_sheet, this.legal_case.running_sheet_entries);
    //        retRunningSheet = this.legal_case.running_sheet_entries;
    //    }
    //    return retRunningSheet;
    //},
    //runningSheetTransform: function() {
    //    let retRunningSheet = null;
    //    if (this.legal_case && this.legal_case.running_sheet_transform) {
    //        //Object.assign(ret_running_sheet, this.legal_case.running_sheet_entries);
    //        retRunningSheet = this.legal_case.running_sheet_transform;
    //    }
    //    return retRunningSheet;
    //},
    //runningSheetObj: function() {
    //    let retRunningSheetObj = {}
    //    if (this.legal_case && this.legal_case.running_sheet_entries) {
    //        for (let r of this.legal_case.running_sheet_entries) {
    //            retRunningSheetObj[r.number] = r;
    //        }
    //    }
    //    return retRunningSheetObj;
    //},
    //running_sheet: function() {
    //    let ret_running_sheet = null;
    //    if (this.legal_case && this.legal_case.running_sheet_object) {
    //        //Object.assign(ret_running_sheet, this.legal_case.running_sheet_entries);
    //        ret_running_sheet = this.legal_case.running_sheet_object;
    //    }
    //    return ret_running_sheet;
    //},
  },
  watch: {
      magicValue: {
          handler: function (){
              if (this.magicValue && 
                this.magicValue.toLowerCase().includes('shibaken') &&
                this.magic) {
                  //this.constructInspectionTeamTable();
                  this.magicMethod()
              }
          },
      },
      runningSheetVuex: {
          immediate: true,
          handler: function(newValue, oldValue) {
              //console.log('vuex running sheet changed')
              //console.log(newValue)
              //console.log(oldValue)
              let i = 0;
              for (let r of newValue) {
                  //console.log(r.description)
                  //console.log(oldValue[i].description)
                  //console.log(oldValue)
                  if (oldValue && oldValue.length > 0 && r.description !== oldValue[i].description) {
                  //if (runningSheetVuexoldValue && oldValue.length > 0 && r.description !== oldValue[i].description) {
                      //console.log("anything?")
                      this.updateRunningSheetEntry({
                          "rowId": i, 
                          "recordNumber": r.number, 
                          "description": r.description
                      });
                  }
                  i += 1;
              }
          },
          deep: true
      },
      //runningSheet: {
      //    immediate: true,
      //    handler: function () {
      //        console.log('component running sheet changed')
      //        //console.log(newVal)
      //        //console.log(oldVal)
      //        //this.runningSheetEventListeners();
      //        //this.constructRunningSheetTable();
      //    },
      //    deep: true
      //},
      //runningSheetEntries: {
      //    handler: function() {
      //        //this.runningSheetEventListeners();
      //        //this.constructRunningSheetTable();
      //    },
      //    deep: true
      //},
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
    updateRunningSheetEntry: function({rowId, recordNumber, description}) {
        //console.log(rowNum)
        //console.log(recordNumber)
        //console.log(description)
        let i = 0;
        for (let r of this.runningSheet) {
            if (rowId === i && recordNumber === r.number) {
                let re = /\{\{ \"person\_id\"\: \d+ \}\}/g;
                let matchArray = re.exec(description)
                console.log(matchArray)
                if (matchArray && matchArray.length > 0) {
                    for (let match of matchArray) {
                        console.log("match")
                        console.log(typeof(match))
                        console.log(match)
                        r.description = description.replace(
                            match, //'blah transform'
                            '<a contenteditable="false" target="_blank"  href="/internal/users/7822">Mark</a>'
                        );
                        //Object.assign(this.runningSheet[i].description, r.description);
                        //this.runningSheet.$set(i, r);
                        this.runningSheet.splice(i, 1, r);
                        console.log(r.description)
                        console.log("this.runningSheet[rowNum].description")
                        console.log(this.runningSheet[i].description)
                        this.constructRunningSheetTableEntry({"rowNum": i, "description": r.description});
                    }
                }
            }
        }

    },

    constructRunningSheetTable: function(){
        this.$refs.running_sheet_table.vmDataTable.clear().draw();
        if (this.runningSheet){
            for(let i = 0;i < this.runningSheet.length; i++){
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
        if (this.$refs.running_sheet_table && this.$refs.running_sheet_table.vmDataTable) {
            console.log("constructRunningSheetTableEntry");
            //let tableCell = this.$refs.running_sheet_table.vmDataTable.rows(rowNum).data()[0].description
            let tableRow = this.$refs.running_sheet_table.vmDataTable.row(rowNum).data()
            //let tableCell3 = this.$refs.running_sheet_table.vmDataTable.cell(rowNum).data()
            //tableCell = description
            tableRow.description = description
            this.$refs.running_sheet_table.vmDataTable.row(rowNum).data(tableRow).draw()
            //console.log(this.$refs.running_sheet_table.vmDataTable.rows(rowNum).columns("Description").data())
            //let tableCell = this.$refs.running_sheet_table.vmDataTable.columns("Description")
            //console.log("constructRunningSheetTableEntry");
            //this.$refs.running_sheet_table.vmDataTable.cell(rowNum, 3).data(description).draw();
            //console.log(this.$refs.running_sheet_table.vmDataTable.cell(rowNum, 3).data())
        }
    },
    //addRunningSheetEntryToTable: function(allegedOffence){
    //    //allegedOffence.uuid = uuid();
    //    this.$refs.running_sheet_table_table.vmDataTable.row.add({ legal_case: legal_case, offence: this.offence }).draw();
    //},
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
    openSearchPersonOrganisation(){
      this.uuid += 1;
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
    magicMethod: function() {
        console.log("magic method");
        this.$refs.magic.isModalOpen = true;
        this.magic = false;
    },
    runningSheetEvents: async function(e) {
        //console.log(e)
        //console.log(e.target.outerHTML)
        let rowObj = {}
        let recordNumber = e.target.id
        //let rowValue = e.target.outerHTML
        let recordDescription = e.target.textContent
        //console.log("rowValue")
        //console.log(rowValue)

        // keycode 49 = !
        if (e.which === 49 && this.magicKeyPressed) {
            // TODO: replace with modal_open call
            console.log("open modal")
            this.openInspection()
            this.magicKeyPressed = false;
        } else if (e.which === 49) {
            this.magicKeyPressed = true;
            // keycode 16 = Shift (must be pressed to access !)
        } else if (e.which === 50 && this.magicKey2Pressed) {
            // TODO: replace with modal_open call
            console.log("open modal")
            this.openSearchPersonOrganisation()
            this.magicKey2Pressed = false;
        } else if (e.which === 50) {
            this.magicKey2Pressed = true;
            // keycode 16 = Shift (must be pressed to access !)
        } else if (e.which === 16) {
            // pass
        } else if (this.magicValue && 
            this.magicValue.toLowerCase().includes('shibaken') &&
            this.magic) {
            //this.magic = true;
            this.magicMethod()
        } else {
            let i = 0;
            for (let r of this.runningSheet) {
                if (r.number === recordNumber) {
                    await this.setRunningSheetEntryDescription({"recordNumber": recordNumber, "description": recordDescription})
                    //this.constructRunningSheetTableEntry({
                    //    "rowNum": i, 
                    //    "description": this.legal_case.running_sheet_transform[i].description
                    //});
                    this.magicKeyPressed = false;
                    this.magicKey2Pressed = false;
                }
                i += 1;
            }
        }
        
        //else if (this.runningSheetObj && this.runningSheetObj[rowId]) {
        //    //console.log("push rowId")
        //    //console.log(this.runningSheetObj[rowId])
        //    //this.tempRunningSheet.push(rowId);
        //    this.setRunningSheetEntryDescription({"rowId": rowId, "description": rowValue})
        //    //if (this.runningSheetObj[rowId].number !== rowId) {
        //    //    this.setRunningSheetEntryDescription({"rowId": rowId, "description": rowValue})
        //    //}

        //} else {
        //    this.magicKeyPressed = false;
        //    this.magicKey2Pressed = false;
        //}

    },
    //runningSheetEventListeners: function() {
    //  console.log("runningSheetEventListeners")
    //  let vm = this;
    //  if (this.legal_case && this.legal_case.running_sheet_entries) {
    //      for (let r of this.legal_case.running_sheet_entries) {
    //          if (r && r.number) {
    //              vm.rowIdStr = '#' + r.number;
    //              vm.rowId = $(vm.rowIdStr);
    //              vm.rowId.on(
    //                  'keydown', 
    //                  function(e) {
    //                      vm.test1(e)
    //                  });
    //          }
    //      }
    //  }

    //},
    addEventListeners: function() {
      let vm = this;
      //let test1 = $('#test1');
      ////let test2 = $('#test2');
      //test1.on(
      //    'keydown', 
      //    function(e) {
      //        vm.test1(e)
      //    });
      let runningSheetTable = $('#running-sheet-table');
      //let test2 = $('#test2');
      runningSheetTable.on(
          'keydown',
          function(e) {
              vm.runningSheetEvents(e)
          });

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
      Object.assign(this.runningSheet, this.legal_case.running_sheet_entries);
      this.constructRunningSheetTable();
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
