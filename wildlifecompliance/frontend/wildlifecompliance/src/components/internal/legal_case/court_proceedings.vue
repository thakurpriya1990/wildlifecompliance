<template lang="html">
    <div class="col-md-9">
        <div class="row">
            <FormSection :formCollapse="false" label="Court Dates">
                <div class="col-sm-12 form-group"><div class="row">

                </div></div>
            </FormSection>

            <FormSection :formCollapse="false" label="Court Journal">
                <div class="col-sm-12 form-group"><div class="row">

                </div></div>
            </FormSection>

            <FormSection :formCollapse="false" label="Court Outcome">
                <div class="col-sm-12 form-group"><div class="row">
                    <textarea :readonly="readonlyForm" class="form-control location_address_field" v-model="legal_case.court_proceedings.court_outcome_details" />
                </div></div>
            </FormSection>
        </div>
    </div>
</template>
<script>
import Vue from "vue";
import FormSection from "@/components/forms/section_toggle.vue";
import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";
import utils from "@/components/external/utils";
import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
import moment from 'moment';
import 'bootstrap/dist/css/bootstrap.css';
import 'eonasdan-bootstrap-datetimepicker';
import _ from 'lodash';


export default {
    name: "ViewBriefOfEvidence",
    data: function() {
        return {
            //boeRoiTicked: [],
            //boeRoiOptions: [],
            //boeOtherStatementsOptions: [],
            uuid: 0,
      };
    },
    components: {
      FormSection,
    },
    computed: {
      ...mapGetters('legalCaseStore', {
        legal_case: "legal_case",
      }),

      csrf_token: function() {
        return helpers.getCookie("csrftoken");
      },
      readonlyForm: function() {
          let readonly = true
          if (this.legal_case && this.legal_case.id) {
              readonly = !this.legal_case.can_user_action;
          }
          return readonly
      },
      canUserAction: function() {
          let return_val = false
          if (this.legal_case && this.legal_case.id) {
              return_val = this.legal_case.can_user_action;
          }
          return return_val
      },
    },
    filters: {
      formatDate: function(data) {
        return data ? moment(data).format("DD/MM/YYYY HH:mm:ss") : "";
      }
    },
    methods: {
      ...mapActions('legalCaseStore', {
        loadLegalCase: 'loadLegalCase',
        saveLegalCase: 'saveLegalCase',
        setLegalCase: 'setLegalCase',
      }),
    },
    created: async function() {
      },
    mounted: function() {
        this.$nextTick(() => {
            $('.vue-treeselect__control').css("display", "none");
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
