<template lang="html">
    <div>
        <h3>{{ displayable_number }}</h3>
        <div class="col-md-3">

            <MenuAccess ref="menu_access" v-show="!is_external"></MenuAccess>          

        </div>

        <!-- Tabs Layout -->
        <div class="col-md-9" >
            <div id="tabs" v-show="displayable_tabs">
                <ul class="nav nav-pills mb-3" id="tab-section" data-tabs="tabs" >
                    <li class="nav-item active"><a id="0" class="nav-link" data-toggle="pill" v-on:click="selectReturnsTab(0)">{{tabs[0]}}</a></li>
                    <li class="nav-item" v-if="returns.has_payment" ><a id="1" class="nav-link" data-toggle="pill" v-on:click="selectReturnsTab(1)">{{tabs[1]}}</a></li>
                </ul>
            </div>
            <div class="tab-content">
              {{ this.$slots.default }}
            </div>
        </div>

    </div>
</template>


<script>
import Vue from 'vue';
import MenuAccess from '../internal/returns/access.vue';
import { mapActions, mapGetters } from 'vuex';
import CommsLogs from '@common-components/comms_logs.vue'
import '@/scss/forms/form.scss';
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'
export default {
  name: 'returns-renderer-form',
  props: {
      level:{
            type: String,
            required: true,
            validator:function(val) {
                let options = ['internal','external'];
                return options.indexOf(val) != -1 ? true: false;
            }
        },
  },
  components: {
    CommsLogs,
    MenuAccess,
  },
  filters: {
    formatDate: function(data){
            return data ? moment(data).format('DD/MM/YYYY HH:mm:ss'): '';
    }
  },
  data: function() {
    return {
        tabs: {
          0: 'Return',
          1: 'Confirmation',
        },
        returns_tab_id: 0,

        assignTo: false,
        loading: [],
        isLoading: false,

        // Filters
        logs_url: helpers.add_endpoint_json(api_endpoints.returns,this.$route.params.return_id+'/action_log'),
        comms_url: helpers.add_endpoint_json(api_endpoints.returns,this.$route.params.return_id+'/comms_log'),
        comms_add_url: helpers.add_endpoint_json(api_endpoints.returns,this.$route.params.return_id+'/add_comms_log'),
    }
  },
  props:{
    form_width: {
        type: String,
        default: 'col-md-9'
    },
  },
  computed: {
    ...mapGetters([
      'returns',
      'returns_tabs',
      'selected_returns_tab_id',
      'species_list',
      'is_external',
      'current_user',
    ]),
    is_submitted: function() {
      return this.returns.lodgement_date != null ? true : false;
    },
    displayable_number: function() {
      // if (this.is_external && this.returns.lodgement_date != null) {
      //     return '\u00A0'
      // }
      return 'Return: ' + this.returns.lodgement_number
    },
    displayable_tabs: function() {
      return true
      if (this.is_external && this.returns.lodgement_date != null) {
          return false
      }
      return true
    }
  },
  methods: {
    ...mapActions([
      'setReturnsTabId',
      'setReturnsSpecies',
      'setReturnsExternal',
      'setReturns',
      'loadCurrentUser',
    ]),
    selectReturnsTab: function(id) {
        this.returns_tab_id = id;
        this.setReturnsTabId({tab_id: id});
    },
    canAssignToOfficer: function(){
      if(!this.userHasRole('licensing_officer')) {
        return false;
      }
      return this.returns && this.returns.processing_status.id == 'with_curator'
    },
    userIsAssignedOfficer: function(){
      return this.current_user.id == this.returns.assigned_to;
    },
  },
  created: function() {
    this.loadCurrentUser({ url: `/api/my_user_details` });
    if (this.returns.format != 'sheet') { // Return Running Sheet checks 'internal' for read-only.
      var headers = this.returns.table[0]['headers']
      for(let i = 0; i<headers.length; i++) {
        headers[i]['readonly'] = !this.is_external || !['Draft', 'Due', 'Overdue'].includes(this.returns.processing_status)
      }
      this.setReturns(this.returns);
    }
    this.setReturnsSpecies({species: this.returns.sheet_species_list});
  },
}
</script>
