<template lang="html">
    <div class="form-group" v-if="court_date && court_time"><div class="row">

        <div class="col-sm-4">
            <div class="input-group date" ref="courtDatePicker">
                <input type="text" class="form-control" data-date-format="DD/MM/YYYY" v-model="court_date" />
                <span class="input-group-addon">
                    <span class="glyphicon glyphicon-calendar"></span>
                </span>
            </div>
        </div>

        <div class="col-sm-4">
            <div class="input-group date" ref="courtTimePicker">
                <input type="text" class="form-control" data-date-format="LT" v-model="court_time" />
                <span class="input-group-addon">
                    <span class="glyphicon glyphicon-calendar"></span>
                </span>
            </div>
        </div>

        <div class="col-sm-4">
            <input type="text" class="form-control" v-model="court_comments" ref="courtComments" />
        </div>

    </div></div>
</template>

<script>
import Vue from "vue";
import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";
import utils from "@/components/external/utils";
import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
import moment from 'moment';
import datatable from '@vue-utils/datatable.vue'
import 'bootstrap/dist/css/bootstrap.css';
import 'eonasdan-bootstrap-datetimepicker';
import _ from 'lodash';

export default {
    name: "CourtDate",
    data: function() {
        return {
            uuid: 0,
            court_date: null,
            court_time: null,
            court_comments: '',
        }
    },
    components: {

    },
    props:{
        court_datetime: {
            type: Date,
            default: null,
        },
        comments: {
            type: String,
            default: '',
        },
        court_date_id: {
            type: Number,
            default: null,
        },
        return_date_format: {
            type: String,
            default: 'DD/MM/YYYY',
        },
        return_time_format: {
            type: String,
            default: 'HH:mm',
        }

    },
    computed: {
        ...mapGetters('legalCaseStore', {
            legal_case: "legal_case",
        }),
        csrf_token: function() {
            return helpers.getCookie("csrftoken");
        },
    },
    filters: {
        formatDate: function(data) {
            return data ? moment(data).format("DD/MM/YYYY HH:mm:ss") : "";
        }
    },
    methods: {
        ...mapActions('legalCaseStore', {

        }),
        commentsChanged: function() {
            this.$emit('comments_changed', { court_date_id: vm.court_date_id, comments: this.comments });
        },
        courtOutcomeDocumentUploaded: function() {
            console.log('courtOutcomeDocumentUploaded');
        },
        addEventListeners: function() {
            let vm = this;
            let el_court_date = $(vm.$refs.courtDatePicker);
            let el_court_time = $(vm.$refs.courtTimePicker);

            // Issue "Date" field
            el_court_date.datetimepicker({
                format: "DD/MM/YYYY",
                showClear: true,
                date: vm.court_datetime,
            });
            el_court_date.on("dp.change", function(e) {
                vm.court_date = e.date.format('DD/MM/YYYY');
                vm.$emit('date_changed', { court_date_id: vm.court_date_id, new_date: e.date.format(vm.return_date_format) });
                e.preventDefault();
                return false;
            });

            // Issue "Time" field
            el_court_time.datetimepicker({
                format: "LT", 
                showClear: true,
                date: vm.court_timetime,
            });
            el_court_time.on("dp.change", function(e) {
                vm.court_time = e.date.format('LT');
                vm.$emit('time_changed', { court_date_id: vm.court_date_id, new_time: e.date.format(vm.return_time_format) });
                e.preventDefault();
                return false;
            });

            let el_comments = $(vm.$refs.courtComments);
            el_comments.on('keyup', function(e){
                let comments = e.target.value
                vm.$emit('comments_changed', { court_date_id: vm.court_date_id, comments: comments });
                e.preventDefault();
                return false;
            });
        },
        courtProceedingsKeyup: function(e) {

        },
    },
    created: async function() {

    },
    mounted: function() {
        console.log('mounted');
        this.$nextTick(() => {
            this.addEventListeners();
        });
        // Convert datetime representation in string to moment obj
        let court_datetime_obj = moment(new Date(this.court_datetime.getTime()));
        // Assign date as String type
        this.court_date = court_datetime_obj.format('DD/MM/YYYY');
        // Assign time as String type
        this.court_time = court_datetime_obj.format('LT');
        this.court_comments = this.comments;
    },
};
</script>

<style lang="css">

</style>
