<template lang="html">
    <div class="panel panel-primary">
        <div class="panel-heading">
            <h4 class="panel-title">Expanders
                <a class="panelClicker" :href="`#`+pExpanderBody" data-toggle="collapse" data-parent="#userInfo" expanded="true" :aria-controls="pExpanderBody">
                    <span class="glyphicon glyphicon-chevron-down pull-right "></span>
                </a>
            </h4>
        </div>
        <div class="panel-body panel-collapse collapse" :id="``+pExpanderBody">
            <div class="row">
                <div v-for="(e, eidx) in addedExpanders" v-bind:key="`e_${eidx}`">

                    <div class="col-md-12">&nbsp; </div>
                    <div class="col-md-12">
                        <div class="col-md-3">
                            <label v-if="eidx===0" class="control-label pull-left" >Add Expanders</label>
                        </div>
                        <div class="col-md-3">
                            <input type='text' class="form-control" v-model="e.label" />
                        </div>
                        <div class="col-md-3">
                            <select class="form-control" :ref="`expander_answer_type_${eidx}`" :name="`select-answer-type-${eidx}`" v-model="e.value" >
                                <option v-for="(ea, eaidx) in answerTypes" :value="ea.value" >{{ea.label}}</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <button v-if="eidx===0" class="btn btn-link pull-right" :name="`add_expander_link_1`" @click.prevent="addExpander()">[ Add Another ]</button>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name:"schema-add-expander",
    props: {
        addedExpanders: Array,
        answerTypes: Array,
    },
    data:function () {
        let vm = this;
        return {
            pExpanderBody: 'pExpanderBody' + vm._uid,
            addedExpander: {
                label: '',
                value: '',
                conditions: null,
            },
        };
    },
    computed:{
    },
    methods: {
        addExpander: function() {
            this.addedExpanders.push(Object.assign(this.addedExpander))
        },
    },
}
</script>