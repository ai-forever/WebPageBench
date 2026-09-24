<template>
  <div class="footer">
    <div class="container">
      <div class="columns" :class="columnsClass">
        <div class="column" v-for="(col, cIndex) in columns" :key="cIndex">
          <div class="link" v-for="(item, iIndex) in col.items" :key="iIndex">
            {{ item.caption }}
          </div>
        </div>
      </div>
      <div class="bottom">
        <div class="copyright">{{ bottomText }}</div>
      </div>
    </div>
  </div>
  
</template>

<script>
export default {
  props: {
    columns: {
      type: Array,
      default: () => []
    },
    bottomText: {
      type: String,
      default: ''
    }
  },
  computed: {
    columnsClass() {
      const count = this.columns?.length || 0;
      return `cols-${count}`;
    }
  }
}
</script>
