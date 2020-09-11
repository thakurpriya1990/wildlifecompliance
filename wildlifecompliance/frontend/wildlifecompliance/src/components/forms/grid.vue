<template lang="html">
     <div>
          <label :id="id" :required="isRequired" > {{ label }} </label>

          <template v-if="help_text">
              <HelpText :help_text="help_text" />
          </template>

          <template v-if="help_text_url">
              <HelpTextUrl :help_text_url="help_text_url" />
          </template>

          <CommentBlock :label="label" :name="name" :field_data="getDeficiencyField" />

          <div class="grid-container">
              <div>
                  <label v-if="headers" v-for="header in headers" >
                      <input class="form-control" v-model="header.label" disabled="disabled" />
                      <div class="grid-item" v-for ="(field, row_no) in field_data" >
                          <div id="header.name" v-for="(title,key) in field" v-if="key == header.name"
                              :name="`${name}::${header.name}`" :key="`f_${key}`" >

                              <div v-if="header.type === 'date'" >
                                  <input type="text"
                                         :id="header.name + '::' + row_no"
                                         :disabled="header.readonly"
                                         :name="name + '::' + header.name"
                                         class="form-control"
                                         placeholder="DD/MM/YYYY"
                                         :v-model="setDateValue(title.value, row_no, header.name, header.readonly)"
                                         :required="isRequired"
                                  />
                              </div>

                              <div v-if="header.type === 'string'">
                                  <input :disabled="header.readonly"
                                         type="text"
                                         :id="header.name + '::' + row_no"
                                         class="form-control"
                                         :name="name + '::' + header.name"
                                         v-model="title.value"
                                         :required="isRequired"
                                  />
                              </div>

                              <div v-if="header.type === 'number'" >
                                  <input :disabled="header.readonly"
                                         :id="header.name + '::' + row_no"
                                         type="text"
                                         class="form-control"
                                         :name="name + '::' + header.name"
                                         v-model="title.value"
                                         :required="isRequired"
                                  />
                              </div>

                          </div>
                      </div>
                  </label>
              </div>
          </div>
          <div >
             <button v-show="showAddRow" class="btn btn-link" @click.prevent="addRow()" >Add Row</button>
          </div>
     </div>
</template>
<script>
import datetimepicker from 'datetimepicker';
import HelpText from './help_text.vue'
import HelpTextUrl from './help_text_url.vue'
import CommentBlock from './comment_block.vue';
const GridBlock = {
  /* Example schema config
     Note: Each grid-item requires a unique name ie.'Table-Name::location'.
     {
      "type": "grid",
      "headers": "{'label': 'LOCATION','name': 'location', 'type': 'string','required': 'true'}",
      "name": "table-name",
      "label": "Grid format of Table Data"
      "data" : "{'key': 'value'}"
     }
  */
  props: ['field_data','headers','name', 'label', 'id', 'help_text', 'help_text_url', 'readonly', 'isRequired'],
  components: {HelpText, HelpTextUrl, CommentBlock},
  data: function() {
    var grid_item = [{'id': 0, 'name': '', 'value': ''}];
    return {
      show_add_row: false,
    }
  },
  computed: {
    getDeficiencyField: function(){
      var def = this.field_data[0][this.name + '-deficiency-field']
      if (def==null){
        return {'deficiency-value': null}
      }
      return this.field_data[0][this.name + '-deficiency-field']
    },
    showAddRow: function(){
      return this.show_add_row
    },
  },
  methods: {
    addRow: function(e) {
      const self = this;
      self.grid_item = self._props['field_data']; // field_data is an Array of grid items.
      let index = self.grid_item.length;
      let fieldObj = Object.assign({}, self.grid_item[0]);
      // schema data type on each field is validated - error value required.
      for(let key in fieldObj) {
        fieldObj[key] = {'value':'', 'error':''};
      };
      self.grid_item.push(fieldObj);
    },
    addColumn: function(e) {
    },
    addArea: function(e) {
    },
    setDateValue: function(value, row, name, readonly) {
      const self = this;
      if (value !== '') {
         self.field_data[row][name].value = value;
         self.value = value;
      }
      self.show_add_row = !readonly
      return self.field_data[row][name].value;
    },
    setDatePicker: function() {
      const self = this;
      for (let row=0; row<self.field_data.length; row++) {
        Object.keys(self.field_data[row]).forEach(function(key) {
          if (key.indexOf('date')>-1) {
            let val = key + '::' + row;
            let dateVal = self.field_data[row][key].value != null ? self.field_data[row][key].value : '';
            let parts = dateVal.split('/');
            var newDate = new Date(parts[2], parts[1] - 1, parts[0]); // format new Date(YYYY,MM,DD)
            $(`[id='${val}']`).datetimepicker({
              format: 'DD/MM/YYYY',
              defaultDate: dateVal != '' ? newDate : null
            }).off('dp.change').on('dp.change', (e) => {
              self.value = $(e.target).data('DateTimePicker').date($(e.target)[0].value).format('DD/MM/YYYY');
              let row_no = e.target.id.split('::')[1]
              let name = e.target.name.split('::')[1]
              self.setDateValue(e.target.value, row_no, name, e.target.disabled)
            });
          }
        });
      }
    } // end of function to set the DatePicker widget for each Grid Item date.
  },
  updated:function () {
      this.setDatePicker();
  },
  mounted:function () {
      this.setDatePicker();
  }
}

export default GridBlock;
</script>

<style lang="css">
    input {
        box-shadow:none;
    }
    .grid-container {
        display: grid;
        width: 100%;
        height: 300px;
        border: 1px solid #ffffff;
        grid-template-columns: [labels] 5120px;
        grid-template-rows: auto;
        overflow: scroll;
        background-color: #ffffff;
    }
    .grid-container > label {
        grid-column: labels;
        grid-row: auto;
    }
    .grid-item {
        grid-column: 1 / 1;
        grid-row: 1 / 1;
        border: 1px solid #ffffff;
    }
</style>






