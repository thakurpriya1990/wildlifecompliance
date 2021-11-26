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
                        <div class="col-md-6">
                            <div class="form-group">
                                <label for="">Licence Purpose</label>
                                <select class="form-control" v-model="filterTablePurpose" >
                                    <option value="All">All</option>
                                    <option v-for="(p, pid) in schemaPurposes" :value="p.value" v-bind:key="`purpose_${pid}`">{{p.label}}</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <button class="btn btn-primary pull-right" @click.prevent="addTableEntry()" name="add_purpose">New Section</button>
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
                            <label class="control-label pull-left" >Licence Purpose</label>
                        </div>
                        <div class="col-md-6">
                            <select class="form-control" ref="select_purpose" name="select-purpose" v-model="sectionPurpose.licence_purpose" >
                                <option value="All">Select...</option>
                                <option v-for="(p, pid) in schemaPurposes" :value="p.value" v-bind:key="`purpose_${pid}`">{{p.label}}</option>
                            </select>                            
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">&nbsp; </div>
                    </div>
                    <div class="row">
                        <div class="col-md-3">
                            <label class="control-label pull-left" >Section Label</label>
                        </div>
                        <div class="col-md-6">
                            <input type='text' class="form-control" v-model='sectionPurpose.section_label' >
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">&nbsp; </div>
                    </div>
                    <div class="row">
                        <div class="col-md-3">
                            <label class="control-label pull-left" >Section Index</label>
                        </div>
                        <div class="col-md-3">
                            <input type='text' class="form-control" v-model='sectionPurpose.index' >
                        </div>
                    </div>
                </form>
            </div>
        </div>
        <div slot="footer">
            <button type="button" class="btn btn-primary" @click="savePurpose()">Save</button>
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
    watch:{
        filterTablePurpose: function() {
            this.$refs.schema_purpose_table.vmDataTable.draw();
        },
    },
    data:function () {
        let vm = this;
        vm.schema_purpose_url = helpers.add_endpoint_join(api_endpoints.schema_purpose_paginated, 'schema_purpose_datatable_list/?format=datatables');
        return {
            schema_purpose_id: 'schema-purpose-datatable-'+vm._uid,
            pPurposeBody: 'pPurposeBody' + vm._uid,
            isModalOpen:false,
            missing_fields: [],
            filterTablePurpose: 'All',
            filterPurposeSection: 'All',
            // masterlist table
            dtHeadersSchemaPurpose: ["ID", "Licence Purpose", "Section Label", "Index", "Action"],
            dtOptionsSchemaPurpose:{
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                searchDelay: 1000,
                responsive: true,
                serverSide: true,
                autowidth: false,
                processing: true,
                ajax: {
                    "url": vm.schema_purpose_url, 
                    "dataSrc": 'data',
                    "data": function (d) {
                        d.licence_purpose_id = vm.filterTablePurpose;
                    }
                },
                columnDefs: [
                    { visible: false, targets: [ 0 ] } 
                ],
                columns: [
                    { 
                        data: "id",
                        width: "10%",
                        searchable: false,
                    },
                    { 
                        data: "licence_purpose",
                        width: "20%",
                        searchable: false,
                        mRender:function (data,type,full) {
                            return data.name
                        }
                    },
                    { 
                        data: "section_label",
                        width: "50%",
                        searchable: false,
                    },
                    { 
                        data: "index",
                        width: "10%",
                        searchable: false,
                    },
                    { 
                        data: "id",
                        width: "10%",
                        searchable: false,
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
                initComplete: function () {
                    var $searchInput = $('div.dataTables_filter input');
                    $searchInput.unbind('keyup search input');
                    $searchInput.bind('keypress', (vm.delay(function(e) {
                        if (e.which == 13) {
                            vm.$refs.schema_purpose_table.vmDataTable.search( this.value ).draw();
                        }
                    }, 0)));
                }
            },
            section_label: '',
            licence_purpose: '',
            schemaPurposes: [],
            sectionPurpose: {
                id: '',
                section_name: '',
                section_label: '',
                index: '',
                licence_purpose: '',
            }
        }

    },
    computed: {
    },
    methods: {
        delay(callback, ms) {
            var timer = 0;
            return function () {
                var context = this, args = arguments;
                clearTimeout(timer);
                timer = setTimeout(function () {
                    callback.apply(context, args);
                }, ms || 0);
            };
        },
        close: function() {
            const self = this;

            if (!self.errors) {

                self.isModalOpen = false;
            }
        },
        savePurpose: async function() {
            const self = this;
            const data = self.sectionPurpose;

            if (data.id === '') {

                await self.$http.post(api_endpoints.schema_purpose, JSON.stringify(data),{
                    emulateJSON:true

                }).then((response) => {

                    self.$refs.schema_purpose_table.vmDataTable.ajax.reload();
                    self.close();

                }, (error) => {
                    swal(
                        'Save Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    )
                });

            } else {

                await self.$http.post(helpers.add_endpoint_json(api_endpoints.schema_purpose,data.id+'/save_purpose'),JSON.stringify(data),{
                        emulateJSON:true,

                }).then((response)=>{

                    self.$refs.schema_purpose_table.vmDataTable.ajax.reload();
                    self.close();

                },(error)=>{
                    swal(
                        'Save Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    )
                });

            }

        },
        cancel: function() {
            const self = this;
            self.isModalOpen = false;
        },
        addTableEntry: function() {
            this.sectionPurpose.id = '';
            this.sectionPurpose.section_label = '';
            this.sectionPurpose.index = '';
            this.sectionPurpose.licence_purpose = '';
            this.isModalOpen = true;
        },
        addEventListeners: function(){
            const self = this;

            self.$refs.schema_purpose_table.vmDataTable.on('click','.edit-row', function(e) {
                e.preventDefault();
                self.$refs.schema_purpose_table.row_of_data = self.$refs.schema_purpose_table.vmDataTable.row('#'+$(this).attr('data-rowid'));

                self.sectionPurpose.id = self.$refs.schema_purpose_table.row_of_data.data().id;
                self.sectionPurpose.section_label = self.$refs.schema_purpose_table.row_of_data.data().section_label;
                self.sectionPurpose.index = self.$refs.schema_purpose_table.row_of_data.data().index;
                self.sectionPurpose.licence_purpose = self.$refs.schema_purpose_table.row_of_data.data().licence_purpose.id;

                self.isModalOpen = true;
            });

            self.$refs.schema_purpose_table.vmDataTable.on('click','.delete-row', function(e) {
                e.preventDefault();
                self.$refs.schema_purpose_table.row_of_data = self.$refs.schema_purpose_table.vmDataTable.row('#'+$(this).attr('data-rowid'));
                self.sectionPurpose.id = self.$refs.schema_purpose_table.row_of_data.data().id;

                swal({
                    title: "Delete Purpose Section",
                    text: "Are you sure you want to delete?",
                    type: "question",
                    showCancelButton: true,
                    confirmButtonText: 'Accept'

                }).then(async (result) => {

                    if (result.value) {

                        await self.$http.delete(helpers.add_endpoint_json(api_endpoints.schema_purpose,(self.sectionPurpose.id+'/delete_purpose')))
    
                        .then((response) => {

                            self.$refs.schema_purpose_table.vmDataTable.ajax.reload();

                        }, (error) => {

                        });
    
                    }

                },(error) => {

                });                
            });
        },
        initSelects: async function() {

            await this.$http.get(helpers.add_endpoint_join(api_endpoints.schema_purpose,'1/get_purpose_selects')).then(res=>{

                    this.schemaPurposes = res.body.all_purpose

            },err=>{

                swal(
                    'Get Application Selects Error',
                    helpers.apiVueResourceError(err),
                    'error'
                )
            });
        },
    },
    mounted: function() {
        this.form = document.forms.schema_purpose;
        this.$nextTick(() => {
            this.addEventListeners();
            this.initSelects();
        });
    }
}
</script>
