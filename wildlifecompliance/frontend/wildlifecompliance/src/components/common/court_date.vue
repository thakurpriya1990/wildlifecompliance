<template lang="html">
    <div class="form-group" v-if="court_datetime"><div class="row">

        <div class="col-sm-4">
            <div class="input-group date" ref="courtDatePicker">
                <input type="text" class="form-control" placeholder="DD/MM/YYYY" v-model="court_datetime" />
                <span class="input-group-addon">
                    <span class="glyphicon glyphicon-calendar"></span>
                </span>
            </div>
        </div>

        <div class="col-sm-4">
            <div class="input-group date" ref="courtTimePicker">
                <input type="text" class="form-control" placeholder="LT" v-model="court_datetime" />
                <span class="input-group-addon">
                    <span class="glyphicon glyphicon-calendar"></span>
                </span>
            </div>
        </div>

        <div class="col-sm-4">
            <input type="text" class="form-control" v-model="comments" />
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
            my_date: null,
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
        }
    },
    computed: {
        ...mapGetters('legalCaseStore', {
            legal_case: "legal_case",
        }),
        csrf_token: function() {
            return helpers.getCookie("csrftoken");
        },
        court_date: function() {
            console.log('court_date formatted');
            return moment(this.court_datetime).format('DD/MM/YYYY');
        }
    },
    filters: {
        formatDate: function(data) {
            return data ? moment(data).format("DD/MM/YYYY HH:mm:ss") : "";
        }
    },
    methods: {
        ...mapActions('legalCaseStore', {

        }),
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
                console.log('--- date changed ---');
                vm.$emit('date_changed', { court_date_id: vm.court_date_id, new_date: e.date });
            });

            // Issue "Time" field
            el_court_time.datetimepicker({ 
                format: "LT", 
                showClear: true,
                date: vm.court_datetime,
            });
            el_court_time.on("dp.change", function(e) {
                console.log('--- time changed ---');
                vm.$emit('time_changed', { court_date_id: vm.court_date_id, new_date: e.date });
            });
        },
        courtProceedingsKeyup: function(e) {

        },
    },
    created: async function() {

    },
    mounted: function() {
        console.log('mounted');
        this.my_date = new Date();
        this.$nextTick(() => {
            this.addEventListeners();
        });
    },
};
</script>

<style lang="css">

</style>
