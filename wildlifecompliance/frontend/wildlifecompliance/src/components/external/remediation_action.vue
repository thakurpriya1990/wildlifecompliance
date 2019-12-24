<template lang="html">
    <div class="container">
        <div class="row">
            <div class="col-md-3">
                <h3>Remediation Action: ---</h3>
            </div>
        </div>
        <div>
            <div class="col-md-3">
            </div>

            <div class="col-md-9" id="main-column">
                <div class="row">
                    <div class="container-fluid">
                        <ul class="nav nav-pills aho2">
                            <li class="nav-item active"><a data-toggle="tab" :href="'#'+reTab">Remediation Action</a></li>
                            <li class="nav-item"><a data-toggle="tab" :href="'#'+coTab">Conformation</a></li>
                        </ul>
                        <div class="tab-content">
                            <div :id="reTab" class="tab-pane fade in active">
                                <FormSection :formCollapse="false" label="Remediation Action" Index="1">
                                    <div class="form-group"><div class="row">
                                        <div class="col-sm-4">
                                            <label>Action Required</label>
                                        </div>
                                        <div class="col-sm-6">
                                            {{ remediation_action.action }}
                                        </div>
                                    </div></div>
                                    <div class="form-group"><div class="row">
                                        <div class="col-sm-4">
                                            <label>Due Date</label>
                                        </div>
                                        <div class="col-sm-6">
                                            {{ remediation_action.due_date }}
                                        </div>
                                    </div></div>
                                    <div class="form-group"><div class="row">
                                        <div class="col-sm-4">
                                            <label>Details of your compliance</label>
                                        </div>
                                        <div class="col-sm-6">
                                            <input :readonly="readonlyForm" class="form-control" v-model="sanction_outcome.identifier"/>
                                        </div>
                                    </div></div>
                                    <div class="form-group"><div class="row">
                                        <div class="col-sm-4">
                                            <label>Any photographic evidence</label>
                                        </div>
                                        <div class="col-sm-6" v-if="remediation_action">
                                            <filefield ref="remediation_action_file"
                                                       name="remediation_action-file"
                                                       :documentActionUrl="remediation_action.remediationActionDocumentUrl"
                                                       @update-parent="remediationActionDocumentUploaded"
                                                       :isRepeatable="true"
                                                       :readonly="readonlyForm" />
                                        </div>
                                    </div></div>
                                </FormSection>
                            </div>

                            <div :id="coTab" class="tab-pane fade in">
                                <FormSection :formCollapse="false" label="Conformation" Index="2">

                                </FormSection>
                            </div>

                        </div>
                    </div>
                </div>
            </div>
        </div>

    </div>
</template>

<script>
import Vue from "vue";
import FormSection from "@/components/forms/section_toggle.vue";
//import datatable from '@vue-utils/datatable.vue'
//import utils from "@/components/external/utils";
import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";
import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
//import CommsLogs from "@common-components/comms_logs.vue";
import filefield from '@/components/common/compliance_file.vue';
import 'bootstrap/dist/css/bootstrap.css';

export default {
    name: 'RemediationAction',
    data() {

        return {
            reTab: 'reTab' + this._uid,
            coTab: 'coTab' + this._uid,
        }
    },
    components: {
        FormSection,
        //CommsLogs,
        //datatable,
        filefield,
    },
    created: async function() {
        if (this.$route.params.remediation_action_id) {
            await this.loadRemediationAction({ remediation_action_id: this.$route.params.remediation_action_id });
        }
    },
    mounted: function() {

    },
    computed: {
        ...mapGetters('remediationActionStore', {
            remediation_action: "remediation_action",
        }),
        readonlyForm: function(){
            return false;
        }
    },
    methods: {
        ...mapActions('remediationActionStore', {
            loadRemediationAction: 'loadRemediationAction',
        }),
        remediationActionDocumentUploaded: function() {
            console.log('remediationActionDocumentUploaded');
        },
    }
}
</script>

<style>

</style>
