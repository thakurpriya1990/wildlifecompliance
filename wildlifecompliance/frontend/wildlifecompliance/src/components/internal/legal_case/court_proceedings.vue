<template lang="html">
    <div class="col-md-9">
        <div class="row">
            <FormSection :formCollapse="false" label="Court Dates">
                <div class="col-sm-12 form-group"><div class="row">

                </div></div>
            </FormSection>

            <FormSection :formCollapse="false" label="Court Journal">
                <div class="col-sm-12 form-group"><div class="row">
                    <div class="row action-button">
                        <div v-if="canUserAction">
                              <a @click="createNewCourtProceedingsEntry()" class="btn btn-primary pull-right new-row-button" >
                                  New Row
                              </a>
                        </div>
                    </div>
                    <datatable 
                        ref="court_proceedings_table" 
                        id="court-proceedings-table" 
                        :dtOptions="dtOptionsCourtProceedings" 
                        :dtHeaders="dtHeadersCourtProceedings"
                        parentStyle=" "
                    />
                </div></div>
            </FormSection>

            <FormSection :formCollapse="false" label="Court Outcome">
                <div class="col-sm-12 form-group"><div class="row">
                    <textarea v-if="hasCourtProceedings" :readonly="readonlyForm" class="form-control location_address_field" v-model="legal_case.court_proceedings.court_outcome_details" />
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
import datatable from '@vue-utils/datatable.vue'
import 'bootstrap/dist/css/bootstrap.css';
import 'eonasdan-bootstrap-datetimepicker';
import _ from 'lodash';


export default {
    name: "ViewCourtProceedings",
    data: function() {
        return {
            uuid: 0,
            dtHeadersCourtProceedings: [
                "id",
                "Number",
                "Date",
                "Time",
                "User",
                "Description",
                "deleted",
                "Action",
            ],
            dtOptionsCourtProceedings: {
                order: [
                    [0, 'desc'],
                    ],
                columns: [
                    {
                        visible: false,
                        mRender: function(data, type, row) {
                            return row.id;
                        }
                    },
                    {
                        mRender: function(data, type, row) {
                            let retStr = row.number;
                            return retStr;
                        }
                    },
                    {
                        mRender: function(data, type, row) {
                            let retStr = row.date_mod;
                            return retStr;
                        }
                    },
                    {
                        mRender: function(data, type, row) {
                            let retStr = row.time_mod;
                            return retStr;
                        }
                    },
                    {
                        mRender: function(data, type, row) {
                            let retStr = row.user_full_name;
                            return retStr;
                        }
                    },
                    {
                        mRender: function(data, type, row) {
                            let retStr = '';
                            retStr = `<div id=${row.number} style="min-height:20px" contenteditable="true">${row.description}</div>`
                            if (row.deleted) {
                                retStr = '<strike>' + 
                                    `<div id=${row.number} style="min-height:20px" contenteditable="false">${row.description}</div>`
                                    '</strike>';
                            }
                            return retStr;

                        }
                    },
                    {
                        visible: false,
                        mRender: function(data, type, row) {
                            return row.deleted;
                        }
                    },
                    {
                        mRender: function(data, type, row) {
                            let retStr = '';
                            let rowIdDel = row.number.replace('-', 'D')
                            let rowIdHist = row.number.replace('-', 'H')
                            let rowIdReinstate = row.number.replace('-', 'R')
                            if (row.action) {
                                retStr += `<a id=${rowIdHist} class="row_history" href="#">History</a><br/><br/>`
                                if (!row.deleted) {
                                    retStr += `<a id=${rowIdDel} class="row_delete" href="#">Delete</a><br/>`
                                } else {
                                    retStr += `<a id=${rowIdReinstate} class="row_reinstate" href="#">Reinstate</a><br/>`
                                }

                            }
                            return retStr;

                        }
                    },
                ]
            }
        };
    },
    components: {
        datatable,
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
        hasCourtProceedings: function() {
            return this.legal_case.court_proceedings ? true : false;
        },
    },
    filters: {
        formatDate: function(data) {
            return data ? moment(data).format("DD/MM/YYYY HH:mm:ss") : "";
        }
    },
    methods: {
        ...mapActions('legalCaseStore', {
          //loadLegalCase: 'loadLegalCase',
          //saveLegalCase: 'saveLegalCase',
          //setLegalCase: 'setLegalCase',
        }),
        createNewCourtProceedingsEntry: function() {

        },
        constructCourtProceedingsTable: function(pk){
            if (this.hasCourtProceedings){
                console.log("constructCourtProceedingsTable")

                this.$refs.court_proceedings_table.vmDataTable.clear().draw();

                let actionColumn = !this.readonlyForm;
                console.log('hasCourtProceedings: ' + this.hasCourtProceedings);
                let entries = this.legal_case.court_proceedings.journal_entries;
                for(let i = 0;i < entries.length; i++){
                    if (!pk || entries[i].id === pk) {
                        this.$refs.court_proceedings_table.vmDataTable.row.add({ 
                            "id": entries[i].id,
                            "number": entries[i].number,
                            "date_mod": entries[i].date_mod,
                            "time_mod": entries[i].time_mod,
                            "user_full_name": entries[i].user_full_name,
                            "description": entries[i].description,
                            "deleted": entries[i].deleted,
                            "action": actionColumn,
                        }).draw();
                    }
                }
            }
            console.log("constructCourtProceedingsTable - end")
        },
    },
    created: async function() {
    },
    mounted: function() {
        this.$nextTick(() => {
            $('.vue-treeselect__control').css("display", "none");
            this.constructCourtProceedingsTable();
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
