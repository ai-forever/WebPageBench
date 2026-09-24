<template>
  <v-row>
    <v-col cols="12" class="text-h5">Track Not Found</v-col>
    <v-col>
      <div>Конфиг задания с указанным track_id не найден.</div>
    </v-col>
  </v-row>
</template>

<script>
import { defineComponent } from "vue";
import { API_URL } from "@/common/config";
import { mapGetters } from "vuex";

export default defineComponent({
  name: "TrackNotFoundView",
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
