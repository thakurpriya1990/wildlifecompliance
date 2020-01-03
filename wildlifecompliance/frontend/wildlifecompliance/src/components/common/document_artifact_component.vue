<template lang="html">
    <div class="container-fluid">
        <div class="col-sm-12 child-artifact-component">
            <div class="form-group">
                <div class="row">
                    <div v-if="!parentModal">
                        <ul class="nav nav-pills">
                            <li class="nav-item active"><a data-toggle="tab" :href="'#'+newTab">Object</a></li>
                            <li class="nav-item"><a data-toggle="tab" :href="'#'+rTab">Related Items</a></li>
                        </ul>
                    </div>
                    <div v-else>
                        <ul class="nav nav-pills">
                            <li class="nav-item active"><a data-toggle="tab" :href="'#'+newTab">New</a></li>
                            <li class="nav-item"><a data-toggle="tab" :href="'#'+existingTab" >Existing</a></li>
                        </ul>
                    </div>
                    <div class="tab-content">
                        <div :id="newTab" class="tab-pane fade in active">
                        <FormSection :formCollapse="false" :label="artifactType" Index="0" :hideHeader="!documentArtifactIdExists">
                            <div :id="objectTab" class="tab-pane fade in active li-top-buffer">
                                <div class="col-sm-12">
                                    <div class="form-group">
                                      <div class="row">
                                        <div class="col-sm-3">
                                          <label>Document Type</label>
                                        </div>
                                        <div class="col-sm-6">
                                          <select class="form-control" v-model="document_artifact.document_type" ref="setArtifactType">
                                            <option  v-for="option in documentArtifactTypes" :value="option" v-bind:key="option.id">
                                              {{ option.artifact_type }}
                                            </option>
                                          </select>
                                        </div>
                                      </div>
                                    </div>
                                </div>
                                <div class="col-sm-12">
                                    <div class="form-group">
                                        <div class="row">
                                            <div class="col-sm-3">
                                                <label class="control-label pull-left" for="Name">Document</label>
                                            </div>
                                            <div class="col-sm-9">
                                                <filefield
                                                ref="default_document"
                                                name="default-document"
                                                :isRepeatable="true"
                                                documentActionUrl="temporary_document"
                                                @update-temp-doc-coll-id="setTemporaryDocumentCollectionId"/>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="form-group">
                                      <div class="row">
                                        <div class="col-sm-3">
                                          <label>Identifier</label>
                                        </div>
                                        <div class="col-sm-9">
                                          <input :readonly="readonlyForm" class="form-control" v-model="document_artifact.identifier"/>
                                        </div>
                                      </div>
                                    </div>
                                    <div v-if="statementVisibility" class="form-group">
                                      <div class="row">
                                        <div class="col-sm-3">
                                          <label>Statement</label>
                                        </div>
                                        <div class="col-sm-6">
                                          <select class="form-control" v-model="document_artifact.statement_id" ref="setStatement">
                                            <option  v-for="option in legal_case.statement_artifacts" :value="option.id" v-bind:key="option.id">
                                            {{ option.document_type.artifact_type }}: {{ option.identifier }}
                                            </option>
                                          </select>
                                        </div>
                                      </div>
                                    </div>
                                    <div class="form-group">
                                      <div class="row">
                                        <div class="col-sm-3">
                                          <label>Description</label>
                                        </div>
                                        <div class="col-sm-9">
                                          <textarea :readonly="readonlyForm" class="form-control" v-model="document_artifact.description"/>
                                        </div>
                                      </div>
                                    </div>
                                    <div v-if="personProvidingStatementVisibility" class="form-group">
                                        <div class="row">
                                            <div class="col-sm-3">
                                                <label>{{ personProvidingStatementLabel }}</label>
                                            </div>
                                            <div class="col-sm-9">
                                                <SearchPersonOrganisation 
                                                :parentEntity="personProvidingStatementEntity"
                                                personOnly
                                                :isEditable="!readonlyForm" 
                                                classNames="form-control" 
                                                @entity-selected="setPersonProvidingStatement"
                                                showCreateUpdate
                                                ref="document_artifact_search_person_organisation"
                                                v-bind:key="updateSearchPersonOrganisationBindId"
                                                addFullName
                                                :displayTitle="false"
                                                domIdHelper="document_artifact"
                                                departmentalStaff
                                                />
                                            </div>
                                        </div>
                                    </div>
                                    <div v-if="interviewerVisibility" class="form-group">
                                        <div class="row">
                                            <div class="col-sm-3">
                                                <label >{{ interviewerLabel }}</label>
                                            </div>
                                            <div class="col-sm-9">
                                                <select ref="department_users" class="form-control" v-model="document_artifact.interviewer_email">
                                                    <option  v-for="option in departmentStaffList" :value="option.email" v-bind:key="option.pk">
                                                    {{ option.name }} 
                                                    </option>
                                                </select>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="form-group">
                                        <div class="row">
                                            <label class="col-sm-3">Date</label>
                                            <div class="col-sm-3">
                                                <div class="input-group date" ref="artifactDatePicker">
                                                    <input :disabled="readonlyForm" type="text" class="form-control" placeholder="DD/MM/YYYY" v-model="document_artifact.artifact_date" />
                                                    <span class="input-group-addon">
                                                        <span class="glyphicon glyphicon-calendar"></span>
                                                    </span>
                                                </div>
                                            </div>
                                            <label class="col-sm-3">Time</label>
                                            <div class="col-sm-3">
                                                <div class="input-group date" ref="artifactTimePicker">
                                                  <input :disabled="readonlyForm" type="text" class="form-control" placeholder="HH:MM" v-model="document_artifact.artifact_time"/>
                                                  <span class="input-group-addon">
                                                      <span class="glyphicon glyphicon-calendar"></span>
                                                  </span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </FormSection>
                        </div>
                        <div :id="existingTab" class="tab-pane fade in li-top-buffer">
                        </div>
                        <div v-if="!parentModal" :id="rTab" class="tab-pane fade in">
                            <FormSection :formCollapse="false" label="Related Items">
                                <div class="col-sm-12 form-group"><div class="row">
                                    <div class="col-sm-12" v-if="relatedItemsVisibility">
                                        <RelatedItems 
                                        :parent_update_related_items="setRelatedItems" 
                                        v-bind:key="relatedItemsBindId" 
                                        :readonlyForm="!canUserAction"
                                        parentComponentName="document_artifact"
                                        />
                                    </div>
                                </div></div>
                            </FormSection>
                        </div>
                    </div>
                </div>
            </div>
        </div>

    </div>
</template>
<script>
import Vue from "vue";
//import modal from '@vue-utils/bootstrap-modal.vue';
import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";
import filefield from '@/components/common/compliance_file.vue';
//import { required, minLength, between } from 'vuelidate/lib/validators'
import 'bootstrap/dist/css/bootstrap.css';
import 'eonasdan-bootstrap-datetimepicker';
import moment from 'moment';
import SearchPersonOrganisation from './search_person_or_organisation'
import FormSection from "@/components/forms/section_toggle.vue";
import RelatedItems from "@common-components/related_items.vue";

export default {
    name: "DocumentArtifactComponent",
    data: function() {
        return {
            uuid: 0,
            newTab: 'newTab'+this._uid,
            existingTab: 'existingTab'+this._uid,
            objectTab: 'objectTab'+this._uid,
            detailsTab: 'detailsTab'+this._uid,
            storageTab: 'storageTab'+this._uid,
            disposalTab: 'disposalTab'+this._uid,
            rTab: 'rTab'+this._uid,
            isModalOpen: false,
            processingDetails: false,
            documentActionUrl: '',
            temporary_document_collection_id: null,
            documentArtifactTypes: [],
            departmentStaffList: [],
            selectedCustodian: {},
            entity: {
                id: null,
            },
            statementArtifactTypes: [
                'Record of Interview',
                'Witness Statement',
                'Expert Statement',
                'Officer Statement',
                ],
            statementVisibility: false,
            //departmentStaffList: [],
            //personProvidingStatementLabel: '',
            //interviewerLabel: '',
        }
    },
    components: {
      //modal,
      filefield,
      SearchPersonOrganisation,
      FormSection,
      RelatedItems,
    },
    props: {
        parentModal: {
            type: Boolean,
            required: false,
            default: false,
        },
    },
    watch: {
        artifactType: {
            handler: function (){
                this.setStatementVisibility();
                //this.setPersonProvidingStatementLabel();
                //this.setInterviewerLabel();
                /*
                if (
                    // legal case exists and Document Type is not a statementArtifactType
                    (this.legalCaseExists && this.artifactType && !this.statementArtifactTypes.includes(this.artifactType)) ||
                    // OR document_artifact already has a linked statement
                    (this.document_artifact && this.document_artifact.statement)
                    )
                {
                    console.log("statementVisibility true")
                    this.statementVisibility = true;
                } else {
                    console.log("statementVisibility false")
                    this.statementVisibility = false;
                }
                */
            },
            deep: true,
        },
        /*
        legalCaseId: {
            handler: async function() {
                if (this.legal_case && this.legal_case.id) {
                    await this.setDocumentArtifactLegalId(this.legal_case.id)
                }
            },
        },
        */

    },
    computed: {
        ...mapGetters('documentArtifactStore', {
            document_artifact: "document_artifact",
        }),
        ...mapGetters('legalCaseStore', {
            legal_case: "legal_case",
        }),
        canUserAction: function() {
            return true;
        },
        personProvidingStatementEntity: function() {
            let entity = {}
            if (this.document_artifact && this.document_artifact.person_providing_statement) {
                entity.id = this.document_artifact.person_providing_statement.id;
                entity.data_type = 'individual';
            }
            return entity;
        },
        legalCaseId: function() {
          let ret_val = null;
          if (this.legal_case && this.legal_case.id) {
              ret_val = this.legal_case.id;
          }
          return ret_val;
        },
        legalCaseExists: function() {
          let caseExists = false;
          if (this.legal_case && this.legal_case.id) {
              caseExists = true;
          }
          return caseExists;
        },
        documentArtifactId: function() {
          let id = null;
          if (this.document_artifact && this.document_artifact.id) {
              id = this.document_artifact.id;
          }
          return id;
        },
        documentArtifactIdExists: function() {
          let recordExists = false;
          if (this.document_artifact && this.document_artifact.id) {
              recordExists = true;
          }
          return recordExists;
        },
        artifactType: function() {
          console.log("artifact type")
          let aType = ''
          if (this.document_artifact && this.document_artifact.document_type) {
              aType = this.document_artifact.document_type.artifact_type;
          }
          return aType;
        },
        personProvidingStatementLabel: function() {
            let label = '';
            if (this.artifactType === 'Witness Statement') {
                label = 'Witness';
            } else if (this.artifactType === 'Expert Statement') {
                label = 'Expert';
            }
            return label;
        },
        interviewerLabel: function() {
            let label = '';
            if (this.artifactType === 'Witness Statement') {
                label = 'Officer taking statement'
            } else if (this.artifactType === 'Record of Interview') {
                label = 'Interviewer';
            } else if (this.artifactType === 'Officer Statement') {
                label = 'Officer';
            }
            return label
        },
        personProvidingStatementVisibility: function() {
            let visibility = false;
            if (this.artifactType === 'Expert Statement' || this.artifactType === 'Witness Statement') {
                visibility = true;
            }
            return visibility;
        },
        interviewerVisibility: function() {
            let visibility = false;
            if (this.artifactType !== 'Expert Statement' && this.statementArtifactTypes.includes(this.artifactType)) {
                visibility = true;
            }
            return visibility;
        },
        readonlyForm: function() {
          return false;
        },
        updateSearchPersonOrganisationBindId: function() {
          this.uuid += 1
          return "DocumentArtifact_SearchPerson_" + this.uuid.toString();
        },
        relatedItemsBindId: function() {
            let timeNow = Date.now()
            let bindId = null;
            if (this.document_artifact && this.document_artifact.id) {
                //bindId = 'document_artifact_' + this.document_artifact.id + '_' + this.uuid;
                bindId = 'document_artifact_' + this.document_artifact.id + '_' + timeNow.toString();
            } else {
                bindId = timeNow.toString();
            }
            return bindId;
        },
        relatedItemsVisibility: function() {
            let related_items_visibility = false;
            if (this.document_artifact && this.document_artifact.id) {
                related_items_visibility = true;
            }
            return related_items_visibility;
        },
    },
    filters: {
      formatDate: function(data) {
          return data ? moment(data).format("DD/MM/YYYY HH:mm:ss") : "";
      }
    },
    methods: {
        ...mapActions('documentArtifactStore', {
            saveDocumentArtifact: 'saveDocumentArtifact',
            loadDocumentArtifact: 'loadDocumentArtifact',
            setDocumentArtifact: 'setDocumentArtifact',
            setRelatedItems: 'setRelatedItems',
            setPersonProvidingStatementId: 'setPersonProvidingStatementId',
            setInterviewerId: 'setInterviewerId',
            //setDocumentArtifactLegalId: 'setDocumentArtifactLegalId',
        }),
        ...mapActions('legalCaseStore', {
            loadLegalCase: 'loadLegalCase',
        }),
        setStatementVisibility: function() {
            if (
                // legal case exists and Document Type is not a statementArtifactType
                (this.legalCaseExists && this.artifactType && !this.statementArtifactTypes.includes(this.artifactType)) ||
                // OR document_artifact already has a linked statement
                (this.document_artifact && this.document_artifact.statement)
                )
            {
                console.log("statementVisibility true")
                this.statementVisibility = true;
            } else {
                console.log("statementVisibility false")
                this.statementVisibility = false;
            }
        },
        setTemporaryDocumentCollectionId: function(val) {
            this.temporary_document_collection_id = val;
        },
        setPersonProvidingStatement: function(entity) {
            console.log(entity);
            //Object.assign(this.entity, entity)
            this.setPersonProvidingStatementId(entity.id);
        },
        save: async function() {
            if (this.document_artifact.id) {
                await this.saveDocumentArtifact({ create: false, internal: false, legal_case_id: this.legalCaseId });
            } else {
                await this.saveDocumentArtifact({ create: true, internal: false, legal_case_id: this.legalCaseId });
            }
        },
        create: async function() {
            //let documentArtifactEntity = null;
            /*
            if (this.saveButtonEnabled) {
                savedEmailUser = await this.saveData('parentSave')
            } else {
                savedEmailUser = {'ok': true};
            }
            */
            await this.saveDocumentArtifact({ create: true, internal: true, legal_case_id: this.legalCaseId });
            //this.entity.id = 
            this.$nextTick(() => {
                this.$emit('entity-selected', {
                    id: this.document_artifact.id,
                    data_type: 'document_artifact',
                    identifier: this.document_artifact.identifier,
                    artifact_type: this.artifactType,
                });
            });
            //return documentArtifactEntity;
        },
        cancel: async function() {
            await this.$refs.default_document.cancel();
        },
        addEventListeners: function() {
            let vm = this;
            let el_fr_date = $(vm.$refs.artifactDatePicker);
            let el_fr_time = $(vm.$refs.artifactTimePicker);

            // "From" field
            el_fr_date.datetimepicker({
            format: "DD/MM/YYYY",
            minDate: "now",
            showClear: true
            });
            el_fr_date.on("dp.change", function(e) {
                console.log(e)
                if (el_fr_date.data("DateTimePicker").date()) {
                  vm.document_artifact.artifact_date = e.date.format("DD/MM/YYYY");
                } else if (el_fr_date.data("date") === "") {
                  vm.document_artifact.artifact_date = "";
                }
            });
            el_fr_time.datetimepicker({ format: "LT", showClear: true });
            el_fr_time.on("dp.change", function(e) {
                console.log(e)
                if (el_fr_time.data("DateTimePicker").date()) {
                  vm.document_artifact.artifact_time = e.date.format("LT");
                } else if (el_fr_time.data("date") === "") {
                  vm.document_artifact.artifact_time = "";
                }
            });
            /*
            // artifact type events
            let artifactEvent = $(vm.$refs.setArtifactType);
            artifactEvent.on("change", function(e) {
            let artifactTypeId = e.target.value;
            });
            */
        },
        compare: function(a, b) {
            console.log("compare")
            const nameA = a.name.toLowerCase();
            const nameB = b.name.toLowerCase();

            let comparison = 0;
            if (this.bandA > this.bandB) {
                comparison = 1;
            } else if (this.bandA < this.bandB) {
                comparison = -1;
            }
            return comparison;
        },

      //createDocumentActionUrl: async function(done) {
      //  if (!this.inspection.id) {
      //      // create inspection and update vuex
      //      let returned_inspection = await this.saveInspection({ create: true, internal: true })
      //      await this.loadInspection({inspection_id: returned_inspection.body.id});
      //  }
      //  // populate filefield document_action_url
      //  this.$refs.comms_log_file.document_action_url = this.inspection.createInspectionProcessCommsLogsDocumentUrl;
      //  return done(true);
      //},

    },
    mounted: function() {
      this.$nextTick(async () => {
          this.addEventListeners();
          /*
          if (this.legal_case && this.legal_case.id) {
              this.setDocumentArtifactLegalId(this.legal_case.id)
          */
      });
    },
    beforeDestroy: async function() {
        console.log("beforeDestroy")
        await this.setDocumentArtifact({});
    },
    created: async function() {
        console.log("created")
        if (this.$route.params.document_artifact_id) {
            await this.loadDocumentArtifact({ document_artifact_id: this.$route.params.document_artifact_id });
        }
        // if main obj page, call loadLegalCase if document_artifact.legal_case_id exists
        if (this.$route.name === 'view-artifact' && this.document_artifact && this.document_artifact.legal_case_id) {
            await this.loadLegalCase({ legal_case_id: this.document_artifact.legal_case_id });
        }
        this.setStatementVisibility();
        // document artifact types
        let returned_document_artifact_types = await cache_helper.getSetCacheList(
          'DocumentArtifactTypes',
          api_endpoints.document_artifact_types
          );
        Object.assign(this.documentArtifactTypes, returned_document_artifact_types);
        // blank entry allows user to clear selection
        this.documentArtifactTypes.splice(0, 0,
          {
            id: "",
            artifact_type: "",
            description: "",
          });
        // retrieve department_users from backend cache
        let returned_department_users = await this.$http.get(api_endpoints.department_users)
        Object.assign(this.departmentStaffList, returned_department_users.body)
        this.departmentStaffList.splice(0, 0,
          {
            pk: "",
            name: "",
          });
    },
};
</script>

<style lang="css">
.child-artifact-component {
    margin-top: 20px;
}
.li-top-buffer {
    margin-top: 20px;
}
.tab-content {
  background: white;
}
</style>
