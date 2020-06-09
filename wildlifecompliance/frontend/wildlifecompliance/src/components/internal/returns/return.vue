<template>
<form method="POST" name="internal_returns_form" enctype="multipart/form-data">
<div class="container" id="internalReturn">
    <Returns v-if="isReturnsLoaded">
        <div class="col-md-3" />
        <div class="col-md-9">

        <template>
        <div class="panel panel-default">
            <div class="panel-heading">
                <h3 class="panel-title">Condition Details
                    <a class="panelClicker" :href="'#'+pdBody" data-toggle="collapse"  data-parent="#userInfo" expanded="true" :aria-controls="pdBody">
                        <span class="glyphicon glyphicon-chevron-up pull-right "></span>
                    </a>
                </h3>
            </div>
            <div class="panel-body panel-collapse in" :id="pdBody">
                <div class="col-sm-12">
                    <form class="form-horizontal" name="return_form">
                        <div class="form-group">
                            <label for="" class="col-sm-3 control-label">Licence Activity</label>
                            <div class="col-sm-6">
                                {{returns.condition.licence_activity.name}}
                            </div>                         
                        </div>
                        <div class="form-group">
                            <label for="" class="col-sm-3 control-label">Condition</label>
                            <div class="col-sm-6">
                                <textarea disabled class="form-control" name="details" placeholder="" v-model="returns.condition.condition"></textarea>
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="" class="col-sm-3 control-label">Due Date</label>
                            <div class="col-sm-6">
                                {{returns.condition.due_date}}
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        </template>
        <ReturnSheet v-if="returns.format==='sheet'"></ReturnSheet>
        <ReturnQuestion v-if="returns.format==='question'"></ReturnQuestion>
        <ReturnData v-if="returns.format==='data'"></ReturnData>

        <!-- End template for Return Tab -->

        <div class="row" style="margin-bottom:50px;">
            <div class="navbar navbar-fixed-bottom" style="background-color: #f5f5f5 ">
                <div class="navbar-inner">
                    <div class="container">
                        <p class="pull-right" style="margin-top:5px;">
                            <button style="width:150px;" class="btn btn-primary btn-md" @click.prevent="save()" name="save_exit">Save Changes</button>
                        </p>
                    </div>
                </div>
            </div>
        </div>

        </div>
    </Returns>
</div>
</form>
</template>

<script>
import Vue from 'vue'
import { mapActions, mapGetters } from 'vuex'
import Returns from '../../returns_form.vue'
import ReturnQuestion from '../../external/returns/enter_return_question.vue'
import ReturnSheet from '../../external/returns/enter_return_sheet.vue'
import ReturnData from '../../external/returns/enter_return.vue'
import CommsLogs from '@common-components/comms_logs.vue'
import ResponsiveDatatablesHelper from "@/utils/responsive_datatable_helper.js"
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'
export default {
  name: 'internal-returns',
  filters: {
    formatDate: function(data){
            return data ? moment(data).format('DD/MM/YYYY HH:mm:ss'): '';
    }
  },
  data() {
    let vm = this;
    return {
        pdBody: 'pdBody' + vm._uid,

        // TODO: check if still required.
        assignTo: false,
        loading: [],
        isLoading: false,
        DATE_TIME_FORMAT: 'DD/MM/YYYY HH:mm:ss',
        members: [],

        // Filters
        logs_url: helpers.add_endpoint_json(api_endpoints.returns,vm.$route.params.return_id+'/action_log'),
        comms_url: helpers.add_endpoint_json(api_endpoints.returns,vm.$route.params.return_id+'/comms_log'),
        comms_add_url: helpers.add_endpoint_json(api_endpoints.returns,vm.$route.params.return_id+'/add_comms_log'),

    }
  },
  components: {
    Returns,
    CommsLogs,
    ReturnQuestion,
    ReturnSheet,
    ReturnData,
  },
  methods: {
    ...mapActions({
      load: 'loadReturns',
    }),
    ...mapActions([
        'setReturns',
    ]),
    save: function(e) {
      const self = this;
      self.form=document.forms.internal_returns_form;
      var data = new FormData(self.form);
      // cache only used in Returns sheets
      for (const speciesID in self.species_cache) { // Running Sheet Cache
        let speciesJSON = []
        for (let i=0;i<self.species_cache[speciesID].length;i++){
          speciesJSON[i] = JSON.stringify(self.species_cache[speciesID][i])
        }
        data.append(speciesID, speciesJSON)
      };
      var speciesJSON = []
      let cnt = 0;
      for (const speciesID in self.species_transfer) { // Running Sheet Transfers
        Object.keys(self.species_transfer[speciesID]).forEach(function(key) {
          speciesJSON[cnt] = JSON.stringify(self.species_transfer[speciesID][key])
          cnt++;
        });
        data.append('transfer', speciesJSON)
      }
      self.$http.post(helpers.add_endpoint_json(api_endpoints.returns,self.returns.id+'/save'),data,{
                      emulateJSON:true,
                    }).then((response)=>{
                      let species_id = self.returns.sheet_species;
                      self.setReturns(response.body);
                      self.returns.sheet_species = species_id;

                      swal( 'Save', 
                            'Return Details Saved', 
                            'success' )
                    
                    },(error)=>{
                      console.log(error);
                      swal('Error',
                           'There was an error saving your return details.<br/>' + error.body,
                           'error'
                      )
                    });
    },

  },
  computed: {
     ...mapGetters([
        'isReturnsLoaded',
        'returns',
        'is_external',
    ]),
    isWithCurator: function() {
        return true;
    },
  },
  beforeRouteEnter: function(to, from, next){
     next(vm => {
       vm.load({ url: `/api/returns/${to.params.return_id}.json` });
     });  // Return Store loaded.
  },
}

</script>
