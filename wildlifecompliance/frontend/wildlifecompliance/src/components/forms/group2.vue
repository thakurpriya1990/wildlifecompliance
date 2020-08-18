<template lang="html">
    <div class="top-buffer bottom-buffer">

        <!--
        <div v-for="(n,idx) in num_groups()" class="panel panel-default">
        <div v-for="(n,idx) in 1" class="panel panel-default">
        -->
        <div class="repeatable-group" v-for="(group, groupIdx) in repeatableGroups">
            <div class="panel-body">
                <!--
                <p> name: {{name}} </p>
                <p> value: {{value}} </p>
                <p> component: {{component}} </p>
                <p> children: {{component.children}} </p>
                -->
                <div class="row header-row">
                    <div v-for="(header, index) in component.children"
                        v-bind:key="`repeatable_group_${component.name}_${index}`">

                        <!-- <p> header: {{header}} </p> -->
                        <span class="header-contents">
                            <renderer-block
                            :component="header"
                            :json_data="value"
                            :instance="group"
                            v-bind:key="`repeatable_group_contents_${component.name}_${index}`"
                            />
                        </span>
                    </div>
                </div>
            </div>
        </div>

        <div class="row" v-if="!readonly">
            <input type="button" value="Add Group" class="btn btn-primary add-new-button"
                @click.prevent="addNewGroup">
        </div>

    </div>
</template>

<script>
import CommentBlock from './comment_block.vue';
import HelpText from './help_text.vue';
import HelpTextUrl from './help_text_url.vue';
import { mapGetters, mapActions } from 'vuex';
import '@/scss/forms/expander_table.scss';

const Group2 = {
    props:{
        name: String,
        label: String,
        id: String,
        isRequired: String,
        help_text: String,
        help_text_url: String,
        component: {
            type: Object | null,
            required: true
        },
        field_data: {
            type: Object | null,
            required: true
        },
        readonly:Boolean,
    },
    components: {
        CommentBlock,
        HelpText,
        HelpTextUrl
    },
    data(){
        return {
            expanded: {},
        };
    },
    methods: {
        ...mapActions([
            'removeFormInstance',
            'setFormValue',
            'refreshApplicationFees',
        ]),
        isExpanded: function(tableId) {
            return this.expanded[tableId];
        },
        toggleGroupVisibility: function(tableId) {
            if(this.expanded[tableId]) {
                this.$delete(this.expanded, tableId);
            }
            else {
                this.$set(this.expanded, tableId, true);
            }
        },
        removeGroup: function(tableId) {
            if(this.expanded[tableId]) {
                this.$delete(this.expanded, tableId);
            }
            this.removeFormInstance(
                this.getInstanceName(tableId)
            );
            this.updateVisibleGroups(
                this.existingGroups.filter(table => table != tableId)
            );
            this.refreshApplicationFees();
        },
        addNewGroup: function(params={}) {
            let { tableId } = params;
            if(!tableId) {
                tableId = this.getTableId(this.lastTableId+1);
            }
            this.existingGroups.push(tableId);
            this.updateVisibleGroups(
                this.existingGroups
            );
            this.refreshApplicationFees();
        },
        updateVisibleGroups: function(tableList) {
            this.setFormValue({
                key: this.component.name,
                value: {
                    "value": tableList,
                }
            });
        },
        getTableId: function(tableIdx) {
            return `${this.id}_table_${tableIdx}`;
        },
        getInstanceName: function(tableId) {
            return `__instance-${tableId}`
        },
        removeLabel: function(header) {
            let newHeader = {...header};
            delete newHeader['label'];
            return newHeader;
        },

        num_groups: function() {
            var default_max_repeatable = 3;
            //if (this.component.isRepeatable && this.component.type === 'group') {
            if (this.component.isRepeatable) {
                return (this.component.maxRepeatable==null ? default_max_repeatable : this.component.maxRepeatable);
            }
            return 1;
        },
    },

    computed:{
        ...mapGetters([
            'canViewComments',
            'canViewDeficiencies',
            'canEditDeficiencies',
            'getFormValue',
        ]),
        lastTableId: function() {
            if(!this.existingGroups.length) {
                return 0;
            }
            let lastId = 0;
            this.existingGroups.map(tableId => tableId[tableId.length-1] > lastId && (lastId = tableId[tableId.length-1]));
            return parseInt(lastId, 10);
        },
        existingGroups: function() {
            return this.getFormValue(this.component.name) || [];
        },
        repeatableGroups: function() {
            if(!this.existingGroups.length) {
                this.addNewGroup();
            }
            return this.existingGroups;
        },
        value: function() {
            console.log('value: ' + JSON.stringify(this.field_data));
            return this.field_data;
        },
    }
}

export default Group2;
</script>
