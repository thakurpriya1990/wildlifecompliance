<template>
<div class="container" id="internalDash">
    <ApplicationDashTable level="internal" :url="applications_url"/>
    <AssessmentDashTable />
</div>
</template>
<script>
import ApplicationDashTable from '@common-components/applications_dashboard.vue'
import AssessmentDashTable from '@common-components/assessments_dashboard.vue'
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
        }
    
    },
    watch: {},
    components: {
        ApplicationDashTable,
        AssessmentDashTable,
    },
    computed: {
    },
    methods: {},
    mounted: function () {
    }
}
</script>
