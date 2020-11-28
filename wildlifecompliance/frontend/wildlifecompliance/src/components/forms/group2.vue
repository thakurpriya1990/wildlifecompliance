<template lang="html">
    <div class="top-buffer bottom-buffer">

        <label :id="id" class="inline">{{label}}</label>
        <!--<i data-toggle="tooltip" v-if="help_text" data-placement="right" class="fa fa-question-circle" :title="help_text"> &nbsp; </i>-->

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
                <div class="panel-body">
                    <!--
                    <p> name: {{name}} </p>
                    <p> value: {{value}} </p>
                    <p> component: {{component}} </p>
                    <p> children: {{component.children}} </p>
                    <p> {{groupIdx}} group: {{group}} </p>
                    <p> {{groupIdx}} value: {{value}} </p>
                    <div :class="{'row':true,'collapse':true, 'in':isExpanded}" style="margin-top:10px;" >
                    -->

                    <a class="collapse-link-top pull-right" @click.prevent="expand(group)"><span class="glyphicon glyphicon-chevron-down"></span></a>
                    <div class="children-anchor-point collapse in" style="padding-left: 0px"></div>
                    <a class="collapse-link-bottom pull-right"  @click.prevent="minimize(group)"><span class="glyphicon glyphicon-chevron-up"></span></a>

                    <div :class="{'collapse':true, 'in':isExpanded}" style="margin-top:10px;" >

                        <div v-for="(subcomponent, index) in components[group].children"
                            v-bind:key="`repeatable_group_subcomponent_${subcomponent.name}_${index}`">

                            <!--
                            <p> {{index}} subcomponent: {{subcomponent.name}} </p>
                            <span v-if="!index" :class="`expand-icon ${isExpanded(group) ? 'collapse' : ''}`"
                            v-on:click="toggleGroupVisibility(group)"></span>

                                :instance="group"
                            <p> components: {{components}} </p>
                            -->

                            <renderer-block
                                :component="subcomponent"
                                :json_data="value"
                                v-bind:key="`repeatable_group_subcomponent_contents_${subcomponent.name}_${index}`"
                            />

                            <div>
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
        /*
        expand: function(group) {
            this.isExpanded(group) = true;
        },
        minimize: function(group) {
            this.isExpanded(group) = false;
        }
        */
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
               NOTE: had to use ES6 arrow function style, because the normal recursion function looped infinately inside vue instance.

           Usage: 
                    -- the below will search all k,v pairs in JSON object and append '-ridx0' (repeatable index 0) to all values with key='name'
                    var ridx = 0;
            vm.components[group] = vm.updateComponent(vm.component, v => v + '-ridx' + ridx)
        */
            return Object.fromEntries(Object
                .entries(json_obj)
                .map(([k, v]) => [k,
                    Array.isArray(v)                        // if
                        ? Array.from(v, v => this.updateComponent(v, fn))
                    : v && typeof v === 'object'                // elif
                        ? this.updateComponent(v, fn)
                    : k===key                           // elif
                        ? fn(v)
                    : v                             // else
                ])
            );
        },

        __updateComponent: function(obj, fn) {
            /* search a nested JSON string for key, and recursively update the value using function fn */
            //console.log("updateComponent 1: " + JSON.stringify(obj))
            //return (f = identity, t = {}) =>
            let vm = this;
            //return (f, t) =>
            const traverse = (f = identity, t = {}) =>
        Array.isArray(t)
            ? Array.from(t, v => traverse(v, f))
        : Object(t) === t
            ? Object.fromEntries(Object
            .entries(t)
            .map(([ k, v ]) =>  [k, v && typeof v === 'object' ? traverse(v, f) : (k==='name' ? f(v) : v)])
              ) 
        : ''

             return traverse(x => x + '101', obj)
        },

        __updateComponent: function(obj, fn) {
            /* search a nested JSON string for key, and recursively update the value using function fn */
            //console.log("updateComponent 1: " + JSON.stringify(obj))
            return Object.fromEntries(Object
                .entries(obj)
                .map(([k, v]) => [k, v && typeof v === 'object' ? this.updateComponent(v, fn) : (k==='name' ? fn(v) : v)])
            );
        },

        __updateComponent2: function(obj, append_str, key='name') {
            /* search a nested JSON string for key, and append 'append_str' to the end 
                -ridx --> repeater index
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

//    created:{
//        traverse = (f = identity, t = {}) =>
//      Array.isArray(t)                         // 1
//          ? Array.from(t, v => this.traverse(f, v))
//      : Object(t) === t                        // 2
//          ? Object.fromEntries(Object
//          .entries(t)
//          .map(([ k, v ]) =>  [k, v && typeof v === 'object' ? this.traverse(f, v) : (k==='name' ? f(v) : v)])
//            )
//    },

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
                //vm.components[group] = vm.traverse(v => v + '-ridx' + ridx, vm.component)
                vm.components[group] = vm.updateComponent(vm.component, v => v + '-ridx' + ridx)
                //vm.components[group] = vm.updateComponent2(vm.component, ridx, 'name')
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
