<template id="application_conditions">

                <div :class="isLicensingOfficer ? 'col-md-12 conditions-table' : 'col-md-12'" > 
                    <div class="row">
                        <div class="panel panel-default">
                            <div class="panel-heading">
                                <h3 class="panel-title">Proposed Conditions
                                    <a class="panelClicker" :href="'#'+panelBody" data-toggle="collapse"  data-parent="#userInfo" expanded="false" :aria-controls="panelBody">
                                        <span class="glyphicon glyphicon-chevron-down pull-right "></span>
                                    </a>
                                </h3>
                            </div>
                            <div class="panel-body panel-collapse collapse in" :id="panelBody">
                                <form class="form-horizontal" action="index.html" method="post">
                                    <div class="col-sm-12">
                                        <button v-if="canAddConditions" @click.prevent="addCondition()" style="margin-bottom:10px;" class="btn btn-primary pull-right">Add Condition</button>
                                    </div>
                                    <datatable ref="conditions_datatable" :id="'conditions-datatable-'+_uid" :dtOptions="condition_options" :dtHeaders="condition_headers"/>
                                </form>
                            </div>
                        </div>
                    </div>
                    <ConditionDetail ref="condition_detail" :application_id="application.id" :conditions="conditions" :licence_activity_tab="selected_activity_tab_id"
                    :condition="viewedCondition" :purposes="purposes"/>
                </div>       

            
</template>
<script>
import {
    api_endpoints,
    helpers
}
from '@/utils/hooks';
import '@/scss/dashboards/application.scss';
import datatable from '@vue-utils/datatable.vue';
import ConditionDetail from './application_add_condition.vue';
import { mapActions, mapGetters } from 'vuex'
export default {
    name: 'InternalApplicationConditions',
    props: {
        activity: {
            type: Object | null,
            required: true
        }
    },
    data: function() {
        let vm = this;
        return {
            form: null,
            datepickerOptions:{
                format: 'DD/MM/YYYY',
                showClear:true,
                allowInputToggle:true
            },
            panelBody: "application-conditions-"+vm._uid,
            viewedCondition: {},
            conditions: [],
            purposes: [],
            condition_headers:["Condition","Purpose","Source","Due Date","Recurrence","Action","Order"],
            condition_options:{
                autoWidth: false,
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                ajax: {
                    "url": helpers.add_endpoint_join(api_endpoints.applications,this.$store.getters.application.id+'/conditions/?licence_activity='+this.$store.getters.selected_activity_tab_id),
                    "dataSrc": ''
                },
                order: [],
                columns: [
                    {
                        data: "condition",
                        mRender:function (data,type,full) {
                            return data ? data.substring(0, 80) : ''
                        },
                        orderable: false
                    },
                    {
                        data: "purpose_name",
                        orderable: false
                    },
                    {
                        data: "source_name",
                        orderable: false
                    },
                    {
                        data: "due_date",
                        mRender:function (data,type,full) {
                            return data != '' && data != null ? moment(data).format('DD/MM/YYYY'): '';
                        },
                        orderable: false
                    },
                    {
                        data: "recurrence",
                        mRender:function (data,type,full) {
                            if (full.recurrence){
                                switch(full.recurrence_pattern){
                                    case 1:
                                    case "weekly":
                                        return `Once per ${full.recurrence_schedule} week(s)`;
                                    case 2:
                                    case "monthly":
                                        return `Once per ${full.recurrence_schedule} month(s)`;
                                    case 3:
                                    case "yearly":
                                        return `Once per ${full.recurrence_schedule} year(s)`;
                                    default:
                                        return '';
                                }
                            }
                            return '';
                        },
                        orderable: false
                    },
                    {
                        data: "source_group",
                        mRender:function (data,type,full) {
                            let links = '';
                            if(full.source_group && vm.activity.processing_status.id !== 'with_officer_finalisation') {
                                links = `
                                    <a href='#' class="editCondition" data-id="${full.id}">Edit</a><br/>
                                    <a href='#' class="deleteCondition" data-id="${full.id}">Delete</a><br/>
                                `;
                            }
                            if(!full.source_group && vm.canEditConditions) {
                                links = `
                                    <a href='#' class="editCondition" data-id="${full.id}">Edit</a><br/>
                                    <a href='#' class="deleteCondition" data-id="${full.id}">Delete</a><br/>
                                `;
                            }
                            return links;
                        },
                        orderable: false
                    },
                    {
                        data: "id",
                        mRender:function (data,type,full) {
                            let links = '';
                            if(vm.canEditConditions) {
                                links +=  `<a class="dtMoveUp" data-id="${full.id}" href='#'><i class="fa fa-angle-up"></i></a><br/>`;
                                links +=  `<a class="dtMoveDown" data-id="${full.id}" href='#'><i class="fa fa-angle-down"></i></a><br/>`;
                            }
                            return links;
                        },
                        orderable: false
                    }
                ],
                processing: true,
                rowCallback: function ( row, data, index) {
                    if (data.return_type && !data.due_date) {
                        $('td', row).css('background-color', 'Red');
                        vm.setApplicationWorkflowState({bool: true})
                    }
                },
                drawCallback: function (settings) {
                    if(vm.$refs.conditions_datatable) {
                        $(vm.$refs.conditions_datatable.table).find('tr:last .dtMoveDown').remove();
                        $(vm.$refs.conditions_datatable.table).children('tbody').find('tr:first .dtMoveUp').remove();
                    }
                    // Remove previous binding before adding it
                    $('.dtMoveUp').unbind('click');
                    $('.dtMoveDown').unbind('click');
                    // Bind clicks to functions
                    $('.dtMoveUp').click(vm.moveUp);
                    $('.dtMoveDown').click(vm.moveDown);
                },
                preDrawCallback: function (settings) {
                    vm.setApplicationWorkflowState({bool: false})
                }
            }
        }
    },
    watch:{
    },
    components:{
        datatable,
        ConditionDetail
    },
    computed:{
        ...mapGetters([
            'application',
            'selected_activity_tab_id',
            'hasRole',
            'sendToAssessorActivities',
            'canEditAssessmentFor',
            'current_user',
            'canAssignOfficerFor',
            'application_workflow_state',
        ]),
        canAddConditions: function() {
            if(!this.selected_activity_tab_id || this.activity == null) {
                return false;
            }

            // check activity is not assigned to another officer.
            var selectedActivity = this.application.activities.find(activity => {
                return activity.licence_activity === this.selected_activity_tab_id;
            });
            if (selectedActivity.assigned_officer != null && selectedActivity.assigned_officer !== this.current_user.id) {
                return false;
            };

            let required_role = false;
            if (this.activity.processing_status.id === 'with_assessor') {
                let assessment = this.canEditAssessmentFor(this.selected_activity_tab_id)
                required_role = assessment && assessment.assessors.find(assessor => assessor.id === this.current_user.id) ? 'assessor' : false;

            } else if (this.activity.processing_status.id === 'with_officer') {
                required_role =  this.canAssignOfficerFor(this.selected_activity_tab_id) ? 'licensing_officer' : false;
            } else if (this.activity.processing_status.id === 'with_officer_conditions') {
                required_role =  this.canAssignOfficerFor(this.selected_activity_tab_id) ? 'licensing_officer' : false;
            }

            // switch(this.activity.processing_status.id) {
            //     case 'with_assessor':
            //         console.log('with_assessor')
            //         let assessment = this.canEditAssessmentFor(this.selected_activity_tab_id)
            //         required_role = assessment && assessment.assessors.find(assessor => assessor.id === this.current_user.id) ? 'assessor' : false;
            //     break;
            //     case 'with_officer_conditions':
            //         console.log('with_officer_condit')
            //         required_role =  this.canAssignOfficerFor(this.selected_activity_tab_id) ? 'licensing_officer' : false;
            //     break;
            // }
      
            return required_role && this.hasRole(required_role, this.selected_activity_tab_id);
        },
        canEditConditions: function() {
            if(!this.selected_activity_tab_id || this.activity == null) {
                return false;
            }

            // check activity is not assigned to another officer.
            var selectedActivity = this.application.activities.find(activity => {
                return activity.licence_activity === this.selected_activity_tab_id;
            });
            if (selectedActivity.assigned_officer != null && selectedActivity.assigned_officer !== this.current_user.id) {
                return false;
            };

            let required_role = false;
            switch(this.activity.processing_status.id) {
                case 'with_assessor':
                    required_role = false;  // only assessors in same group for added condition row can edit.
                break;
                case 'with_officer_conditions':
                    required_role =  this.canAssignOfficerFor(this.selected_activity_tab_id) ? 'licensing_officer' : false;
                break;
            }
            return required_role && this.hasRole(required_role, this.selected_activity_tab_id);
        },    
        isLicensingOfficer: function() {
            return this.hasRole('licensing_officer', this.selected_activity_tab_id);
        },
    },
    methods:{
        ...mapActions([
            'setApplicationWorkflowState',
        ]),
        addCondition(preloadedCondition){
            var showDueDate = false
            if(preloadedCondition) {
                this.viewedCondition = preloadedCondition;
                this.viewedCondition.due_date = preloadedCondition.due_date != null ? moment(preloadedCondition.due_date).format('DD/MM/YYYY'): '';
                showDueDate=this.viewedCondition.require_return
            }
            else {
                this.viewedCondition = {
                    standard: true,
                    recurrence: false,
                    due_date: '',
                    free_condition: '',
                    recurrence_pattern: 'weekly',
                    application: this.application.id
                };
            }
            this.$refs.condition_detail.showDueDate = showDueDate
            this.$refs.condition_detail.licence_activity = this.selected_activity_tab_id;
            this.$refs.condition_detail.isModalOpen = true;
        },
        removeCondition(_id){
            let vm = this;
            swal({
                title: "Remove Condition",
                text: "Are you sure you want to remove this condition?",
                type: "warning",
                showCancelButton: true,
                confirmButtonText: 'Remove Condition',
                confirmButtonColor:'#d9534f'
            }).then((result) => {
                if (result.value) {
                    vm.$http.delete(helpers.add_endpoint_json(api_endpoints.application_conditions,_id+'/delete'))
                    .then((response) => {
                        vm.$refs.conditions_datatable.vmDataTable.ajax.reload();
                    }, (error) => {
                        console.log(error);
                    });
                }
            },(error) => {
            });
        },
        async fetchConditions(){
            let vm = this;
            await vm.$http.get(api_endpoints.application_standard_conditions).then((response) => {
                vm.conditions = response.body
            },(error) => {
                console.log(error);
            })
        },
        fetchPurposes(){
            this.purposes = [];
            var selectedActivity = this.application.activities.find(activity => {
                return activity.licence_activity === this.selected_activity_tab_id;
            });
            this.purposes = selectedActivity.purposes;
        },
        async editCondition(_id){
            let vm = this;
            await vm.$http.get(helpers.add_endpoint_json(api_endpoints.application_conditions,_id)).then((response) => {
                response.body.standard ? $(this.$refs.condition_detail.$refs.standard_req).val(response.body.standard_condition).trigger('change'): '';
                this.addCondition(response.body);
            },(error) => {
                console.log(error);
            })
        },
        updatedConditions(){
            this.$refs.conditions_datatable.vmDataTable.ajax.reload();
        },
        eventListeners(){
            let vm = this;
            if (vm.$refs.conditions_datatable==null){
                return
            }
            vm.$refs.conditions_datatable.vmDataTable.on('click', '.deleteCondition', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-id');
                vm.removeCondition(id);
            });
            vm.$refs.conditions_datatable.vmDataTable.on('click', '.editCondition', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-id');
                vm.editCondition(id);
            });
            vm.$refs.conditions_datatable.vmDataTable.on('click', '.dtMoveUp', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-id');
                vm.moveUp(e);
            });
            vm.$refs.conditions_datatable.vmDataTable.on('click', '.dtMoveDown', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-id');
                vm.moveDown(e);
            });
        },
        async sendDirection(req,direction){
            let movement = direction == 'down'? 'move_down': 'move_up';
            await this.$http.get(helpers.add_endpoint_json(api_endpoints.application_conditions,req+'/'+movement)).then((response) => {
            },(error) => {
                console.log(error);
                
            })
        },
        async moveUp(e) {
            // Move the row up
            let vm = this;
            e.preventDefault();
            var tr = $(e.target).parents('tr');
            if (await vm.moveRow(tr, 'up')){
                await vm.sendDirection($(e.target).parent().data('id'),'up');
            }
        },
        async moveDown(e) {
            // Move the row down
            e.preventDefault();
            let vm = this;
            var tr = $(e.target).parents('tr');
            if (await vm.moveRow(tr, 'down')){
                await vm.sendDirection($(e.target).parent().data('id'),'down');
            }
        },
        async moveRow(row, direction) {
            // Move up or down (depending...)
            const table = this.$refs.conditions_datatable.vmDataTable;
            let index = row[0].sectionRowIndex - 1;
            let order = -1;
            if (direction === 'down') {
              order = 1;
            }
            let new_index = index + order
            if (new_index<0){
                new_index = 1
            }
            if (new_index>table.data().length-1){
                new_index = table.data().length-2
            }
            let selected = table.rows(index).data();
            let replaced = table.rows(new_index).data();
            order = selected.order
            selected.order = replaced.order;
            replaced.order = order;
            let old_data = table.data()
            let new_data = table.data()
            for (let i=0; i<old_data.length; i++){
                if (i===new_index){
                    new_data[i] = selected[0]
                    continue
                }
                if (i===index){
                    new_data[i] = replaced[0]
                    continue
                }
                new_data[i] = old_data[i]
            }
            table.clear()
            table.rows.add(new_data)
            table.draw();
            return true
        },
    },
    mounted: function(){
        this.fetchConditions();
        this.fetchPurposes();
        this.$nextTick(() => {
            this.eventListeners();
            this.form = document.forms.assessment_form;
        });
    },
    updated: function() {
    }
}
</script>
<style scoped>
</style>