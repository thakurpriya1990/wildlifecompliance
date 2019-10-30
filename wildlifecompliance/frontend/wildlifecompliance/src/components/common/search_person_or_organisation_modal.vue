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
                v-bind:key="updateSearchPersonOrganisationBindId"/>
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
            this.isModalOpen = false;
        },
        close: function () {
            this.isModalOpen = false;
        },
        entitySelected: async function(para) {
            console.log(para);
            // now send back to parent
        },
    },
    created: async function() {
    }
};
</script>

<style lang="css">
</style>
