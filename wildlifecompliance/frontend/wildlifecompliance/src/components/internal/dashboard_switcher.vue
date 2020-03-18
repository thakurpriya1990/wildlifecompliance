<template>
    <div v-if="showComplianceManagement" class="container" id="internalDash">
        <CallEmailDashTable />
    </div>
    <div v-else-if="showWildlifeLicensing" class="container" id="internalDash">
        <ApplicationDashTable level="internal" :url="applications_url"/>
        <AssessmentDashTable />
    </div>
</template>
<script>
import ApplicationDashTable from '@common-components/applications_dashboard.vue'
import AssessmentDashTable from '@common-components/assessments_dashboard.vue'
import CallEmailDashTable from './call_email/call_email_dashboard.vue'
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'
export default {
    name: 'InternalDashboard',
    data() {
        let vm = this;
        return {
            applications_url: helpers.add_endpoint_join(api_endpoints.applications_paginated,'internal_datatable_list/?format=datatables'),
            preferredDashboard: null,
        }
    },
    watch: {},
    components: {
        ApplicationDashTable,
        AssessmentDashTable,
        CallEmailDashTable,
    },
    computed: {
        showComplianceManagement: function() {
            let systemPreference = false;
            if (this.preferredDashboard === 'compliance_management') {
                systemPreference = true;
            }
            return systemPreference;
        },
        showWildlifeLicensing: function() {
            let systemPreference = false;
            if (this.preferredDashboard === 'wildlife_licensing') {
                systemPreference = true;
            }
            return systemPreference;
        },

    },
    methods: {},
    mounted: function () {
    },
    created: async function() {
        this.preferredDashboard = await helpers.getPreferredDashboard();
        console.log(this.preferredDashboard);
    },

}
</script>
