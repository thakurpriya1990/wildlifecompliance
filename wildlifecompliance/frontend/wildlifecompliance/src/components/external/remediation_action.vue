<template lang="html">
    <div class="container">
        <div class="row">
            <div class="col-md-3">
                <h3>Remediation Action: ---</h3>
            </div>
        </div>
        <div>
            <div class="col-md-9" id="main-column">
                <div class="row">
                    <div class="container-fluid">

                    </div>
                </div>
            </div>
        </div>

    </div>
</template>

<script>
import Vue from "vue";
//import FormSection from "@/components/forms/section_toggle.vue";
//import datatable from '@vue-utils/datatable.vue'
//import utils from "@/components/external/utils";
//import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";
//import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
//import CommsLogs from "@common-components/comms_logs.vue";
//import filefield from '@/components/common/compliance_file.vue';
//import 'bootstrap/dist/css/bootstrap.css';

export default {
    name: 'RemediationAction',
    data() {

        return {
        }
    },
    components: {
        //FormSection,
        //CommsLogs,
        //datatable,
        //filefield,
    },
    created: async function() {

    },
    mounted: function() {

    },
    computed: {
        ...mapGetters('remediationActionStore', {
            remediation_action: "remediation_action",
        }),
    },
    methods: {
        ...mapActions('remediationActionStore', {
            loadRemediationAction: 'loadRemediationAction',
        }),
    }
}
</script>

<style>

</style>
