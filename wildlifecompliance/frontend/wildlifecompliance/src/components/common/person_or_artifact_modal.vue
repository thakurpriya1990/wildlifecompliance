<template lang="html">
    <div id="PersonOrArtifactModal">
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" title="" large force>
            <div class="container-fluid">
                <ul class="nav nav-pills">
                    <li :class="personTabListClass"><a data-toggle="tab" @click="updateTabSelected('pTab')" :href="'#'+pTab">Person</a></li>
                    <li :class="artifactTabListClass"><a data-toggle="tab" @click="updateTabSelected('aTab')" :href="'#'+aTab" >Object</a></li>
                    <li :class="urlTabListClass"><a data-toggle="tab" @click="updateTabSelected('uTab')" :href="'#'+uTab">URL</a></li>
                </ul>
                <div class="tab-content ul-top-buffer">
                    <div :id="pTab" :class="personTabClass"><div class="row">
                        <div class="col-sm-12 form-group"><div class="row">
                            <div class="col-sm-12">
                                <SearchPersonOrganisation 
                                personOnly
                                :excludeStaff="true" 
                                :isEditable="!readonlyForm" 
                                classNames="form-control" 
                                @entity-selected="entitySelected"
                                showCreateUpdate
                                ref="search_person_organisation"
                                v-bind:key="updateSearchPersonOrganisationBindId"
                                addFullName
                                :displayTitle="false"
                                />
                            </div>
                        </div></div>
                    </div></div>
                    <div :id="aTab" :class="artifactTabClass">
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
                            @entity-selected="entitySelected"
                            parentModal
                            v-bind:key="updateDocumentArtifactBindId"
                            />
                        </div>
                        <div v-if="showPhysicalArtifactComponent" class="row">
                            <PhysicalArtifact 
                            ref="physical_artifact"
                            @entity-selected="entitySelected"
                            parentModal
                            v-bind:key="updatePhysicalArtifactBindId"
                            />
                        </div>
                        <!--Artifact 
                        ref="artifact"
                        @entity-selected="entitySelected"
                        /-->
                    </div>
                    <div :id="uTab" :class="urlTabClass">
                        <div class="col-sm-12">
                            <div class="col-sm-2">
                                <select class="form-control" name="protocol" v-model="urlProtocol">
                                    <option value="https">https</option>
                                    <option value="http">http</option>
                                </select>
                            </div>
                            <div class="col-sm-6">
                                <input class="form-control" id="inputUrl" type="text" v-model="urlText"/>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </modal>
    </div>
</template>
<script>
import Vue from "vue";
import modal from '@vue-utils/bootstrap-modal.vue';
import SearchPersonOrganisation from './search_person_or_organisation'
import DocumentArtifact from './document_artifact_component'
import PhysicalArtifact from './physical_artifact_component'
import { mapState, mapGetters, mapActions, mapMutations } from "vuex";

export default {
    name: "PersonOrArtifactModal",
    data: function() {
      return {
        isModalOpen: false,
        tabSelected: '',
        urlText: '',
        urlProtocol: 'https',
        uuid: 0,
        entity: {},
        pTab: 'pTab' + this._uid,
        aTab: 'aTab' + this._uid,
        uTab: 'uTab' + this._uid,
        componentType: '',
        //image: "/static/wildlifecompliance_vue/img/shibaken.jpg"
        //image: "/static/wildlifecompliance_vue/img/shibaken.c4c9d81.jpg"
        //image: "../../../assets/img/shibaken.jpg"
      }
    },
    props: {
        readonlyForm: {
            required: false,
            default: true
        },
        rowNumberSelected: {
            type: String,
            required: true,
        },
        initialTabSelected: {
            type: String,
        },
        //caseRunningSheet: {
        //    type: Boolean,
        //    required: false,
        //    default: false,
        //},
    },
    components: {
      modal,
      SearchPersonOrganisation,
      DocumentArtifact,
      PhysicalArtifact,
    },
    watch: {
        tabSelected: {
            handler: async function (){
                //await this.cancelArtifactComponent();
                this.uuid += 1;
                //this.urlProtocol = 'https';
                //this.urlText = '';
            }
        }
    },
    computed: {
        ...mapGetters('legalCaseStore', {
          legal_case: "legal_case",
        }),
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
        updateSearchPersonOrganisationBindId: function() {
            return "PersonOrArtifact_SearchPerson_" + this.uuid.toString();
        },
        updateDocumentArtifactBindId: function() {
            return "PersonOrArtifact_DocumentArtifact_" + this.uuid.toString();
        },
        updatePhysicalArtifactBindId: function() {
            return "PersonOrArtifact_PhysicalArtifact_" + this.uuid.toString();
        },
        updateURLBindId: function() {
            return "PersonOrArtifact_URL_" + this.uuid.toString();
        },
        personTabSelected: function() {
            let isPersonTab = false;
            if (this.tabSelected === 'pTab') {
                isPersonTab = true;
            }
            return isPersonTab;
        },
        artifactTabSelected: function() {
            let isArtifactTab = false;
            if (this.tabSelected === 'aTab') {
                isArtifactTab = true;
            }
            return isArtifactTab;
        },
        urlTabSelected: function() {
            let isUrlTab = false;
            if (this.tabSelected === 'uTab') {
                isUrlTab = true;
            }
            return isUrlTab;
        },
        personTabClass: function() {
            let tabClass = 'tab-pane fade in';
            if (this.personTabSelected) {
                tabClass += ' active';
            }
            return tabClass;
        },
        personTabListClass: function() {
            let tabClass = 'nav-item';
            if (this.personTabSelected) {
                tabClass += ' active';
            }
            return tabClass;
        },
        artifactTabClass: function() {
            let tabClass = 'tab-pane fade in';
            if (this.artifactTabSelected) {
                tabClass += ' active';
            }
            return tabClass;
        },
        artifactTabListClass: function() {
            let tabClass = 'nav-item';
            if (this.artifactTabSelected) {
                tabClass += ' active';
            }
            return tabClass;
        },
        urlTabClass: function() {
            let tabClass = 'tab-pane fade in';
            if (this.urlTabSelected) {
                tabClass += ' active';
            }
            return tabClass;
        },
        urlTabListClass: function() {
            let tabClass = 'nav-item';
            if (this.urlTabSelected) {
                tabClass += ' active';
            }
            return tabClass;
        },
    },

    methods: {
        updateTabSelected: function(tabValue) {
            this.tabSelected = tabValue;
        },
        cancelArtifactComponent: async function() {
            if (this.artifactTabSelected) {
                if (this.showDocumentArtifactComponent) {
                    await this.$refs.document_artifact.cancel();
                } else if (this.showPhysicalArtifactComponent) {
                    await this.$refs.physical_artifact.cancel();
                }
            }
        },
        cancel: async function() {
            this.cancelArtifactComponent();
            this.$emit('modal-action', {
                row_number_selected: this.rowNumberSelected,
                action: 'cancel',
            });
            //this.isModalOpen = false;
            this.close();
        },
        ok: async function() {
            if (this.artifactTabSelected) {
                if (this.showDocumentArtifactComponent) {
                    await this.$refs.document_artifact.create();
                } else if (this.showPhysicalArtifactComponent) {
                    await this.$refs.physical_artifact.create();
                }
            }
            if (this.urlTabSelected && this.urlText) {
                this.submitUrl();
            }
            this.$nextTick(() => {
                if (this.entity.id || this.urlTabSelected && this.urlText) {
                    this.$emit('modal-action', {
                        entity: this.entity,
                        row_number_selected: this.rowNumberSelected,
                        action: 'ok',
                    });
                } else {
                    this.cancel();
                }
                //this.isModalOpen = false;
                this.close();
            });
        },
        close: function () {
            this.isModalOpen = false;
        },
        entitySelected: function(entity) {
            console.log(entity);
            Object.assign(this.entity, entity)
        },
        submitUrl: function() {
            console.log(this.urlText);
            let urlEntity = {
                data_type: 'url',
                url: this.urlText,
                urlProtocol: this.urlProtocol,
            }
            Object.assign(this.entity, urlEntity);
        }
    },
    /*
    destroyed: function() {
        console.log("destroyed")
    },
    */
    created: async function() {
        if (this.initialTabSelected === 'person') {
            this.tabSelected = 'pTab';
        } else if (this.initialTabSelected === 'artifact') {
            this.tabSelected = 'aTab';
        } else if (this.initialTabSelected === 'url') {
            this.tabSelected = 'uTab';
        }
    }
};
</script>

<style lang="css">
    .ul-top-buffer {
        margin-top: 20px;
    }
</style>
