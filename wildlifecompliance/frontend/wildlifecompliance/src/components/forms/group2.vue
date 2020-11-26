<template lang="html">
    <div class="top-buffer bottom-buffer">

        <!--
        <div v-for="(n,idx) in num_groups()" class="panel panel-default">
        <div v-for="(n,idx) in 1" class="panel panel-default">
        -->
        <div class="repeatable-group" v-for="(group, groupIdx) in repeatableGroups" 
            :id="`repeatable_group_${component.name}_${groupIdx}`"
            v-bind:key="`repeatable_group_${component.name}_${groupIdx}`">
            <div class="panel panel-default">
                <div class="panel-body">
                    <!--
                    <p> name: {{name}} </p>
                    <p> value: {{value}} </p>
                    <p> component: {{component}} </p>
                    <p> children: {{component.children}} </p>
                    -->

                    <p> {{groupIdx}} group: {{group}} </p>
                    <p> {{groupIdx}} value: {{value}} </p>
                    <!--
                    <div class="row header-row">
                            :subcomponent="updateComponent(subcomponent_item, 'name', groupIdx)"
                            :set="subcomponent = updateComponent(subcomponent_item, v => v + ' ****')"
                    -->
                    <div>
                        <div v-for="(subcomponent, index) in components[group].children"
                            v-bind:key="`repeatable_group_subcomponent_${subcomponent.name}_${index}`">
                        <!--
                        <div v-for="(subcomponent, index) in component.children">
                        -->

                            <p> {{index}} subcomponent: {{subcomponent.name}} </p>
                            <!--
                            <p> {{group}} component: {{components.length}} </p>

                            <span v-if="!index" :class="`expand-icon ${isExpanded(group) ? 'collapse' : ''}`"
                                v-on:click="toggleGroupVisibility(group)"></span>

                                    :component="updateComponent(subcomponent, 'name', groupIdx)"
                                    :instance="group"
                            -->

                            <span class="header-contents">
                                <renderer-block
                                    :component="subcomponent"
                                    :json_data="value"
                                    v-bind:key="`repeatable_group_subcomponent_contents_${subcomponent.name}_${index}`"
                                />
                            </span>

                            <div>
                                <p> {{ group }} </p>
                                <button v-if="groupIdx && index == component.children.length-1 && !readonly" type="button" class="btn btn-danger"
                                    @click.prevent="removeGroup(group)">Delete group</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row" v-if="component.isRepeatable && !readonly">
            <input type="button" value="Add Group" class="btn btn-primary add-new-button"
                @click.prevent="addNewGroup">
        </div>

    </div>
</template>

<script>
import CommentBlock from './comment_block.vue';
import HelpText from './help_text.vue';
import HelpTextUrl from './help_text_url.vue';
import ExpanderTable from '@/components/forms/expander_table.vue'
import { mapGetters, mapActions } from 'vuex';
import '@/scss/forms/expander_table.scss';
import {helpers,api_endpoints} from "@/utils/hooks.js"

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
        HelpTextUrl,
        ExpanderTable,
    },
    data(){
        //console.log("DATA: " + JSON.stringify(this.component)) 
        return {
            expanded: {},
            components: {},
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
            //console.log("remove 1" + this.components[tableId].length)
            delete this.components[tableId]
            console.log("Remove: " + JSON.stringify(this.components))
            console.log("*************************************************************")
            this.refreshApplicationFees();
        },
        addNewGroup: function(params={}) {
            let { tableId } = params;
            if(!tableId) {
                //console.log("1 tableId: " + JSON.stringify(tableId)) 
                tableId = this.getTableId(this.lastTableId+1);
                //console.log("2 tableId: " + JSON.stringify(tableId)) 
            }
            this.existingGroups.push(tableId);
            this.updateVisibleGroups(
                this.existingGroups
            );
            this.refreshApplicationFees();
            //console.log("component(s) : " + JSON.stringify(this.components))
        },
        updateVisibleGroups: function(tableList) {
            //console.log("tableList: " + tableList)
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

        updateComponent: function(obj, fn) {
            /* search a nested JSON string for key, and recursively update the value using function fn */
            //console.log("updateComponent 1: " + JSON.stringify(obj))
            return Object.fromEntries(Object
                .entries(obj)
                .map(([k, v]) => [k, v && typeof v === 'object' ? this.updateComponent(v, fn) : (k==='name' ? fn(v) : v)])
            );
        },

        _updateComponent: function(obj, key, append_str, k='') {
            /* search a nested JSON string for key, and append 'append_str' to the end 
                -ridx --> repeater index
            */

            let vm = this;
            Object.keys(obj).forEach(function (k) {
                if (obj[k] && typeof obj[k] === 'object') {
                    return vm.updateComponent(obj[k], key, append_str, k)
                }
                if (k === key) {
                    obj[k] = obj[k] + '-ridx' + append_str;
                }
            });

            return obj
        },


        /*
        clone: function(id) {
             var $row = $('#' + id);

             var $clone = $row.clone(); //Making the clone                      
             counter++; // +1 counter

             //Change the id of the cloned elements, append the counter onto the ID 
             $clone.find('[id]').each(function () { this.id += counter });
        }
        */

        /*
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
        */
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
            let vm = this;
            if(!this.existingGroups.length) {
                this.addNewGroup();
            }

            //console.log("repeatGroups 3: " + this.existingGroups)
            this.existingGroups.forEach(function (group, index) {
                var ridx = group.split('_').slice(-1)[0];
                vm.components[group] = vm.updateComponent(vm.component, v => v + '-ridx' + ridx)
                //console.log(group, index);
            });

            console.log("repeatableGroups: " + JSON.stringify(this.components))
            console.log("*************************************************************")
            return this.existingGroups;
        },
        value: function() {
            //console.log('value: ' + JSON.stringify(this.field_data));
            return this.field_data;
        },
    }
}

export default Group2;
</script>
