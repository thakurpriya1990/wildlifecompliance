<template lang="html">
    <div id="PersonOrArtifactModal">
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" title="" large force>
            <div class="container-fluid">
                <ul class="nav nav-pills">
                    <li :class="personTabListClass"><a data-toggle="tab" @click="updateTabSelected('pTab')" :href="'#'+pTab">Search Person</a></li>
                    <li :class="artifactTabListClass"><a data-toggle="tab" @click="updateTabSelected('aTab')" :href="'#'+aTab" >Search Object</a></li>
                    <li :class="urlTabListClass"><a data-toggle="tab" @click="updateTabSelected('uTab')" :href="'#'+uTab">Insert URL</a></li>
                </ul>
                <div class="tab-content">
                    <div :id="pTab" :class="personTabClass">
                        <div>
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
                            />
                        </div>
                    </div>
                    <div :id="aTab" :class="artifactTabClass">
                    </div>
                    <div :id="uTab" :class="urlTabClass">
                        <div class="col-sm-12 form-group"><div class="row">
                            <div class="col-sm-6">
                                <label for="url">URL</label>
                                <span>https://</span>
                                <input id="inputUrl" type="text" v-model="urlText"/>
                            </div>
                        </div></div>
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

export default {
    name: "PersonOrArtifactModal",
    data: function() {
      return {
        isModalOpen: false,
        tabSelected: '',
        urlText: '',
        uuid: 0,
        entity: {},
        pTab: 'pTab' + this._uid,
        aTab: 'aTab' + this._uid,
        uTab: 'uTab' + this._uid,
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
    },
    computed: {
        updateSearchPersonOrganisationBindId: function() {
            this.uuid += 1
            return "SearchPerson_" + this.uuid.toString();
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
        cancel: function() {
            this.$emit('modal-action', {
                row_number_selected: this.rowNumberSelected,
                action: 'cancel',
            });
            this.isModalOpen = false;
        },
        ok: function() {
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
                this.isModalOpen = false;
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
            }
            Object.assign(this.entity, urlEntity);
        }
    },
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
</style>
