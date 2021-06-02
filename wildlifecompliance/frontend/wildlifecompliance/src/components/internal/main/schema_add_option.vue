<template lang="html">
    <div class="panel panel-primary">
        <div class="panel-heading">
            <h4 class="panel-title">Options
                <a class="panelClicker" :href="`#`+pOptionBody" data-toggle="collapse" data-parent="#userInfo" expanded="true" :aria-controls="pOptionBody">
                    <span class="glyphicon glyphicon-chevron-down pull-right "></span>
                </a>
            </h4>
        </div>
        <div class="panel-body panel-collapse collapse" :id="``+pOptionBody">
            <div class="row">
                <div v-for="(a, aidx) in addedOptions" v-bind:key="`a_${aidx}`">

                    <div class="col-md-12">&nbsp; </div>
                    <div class="col-md-12">
                        <div class="col-md-3">
                            <label v-if="aidx===0" class="control-label pull-left" >Add Options</label>
                        </div>
                        <div class="col-md-3">
                            <input type='text' />
                        </div>
                        <div class="col-md-3">
                            <div v-for="c in a.conditions" :value="c.value"><input type="checkbox">&nbsp; {{c.label}} &nbsp;</input><input type='text' v-if="c.value===''"/></div>
                        </div>
                        <div class="col-md-3">
                            <button v-if="canAddMore && aidx===0" class="btn btn-link pull-right" :name="`select_option_link_1`" @click.prevent="addOption()">[ Add Another ]</button>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name:"schema-add-option",
    props: {
        addedOptions: Array,
        canAddMore: Boolean,
    },
    data:function () {
        let vm = this;
        return {
            pOptionBody: 'pOptionBody' + vm._uid,
            addedOption: {
                label: '',
                value: '',
                conditions: null,
            },
        };
    },
    computed:{
    },
    methods: {
        addOption: function() {
            this.addedOptions.push(Object.assign(this.addedOption))
        },
    },
}
</script>
