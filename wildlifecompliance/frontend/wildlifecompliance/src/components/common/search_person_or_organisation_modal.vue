<template lang="html">
    <div id="SearchPersonOrganisationModal">
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" title="" large force>
            <div class="container-fluid">
                <ul class="nav nav-pills aho2">
                    <li class="nav-item active"><a data-toggle="tab" :href="'#'+pTab">Search Person</a></li>
                    <li class="nav-item"><a data-toggle="tab" :href="'#'+oTab" >Search Object</a></li>
                    <li class="nav-item"><a data-toggle="tab" :href="'#'+uTab">Insert URL</a></li>
                </ul>
                <div class="tab-content">
                    <div :id="pTab" class="tab-pane fade in active">
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
                    <div :id="oTab" class="tab-pane fade in">
                    </div>
                    <div :id="uTab" class="tab-pane fade in">
                        <div>
                            <!--form action="#" @submit="checkUrlForm"-->
                            <form action="#">
                                <label for="url">url</label>
                                <input type="url" value="http"/>
                                <input type="submit" value="Submit"/>
                            </form>
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

export default {
    name: "SearchPersonOrganisationModal",
    data: function() {
      return {
        isModalOpen: false,
        uuid: 0,
        entity: {},
        pTab: 'pTab' + this._uid,
        oTab: 'oTab' + this._uid,
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
            required: true,
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
            //if (this.inspectedEntity.data_type && this.inspectedEntity.id) {
            //    return this.inspectedEntity.data_type + '_' + this.inspectedEntity.id
            //}
        },
    },

    methods: {
        cancel: function() {
            this.$emit('cancel-person-selected', {
                row_number_selected: this.rowNumberSelected,
            });
            this.isModalOpen = false;
        },
        ok: function() {
            if (this.entity.id) {
                this.$emit('person-selected', {
                    id: this.entity.id, 
                    data_type: this.entity.data_type,
                    row_number_selected: this.rowNumberSelected,
                    full_name: this.entity.full_name,
                });
            } else {
                this.cancel();
            }
            this.isModalOpen = false;
        },
        close: function () {
            this.isModalOpen = false;
        },
        entitySelected: async function(entity) {
            console.log(entity);
            Object.assign(this.entity, entity)
        },
    },
    created: async function() {
    }
};
</script>

<style lang="css">
</style>
