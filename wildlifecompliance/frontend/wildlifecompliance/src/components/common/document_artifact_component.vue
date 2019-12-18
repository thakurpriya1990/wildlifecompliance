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
                            <div :id="objectTab" class="tab-pane fade in active li-top-buffer">
                                <div class="col-sm-12">
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
                                    <div class="form-group">
                                        <div class="row">
                                            <div class="col-sm-3">
                                                <label>Witness</label>
                                            </div>
                                            <div class="col-sm-9">
                                                <SearchPersonOrganisation 
                                                personOnly
                                                :isEditable="!readonlyForm" 
                                                classNames="form-control" 
                                                @entity-selected="entitySelected"
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
//import modal from '@vue-utils/bootstrap-modal.vue';
import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";
import filefield from '@/components/common/compliance_file.vue';
//import { required, minLength, between } from 'vuelidate/lib/validators'
import 'bootstrap/dist/css/bootstrap.css';
import 'eonasdan-bootstrap-datetimepicker';
import moment from 'moment';
import SearchPersonOrganisation from './search_person_or_organisation'

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
            isModalOpen: false,
            processingDetails: false,
            documentActionUrl: '',
            temporary_document_collection_id: null,
            documentArtifactTypes: [],
            physicalArtifactTypes: [],
            entity: {
                id: null,
            },
        }
    },
    components: {
      //modal,
      filefield,
      SearchPersonOrganisation,
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
      readonlyForm: function() {
          return false;
      },
      updateSearchPersonOrganisationBindId: function() {
          this.uuid += 1
          return "DocumentArtifact_SearchPerson_" + this.uuid.toString();
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
        }),
        setTemporaryDocumentCollectionId: function(val) {
            this.temporary_document_collection_id = val;
        },
        entitySelected: function(entity) {
            console.log(entity);
            Object.assign(this.entity, entity)
        },
        save: async function() {
            if (this.document_artifact.id) {
                await this.saveDocumentArtifact({ create: false, internal: false });
            } else {
                await this.saveDocumentArtifact({ create: true, internal: false });
            }
        },
        parentSave: async function() {
            //let documentArtifactEntity = null;
            /*
            if (this.saveButtonEnabled) {
                savedEmailUser = await this.saveData('parentSave')
            } else {
                savedEmailUser = {'ok': true};
            }
            */
            await this.save();
            //this.entity.id = 
            this.$emit('entity-selected', {
                id: this.document_artifact.id,
                data_type: 'document_artifact',
                artifact_type: this.artifactType,
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
      });
    },
    beforeDestroy: async function() {
        console.log("beforeDestroy")
        await this.setDocumentArtifact({});
    },
    /*
    destroyed: function() {
        console.log("destroyed")
    },
    */
    created: async function() {
      console.log("created")
      if (this.$route.params.document_artifact_id) {
          await this.loadDocumentArtifact({ document_artifact_id: this.$route.params.document_artifact_id });
      }
      //await this.loadDocumentArtifact({ document_artifact_id: 1 });
      //console.log(this)
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
