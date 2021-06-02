<template lang="html">
  <div id="schema-question">

    <div class="row">
        <div class="col-sm-12">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <h3 class="panel-title">Schema Section Question
                        <a :href="'#'+pQuestionBody" data-toggle="collapse"  data-parent="#userInfo" expanded="true" :aria-controls="pQuestionBody">
                            <span class="glyphicon glyphicon-chevron-up pull-right "></span>
                        </a>
                    </h3>
                </div>
                <div class="panel-body collapse in" :id="pQuestionBody">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label for="">Licence Purpose</label>
                                <select class="form-control" v-model="filterLicencePurpose" >
                                    <option value="All">All</option>
                                    <option v-for="(p, pid) in schemaPurposes" :value="p.value" v-bind:key="`purpose_${pid}`">{{p.label}}</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <button class="btn btn-primary pull-right" @click.prevent="addTableEntry()" name="add_purpose">New Question</button>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label for="">Section</label>
                                <select class="form-control" v-model="filterSection" >
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

                                <datatable ref="schema_question_table"
                                    :id="schema_question_id" 
                                    :dtOptions="dtOptionsSchemaQuestion"
                                    :dtHeaders="dtHeadersSchemaQuestion" 
                                />

                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <modal transition="modal fade" @ok="ok()" title="Schema Section Question" large>
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
                <form class="form-horizontal" name="schema_question">

                    <div class="row">
                        <div class="col-md-3">
                            <label class="control-label pull-left" >Licence Purpose</label>
                        </div>
                        <div class="col-md-6">
                            <select class="form-control" ref="select_purpose" name="select-purpose" v-model="filterQuestionPurpose" >
                                <option value="All">All</option>
                                <option v-for="(p, pid) in schemaPurposes" :value="p.value" v-bind:key="`purpose_${pid}`">{{p.label}}</option>
                            </select>                            
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-3">
                            <label class="control-label pull-left" >Section</label>
                        </div>
                        <div class="col-md-6">
                            <select class="form-control" ref="select_section" name="select-section" v-model="filterQuestionSection" >
                                <option value="All">All</option>
                                <option v-for="(s, sid) in schemaSections" :value="s.value" v-bind:key="`section_${sid}`">{{s.label}}</option>
                            </select>                            
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-3">
                            <label class="control-label pull-left" >Question</label>
                        </div>
                        <div class="col-md-9">
                            <select class="form-control" ref="select_question" name="select-question" v-model="sectionQuestion.question_id" >
                                <option v-for="m in masterlist" :value="m.id" >{{m.question}}</option>
                            </select>                            
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">&nbsp; </div>
                    </div>
                    <div class="row" v-if="showOptions">

                        <SchemaOption :addedOptions="addedOptions" />

                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <input ref="check_repeatable" name="check-repeatable" type="checkbox" :value="true">&nbsp;&nbsp;&nbsp;<label>isRepeatable</label></input>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <input ref="check_required" name="check-required" type="checkbox" :value="true">&nbsp;&nbsp;&nbsp;<label>isRequired</label></input>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-3">
                            <label class="control-label pull-left" >Parent Question</label>
                        </div>
                        <div class="col-md-9">
                            <select class="form-control" ref="select_parent" name="select-parent" v-model="sectionQuestion.parent_id" >
                                <option v-for="m in parentList" :value="m.id" >{{m.question}}</option>
                            </select>                            
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-3">
                            <label class="control-label pull-left" >Parent Answer</label>
                        </div>
                        <div class="col-md-3">
                            <select class="form-control" ref="select_answer" name="select-answer" v-model="sectionQuestion.answer_id" >
                                <option v-for="o in answerList" :value="m.id" >{{o.label}}</option>
                            </select>                            
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-3">
                            <label class="control-label pull-left" >Group</label>
                        </div>
                        <div class="col-md-6">
                            <select class="form-control" ref="select_group" name="select-group" v-model="sectionQuestion.group_id" >
                                <option v-for="g in groupList" :value="m.id" >{{g.label}}</option>
                            </select>                            
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-3">
                            <label class="control-label pull-left" >Order</label>
                        </div>
                        <div class="col-md-3">
                            <input type='text' />
                        </div>
                    </div>
                </form>
            </div>
        </div>
        <div slot="footer">
            <button type="button" class="btn btn-primary" @click="saveQuestion">Save</button>
        </div>
    </modal>

  </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue'
import modal from '@vue-utils/bootstrap-modal.vue'
import alert from '@vue-utils/alert.vue'
import SchemaOption from './schema_add_option.vue'
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'

var select2 = require('select2');
require("select2/dist/css/select2.min.css");
require("select2-bootstrap-theme/dist/select2-bootstrap.min.css");

export default {
    name:'schema-question',
    components: {
        modal,
        alert,
        datatable,
        SchemaOption,
    },
    props:{
    },
    data:function () {
        let vm = this;
        vm.schema_question_url = helpers.add_endpoint_join(api_endpoints.schema_question_paginated, 'schema_question_datatable_list/?format=datatables');

        return {
            schema_question_id: 'schema-question-datatable-'+vm._uid,
            pOptionsBody: 'pOptionsBody' + vm._uid,
            pQuestionBody: 'pQuestionBody' + vm._uid,
            isModalOpen:false,
            missing_fields: [],
            filterLicencePurpose: 'All',
            filterParentQuestion: 'All',
            filterSection: 'All',
            filterQuestionSection: 'All',
            filterQuestionPurpose: 'All',
            dtHeadersSchemaQuestion: ["ID", "QuestionID", "SectionID", "QuestionOP", "Licence Purpose", "Section", "Question", "Action"],
            dtOptionsSchemaQuestion:{
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                serverSide: true,
                autowidth: false,
                processing: true,
                searchDelay: 1000,
                ajax: {
                    "url": vm.schema_question_url,
                    "dataSrc": 'data',
                    "data": function (d) {
                        d.licence_purpose_id = vm.filterLicencePurpose;
                        d.section_id = vm.filterSection;
                    }
                },
                columnDefs: [
                    { visible: false, targets: [ 0, 1, 2, 3 ] } 
                ],
                columns: [
                    { 
                        data: "id",
                        searchable: false,
                    },
                    { 
                        data: "question_id",
                        searchable: false,
                    },
                    { 
                        data: "section",
                        searchable: false,
                    },
                    { 
                        data: "conditions",
                        searchable: false,
                    },
                    { 
                        data: "licence_purpose",
                        searchable: true,
                    },
                    { 
                        data: "section",
                        searchable: false,
                        mRender:function (data,type,full) {
                            return data.section_label;
                        }
                    },
                    { 
                        data: "question",
                        searchable: false,
                        width: "40%",
                    },
                    { 
                        data: "id",
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
                            vm.$refs.schema_question_table.vmDataTable.search( this.value ).draw();
                        }
                    }, 0)));
                }
            },
            sectionQuestion: {
                id: '',
                section: '',
                question_id: 0,
                question: '',
                group_id: 0,
                order_id: 0,
                conditions: null,
                purpose_id: 0,
                parent_id: 0,
                answer_id: 0,
            },
            // condition: {
            //     label: '',
            //     value: '',
            // },
            // option: {
            //     label: '',
            //     value: '',
            // },
            masterlist: null,
            checked: false,
            selectedType: '',
            showOptions: false,
            optionList: [],
            groupList: [],
            addedOptions: [],
            addedOption: {
                label: '',
                value: '',
                conditions: '',
            },
            defaultOptions: null,
            schemaPurposes: [],
            schemaSections: [],
            parentList: [],
            answerList: [],
        }

    },
    watch:{
        filterLicencePurpose: function() {
            this.$refs.schema_question_table.vmDataTable.draw();
        },
        filterSection: function(){
            this.$refs.schema_question_table.vmDataTable.draw();
        },
        filterQuestionPurpose: function(){
            const data = {licence_purpose_id: this.filterQuestionPurpose};
            this.$http.get(helpers.add_endpoint_json(api_endpoints.schema_question,'1/get_question_sections'),JSON.stringify(data),{
                        emulateJSON:true,
            }).then((res)=>{

            },err=>{

            });
        },
        filterQuestionSection: function(){
            const data = {section_id: this.filterQuestionSection};
            this.$http.get(helpers.add_endpoint_json(api_endpoints.schema_question,'1/get_question_parents'),JSON.stringify(data),{
                        emulateJSON:true,
            }).then((res)=>{

            },err=>{

            });
        },

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
                $(this.$refs.select_question).val(null).trigger('change');
                $('.has-error').removeClass('has-error');
                self.addedOptions = [];
                self.showOptions = false;
                self.isModalOpen = false;
            }
        },
        setShowOptions: function(selected_id) {
            let show = this.masterlist.filter( m => {
                return m.id == selected_id && ['checkbox'].includes(m.answer_type)
            })[0]

            this.showOptions = show ? true : false
        },
        saveQuestion: async function() {
            const self = this;
            const data = self.sectionQuestion

            if (data.id === '') {

                await self.$http.post(api_endpoints.schema_question, JSON.stringify(data),{
                    emulateJSON:true

                }).then((response) => {

                    self.$refs.schema_question_table.vmDataTable.ajax.reload();
                    self.close();

                }, (error) => {

                    swal(
                        'Save Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    )
                });

            } else {

                await self.$http.post(helpers.add_endpoint_json(api_endpoints.schema_question,data.id+'/save_question'),JSON.stringify(data),{
                        emulateJSON:true,

                    }).then((response)=>{

                        self.$refs.schema_question_table.vmDataTable.ajax.reload();
                        self.close();

                    },(error)=>{
                        'Save Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    });

            }

        },
        addTableEntry: function() {
            this.sectionQuestion.id = '';
            this.sectionQuestion.section = '';
            this.sectionQuestion.question = '';
            this.sectionQuestion.question_id = null;
            // this.sectionQuestion.question_options = null;

            let newOption = Object.assign(this.addedOption)
            newOption.conditions = this.defaultOptions;
            this.addedOptions.push(newOption);
            this.isModalOpen = true;
        },
        initEventListeners: function(){
            const self = this;

            self.$refs.schema_question_table.vmDataTable.on('click','.edit-row', function(e) {
                e.preventDefault();
                self.$refs.schema_question_table.row_of_data = self.$refs.schema_question_table.vmDataTable.row('#'+$(this).attr('data-rowid'));

                self.sectionQuestion.id = self.$refs.schema_question_table.row_of_data.data().id;
                self.sectionQuestion.section = self.$refs.schema_question_table.row_of_data.data().section;
                self.filterQuestionSection = self.$refs.schema_question_table.row_of_data.data().section.id;
                self.filterQuestionPurpose = self.$refs.schema_question_table.row_of_data.data().section.licence_purpose;
                self.sectionQuestion.question_id = self.$refs.schema_question_table.row_of_data.data().question_id;
                // self.sectionQuestion.question_options = self.$refs.schema_question_table.row_of_data.data().question_options;
                self.addedOption.conditions = self.$refs.schema_question_table.row_of_data.data().conditions
                self.addedOptions.push(self.addedOption)

                $(self.$refs.select_question).val(self.sectionQuestion.question_id).trigger('change');
                self.setShowOptions(self.sectionQuestion.question_id)
                self.isModalOpen = true;
            });

            self.$refs.schema_question_table.vmDataTable.on('click','.delete-row', function(e) {
                e.preventDefault();
                self.$refs.schema_question_table.row_of_data = self.$refs.schema_question_table.vmDataTable.row('#'+$(this).attr('data-rowid'));
                self.question.id = self.$refs.schema_question_table.row_of_data.data().id;

                swal({
                    title: "Delete Section Question",
                    text: "Are you sure you want to delete?",
                    type: "question",
                    showCancelButton: true,
                    confirmButtonText: 'Accept'

                }).then(async (result) => {

                    if (result.value) {

                        await self.$http.delete(helpers.add_endpoint_json(api_endpoints.schema_question,(self.question.id+'/delete_question')))
    
                        .then((response) => {

                            self.$refs.schema_question_table.vmDataTable.ajax.reload();

                        }, (error) => {

                        });
    
                    }

                },(error) => {

                });                
            });

        },
        initQuestionSelector: function () {
                const self = this;
                $(self.$refs.select_question).select2({
                    "theme": "bootstrap",
                    allowClear: true,
                    minimumInputLength: 2,
                    placeholder:"Select Question..."
                }).
                on("select2:selecting",function (e) {
                    let selected = $(e.currentTarget);
                }).
                on("select2:select",function (e) {
                    let selected = $(e.currentTarget);
                    self.sectionQuestion.question_id=selected.val()
                    self.setShowOptions(selected.val())
                }).
                on("select2:unselect",function (e) {
                    let selected = $(e.currentTarget);
                    self.sectionQuestion.question_id=selected.val()
                });
        },
        initParentSelector: function () {
                const self = this;
                $(self.$refs.select_parent).select2({
                    "theme": "bootstrap",
                    allowClear: true,
                    minimumInputLength: 2,
                    placeholder:"Select Parent Question..."
                }).
                on("select2:selecting",function (e) {
                    let selected = $(e.currentTarget);
                }).
                on("select2:select",function (e) {
                    let selected = $(e.currentTarget);
                }).
                on("select2:unselect",function (e) {
                    let selected = $(e.currentTarget);
                });
        },
        initAnswerSelector: function () {
                const self = this;
                $(self.$refs.select_answer).select2({
                    "theme": "bootstrap",
                    allowClear: true,
                    minimumInputLength: 2,
                    placeholder:"Select Parent Answer..."
                }).
                on("select2:selecting",function (e) {
                    let selected = $(e.currentTarget);
                }).
                on("select2:select",function (e) {
                    let selected = $(e.currentTarget);
                }).
                on("select2:unselect",function (e) {
                    let selected = $(e.currentTarget);
                });
        },
        initGroupSelector: function () {
                const self = this;
                $(self.$refs.select_group).select2({
                    "theme": "bootstrap",
                    allowClear: true,
                    minimumInputLength: 2,
                    placeholder:"Select Section Group..."
                }).
                on("select2:selecting",function (e) {
                    let selected = $(e.currentTarget);
                }).
                on("select2:select",function (e) {
                    let selected = $(e.currentTarget);
                }).
                on("select2:unselect",function (e) {
                    let selected = $(e.currentTarget);
                });
        },
        initSelects: async function() {

            await this.$http.get(helpers.add_endpoint_join(api_endpoints.schema_question,'1/get_question_selects')).then(res=>{

                    this.masterlist = res.body.all_masterlist
                    this.schemaPurposes = res.body.all_purpose
                    this.defaultOptions = res.body.question_options
                    this.schemaSections = res.body.all_section

            },err=>{

                swal(
                    'Get Application Selects Error',
                    helpers.apiVueResourceError(err),
                    'error'
                )
            });
            this.initQuestionSelector();
            this.initParentSelector();
            this.initAnswerSelector();
            this.initGroupSelector();
        },
    },
    mounted: function() {
        this.form = document.forms.schema_question;
        this.$nextTick(() => {
            this.initEventListeners();
            this.initSelects();
        });
    }
}
</script>
