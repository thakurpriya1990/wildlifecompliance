<template lang="html">
    <div class="form-group"><div class="flexContainer">

        <label class="flex-item">Date</label>
        <div class="flex-item">
            <div class="input-group date" ref="courtDatePicker">
                <input type="text" class="form-control" :value="court_date" />
                <span class="input-group-addon">
                    <span class="glyphicon glyphicon-calendar"></span>
                </span>
            </div>
        </div>

        <label class="flex-item">Time</label>
        <div class="">
            <div class="input-group date" ref="courtTimePicker">
                <input type="text" class="form-control" :value="court_time" />
                <span class="input-group-addon">
                    <span class="glyphicon glyphicon-calendar"></span>
                </span>
            </div>
        </div>

        <label class="flex-item">Comments</label>
        <div class="">
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
    methods: {
        ...mapActions('legalCaseStore', {

        }),
        commentsChanged: function() {
            this.$emit('comments_changed', { court_date_id: vm.court_date_id, comments: this.comments });
        },
        courtOutcomeDocumentUploaded: function() {
            console.log('courtOutcomeDocumentUploaded');
        },
        emitEvent: function() {
            // Construct moment to emit
            let test_m_datetime = moment(this.court_date + ' ' + this.court_time, 'DD/MM/YYYY LT');
            this.$emit('data_changed', {
                id: this.court_date_id,
                court_datetime: test_m_datetime,
                comments: this.court_comments,
            });
        },
        addEventListeners: function() {
            let vm = this;
            let el_court_date = $(vm.$refs.courtDatePicker);
            let el_court_time = $(vm.$refs.courtTimePicker);

            // Date
            el_court_date.datetimepicker({
                format: "DD/MM/YYYY",
                showClear: true,
                date: vm.court_datetime,
            });
            el_court_date.on("dp.change", function(e) {
                if (el_court_date.data("DateTimePicker").date()) {
                    vm.court_date = e.date.format('DD/MM/YYYY');
                    vm.emitEvent();
                } else if (el_court_date.data("date") === "") {
                    vm.court_date = null;
                }
            });

            // Time
            el_court_time.datetimepicker({
                format: "LT", 
                showClear: true,
                date: vm.court_datetime,
            });
            el_court_time.on("dp.change", function(e) {
                if (el_court_time.data("DateTimePicker").date()) {
                    vm.court_time = e.date.format('LT');
                    vm.emitEvent();
                } else if (el_court_time.data("date") === "") {
                    vm.court_time = null;
                }
            });

            // Comments
            let el_comments = $(vm.$refs.courtComments);
            el_comments.on('keyup', function(e){
                try {
                    vm.emitEvent();
                } catch (err) {
                    console.log(err); 
                }
            });
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
        if (this.court_datetime){
            let court_datetime_obj = moment(new Date(this.court_datetime.getTime()));
            // Assign date as String type
            this.court_date = court_datetime_obj.format('DD/MM/YYYY');
            // Assign time as String type
            this.court_time = court_datetime_obj.format('LT');
        }
        this.court_comments = this.comments;
    },
};
</script>

<style lang="css">
.bottom-align-text {

}
.flexContainer {
    display: flex;
    align-items: center;
}
</style>
