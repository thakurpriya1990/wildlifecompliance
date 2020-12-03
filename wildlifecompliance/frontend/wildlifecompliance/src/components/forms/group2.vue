<template lang="html">
    <div class="top-buffer bottom-buffer">

        <!-- <label :id="id" class="inline">{{label}}</label> -->
        <template v-if="help_text">
            <HelpText :help_text="help_text" /> 
        </template>
        <template v-if="help_text_url">
            <HelpTextUrl :help_text_url="help_text_url" /> 
        </template>

        <div class="repeatable-group" v-for="(group, groupIdx) in repeatableGroups" 
            :id="`repeatable_group_${component.name}_${groupIdx}`"
            v-bind:key="`repeatable_group_${component.name}_${groupIdx}`">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <label :id="`${id}_${groupIdx}`" class="inline">{{label}} {{add_1(groupIdx)}}</label>
                    <a class="collapse-link-top pull-right" @click.prevent="toggleGroupVisibility(group)">
                        <span v-if="isExpanded(group)" class="glyphicon glyphicon-chevron-down"></span>
                        <span v-else class="glyphicon glyphicon-chevron-up"></span>
                    </a>
                </div>

                <div class="panel-body">
                    <!-- DEBUGGING
                    <p> name: {{name}} </p>
                    <p> value: {{value}} </p>
                    <p> component: {{component}} </p>
                    <p> children: {{component.children}} </p>
                    <p> {{groupIdx}} group: {{group}} </p>
                    <p> {{groupIdx}} value: {{value}} </p>
                    <p> Expanded: {{ !isExpanded(group) }} </p>
                    -->

                    <div :class="{'collapse':true, 'in':!isExpanded(group)}" style="margin-top:10px;" >

                        <div v-for="(subcomponent, index) in components[group].children"
                            v-bind:key="`repeatable_group_subcomponent_${subcomponent.name}_${index}`">

                            <renderer-block
                                :component="subcomponent"
                                :json_data="value"
                                v-bind:key="`repeatable_group_subcomponent_contents_${subcomponent.name}_${index}`"
                            />

                            <div>
                                <button v-if="num_groups() > 1 && index == component.children.length-1 && !readonly" type="button" class="btn btn-danger"
                                    @click.prevent="removeGroup(group)">Delete {{label}}</button>
                            </div>
                        </div>

                    </div>
                </div>
            </div>
        </div>

        <div class="row" v-if="component.isRepeatable && !readonly">
            <button type="button" class="btn btn-primary add-new-button"
                @click.prevent="addNewGroup">Add {{label}}</button>
        </div>

    </div>
</template>

<script>
import HelpText from './help_text.vue';
import HelpTextUrl from './help_text_url.vue';
import { mapGetters, mapActions } from 'vuex';

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
        HelpText,
        HelpTextUrl,
    },
    data(){
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
        add_1: function(tableId) {
            return tableId + 1;
        },
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
            console.log('toggle: ' + JSON.stringify(this.expanded));

            return this.expanded[tableId];
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
            delete this.components[tableId]
            //console.log("Remove: " + JSON.stringify(this.components))
            //console.log("*************************************************************")
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

        updateComponent: function(json_obj, fn, key='name') {
            /* search a nested JSON string for key, and recursively update the value using function fn 
               NOTE: had to use ES6 arrow function style, because the normal recursion function looped infinitely inside Vue instance (because 'this' instance is always the original instance).

                Usage: 
                    -- the below will search all k,v pairs in JSON object and append '-ridx0' (repeatable index 0) to all values with key='name'
                    var ridx = 0;
                    vm.components[group] = vm.updateComponent(vm.component, v => v + '-ridx' + ridx)
            */
            return Object.fromEntries(Object
                .entries(json_obj)
                .map(([k, v]) => [k,
                    Array.isArray(v)                                       // if
                        ? Array.from(v, v => this.updateComponent(v, fn))
                    : v && typeof v === 'object'                           // elif
                        ? this.updateComponent(v, fn)
                    : k===key                                              // elif
                        ? fn(v)
                    : v                                                    // else
                ])
            );
        },

        __updateComponent: function(obj, fn) {
            /* search a nested JSON string for key, and recursively update the value using function fn 

               PROBLEM: DOES NOT work for internal lists!
            */
            //console.log("updateComponent 1: " + JSON.stringify(obj))
            return Object.fromEntries(Object
                .entries(obj)
                .map(([k, v]) => [k, v && typeof v === 'object' ? this.updateComponent(v, fn) : (k==='name' ? fn(v) : v)])
            );
        },

        __updateComponent2: function(obj, append_str, key='name') {
            /* search a nested JSON string for key, and append 'append_str' to the end 
                -ridx --> repeater index

                PROBLEM: LOOPS INFINITELY inside a Vue instance
                Usage:
                    vm.components[group] = vm.updateComponent2(vm.component, ridx, 'name')
            */

            let vm = this;
            //Object.keys(obj).forEach(function (k) {
            Object.keys(obj).forEach(k => {
                if (obj[k] && typeof obj[k] === 'object') {
                    return vm.updateComponent2(obj[k], append_str, 'name')
                }
                if (k === key) {
                    obj[k] = obj[k] + '-ridx' + append_str;
                }
            });

            //return obj
        },
        num_groups: function() {
            return Object.keys(this.components).length
        },

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

            this.existingGroups.forEach(function (group, index) {
                var ridx = group.split('_').slice(-1)[0];
                vm.components[group] = vm.updateComponent(vm.component, v => v + '-ridx' + ridx)
            });

            //console.log("repeatableGroups: " + JSON.stringify(this.components))
            //console.log("*************************************************************")
            return this.existingGroups;
        },
        value: function() {
            return this.field_data;
        },
    }
}

export default Group2;
</script>

<style lang="css">
    .collapse-link-top,.collapse-link-bottom{
        cursor:pointer;
    }
</style>
