<template>
<div class="container" id="schema-manager">
    <div class="col-md-12">

    <SchemaTabs :tabs="tabs" :initialTab="initialTab">

    </SchemaTabs>

    </div>
</div>
</template>
<script>
import SchemaTabs from '@/components/forms/tab.vue'

export default {
    name: 'schema-manager',
    components: {
        SchemaTabs,
    },
    data() {
        return {
            initialTab: 'masterlist',
            tabs: [

            ],
        }
    },
}
</script>
