<template lang="html">
  <div id="schema-group">

    <div class="row">
        <div class="col-sm-12">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <h3 class="panel-title">Schema Section Groups
                        <a :href="'#'+pGroupBody" data-toggle="collapse"  data-parent="#userInfo" expanded="true" :aria-controls="pGroupBody">
                            <span class="glyphicon glyphicon-chevron-up pull-right "></span>
                        </a>
                    </h3>
                </div>
                <div class="panel-body collapse in" :id="pGroupBody">

                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label for="">Licence Purpose</label>
                                <select class="form-control" v-model="filterTablePurpose" >
                                    <option value="All">All</option>
                                    <option v-for="(p, pid) in schemaPurposes" :value="p.value" v-bind:key="`group_${pid}`">{{p.label}}</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <button class="btn btn-primary pull-right" @click.prevent="addTableEntry()" name="add_group">New Group</button>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label for="">Section</label>
                                <select class="form-control" v-model="filterTableSection" >
                                    <option value="All">All</option>
                                    <option v-for="(s, sid) in schemaSections" :value="s.value" v-bind:key="`section_${sid}`">{{s.label}}</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="row"><br/></div> 
                    <div class="row">
                        <div class="col-md-12">
                            <div class="form-group">

                                <datatable ref="schema_group_table"
                                    :id="schema_group_id" 
                                    :dtOptions="dtOptionsSchemaGroup"
                                    :dtHeaders="dtHeadersSchemaGroup" 
                                />

                            </div>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    </div>

    <modal transition="modal fade" @ok="ok()" title="Schema Section Group" large>
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
                <form class="form-horizontal" name="schema_group">

                    <div class="row">
                        <div class="col-md-3">
                            <label class="control-label pull-left" >Licence Purpose</label>
                        </div>
                        <div class="col-md-6">
                            <select class="form-control" ref="select_purpose" name="select-purpose" v-model="filterGroupSection" >
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
                            <label class="control-label pull-left" >Section</label>
                        </div>
                        <div class="col-md-6">
                            <select class="form-control" ref="select_section" name="select-section" v-model="sectionGroup.section" >
                                <option value="All">Select...</option>
                                <option v-for="(s, sid) in schemaSections" :value="s.value" v-bind:key="`section_${sid}`">{{s.label}}</option>
                            </select>                            
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">&nbsp; </div>
                    </div>
                    <div class="row">
                        <div class="col-md-3">
                            <label class="control-label pull-left" >Group Label</label>
                        </div>
                        <div class="col-md-6">
                            <input type="text" class="form-control" v-model="sectionGroup.group_label"/>
                        </div>
                    </div>
                    <div class="row"><div class="col-md-12" >&nbsp;</div></div>
                    <div class="row">
                        <div class="col-md-6">
                            <input type="checkbox" :value="true" v-model="getCheckedRepeatable('isRepeatable').isChecked" >&nbsp;&nbsp;&nbsp;<label>isRepeatable</label></input>
                        </div>
                    </div>
                </form>
            </div>
        </div>
        <div slot="footer">
            <button type="button" class="btn btn-primary" @click="saveGroup">Save</button>
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
    name:'schema-group',
    components: {
        modal,
        alert,
        datatable,
    },
    props:{
    },
    watch:{
        filterTablePurpose: function() {
            this.$refs.schema_group_table.vmDataTable.draw();
        },
        filterTableSection: function() {
            this.$refs.schema_group_table.vmDataTable.draw();
        },
        filterGroupSection: function() {
            this.$http.get(helpers.add_endpoint_json(api_endpoints.schema_group,'1/get_group_sections'),{
                params: { licence_purpose_id: this.filterGroupSection },
            }).then((res)=>{
                this.schemaSections = res.body.group_sections;
            },err=>{

            });
        },
    },
    data:function () {
        let vm = this;
        vm.schema_group_url = helpers.add_endpoint_join(api_endpoints.schema_group_paginated, 'schema_group_datatable_list/?format=datatables');
        return {
            schema_group_id: 'schema-group-datatable-'+vm._uid,
            pGroupBody: 'pGroupBody' + vm._uid,
            isModalOpen:false,
            missing_fields: [],
            filterTablePurpose: 'All',
            filterTableSection: 'All',
            filterGroupSection: 'All',
            dtHeadersSchemaGroup: ["ID", "Licence Purpose", "Section Label", "Group Label", "Action"],
            dtOptionsSchemaGroup:{
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                searchDelay: 1000,
                responsive: true,
                serverSide: true,
                autowidth: false,
                processing: true,
                ajax: {
                    "url": vm.schema_group_url,
                    "dataSrc": 'data',
                    "data": function (d) {
                        d.licence_purpose_id = vm.filterTablePurpose;
                        d.section_id = vm.filterTableSection;
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
                            return data.name;
                        }
                    },
                    { 
                        data: "section",
                        width: "20%",
                        searchable: false,
                        mRender:function (data,type,full) {
                            return data.section_label;
                        }
                    },
                    { 
                        data: "group_label",
                        width: "60%",
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
                            vm.$refs.schema_group_table.vmDataTable.search( this.value ).draw();
                        }
                    }, 0)));
                }
            },
            licence_purpose: '',
            schemaPurposes: [],
            schemaSections: [],
            sectionGroup: {
                id: '',
                group_name: '',
                group_label: '',
                section: 'All',
                repeatable: false,
            },
            checkedRepeatable: [{
                id: null,
                isChecked: false,
            }],
        }

    },
    computed: {
    },
    methods: {
        getCheckedRepeatable: function(anID, set_checked=false){
            let checked = this.checkedRepeatable.find(r => {return r.id==anID})
            if (!checked) {
                checked = {
                    id: anID,
                    isChecked: set_checked,
                }
                if (['isRepeatable',].includes(anID)){
                    this.checkedRepeatable.push(checked)
                }
            }
            return checked;
        },
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
        saveGroup: async function() {
            const self = this;
            const data = self.sectionGroup;

            data.repeatable = false;
            if (self.checkedRepeatable.length>0){
                self.checkedRepeatable.filter( r => {
                    if (r.isChecked) {
                        data.repeatable = true;
                    }
                    return
                })
            }

            if (data.id === '') {

                await self.$http.post(api_endpoints.schema_group, JSON.stringify(data),{
                    emulateJSON:true

                }).then((response) => {

                    self.$refs.schema_group_table.vmDataTable.ajax.reload();
                    self.close();

                }, (error) => {
                    swal(
                        'Save Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    )
                });

            } else {

                await self.$http.post(helpers.add_endpoint_json(api_endpoints.schema_group,data.id+'/save_group'),JSON.stringify(data),{
                        emulateJSON:true,

                }).then((response)=>{

                    self.$refs.schema_group_table.vmDataTable.ajax.reload();
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
            this.licence_purpose = '';

            this.sectionGroup.id = '';
            this.sectionGroup.group_name = '';
            this.sectionGroup.group_label = '';
            this.sectionGroup.section = 'All';
            this.sectionGroup.repeatable = false;
            this.checkedRepeatable = [];

            this.isModalOpen = true;
        },
        initEventListeners: function(){
            const self = this;

            self.$refs.schema_group_table.vmDataTable.on('click','.edit-row', function(e) {
                e.preventDefault();
                self.$refs.schema_group_table.row_of_data = self.$refs.schema_group_table.vmDataTable.row('#'+$(this).attr('data-rowid'));

                self.sectionGroup.id = self.$refs.schema_group_table.row_of_data.data().id;
                self.sectionGroup.section = self.$refs.schema_group_table.row_of_data.data().section.id;
                self.sectionGroup.group_label = self.$refs.schema_group_table.row_of_data.data().group_label;
                self.filterGroupSection = self.$refs.schema_group_table.row_of_data.data().licence_purpose.id;

                self.sectionGroup.repeatable = self.$refs.schema_group_table.row_of_data.data().repeatable
                self.checkedRepeatable = []
                self.getCheckedRepeatable('isRepeatable', self.sectionGroup.repeatable);

                self.isModalOpen = true;
            });

            self.$refs.schema_group_table.vmDataTable.on('click','.delete-row', function(e) {
                e.preventDefault();
                self.$refs.schema_group_table.row_of_data = self.$refs.schema_group_table.vmDataTable.row('#'+$(this).attr('data-rowid'));
                self.sectionGroup.id = self.$refs.schema_group_table.row_of_data.data().id;

                swal({
                    title: "Delete Section Group",
                    text: "Are you sure you want to delete?",
                    type: "question",
                    showCancelButton: true,
                    confirmButtonText: 'Accept'

                }).then(async (result) => {

                    if (result.value) {

                        await self.$http.delete(helpers.add_endpoint_json(api_endpoints.schema_group,(self.sectionGroup.id+'/delete_group')))
    
                        .then((response) => {

                            self.$refs.schema_group_table.vmDataTable.ajax.reload();

                        }, (error) => {

                        });
    
                    }

                },(error) => {

                });                
            });
        },
        initSelects: async function() {

            await this.$http.get(helpers.add_endpoint_join(api_endpoints.schema_group,'1/get_group_selects')).then(res=>{

                    this.schemaPurposes = res.body.all_purpose
                    this.schemaSections = res.body.all_section

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
        this.form = document.forms.schema_group;
        this.$nextTick(() => {
            this.initEventListeners();
            this.initSelects();
        });
    }
}
</script>
