<template lang="html">
  <div id="schema-purpose">

    <div class="row">
        <div class="col-sm-12">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <h3 class="panel-title">Schema Purpose Section
                        <a :href="'#'+pPurposeBody" data-toggle="collapse"  data-parent="#userInfo" expanded="true" :aria-controls="pPurposeBody">
                            <span class="glyphicon glyphicon-chevron-up pull-right "></span>
                        </a>
                    </h3>
                </div>
                <div class="panel-body collapse in" :id="pPurposeBody">

                    <div class="row">
                        <div class="col-md-12">
                            <button class="btn btn-primary pull-right" @click.prevent="addTableEntry()" name="add_purpose">New Entry</button>
                        </div>
                    </div>
                    <div class="row"><br/></div> 
                    <div class="row">
                        <div class="col-md-12">
                            <div class="form-group">

                                <datatable ref="schema_purpose_table"
                                    :id="schema_purpose_id" 
                                    :dtOptions="dtOptionsSchemaPurpose"
                                    :dtHeaders="dtHeadersSchemaPurpose" 
                                />

                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <modal transition="modal fade" @ok="ok()" title="Schema Purpose Section" large>
        <div class="container-fluid">
            <div id="error" v-if="missing_fields.length > 0" style="margin: 10px; padding: 5px; color: red; border:1px solid red;">
                <b>Please answer the following mandatory question(s):</b>
                <ul>
                    <li v-for="error in missing_fields">
                        {{ error.label }}
                    </li>
                </ul>
            </div>
            <div>
                <form class="form-horizontal" name="schema_purpose">

                    <div class="row">
                        <div class="col-md-3">
                            <label class="control-label pull-left" >Section Label</label>
                        </div>
                        <div class="col-md-9">
                            <input type='text' v-model='section_label' >
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-3">
                            <label class="control-label pull-left" >Licence Purpose</label>
                        </div>
                        <div class="col-md-9">
                            <textarea class="form-control" name="licence_purpose" v-model="licence_purpose"></textarea>
                        </div>
                    </div>
                </form>
            </div>
        </div>
        <div slot="footer">
            <button type="button" class="btn btn-primary" @click="ok">Save</button>
        </div>
    </modal>

  </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue'
import modal from '@vue-utils/bootstrap-modal.vue'
import alert from '@vue-utils/alert.vue'
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'
export default {
    name:'schema-purpose',
    components: {
        modal,
        alert,
        datatable,
    },
    props:{
    },
    data:function () {
        let vm = this;
        vm.schema_purpose_url = helpers.add_endpoint_join(api_endpoints.schema_purpose_paginated, 'schema_purpose_datatable_list/?format=datatables');
        return {
            schema_purpose_id: 'schema-purpose-datatable-'+vm._uid,
            pPurposeBody: 'pPurposeBody' + vm._uid,
            isModalOpen:false,
            missing_fields: [],
            // masterlist table
            dtHeadersSchemaPurpose: ["ID", "Section Label", "Licence Purpose", "Action"],
            dtOptionsSchemaPurpose:{
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                serverSide: true,
                autowidth: false,
                processing: true,
                ajax: {
                    "url": vm.schema_purpose_url, 
                },
                columnDefs: [
                    { visible: false, targets: [ 0 ] } 
                ],
                columns: [
                    { 
                        data: "id",
                        width: "10%",
                    },
                    { 
                        data: "section_label",
                        width: "60%",
                    },
                    { 
                        data: "licence_purpose",
                        width: "20%",
                    },
                    { 
                        data: "id",
                        width: "10%",
                        mRender:function (data,type,full) {
                            var column = `<a class="edit-row" data-rowid=\"__ROWID__\">Edit</a><br/>`;
                            column += `<a class="delete-row" data-rowid=\"__ROWID__\">Delete</a><br/>`;
                            return column.replace(/__ROWID__/g, full.id);
                        }
                    },
                ],
                rowId: function(_data) {
                    return _data.id
                },
            },
            section_label: '',
            licence_purpose: '',

        }

    },
    computed: {
    },
    methods: {
        close: function() {
            const self = this;

            if (!self.errors) {

                self.isModalOpen = false;
            }
        },
        ok: function() {
            const self = this;
        },
        cancel: function() {
            const self = this;
            self.isModalOpen = false;
        },
        addTableEntry: function() {
            self.section_label = '';
            self.licence_purpose = '';
            this.isModalOpen = true;
        },
        addEventListeners: function(){
            const self = this;

            self.$refs.schema_purpose_table.vmDataTable.on('click','.edit-row', function(e) {
                e.preventDefault();
                self.$refs.schema_purpose_table.row_of_data = self.$refs.schema_purpose_table.vmDataTable.row('#'+$(this).attr('data-rowid'));

                self.section_label = self.$refs.schema_purpose_table.row_of_data.data().section_label;
                self.licence_purpose = self.$refs.schema_purpose_table.row_of_data.data().licence_purpose;
                self.isModalOpen = true;
            });
        }

    },
    mounted: function() {
        this.form = document.forms.schema_purpose;
        this.$nextTick(() => {
            this.addEventListeners();
        });
    }
}
</script>
