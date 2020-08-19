<template lang="html">
    <div>
        <div class="form-group">
            <label :id="id">{{ label }}</label>

            <template v-if="help_text">
                <HelpText :help_text="help_text" />
            </template>

            <template v-if="help_text_url">
                <HelpText :help_text_url="help_text_url" />
            </template>
     
            <template v-if="readonly">
                <select v-if="!isMultiple" disabled ref="selectB" :id="selectid" :name="name" class="form-control" :data-conditions="cons" style="width:100%">
                    <option value="">Select...</option>
                    <option v-for="(op, idx1) in species"  :value="op.value" @change="handleChange" :selected="op.value == value" v-bind:key="`value_${op.value}_${idx1}`">{{ op.label }}</option>
                </select>
                <select v-else disabled ref="selectB" :id="selectid" class="form-control" multiple style="width:100%">
                    <option value="">Select...</option>
                    <option v-for="(op, idx1) in species"  :value="op.value" :selected="multipleSelection(op.value)" v-bind:key="`value_${op.value}_${idx1}`">{{ op.label }}</option>
                </select>
                <template v-if="isMultiple">
                    <input v-for="(v, idx2) in value" input type="hidden" :name="name" :value="v" :required="isRequired" v-bind:key="`value_${v}_${idx2}`"/>
                </template>
                <template v-else>
                    <input type="hidden" :name="name" :value="value" :required="isRequired"/>
                </template>
            </template>
            <template v-else>
                <select v-if="!isMultiple" ref="selectB" :id="selectid" :name="name" class="form-control" :data-conditions="cons" style="width:100%" :required="isRequired">
                    <option value="">Select...</option>
                    <option v-for="(op, idx1) in species"  :value="op.value" @change="handleChange" :selected="op.value == value" v-bind:key="`value_${op.value}_${idx1}`">{{ op.label }}</option>
                </select>
                <select v-else ref="selectB" :id="selectid" :name="name" class="form-control" multiple style="width:100%" :required="isRequired">
                    <option value="">Select...</option>
                    <option v-for="(op, idx1) in species" :value="op.value" :selected="multipleSelection(op.value)" v-bind:key="`value_${op.value}_${idx1}`">{{ op.label }}</option>
                </select>
            </template>
        </div>

    </div>
</template>

<script>
import Vue from 'vue';
import { mapActions, mapGetters } from 'vuex';
import HelpText from './help_text.vue';
import HelpTextUrl from './help_text_url.vue';

var select2 = require('select2');
require("select2/dist/css/select2.min.css");
require("select2-bootstrap-theme/dist/select2-bootstrap.min.css");

export default {
    props: {
        "label": {
            type: String
        },
        "name": {
            type: String
        },
        "field_data": {
            type: Object,
            required: true
        },
        "options": {
            type: Array,
            required: true,
            default:function () {
                return [];
            }
        },
        "readonly": {
            type: Boolean,
            default: false
        },
        "id": {
            type: String,
        },
        "isRequired": {
            type: Boolean,
            default: false
        },
        "help_text": {
            type: String,
        },
        "help_text_url": {
            type: String,
        },
        "isMultiple":{
            default:function () {
                return false;
            }
        },
        "handleChange":null,
    },
    data:function () {
        let vm =this;
        return{
            selected: (this.isMultiple) ? [] : "",
            selectid: "select"+vm._uid,
            multipleSelected: [],
        }
    },
    computed:{
        ...mapGetters([
            'application_id',
            'renderer_form_data',
        ]),
        cons: function () {
            return JSON.stringify(this.field_data);
        },
        value: function() {
            return this.field_data.value;
        },
        species: function() {
            var species = this.options
            if (this.field_data.component_attribute) {
                species = this.field_data.component_attribute
            } else {
                this.field_data.component_attribute = species
            }
            return species
        }
    },
    components: { HelpText, HelpTextUrl, },
    methods:{
        multipleSelection2: function(val){
            if (Array.isArray(this.options)){
                if (this.species.find(v => v == val)){
                    return true;
                }
            }else{
                if (this.species == val){return true;}
            }
            return false;
        },
        multipleSelection: function(val){
            if (Array.isArray(this.field_data.value)){
                let selected = '0'
                for (let i=0; i < this.field_data.value.length; i++){
                    if (this.field_data.value[i] == val){
                        selected = this.field_data.value[i];
                        break;
                    }
                }
                if (this.species.find(v => v.value == selected && v.value === val)){
                    return true;
                }
            }else{
                if (this.species.find(v => v.value === this.field_data.value && v.value === val)){
                    return true;
                }
            }
            return false;
        },
        init:function () {
            let vm =this;
            vm.multipleSelected = vm.field_data.value;
            setTimeout(function (e) {
                   $('#'+vm.selectid).select2({
                       "theme": "bootstrap",
                       allowClear: true,
                       placeholder:"Select..."
                   }).
                   on("select2:select",function (e) {
                       var selected = $(e.currentTarget);
                       vm.handleChange(selected[0])
                       e.preventDefault();
                        if( vm.isMultiple){
                            vm.field_data.value = vm.multipleSelected = selected.val();
                        }
                   }).
                   on("select2:unselect",function (e) {
                        var selected = $(e.currentTarget);
                        vm.handleChange(selected[0])
                        e.preventDefault();
                        if( vm.isMultiple){
                            vm.field_data.value = vm.multipleSelected = selected.val();
                        }
                   });
                   if (vm.value) {
                       vm.handleChange(vm.$refs.selectB);
                   }
               },100);
        }
    },
    updated:function (){
        this.$nextTick(() => {
            this.field_data.value = this.multipleSelected[0] ? this.multipleSelected : this.field_data.value;
        });
    },
    mounted:function () {
        this.init();
    }
}
</script>

<style lang="css">
.select2-container {
    width: 100% !important;
}

input {
    box-shadow:none;
}
</style>

