<template lang="html">
    <div id="SearchPersonOrganisationModal">
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" title="Search Person" large force>
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
