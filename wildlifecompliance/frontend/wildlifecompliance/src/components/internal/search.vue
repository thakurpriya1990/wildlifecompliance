<template>
<div class="container" id="internalSearch">
    <!--UserDashTable level="internal" :url="users_url" />
    <OrganisationDashTable /-->
    <div class="row">
        <div class="col-sm-12">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <h3 class="panel-title">Person and Organisation Search
                        <a :href="'#'+rBody" data-toggle="collapse"  data-parent="#personOrgSearch" expanded="true" :aria-controls="rBody">
                            <span class="glyphicon glyphicon-chevron-up pull-right "></span>
                        </a>
                    </h3>
                </div>
                <div class="panel-body collapse in" :id="kBody">
                    <div class="row">
                        <div class="form-group">
                            <!--label for="person_lookup" class="col-sm-3 control-label">Search</label-->
                            <div class="col-sm-6">
                                <select 
                                    id="person_lookup"  
                                    name="person_lookup"  
                                    ref="person_lookup" 
                                    class="form-control" 
                                />
                            </div>
                            <div class="col-sm-3">
                                <input 
                                type="button" 
                                @click.prevent="personOrganisationSearch" 
                                class="btn btn-primary" 
                                value="View Details"
                                />
                            </div>
                        </div>
                      </div>
                </div>
            </div>
        </div>
    </div>
    <div v-if="showSearchKeywords" class="row">
        <div class="col-sm-12">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <h3 class="panel-title">Keywords
                        <a :href="'#'+kBody" data-toggle="collapse"  data-parent="#keywordInfo" expanded="true" :aria-controls="kBody">
                            <span class="glyphicon glyphicon-chevron-up pull-right "></span>
                        </a>
                    </h3>
                </div>
                <div class="panel-body collapse in" :id="kBody">
                    <div class="row">
                      <div>
                        <div class="form-group">
                          <label for="" class="control-label col-lg-12">Filter</label>
                          <div class="form-check form-check-inline col-md-3">
                              <input  class="form-check-input" ref="searchApplication" id="searchApplication" name="searchApplication" type="checkbox" v-model="searchApplication" />
                              <label class="form-check-label" for="searchApplication">Application</label>

                          </div>
                          <div class="form-check form-check-inline col-md-3">
                              <input  class="form-check-input" ref="searchLicence" id="searchLicence" name="searchLicence" type="checkbox" v-model="searchLicence" />
                              <label class="form-check-label" for="searchLicence">Licence</label>
                          </div>
                          <div class="form-check form-check-inline col-md-3">
                              <input  class="form-check-input" ref="searchReturn" id="searchReturn" name="searchReturn" type="checkbox" v-model="searchReturn" />
                              <label class="form-check-label" for="searchReturn">Return with requirements</label>
                          </div>
                          <label for="" class="control-label col-lg-12">Keyword</label>
                            <div class="col-md-8">
                              <input type="search"  class="form-control input-sm" name="details" placeholder="" v-model="keyWord"></input>
                            </div>
                            <div class="col-md-1">
                            </div>
                            <div class="col-md-3">
                              <input type="button" @click.prevent="addKeyword" class="btn btn-primary" value="Add"/>
                            </div>
                        </div>
                      </div>
                    </div>
                    <div class="row">
                      <div class="col-lg-12">
                          <ul class="list-inline" style="display: inline; width: auto;">
                              <li class="list-inline-item" v-for="(item,i) in searchKeywords">
                                <button @click.prevent="" class="btn btn-light" style="margin-top:5px; margin-bottom: 5px">{{item}}</button><a href="" @click.prevent="removeKeyword(i)"><span class="glyphicon glyphicon-remove "></span></a>
                              </li>
                          </ul>
                      </div>
                    </div>
                    <div class="row">
                      <div class="col-lg-12">
                        <div>
                          <input :disabled="!hasSearchKeywords" type="button" @click.prevent="searchKeyword" class="btn btn-primary" style="margin-bottom: 5px"value="Search"/>
                          <input type="reset" @click.prevent="clearKeywordSearch" class="btn btn-primary" style="margin-bottom: 5px"value="Clear"/>
                        </div>
                      </div>
                    </div>
                    <div class="row">
                        <div class="col-lg-12">
                            <datatable ref="keyword_search_datatable" :id="datatable_id" :dtOptions="keyword_search_options"  :dtHeaders="keyword_search_headers"/>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="row">
        <div class="col-sm-12">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <h3 class="panel-title">Reference Number
                        <a :href="'#'+rBody" data-toggle="collapse"  data-parent="#referenceNumberInfo" expanded="true" :aria-controls="rBody">
                            <span class="glyphicon glyphicon-chevron-up pull-right "></span>
                        </a>
                    </h3>
                </div>
                <div class="panel-body collapse in" :id="rBody">
                    <div class="row col-lg-12">
                        <span>Search on the following items via Reference Number:</span>
                        <ul>
                            <li>Applications (e.g. A000001)</li>
                            <li>Licences (e.g. L000001)</li>
                            <li>Returns (e.g. R000001)</li>
                            <li>Tag Purchases (e.g. T000001)</li>
                            <li>Organisation Access Requests (e.g. OAR000001)</li>
                            <li>Advices to CEO (e.g. AD000001)</li>
                            <li>Endorsement Applications (e.g. E000001)</li>
                            <li>Lawful Authority Applications (e.g. LAA000001)</li>
                            <li>Lawful Authorities (e.g. LA000001)</li>

                            <li>Calls/Emails (e.g. C000001)</li>
                            <li>Offences (e.g. OF000001)</li>
                            <li>Inspections (e.g. IN000001)</li>
                            <li>Sanction Outcomes (e.g. IF000001)</li>
                            <li>Legal Cases (e.g. CS000001)</li>
                            <li>Objects (e.g. OB000001)</li>
                        </ul>
                    </div>
                    <div class="row">
                       <label for="" class="control-label col-lg-12">Reference Number</label>
                          <div class="col-md-8">
                              <input type="search"  class="form-control input-sm" name="referenceWord" placeholder="" v-model="referenceWord"></input>
                          </div>
                          <div v-if="showSpinner">
                            <i class='fa fa-2x fa-spinner fa-spin'></i>
                          </div>
                          <div v-else>
                            <input type="button" @click.prevent="search_reference" class="btn btn-primary" style="margin-bottom: 5px" value="Search"/>
                        </div>
                        <alert :show.sync="showError" type="danger"><strong>{{errorString}}</strong></alert>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
</template>
<script>
import $ from 'jquery'
import datatable from '@/utils/vue/datatable.vue'
import alert from '@/utils/vue/alert.vue'
import UserDashTable from '@common-components/users_dashboard.vue'
import OrganisationDashTable from '@internal-components/organisations/organisations_dashboard.vue'
import '@/scss/dashboards/search.scss';
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'
import utils from './utils'
export default {
    name: 'SearchDashboard',
    data() {
        let vm = this;
        return {
            personOrgEntity: {},
            preferredSystem: null,
            showSpinner: false,
            users_url: helpers.add_endpoint_join(api_endpoints.users_paginated,'datatable_list/?format=datatables'),
            rBody: 'rBody' + vm._uid,
            oBody: 'oBody' + vm._uid,
            cBody: 'cBody' + vm._uid,
            kBody: 'kBody' + vm._uid,
            loading: [],
            searchKeywords: [],
            hasSearchKeywords: false,
            selected_organisation:'',
            organisations: null,
            searchApplication: true,
            searchLicence: false,
            searchReturn: false,
            referenceWord: '',
            keyWord: null,
            results: [],
            errors: false,
            errorString: '',
            datatable_id: 'keyword-search-datatable-'+vm._uid,
            keyword_search_headers:["Number","Type","Applicant","Text Found","Action"],
            keyword_search_options:{
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                data: vm.results,
                columns: [
                    {data: "number"},
                    {data:"record_type"},
                    {data: "applicant"},
                    {
                        data: "text",
                        className: "normal-white-space",
                        mRender: function (data,type,full) {
                            if(data.value) {
                                return data.value;
                            }
                            else {
                                return data;
                            }
                        }
                    },
                    {data: "record_id",
                        mRender:function (data,type,full) {
                            let links = '';
                            if(full.type == 'Application') {
                              links +=  `<a href='/internal/application/${full.id}'>View</a><br/>`;
                            }
                            if(full.type == 'Licence') {
                              links +=  `<a href="${full.licence_document}" target="_blank">View</a>`;
                            }
                            if(full.type == 'Return') {
                              links +=  `<a href='/internal/return/${full.id}'>View</a><br/>`;
                            }
                            return links;
                        }
                    }
                ],
                processing: true
            }
        }
    },
    watch: {
        searchKeywords: function() {
            if (this.searchKeywords.length > 0){
                this.hasSearchKeywords = true;
            } else {
                this.hasSearchKeywords = false;
            };
        }
    },
    components: {
        alert,
        datatable,
        UserDashTable,
        OrganisationDashTable
    },
    beforeRouteEnter:function(to,from,next){
        let initialisers = [
            utils.fetchOrganisations(),
        ]
        Promise.all(initialisers).then(data => {
            next(vm => {
                vm.organisations = data[0].results;
            });
        });
    },
    computed: {
        isLoading: function () {
            return this.loading.length == 0;
        },
        showError: function() {
            return this.errors;
        },
        showSearchKeywords: function() {
            let show = true;
            if (this.preferredSystem === 'compliance_management') {
                show = false;
            }
            return show;
        },
    },
    methods: {
        personOrganisationSearch: function() {
            this.$nextTick(() => {
                //users
                //organisations
                if (this.personOrgEntity && this.personOrgEntity.entity_type === 'user') {
                    window.location.replace("/internal/users/" + this.personOrgEntity.id);
                } else if (this.personOrgEntity && this.personOrgEntity.entity_type === 'org') {
                    window.location.replace("/internal/organisations/" + this.personOrgEntity.id);
                }
            });

        },
        initialisePersonLookup: function(){
            let vm = this;
            $(vm.$refs.person_lookup).select2({
                minimumInputLength: 2,
                "theme": "bootstrap",
                allowClear: true,
                placeholder:"Select Person",
                ajax: {
                    url: api_endpoints.person_org_lookup,
                    //url: api_endpoints.vessel_rego_nos,
                    dataType: 'json',
                    data: function(params) {
                        console.log(params)
                        var query = {
                            term: params.term,
                            type: 'public',
                        }
                        return query;
                    },
                },
            }).
            on("select2:select", function (e) {
                var selected = $(e.currentTarget);
                vm.personOrgEntity = Object.assign({}, e.params.data);
            }).
            on("select2:unselect",function (e) {
                var selected = $(e.currentTarget);
                vm.personOrgEntity = {};
                //vm.approval_id = null;
            }).
            on("select2:open",function (e) {
                //const searchField = $(".select2-search__field")
                const searchField = $('[aria-controls="select2-person_lookup-results"]')
                // move focus to select2 field
                searchField[0].focus();
            });
        },

        addListeners: function(){
            let vm = this;
            // Initialise select2 for organisation
            $(vm.$refs.searchOrg).select2({
                "theme": "bootstrap",
                allowClear: true,
                placeholder:"Select Organisation"
            }).
            on("select2:select",function (e) {
                var selected = $(e.currentTarget);
                vm.selected_organisation = selected.val();
            }).
            on("select2:unselect",function (e) {
                var selected = $(e.currentTarget);
                vm.selected_organisation = selected.val();
            });
        },
        search_reference: async function() {
          let vm = this;
          if(vm.referenceWord)
          {
            vm.showSpinner = true;
            vm.errors = false;
            vm.errorString = '';
            try {
              const res = await vm.$http.post('/api/search_reference.json',{"reference_number": vm.referenceWord,});
              console.log(res)
              if (res.body.url_string) {
                  window.location.href = res.body.url_string;
              } else if (res.body.error) {
                  console.log(res.body.error)
                  vm.errors = true;
                  vm.errorString = res.body.error;
              }
            } catch(error) {
              //console.log(error);
              vm.errors = true;
              vm.errorString = helpers.apiVueResourceError(error);
            }
            vm.showSpinner = false;
          }
        },
        addKeyword: function() {
          let vm = this;
          if(vm.keyWord != null)
          {
            vm.searchKeywords.push(vm.keyWord);
          }
        },
        removeKeyword: function(index) {
          let vm = this;
          if(index >-1)
          {
            vm.searchKeywords.splice(index,1);
          }
        },
        clearKeywordSearch: function() {
          let vm = this;
          if(vm.keyWord != null)
          {
            vm.searchKeywords = [];
          }
          vm.keyWord = null;
          vm.results = [];
          vm.$refs.keyword_search_datatable.vmDataTable.clear()
          vm.$refs.keyword_search_datatable.vmDataTable.draw();
        },
        searchKeyword: function() {
          let vm = this;
          if(this.searchKeywords.length > 0)
          {
            vm.$http.post('/api/search_keywords.json',{
              searchKeywords: vm.searchKeywords,
              searchApplication: vm.searchApplication,
              searchLicence: vm.searchLicence,
              searchReturn: vm.searchReturn,
              is_internal: true,
            }).then(res => {
              vm.results = res.body;
              vm.$refs.keyword_search_datatable.vmDataTable.clear()
              vm.$refs.keyword_search_datatable.vmDataTable.rows.add(vm.results);
              vm.$refs.keyword_search_datatable.vmDataTable.draw();
            },
            err => {
              console.log(err);
            });
          }
        },
    },
    mounted: function () {
        let vm = this;
        vm.keyword_search_options.data = vm.results;
        vm.$refs.keyword_search_datatable.vmDataTable.draw();
        $( 'a[data-toggle="collapse"]' ).on( 'click', function () {
            var chev = $( this ).children()[ 0 ];
            window.setTimeout( function () {
                $( chev ).toggleClass( "glyphicon-chevron-down glyphicon-chevron-up" );
            }, 100 );
        } );
        this.initialisePersonLookup();
    },
    created: async function() {
        this.preferredSystem = await helpers.getPreferredDashboard();
    },
    updated: function(){
        let vm = this;
        this.$nextTick(() => {
            vm.addListeners();
        });
        
    }
}
</script>
