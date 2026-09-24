<template>
  <v-row>
    <v-col cols="12" class="text-h5">Старт</v-col>
    <v-col>
      <div>Задание доступно по адресу <strong>host/&lt;track_id&gt;</strong></div>
      <v-card class="mt-5" elevation="2">
        <v-card-title>Инструменты</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12">
              <div>Просмотр логов событий: <strong>host/&lt;track_id&gt;/events</strong></div>
              <v-text-field v-model="trackId" label="Track ID" placeholder="Введите ID трека"></v-text-field>
              <v-btn color="primary" @click="goToEventLog">Перейти к логам событий</v-btn>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>

<script>
import { defineComponent } from "vue";
import { API_URL } from "@/common/config";
import { mapGetters } from "vuex";

export default defineComponent({
  name: "HomeView",
  data() {
    return {
      API_URL,
      trackId: ""
    };
  },
  methods: {
    goToEventLog() {
      if (this.trackId) {
        this.$router.push({ name: "event_log", params: { track_id: this.trackId } });
      }
    }
    // authorize() {
    //   this.$store 
    //     .dispatch(GET_AUTHORIZATION, {}).then(() => {
    //       console.log(this.authorized)
    //       if (!this.authorized) {
    //         this.$router.push({ name: "view1" });
    //       } else {
    //         this.$router.push({ name: "submitlist" });
    //       }
    //     });
    // },
  },
  computed: {
    ...mapGetters([""]),
  },
  watch: {},
  mounted() {
    // this.$router.push({ name: "type_1", params: { state_id: 'state_1', track_id: 'test_track' } });
  },
  components: {
  },
});
</script>