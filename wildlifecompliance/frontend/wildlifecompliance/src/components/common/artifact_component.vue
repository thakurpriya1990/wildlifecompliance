<template lang="html">
    <div class="container-fluid">
        <div class="col-sm-12 parent-artifact">
            <div class="form-group">
                <div class="row">
                    <div class="col-sm-12">
                        <div class="col-sm-3">
                            <input type="radio" id="document" value="document" v-model="componentType">
                            <label for="document">Document</label>
                        </div>
                        <div class="col-sm-3">
                            <input type="radio" id="physical" value="physical" v-model="componentType">
                            <label for="physical">Physical Object</label>
                        </div>
                        <!--select class="form-control" v-model="componentType">
                            <option value="document">Document</option>
                            <option value="physical">Physical Object</option>
                          </select-->
                </div>
                <div v-if="showDocumentArtifactComponent" class="row">
                    <DocumentArtifact 
                    ref="document_artifact"
                    />
                </div>
                <!--div v-if="documentArtifactComponent" class="row">
                    <DocumentArtifact />
                </div-->

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
import DocumentArtifact from './document_artifact_component.vue';

export default {
    name: "ArtifactComponent",
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
            componentType: '',
        }
    },
    components: {
      modal,
      filefield,
      DocumentArtifact,
    },
    computed: {
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
    },
    filters: {
      formatDate: function(data) {
          return data ? moment(data).format("DD/MM/YYYY HH:mm:ss") : "";
      }
    },
    methods: {
        setTemporaryDocumentCollectionId: function(val) {
            this.temporary_document_collection_id = val;
        },
        parentSave: async function() {
            let entity = {};
            //if (this.showDocumentArtifactComponent && this.documentEntityDatatype) {
            if (this.showDocumentArtifactComponent) {
                let documentArtifactEntity = null;
                //documentArtifactEntity = await this.$refs.document_artifact.parentSave({'parentSave': true})
                documentArtifactEntity = await this.$refs.document_artifact.parentSave({'parentSave': true})
                console.log(documentArtifactEntity);
                Object.assign(entity, documentArtifactEntity)
            }
            // emit?
            return entity;
        },
    },
    created: async function() {
    /*
      if (this.$route.params.inspection_id) {
          await this.loadInspection({ inspection_id: this.$route.params.inspection_id });
      }
      */
    },
};
</script>

<style lang="css">
</style>
