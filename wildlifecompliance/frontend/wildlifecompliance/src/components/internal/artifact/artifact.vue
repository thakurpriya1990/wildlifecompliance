<template lang="html">
    <div class="container">
      <div class="row">
        <div class="col-md-3">
          <!--h3>Case: {{ legal_case.number }}</h3-->
        </div>
      </div>
          <div class="col-md-3">
            <CommsLogs :comms_url="comms_url" :logs_url="logs_url" :comms_add_url="comms_add_url" :disable_add_entry="false"/>
            <div class="row">
                <div class="panel panel-default">
                    <div class="panel-heading">
                        Workflow
                    </div>
                    <!--div class="panel-body panel-collapse">
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
                    </div-->
                </div>
            </div>

          </div>
          <div class="col-md-9" id="main-column">
            <div class="row">

                <div class="container-fluid">
                    <ul class="nav nav-pills aho2">
                        <li class="nav-item active"><a data-toggle="tab" :href="'#'+oTab">Object</a></li>
                        <li class="nav-item"><a data-toggle="tab" :href="'#'+rTab">Related Items</a></li>
                    </ul>
                    <div class="tab-content">
                        <div :id="oTab" class="tab-pane fade in active">
                            <div v-if="showDocumentArtifactComponent" class="row">
                                <DocumentArtifact 
                                ref="document_artifact"
                                v-bind:key="updateDocumentArtifactBindId"
                                />
                            </div>
                            <div v-if="showPhysicalArtifactComponent" class="row">
                                <PhysicalArtifact 
                                ref="physical_artifact"
                                v-bind:key="updatePhysicalArtifactBindId"
                                />
                            </div>
                        </div>

                        <div :id="rTab" class="tab-pane fade in">
                            <FormSection :formCollapse="false" label="Related Items">
                                <div class="col-sm-12 form-group"><div class="row">
                                    <div class="col-sm-12" v-if="relatedItemsVisibility">
                                        <RelatedItems 
                                        v-bind:key="relatedItemsBindId" 
                                        :readonlyForm="!canUserAction"/>
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
                        <button v-else type="button" @click.prevent="saveExit()" class="btn btn-primary" >Save and Exit</button>
                        <button v-if="showSpinner && !showExit" disabled type="button" @click.prevent="save('noexit')" class="btn btn-primary" >
                            <i class="fa fa-spinner fa-spin"/> Saving</button>
                        <button v-else type="button" @click.prevent="save()" class="btn btn-primary">Save and Continue</button>
                    </p>
                </div>
            </div>
        </div>
    </div>
</template>
<script>
import Vue from "vue";
import FormSection from "@/components/forms/section_toggle.vue";
import CommsLogs from "@common-components/comms_logs.vue";
import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";
import utils from "@/components/external/utils";
import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
import moment from 'moment';
import 'bootstrap/dist/css/bootstrap.css';
import 'eonasdan-bootstrap-datetimepicker';
import RelatedItems from "@common-components/related_items.vue";
require("select2/dist/css/select2.min.css");
require("select2-bootstrap-theme/dist/select2-bootstrap.min.css");
import hash from 'object-hash';
import _ from 'lodash';
import DocumentArtifact from '@common-components/document_artifact_component'
import PhysicalArtifact from '@common-components/physical_artifact_component'


export default {
    name: "ViewArtifact",
    data: function() {
        return {
            uuid: 0,
            //componentType: '',
            showSpinner: false,
            showExit: false,
            rowNumberSelected: '',
            tabSelected: '',
            objectHash: null,
            oTab: 'runTab'+this._uid,
            rTab: 'rTab'+this._uid,
            /*
            current_schema: [],
            workflowBindId: '',
            workflow_type: '',
            */
            comms_url: helpers.add_endpoint_json(
              api_endpoints.artifact,
              this.$route.params.artifact_id + "/comms_log"
            ),
            comms_add_url: helpers.add_endpoint_json(
              api_endpoints.artifact,
              this.$route.params.artifact_id + "/add_comms_log"
            ),
            logs_url: helpers.add_endpoint_json(
              api_endpoints.artifact,
              this.$route.params.artifact_id + "/action_log"
            ),
            /*
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
            */

      };
  },
  components: {
    CommsLogs,
    FormSection,
    RelatedItems,
    DocumentArtifact,
    PhysicalArtifact,
  },
  computed: {
    ...mapGetters('documentArtifactStore', {
      document_artifact: "document_artifact",
    }),
    ...mapGetters('physicalArtifactStore', {
      physical_artifact: "physical_artifact",
    }),
    componentType: function() {
        let returnType = '';
        if (this.document_artifact && this.document_artifact.id) {
            returnType = 'document';
        } else if (this.physical_artifact && this.physical_artifact.id) {
            returnType = 'physical';
        }
        return returnType;
    },
    artifactComponent: function() {
        let component = null;
        if (this.document_artifact && this.document_artifact.id) {
            component = this.document_artifact;
        } else if (this.physical_artifact && this.physical_artifact.id) {
            component = this.physical_artifact;
        }
        return component;
    },

    ...mapGetters({
        current_user: 'current_user'
    }),
    csrf_token: function() {
      return helpers.getCookie("csrftoken");
    },
      /*
    statusDisplay: function() {
        return this.legal_case.status ? this.legal_case.status.name : '';
    },
    statusId: function() {
        return this.legal_case.status ? this.legal_case.status.id : '';
    },
    */
    readonlyForm: function() {
        /*
        let readonly = true
        if (this.legal_case && this.legal_case.id) {
            readonly = !this.legal_case.can_user_action;
        }
        return readonly
        */
        return false;
    },
    canUserAction: function() {
        /*
        let return_val = false
        if (this.legal_case && this.legal_case.id) {
            return_val = this.legal_case.can_user_action;
        }
        return return_val
        */
        return true;
    },
    updateDocumentArtifactBindId: function() {
        return "PersonOrArtifact_DocumentArtifact_" + this.uuid.toString();
    },
    updatePhysicalArtifactBindId: function() {
        return "PersonOrArtifact_PhysicalArtifact_" + this.uuid.toString();
    },
    showDocumentArtifactComponent: function() {
        let showComponent = false;
        if (this.componentType === 'document') {
            showComponent = true;
        }
        return showComponent;
    },
    showPhysicalArtifactComponent: function() {
        let showComponent = false;
        if (this.componentType === 'physical') {
            showComponent = true;
        }
        return showComponent;
    },
    relatedItemsBindId: function() {
        let timeNow = Date.now()
        let bindId = null;
        if (this.artifactComponent && this.artifactComponent.id) {
            bindId = 'artifact_' + this.artifactComponent.id + '_' + this._uid;
        } else {
            bindId = timeNow.toString();
        }
        return bindId;
    },
    relatedItemsVisibility: function() {
        let related_items_visibility = false;
        if (this.artifactComponent && this.artifactComponent.id) {
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
          //setDocumentArtifactRelatedItems: 'setRelatedItems',
      }),
      ...mapActions('physicalArtifactStore', {
          savePhysicalArtifact: 'savePhysicalArtifact',
          loadPhysicalArtifact: 'loadPhysicalArtifact',
          setPhysicalArtifact: 'setPhysicalArtifact',
          //setPhysicalArtifactRelatedItems: 'setRelatedItems',
      }),
    ...mapActions({
        loadCurrentUser: 'loadCurrentUser',
    }),
      /*
    setRelatedItems: async function() {
        if (this.componentType === 'document') {
            await this.setDocumentArtifactRelatedItems();
        } else if (this.componenetType === 'physical') {
            await this.setPhysicalArtifactRelatedItems();
        }
    },
*/
    /*
    entitySelected: function(entity) {
        console.log(entity);
        Object.assign(this.entity, entity)
    },
    */
      /*
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
    */
    saveExit: async function() {
        await this.save({ "returnToDash": true })
    },
    save: async function({ returnToDash=false } = {}) {
      this.showSpinner = true;
      if (returnToDash) {
          this.showExit = true;
      }
      // save document or physical component
      if (this.componentType ==='document') {
          await this.$refs.document_artifact.parentSave();
      } else if (this.componentType === 'physical') {
          await this.$refs.physical_artifact.parentSave();
      }

      if (returnToDash) {
        // remove redundant eventListeners
        window.removeEventListener('beforeunload', this.leaving);
        window.removeEventListener('onblur', this.leaving);
        // return to dash
        this.$router.push({ name: 'internal-artifact-dash' });
      } else {
          //this.calculateHash();
          this.runningSheetEntriesUpdated = [];
          //this.constructRunningSheetTableWrapper();
      }
      this.showSpinner = false;
      this.showExit = false;
    },
      /*
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
    */
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
  },
  created: async function() {
      if (this.$route.params.artifact_id) {
          const returnedArtifact = await Vue.http.get(
              helpers.add_endpoint_json(
                  api_endpoints.artifact,
                  this.$route.params.artifact_id)
              );
          let artifactId = returnedArtifact.body.id
          let artifactObjectType = returnedArtifact.body.artifact_object_type
          console.log(artifactId)
          console.log(artifactObjectType)
          if (artifactId && artifactObjectType === 'document') {
              await this.loadDocumentArtifact({ document_artifact_id: artifactId });
          } else if (artifactId && artifactObjectType === 'physical') {
              await this.loadPhysicalArtifact({ physical_artifact_id: artifactId });
          }
      }
      await this.loadCurrentUser({ url: `/api/my_compliance_user_details` });
      console.log(this)
      /*

      this.calculateHash();
      this.constructRunningSheetTableWrapper();
      */
  },
    /*
  destroyed: function() {
      window.removeEventListener('beforeunload', this.leaving);
      window.removeEventListener('onblur', this.leaving);
  },
*/
  mounted: function() {
      this.$nextTick(() => {
          //this.addEventListeners();
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
