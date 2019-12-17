<template lang="html">
    <div class="container-fluid">
        <div class="col-sm-12 child-artifact-component">
            <div class="form-group">
                <div class="row">
                    <ul class="nav nav-pills">
                        <li class="nav-item active"><a data-toggle="tab" :href="'#'+newTab">New</a></li>
                        <li class="nav-item"><a data-toggle="tab" :href="'#'+existingTab" >Existing</a></li>
                    </ul>
                    <div class="tab-content">
                        <div :id="newTab" class="tab-pane fade in active">
                            <ul class="nav nav-pills">
                                <li class="nav-item active"><a data-toggle="tab" :href="'#'+objectTab">Object</a></li>
                                <li class="nav-item"><a data-toggle="tab" :href="'#'+detailsTab" >Details</a></li>
                                <li class="nav-item"><a data-toggle="tab" :href="'#'+storageTab" >Storage</a></li>
                                <li class="nav-item"><a data-toggle="tab" :href="'#'+disposalTab" >Disposal</a></li>
                            </ul>
                            <div class="tab-content">
                                <div :id="objectTab" class="tab-pane fade in active li-top-buffer">
                                    <div class="form-group">
                                      <div class="row">
                                        <div class="col-sm-3">
                                          <label>Document Type</label>
                                        </div>
                                        <div class="col-sm-6">
                                          <!--select :disabled="readonlyForm" class="form-control" v-model="artifact.artifact_id" @change="loadSchema"-->
                                          <select class="form-control" v-model="document_artifact.document_type_id">
                                            <option  v-for="option in documentArtifactTypes" :value="option.id" v-bind:key="option.id">
                                              {{ option.artifact_type }}
                                            </option>
                                          </select>
                                        </div>
                                      </div>
                                    </div>
                                    <div class="col-sm-12">
                                        <div class="form-group">
                                            <div class="row">
                                                <div class="col-sm-3">
                                                    <label class="control-label pull-left" for="Name">Attachments</label>
                                                </div>
                                                <div class="col-sm-9">
                                                    <filefield 
                                                    ref="comms_log_file" 
                                                    name="comms-log-file" 
                                                    :isRepeatable="true" 
                                                    documentActionUrl="temporary_document" 
                                                    @update-temp-doc-coll-id="setTemporaryDocumentCollectionId"/>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div :id="detailsTab" class="tab-pane fade in li-top-buffer">
                                    details
                                </div>
                                <div :id="storageTab" class="tab-pane fade in li-top-buffer">
                                    storage
                                </div>
                                <div :id="disposalTab" class="tab-pane fade in li-top-buffer">
                                    disposal
                                </div>
                            </div>
                        </div>
                        <div :id="existingTab" class="tab-pane fade in li-top-buffer">
                        </div>
                    </div>
                </div>
            </div>
        </div>

    </div>
</template>
<script>
import Vue from "vue";
import modal from '@vue-utils/bootstrap-modal.vue';
import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";
import filefield from '@/components/common/compliance_file.vue';
import { required, minLength, between } from 'vuelidate/lib/validators'

export default {
    name: "DocumentArtifactComponent",
    data: function() {
        return {
            newTab: 'newTab'+this._uid,
            existingTab: 'existingTab'+this._uid,
            objectTab: 'objectTab'+this._uid,
            detailsTab: 'detailsTab'+this._uid,
            storageTab: 'storageTab'+this._uid,
            disposalTab: 'disposalTab'+this._uid,
            isModalOpen: false,
            processingDetails: false,
            documentActionUrl: '',
            temporary_document_collection_id: null,
            documentArtifactTypes: [],
            physicalArtifactTypes: [],
            /*
            entity: {
                id: null,
                data_type: 'document_artifact',
            },
            */
        }
    },
    components: {
      modal,
      filefield,
    },
    computed: {
      ...mapGetters('documentArtifactStore', {
        document_artifact: "document_artifact",
      }),
      artifactType: function() {
          let aType = ''
          if (this.document_artifact && this.document_artifact.document_type) {
              aType = this.document_artifact.document_type.artifact_type;
          }
          return aType;
      },
        /*
      ...mapGetters('physicalArtifactStore', {
        physical_artifact: "physical_artifact",
      }),
      */
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
        }),
        setTemporaryDocumentCollectionId: function(val) {
            this.temporary_document_collection_id = val;
        },
        parentSave: async function() {
            let documentArtifactEntity = null;
            /*
            if (this.saveButtonEnabled) {
                savedEmailUser = await this.saveData('parentSave')
            } else {
                savedEmailUser = {'ok': true};
            }
            */
            await this.saveDocumentArtifact({'parentSave': true})
            //this.entity.id = 
            this.$emit('entity-selected', {
                id: this.document_artifact.id,
                data_type: 'document_artifact',
                artifact_type: this.artifactType,
            });
            //return documentArtifactEntity;
        },
        cancel: async function() {
            await this.$refs.comms_log_file.cancel();
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
    created: async function() {
    /*
      if (this.$route.params.inspection_id) {
          await this.loadInspection({ inspection_id: this.$route.params.inspection_id });
      }
      */
      await this.loadDocumentArtifact({ document_artifact_id: 1 });
      console.log(this)
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
