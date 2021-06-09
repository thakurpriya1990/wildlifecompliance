<template lang="html">
    <div class="panel panel-primary">
        <div class="panel-heading">
            <h4 class="panel-title">Headers
                <a class="panelClicker" :href="`#`+pHeaderBody" data-toggle="collapse" data-parent="#userInfo" expanded="true" :aria-controls="pHeaderBody">
                    <span class="glyphicon glyphicon-chevron-down pull-right "></span>
                </a>
            </h4>
        </div>
        <div class="panel-body panel-collapse collapse" :id="``+pHeaderBody">
            <div class="row">
                <div v-for="(h, hidx) in addedHeaders" v-bind:key="`h_${hidx}`" >

                    <div class="col-md-12">&nbsp; </div>
                    <div class="col-md-12">
                        <div class="col-md-3">
                            <label v-if="hidx===0" class="control-label pull-left" >Add Headers</label>
                        </div>
                        <div class="col-md-3">
                            <input type='text' class="form-control" v-model="h.label" />
                        </div>
                        <div class="col-md-3">
                            <select class="form-control" :ref="`header_answer_type_${hidx}`" :name="`select-answer-type-${hidx}`" v-model="h.value" >
                                <option v-for="(ha, haidx) in answerTypes" :value="ha.value" >{{ha.label}}</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <button v-if="hidx===0" class="btn btn-link pull-right" :name="`add_header_link_1`" @click.prevent="addHeader()">[ Add Another ]</button>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name:"schema-add-header",
    props: {
        addedHeaders: Array,
        answerTypes: Array,
    },
    data:function () {
        let vm = this;
        return {
            pHeaderBody: 'pHeaderBody' + vm._uid,
            addedHeader: {
                label: '',
                value: '',
            },
        };
    },
    computed:{
    },
    methods: {
        addHeader: function() {
            this.addedHeaders.push(Object.assign(this.addedHeader))
        },
    },
}
</script>