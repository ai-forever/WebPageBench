<template>
  <v-row>
    <v-col cols="12" class="text-h5">State Not Found</v-col>
    <v-col>
      <div>Не найден шаг state_id в конфиге.</div>
    </v-col>
  </v-row>
</template>

<script>
import { defineComponent } from "vue";
import { API_URL } from "@/common/config";
import { mapGetters } from "vuex";

export default defineComponent({
  name: "StateNotFoundView",
  components: {},
  data() {
    return {
      API_URL,
    };
  },
  methods: {
  },
  computed: {
    ...mapGetters([""]),
  },
  watch: {},
  mounted() {
  },
  components: {
  },
});
</script>
