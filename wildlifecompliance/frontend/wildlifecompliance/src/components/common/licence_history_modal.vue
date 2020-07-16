<template lang="html">
    <div id="historyDetail" v-show='showLicenceHistory'>

        <modal transition="modal fade" title="Licence History" large force>
            <div class="container-fluid">

                <form class="form-horizontal" name="licenceHistoryForm">

                    <div class="col-sm-12">

                        <datatable ref="licence_history_table" 
                            id="licence-history-table" 
                            :dtOptions="dtOptionsLicenceHistory"
                            :dtHeaders="dtHeadersLicenceHistory" 
                        />

                    </div>
                </form>

            </div>
            <div slot="footer" />
        </modal>

    </div>
</template>
<script>
import Vue from "vue";
import modal from "@vue-utils/bootstrap-modal.vue";
import datatable from "@vue-utils/datatable.vue";
import alert from '@vue-utils/alert.vue';
import {
    api_endpoints,
    helpers
}from '@/utils/hooks'
export default {
    name: 'LicenceHistoryModal',
    props: {
        licence_id: String,
    },
    components:{
        modal,
        datatable,
        alert,
    },
    data() {
        let vm = this;
        vm.history_url = helpers.add_endpoint_json(api_endpoints.licences,'licence_history');
        return {
            isModalOpen: false,
            processingDetails: false,

            licence_history_id: '0',
            historyTable: null,
            popoversInitialised: false,
            dtHeadersLicenceHistory: ["order","Date","Licence"],
            dtOptionsLicenceHistory:{
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                deferRender: true, 
                autowidth: true,
                order: [[2, 'desc']],
                dom:
                    "<'row'<'col-sm-5'l><'col-sm-6'f>>" +
                    "<'row'<'col-sm-12'tr>>" +
                    "<'row'<'col-sm-5'i><'col-sm-7'p>>",
                processing:true,
                ajax: {
                    "url": vm.history_url, 
                    type: 'GET',
                    "dataSrc": '',
                    data: function(_data) {
                        _data.licence_history_id = vm.licence_history_id
                    return _data;
                    },
                },
                order: [0],
                columnDefs: [
                    { visible: false, targets: [ 0 ] } // hide order column.
                ],
                columns:[
                    { data:"history_date" },
                    { data:"history_date" },
                    {
                        data:"history_document_url",
                        mRender:function(data,type,full){
                            return `<a href="${data}" target="_blank"><i style="color:red" class="fa fa-file-pdf-o"></i></a>`;
                        },
                        orderable: false
                    },
                ]
            },
        }
    },
    watch:{

    },
    computed: {
        is_external: function(){
            return this.level == 'external';
        },
        showLicenceHistory: function(){
            if (this.isModalOpen && !this.processingDetails){
                this.getHistory()
            }
            return this.isModalOpen
        },
    },
    methods:{
        cancel: function() {
            this.close();
        },
        close: function() {
            this.processingDetails = false;
            this.isModalOpen = false;
        },
        getHistory: function() {
            this.processingDetails = true;  
            this.$refs.licence_history_table.vmDataTable.clear().draw();
            this.url = this.$refs.licence_history_table.vmDataTable.ajax.url
            this.$refs.licence_history_table.vmDataTable.ajax.reload();
        }
    },
}
</script>
