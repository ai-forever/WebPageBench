<template>
  <div class="bench-rail rail-booking-page rail-gray-bg">
    <div v-if="!configLoaded" class="loading-box">
      <v-progress-circular indeterminate color="#e21a1a" :size="48"></v-progress-circular>
    </div>

    <template v-else>
      <!-- Header -->
      <RailSearchHeader :rail-logo="railLogo" :is-logged-in="loggedIn" :user-name="currentUserName" @open-login="openLoginDrawer" @logout="handleLogout" />

      <!-- Main Content -->
      <div class="booking-content">
        <div class="booking-container">
          <div class="top-card">
            <!-- Back button and steps -->
            <div class="booking-header">
              <button class="back-btn" @click="goBack">
                <v-icon size="24">mdi-arrow-left</v-icon>
              </button>
              <div class="steps-indicator">
                <span v-for="step in 7" :key="step" :class="getStepClass(step)">{{ step }}</span>
              </div>
            </div>

            <h1 class="booking-title">Укажите данные пассажиров</h1>

            <!-- Train Info -->
            <div class="train-info-bar">
              <div class="train-info-content">
                <span class="train-number">{{ train.number }}</span>
                <span class="train-name">{{ train.name }}</span>
                <span class="train-route">{{ train.fromStation }} — {{ train.toStation }}</span>
                <span class="train-departure">, отпр. {{ train.departureTime }}, {{ formatDateShort(departureDate) }}</span>
              </div>
            </div>
          </div>

          <div class="passenger-cards-block">
            <!-- Passenger Cards -->
            <div class="passenger-cards">
              <div v-for="(seat, index) in selectedSeats" :key="seat.seatNumber + '-' + seat.carriageNumber" class="passenger-card">
              <div class="card-header">
                <h3 class="passenger-title">Пассажир {{ index + 1 }}</h3>
                <span class="passenger-price">{{ formatPrice(seat.price) }}</span>
              </div>

              <div class="seat-details">
                <div class="seat-info-row">
                  <span class="seat-info">Вагон {{ seat.carriageNumber }}</span>
                  <span class="seat-info">Купе {{ getCompartmentNumber(seat.seatNumber) }}</span>
                  <span class="seat-info">Место {{ seat.seatNumber }}</span>
                </div>
                <div class="seat-type-row">
                  <span class="seat-type">{{ selectedClassName }} {{ selectedClassCode }}, {{ getCarriageType(seat) }}, {{ getBerthType(seat.seatNumber) }}</span>
                </div>
              </div>

              <!-- Passenger Selector (always visible) -->
              <div class="selectors-row">
                <div class="selectors-group">
                  <v-select
                    :model-value="passengers[index]"
                    :items="passengerOptions"
                    item-title="text"
                    item-value="value"
                    :placeholder="'Пассажир не выбран *'"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                    class="passenger-select"
                    @update:model-value="updatePassenger(index, $event)"
                  >
                    <template #selection="{ item }">
                      <div v-if="item.value && item.value !== 'new'" class="passenger-option-selected">
                        <span class="passenger-name">{{ item.raw.displayName || item.title }}</span>
                        <span v-if="item.raw.birthDate" class="passenger-birthdate">{{ item.raw.birthDate }}</span>
                      </div>
                      <span v-else :class="{ 'placeholder-text': !item.value }">
                        {{ item.title || 'Пассажир не выбран' }}
                      </span>
                    </template>
                    <template #item="{ item, props }">
                      <v-list-item v-bind="props">
                        <template #title>
                          <div v-if="item.value && item.value !== 'new'" class="passenger-option-item">
                            <span class="passenger-name">{{ item.raw.displayName || item.title }}</span>
                            <span v-if="item.raw.birthDate" class="passenger-birthdate">{{ item.raw.birthDate }}</span>
                          </div>
                          <span v-else>{{ item.title }}</span>
                        </template>
                      </v-list-item>
                    </template>
                  </v-select>

                  <!-- Document Selector (only when saved passenger selected) -->
                  <v-select
                    v-if="isPassengerSaved(index)"
                    v-model="selectedDocuments[index]"
                    :items="getDocumentOptions(index)"
                    item-title="text"
                    item-value="value"
                    placeholder="Выберите документ"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                    class="document-select"
                  >
                    <template #selection="{ item }">
                      <div class="document-option-selected">
                        <span class="document-type">{{ item.raw.docType }}</span>
                        <span class="document-number">{{ item.raw.docNumber }}</span>
                      </div>
                    </template>
                  </v-select>
                </div>

                <!-- Hint (only when no passenger selected) -->
                <div v-if="!passengers[index]" class="selector-hint selector-hint-inline">
                  Вы можете выбрать ранее сохраненного пассажира или добавить нового
                </div>

                <!-- Edit Button (only when saved passenger selected) -->
                <button v-if="isPassengerSaved(index)" class="edit-passenger-btn" title="Редактировать данные пассажира">
                  <v-icon size="20">mdi-pencil-outline</v-icon>
                </button>
              </div>

              <!-- New Passenger Form (shown when "new" is selected) -->
              <template v-if="passengers[index] === 'new'">
              <div class="new-passenger-form">
                <div class="form-row">
                  <v-text-field
                    v-model="passengerData[index].lastName"
                    label="Фамилия *"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                    class="form-field"
                  />
                  <v-text-field
                    v-model="passengerData[index].firstName"
                    label="Имя *"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                    class="form-field"
                  />
                  <v-text-field
                    v-model="passengerData[index].middleName"
                    label="Отчество"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                    class="form-field"
                  />
                </div>
                <div class="form-row">
                  <v-select
                    v-model="passengerData[index].documentType"
                    :items="documentTypes"
                    item-title="text"
                    item-value="value"
                    label="Тип документа *"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                    class="form-field"
                  />
                  <v-text-field
                    v-model="passengerData[index].documentNumber"
                    label="Номер документа *"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                    class="form-field"
                  />
                  <v-text-field
                    v-model="passengerData[index].birthDate"
                    label="Дата рождения *"
                    type="date"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                    class="form-field"
                  />
                </div>
                <div class="form-row">
                  <v-select
                    v-model="passengerData[index].gender"
                    :items="genderOptions"
                    item-title="text"
                    item-value="value"
                    label="Пол *"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                    class="form-field small"
                  />
                </div>
              </div>
              </template>

              <!-- Sections visible only when a passenger is selected -->
              <template v-if="passengers[index]">

              <!-- Tariff Selector -->
              <div class="tariff-section">
                <v-select
                  v-model="passengerTariffs[index]"
                  :items="ticketTariffOptions"
                  item-title="text"
                  item-value="value"
                  placeholder="Тариф не выбран *"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                  class="tariff-select"
                >
                  <template #selection="{ item }">
                    <span class="tariff-name">{{ item.title }}</span>
                  </template>
                </v-select>
                <div v-if="passengerTariffs[index]" class="tariff-hint">
                  {{ getTariffDescription(passengerTariffs[index]) }}
                </div>
              </div>

              <!-- Checkboxes -->
              <div class="options-checkboxes">
                <v-checkbox
                  v-model="passengerOptions_food[index]"
                  label="Оформить заказ с питанием"
                  hide-details
                  density="comfortable"
                  color="#e21a1a"
                />
                <v-checkbox
                  v-model="passengerOptions_child[index]"
                  label="Добавить ребёнка без занятия места (до 5 лет на момент поездки)"
                  hide-details
                  density="comfortable"
                  color="#e21a1a"
                />
              </div>

              <!-- Expandable Sections -->
              <div class="expandable-sections">
                <v-expansion-panels multiple flat>
                  <v-expansion-panel>
                    <v-expansion-panel-title class="section-title">
                      Льготный проезд и ВТТ
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <div class="section-content-wrapper">
                        <p class="section-hint">
                          Для оформления билета по льготе укажите СНИЛС (или номер депутатского удостоверения для соответствующей льготы) и выберите категорию льготы. Будет выполнена проверка наличия льготы. Введенный номер будет сохранен в профиле пассажира автоматически.
                        </p>
                        <p class="section-hint">
                          Для оформления билета на ребенка до 18 лет по льготе ВТТ необходимо ввести СНИЛС родителя-железнодорожника.
                        </p>
                        <div class="section-field-group">
                          <label class="field-label">Основание получения льготы</label>
                          <v-select
                            v-model="benefitBasis[index]"
                            :items="benefitOptions"
                            item-title="text"
                            item-value="value"
                            placeholder="Не выбрано"
                            variant="outlined"
                            density="comfortable"
                            hide-details
                            class="benefit-select"
                          />
                        </div>
                      </div>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                  <v-expansion-panel>
                    <v-expansion-panel-title class="section-title">
                      Проездная карта
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <div class="section-content-wrapper">
                        <div class="section-field-group">
                          <label class="field-label">Карта</label>
                          <div class="field-with-button">
                            <v-select
                              v-model="travelCard[index]"
                              :items="travelCardOptions"
                              item-title="text"
                              item-value="value"
                              placeholder="Выберите карту или добавьте новую"
                              variant="outlined"
                              density="comfortable"
                              hide-details
                              class="travel-card-select"
                            />
                            <button class="link-button">
                              Приобрести проездную карту
                            </button>
                          </div>
                        </div>
                      </div>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                  <v-expansion-panel>
                    <v-expansion-panel-title class="section-title">
                      Бонус
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <div class="section-content-wrapper">
                        <div class="section-field-group">
                          <label class="field-label">Номер карты «Бонус»</label>
                          <div class="field-with-hint-button">
                            <v-text-field
                              v-model="railBonusCard[index]"
                              placeholder="Заполните поле для накопления баллов"
                              variant="outlined"
                              density="comfortable"
                              hide-details
                              class="bonus-card-field"
                            />
                            <div class="hint-with-button">
                              <p class="inline-hint">
                                Для приобретения билетов за баллы необходимо войти в систему «Бонус» в профиле пассажира
                              </p>
                              <button class="link-button">
                                Перейти в профиль пассажира
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                  <v-expansion-panel>
                    <v-expansion-panel-title class="section-title">
                      Если пассажир медработник
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <div class="section-content-wrapper">
                        <div class="medical-worker-checkbox">
                          <v-checkbox
                            v-model="isMedicalWorker[index]"
                            hide-details
                            density="comfortable"
                            color="#e21a1a"
                          >
                            <template #label>
                              <div class="checkbox-label-with-icon">
                                <span>Пассажир является медицинским работником и готов оказать первую помощь в экстренном случае</span>
                                <v-icon size="20" class="info-icon">mdi-information-outline</v-icon>
                              </div>
                            </template>
                          </v-checkbox>
                        </div>
                      </div>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
              </div>

              <!-- Contact Details Section -->
              <div class="contact-section">
                <v-expansion-panels v-model="contactPanelOpen[index]" variant="accordion" flat>
                  <v-expansion-panel value="open">
                    <v-expansion-panel-title class="section-title">
                      Контактные данные
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <div class="contact-form">
                        <div class="contact-row">
                          <v-text-field
                            v-model="contactData[index].phone"
                            label="Телефон *"
                            variant="outlined"
                            density="comfortable"
                            hide-details
                            class="contact-field"
                            placeholder="+7"
                          />
                          <v-text-field
                            v-model="contactData[index].email"
                            label="Эл. почта"
                            variant="outlined"
                            density="comfortable"
                            hide-details
                            class="contact-field"
                            type="email"
                          />
                        </div>
                        <p class="contact-hint">
                          Телефон и электронная почта будут использованы для уведомлений об изменении условий перевозки и для экстренных сообщений, а также для информирования при оформлении УПДЖД для поездки в Калининград.
                        </p>
                      </div>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
              </div>

              </template>
              </div>
            </div>

            <!-- Trip Summary -->
            <div class="trip-summary">
              <p class="summary-text">
                Поездка <span class="summary-text-accent">{{ train.fromStation }} — {{ train.toStation }}</span>, поезд {{ train.number }}, {{ selectedClassName }},
                <span v-for="(seat, idx) in selectedSeats" :key="idx">
                  вагон {{ seat.carriageNumber }}, место {{ seat.seatNumber }}{{ idx < selectedSeats.length - 1 ? '; ' : '' }}
                </span>
                добавлена в корзину.
              </p>
            </div>

            <!-- Bottom Bar -->
            <div class="booking-bottom-bar">
              <div class="action-buttons">
                <template v-if="isReturnTrip">
                  <!-- Return trip: show additional trips + submit order -->
                  <button class="additional-trips-btn" @click="goToAdditionalTrips">
                    ВЫБРАТЬ ДОПОЛНИТЕЛЬНЫЕ ПОЕЗДКИ
                  </button>
                  <button class="submit-order-btn" :disabled="!isFormValid" @click="submitOrder">
                    ОФОРМИТЬ ЗАКАЗ
                  </button>
                </template>
                <template v-else-if="hasReturnTrip">
                  <!-- Outbound trip with return planned -->
                  <button class="return-trip-btn" @click="goToReturnTrip" :disabled="!isFormValid">
                    К ОБРАТНОЙ ПОЕЗДКЕ
                  </button>
                </template>
                <template v-else>
                  <!-- One-way trip: show additional trips + submit order -->
                  <button class="additional-trips-btn" @click="goToAdditionalTrips">
                    ВЫБРАТЬ ДОПОЛНИТЕЛЬНЫЕ ПОЕЗДКИ
                  </button>
                  <button class="submit-order-btn" :disabled="!isFormValid" @click="submitOrder">
                    ОФОРМИТЬ ЗАКАЗ
                  </button>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Login Drawer -->
      <RailLoginDrawer
        v-model="loginDrawer"
        :is-logged-in="loggedIn"
        :login-credentials="loginCredentials"
        :user-data="loginCredentials"
        :current-user-name="currentUserName"
        :current-user-email="currentUserEmail"
        @login="handleLogin"
        @logout="handleLogout"
      />
    </template>
  </div>
</template>

<script>
import { defineComponent } from "vue";
import { mapGetters } from "vuex";
import { GET_TRACK_CONFIG, GET_KV_STORE } from "@/store/actions.type";
import { railAssets } from "@/assets/rail-assets.js";
import { setRailTicketLoggedIn, setRailTicketCurrentUser, setRailTicketUserData, getRailTicketUserData, clearRailTicketLogin, getRailBookingSession, setRailBookingSession, clearRailBookingSession, addRailTicket, syncRailTicketLoggedInFromTrack } from "@/utils/localCache.js";
import { StateDelayMixin } from "@/common/stateDelayMixin.js";
import { benchUserContextMixin } from "@/common/benchUserContextMixin.js";
import { _logActivity } from "@/common/trackHelper";
import RailSearchHeader from "./components/RailSearchHeader.vue";
import RailLoginDrawer from "./components/RailLoginDrawer.vue";

export default defineComponent({
  name: "RailPassengerSelection",
  mixins: [benchUserContextMixin,StateDelayMixin],
  components: { RailSearchHeader, RailLoginDrawer },
  data() {
    return {
      loginDrawer: false,
      loggedIn: false,
      passengers: [],
      passengerData: [],
      selectedDocuments: [],
      passengerTariffs: [],
      passengerOptions_food: [],
      passengerOptions_child: [],
      contactData: [],
      contactPanelOpen: [],
      benefitBasis: [],
      travelCard: [],
      railBonusCard: [],
      isMedicalWorker: [],
      documentTypes: [
        { text: "Паспорт РФ", value: "passport_rf" },
        { text: "Заграничный паспорт РФ", value: "passport_foreign" },
        { text: "Свидетельство о рождении", value: "birth_certificate" },
        { text: "Иностранный документ", value: "foreign_doc" },
      ],
      genderOptions: [
        { text: "Мужской", value: "male" },
        { text: "Женский", value: "female" },
      ],
      ticketTariffOptions: [
        { text: "Полный", value: "full", description: "Стандартный тариф без скидок." },
        { text: "«Туда-обратно»", value: "round_trip", description: "Для единовременного оформления проезда «туда» и «обратно». Снижает стоимость проездного документа в направлении «обратно» на 20%." },
      ],
      benefitOptions: [
        { text: "Не выбрано", value: null },
      ],
      travelCardOptions: [
        { text: "Выберите карту или добавьте новую", value: null },
      ],
    };
  },
  computed: {
    ...mapGetters(["trackConfig", "kvStore"]),
    configLoaded() {
      return this.trackConfig && Object.keys(this.trackConfig).length > 0;
    },
    common() {
      return (this.trackConfig && this.trackConfig.common_elements) || {};
    },
    testData() {
      return (this.trackConfig && this.trackConfig.test_data) || {};
    },
    loginCredentials() {
      return (this.testData && this.testData.login_data) || {};
    },
    configUserData() {
      return this.railPassengers;
    },
    currentUserName() {
      if (!this.loggedIn) return "";
      const userData = getRailTicketUserData();
      return userData.name || "";
    },
    currentUserEmail() {
      if (!this.loggedIn) return "";
      const userData = getRailTicketUserData();
      return userData.email || "";
    },
    railLogo() {
      return railAssets["rail_logo"] || "";
    },
    bookingSession() {
      return getRailBookingSession() || {};
    },
    train() {
      return this.bookingSession.train || {
        id: "train_1",
        number: "022",
        name: "«Ночной экспресс»",
        fromStation: "Москва Октябрьская",
        toStation: "Санкт-Петербург-Главный",
        departureTime: "00:25",
      };
    },
    departureDate() {
      return this.bookingSession.departureDate || new Date().toISOString().split('T')[0];
    },
    selectedSeats() {
      return this.bookingSession.selectedSeats || [];
    },
    selectedClass() {
      return this.bookingSession.selectedClass || { type: "kupe", name: "Купе" };
    },
    selectedClassName() {
      return this.selectedClass.name || "Купе";
    },
    selectedClassCode() {
      const options = this.selectedClass.options || [];
      return options[0]?.code || "2Л";
    },
    totalPrice() {
      return this.bookingSession.totalPrice || this.selectedSeats.reduce((sum, seat) => sum + (seat.price || 0), 0);
    },
    hasReturnTrip() {
      return !!this.bookingSession.returnDate;
    },
    isReturnTrip() {
      return !!this.bookingSession.isReturnTrip;
    },
    currentStep() {
      // For outbound trip: step 3 (passenger selection)
      // For return trip: step 6 (return passenger selection)
      return this.isReturnTrip ? 6 : 3;
    },
    passengerOptions() {
      const options = [
        { text: "Пассажир не выбран", value: null },
        { text: "Добавить нового пассажира", value: "new" },
      ];

      // Add prefilled passengers from config (user_data array)
      if (Array.isArray(this.configUserData)) {
        this.configUserData.forEach((user, idx) => {
          if (user && user.name) {
            const birthDate = user.birthday
              ? this.formatBirthDate(user.birthday)
              : "";
            options.push({
              text: user.name,
              value: `config_user_${idx}`,
              displayName: user.name,
              birthDate: birthDate,
              userData: user
            });
          }
        });
      }

      // Add saved passengers if logged in
      if (this.loggedIn) {
        const userData = getRailTicketUserData();
        const configUserNames = Array.isArray(this.configUserData)
          ? this.configUserData.map(u => u?.name)
          : [];
        if (userData.name && !configUserNames.includes(userData.name)) {
          const birthDate = userData.birthday
            ? this.formatBirthDate(userData.birthday)
            : "";
          options.push({
            text: userData.name,
            value: "self",
            displayName: userData.name,
            birthDate: birthDate,
            userData: userData
          });
        }
        // Add other saved passengers from userData
        const savedPassengers = userData.passengers || [];
        savedPassengers.forEach((p, idx) => {
          if (p?.name && configUserNames.includes(p.name)) return;
          const birthDate = p.birthday ? this.formatBirthDate(p.birthday) : "";
          options.push({
            text: p.name || `Пассажир ${idx + 1}`,
            value: `saved_${idx}`,
            displayName: p.name || `Пассажир ${idx + 1}`,
            birthDate: birthDate,
            userData: p
          });
        });
      }

      return options;
    },
    isFormValid() {
      // Check if all passengers are selected and have required data
      for (let i = 0; i < this.selectedSeats.length; i++) {
        const passengerValue = this.passengers[i];
        if (!passengerValue) return false;

        // Check if tariff is selected (mandatory)
        if (!this.passengerTariffs[i]) return false;

        if (passengerValue === 'new') {
          const data = this.passengerData[i];
          if (!data || !data.lastName || !data.firstName || !data.documentType || !data.documentNumber || !data.birthDate || !data.gender) {
            return false;
          }
        }
        // For saved passengers (config_user, self, saved_*), form is valid
      }
      return true;
    }
  },
  methods: {
    getTrackConfig() {
      this.$store.dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id }).then(() => {
        if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
          this.$router.push({ name: "not_found" });
          return;
        }
        const kvPath = this.testData.kv_store_path || "";
        if (kvPath) {
          this.$store.dispatch(GET_KV_STORE, { kvPath });
        }
        if (!this.trackConfig[this.$route.params.state_id]) {
          this.$router.push({ name: "state_not_found" });
        }
        this.applyStateDelay();
      });
    },
    openLoginDrawer() {
      this.loginDrawer = true;
    },
    handleLogin(formData) {
      this.loggedIn = true;
      setRailTicketLoggedIn(true);
      setRailTicketCurrentUser(formData.username || "guest");
      setRailTicketUserData(formData.userData || {});
    },
    handleLogout() {
      this.loggedIn = false;
      clearRailTicketLogin();
    },
    goBack() {
      this.$router.back();
    },
    getCompartmentNumber(seatNumber) {
      return Math.ceil(seatNumber / 4);
    },
    getCarriageType(seat) {
      return "ТВЕРСК";
    },
    getBerthType(seatNumber) {
      // Odd numbers are lower, even are upper in standard compartments
      return seatNumber % 2 === 1 ? "Нижнее" : "Верхнее";
    },
    initializePassengerData() {
      this.passengers = this.selectedSeats.map(() => null);
      this.passengerData = this.selectedSeats.map(() => ({
        lastName: "",
        firstName: "",
        middleName: "",
        documentType: "passport_rf",
        documentNumber: "",
        birthDate: "",
        gender: null,
      }));
      this.selectedDocuments = this.selectedSeats.map(() => null);
      this.passengerTariffs = this.selectedSeats.map(() => null);
      this.passengerOptions_food = this.selectedSeats.map(() => false);
      this.passengerOptions_child = this.selectedSeats.map(() => false);
      this.contactData = this.selectedSeats.map(() => ({
        phone: this.railPrimaryPassenger?.phone || "",
        email: this.railPrimaryPassenger?.email || "",
      }));
      this.contactPanelOpen = this.selectedSeats.map(() => "open");
      this.benefitBasis = this.selectedSeats.map(() => null);
      this.travelCard = this.selectedSeats.map(() => null);
      this.railBonusCard = this.selectedSeats.map(() => "");
      this.isMedicalWorker = this.selectedSeats.map(() => false);
    },
    getDocumentOptions(index) {
      const passenger = this.passengers[index];
      if (!passenger || passenger === 'new') return [];

      const option = this.passengerOptions.find(opt => opt.value === passenger);
      if (!option || !option.userData) return [];

      const userData = option.userData;
      const options = [];

      if (userData.passport_number) {
        options.push({
          text: `Паспорт РФ ${userData.passport_number}`,
          value: "passport_rf",
          docType: "Паспорт РФ",
          docNumber: userData.passport_number
        });
      }

      return options;
    },
    getTariffDescription(tariffValue) {
      const tariff = this.ticketTariffOptions.find(t => t.value === tariffValue);
      return tariff ? tariff.description : "";
    },
    goToReturnTrip() {
      // Save current ticket to basket first, then go to return trip selection
      this.saveTicketToBasket();

      // Log basket_add event for outbound trip
      const passengersData = this.passengers.map((p, idx) => {
        if (p === 'new') {
          const data = this.passengerData[idx];
          return {
            type: 'new',
            name: `${data.lastName} ${data.firstName} ${data.middleName}`.trim(),
            birth_date: data.birthDate,
            gender: data.gender,
            document_type: data.documentType,
            tariff: this.passengerTariffs[idx],
          };
        } else if (p) {
          const option = this.passengerOptions.find(opt => opt.value === p);
          return {
            type: p.startsWith('saved_') ? 'saved' : p,
            name: option?.userData?.name || null,
            birth_date: option?.userData?.birthday || null,
            gender: option?.userData?.gender || null,
            tariff: this.passengerTariffs[idx],
          };
        }
        return null;
      }).filter(Boolean);

      _logActivity(this, {
        type: "basket_add",
        train_id: this.train.id,
        train_number: this.train.number,
        train_name: this.train.name,
        from_station: this.train.fromStation,
        to_station: this.train.toStation,
        departure_date: this.departureDate,
        departure_time: this.train.departureTime,
        tariff_name: this.selectedClassName,
        tariff_code: this.selectedClassCode,
        seats: this.selectedSeats.map(seat => ({
          carriage_number: seat.carriageNumber,
          seat_number: seat.seatNumber,
          price: seat.price,
        })),
        passengers: passengersData,
        total_price: this.totalPrice,
        direction: "outbound",
      });

      // Set up return trip booking session
      const session = getRailBookingSession() || {};
      const returnSession = {
        from: session.to,
        to: session.from,
        departureDate: session.returnDate,
        adults: session.adults,
        children: session.children,
        isReturnTrip: true,
        outboundTicketId: session.ticketId
      };
      setRailBookingSession(returnSession);

      // Navigate to search for return trip
      this.$router.push({
        name: "bench_rail_search",
        params: {
          track_id: this.$route.params.track_id,
          state_id: this.$route.params.state_id,
        },
        query: {
          from: returnSession.from,
          to: returnSession.to,
          date: returnSession.departureDate,
          adults: returnSession.adults,
          children: returnSession.children,
        }
      });
    },
    saveTicketToBasket() {
      const session = this.bookingSession;

      // Create ticket object
      const ticket = {
        train: session.train,
        departureDate: session.departureDate,
        selectedClass: session.selectedClass,
        selectedSeats: session.selectedSeats,
        passengers: this.passengers.map((p, idx) => {
          if (p === 'new') {
            return { ...this.passengerData[idx], type: 'new' };
          } else if (p === 'self') {
            const userData = getRailTicketUserData();
            return { name: userData.name, type: 'self' };
          } else if (p && p.startsWith('saved_')) {
            const userData = getRailTicketUserData();
            const savedIdx = parseInt(p.replace('saved_', ''));
            return { ...userData.passengers[savedIdx], type: 'saved' };
          }
          return null;
        }),
        totalPrice: this.totalPrice,
        createdAt: new Date().toISOString(),
      };

      // Add to basket
      const ticketId = addRailTicket(null, ticket);

      // Update session with ticket ID
      session.ticketId = ticketId;
      setRailBookingSession(session);

      return ticketId;
    },
    addToBasket() {
      if (!this.isFormValid) return;

      this.saveTicketToBasket();

      if (this.hasReturnTrip) {
        this.goToReturnTrip();
      } else {
        // Clear booking session and go back to search
        clearRailBookingSession();

        // Navigate back to search with success message
        this.$router.push({
          name: "bench_rail_search",
          params: {
            track_id: this.$route.params.track_id,
            state_id: this.$route.params.state_id,
          },
          query: {
            ticketAdded: 'true'
          }
        });
      }
    },
    formatPrice(price) {
      return price.toLocaleString("ru-RU", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).replace(',', ',') + " ₽";
    },
    formatDateShort(date) {
      if (!date) return "";
      const d = new Date(date);
      const day = d.getDate();
      const months = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"];
      const weekdays = ["вс", "пн", "вт", "ср", "чт", "пт", "сб"];
      return `${day} ${months[d.getMonth()]}, ${weekdays[d.getDay()]}`;
    },
    formatBirthDate(date) {
      if (!date) return "";
      const d = new Date(date);
      const day = String(d.getDate()).padStart(2, "0");
      const month = String(d.getMonth() + 1).padStart(2, "0");
      const year = d.getFullYear();
      return `${day}.${month}.${year}`;
    },
    getStepClass(step) {
      // For outbound trip: current step is 3, completed are 1-2
      // For return trip: current step is 6, completed are 1-5 (including steps 4-5 for return tariff/seat)
      const current = this.currentStep;
      if (step === current) return "step active";
      if (step < current) return "step completed";
      return "step";
    },
    isPassengerSaved(index) {
      const val = this.passengers[index];
      return val && val !== 'new';
    },
    updatePassenger(index, value) {
      // Update the passengers array
      this.passengers[index] = value;

      if (!value || value === "new") {
        // Reset to empty form for new passenger
        this.passengerData[index] = {
          lastName: "",
          firstName: "",
          middleName: "",
          documentType: "passport_rf",
          documentNumber: "",
          birthDate: "",
          gender: null,
        };
        this.selectedDocuments[index] = null;

        // Log select_passenger event for new passenger
        _logActivity(this, {
          type: "select_passenger",
          direction: this.isReturnTrip ? "return" : "outbound",
          passenger_index: index + 1,
          passenger_type: value === "new" ? "new" : "none",
          passenger_name: null,
        });
        return;
      }

      // Find the selected option to get userData
      const option = this.passengerOptions.find(opt => opt.value === value);
      if (option && option.userData) {
        const userData = option.userData;
        // Parse name into parts
        const nameParts = (userData.name || "").split(" ");
        const lastName = nameParts[0] || "";
        const firstName = nameParts[1] || "";
        const middleName = nameParts.slice(2).join(" ") || "";

        // Fill in the form with saved passenger data
        this.passengerData[index] = {
          lastName: lastName,
          firstName: firstName,
          middleName: middleName,
          documentType: userData.document_type || "passport_rf",
          documentNumber: userData.passport_number || "",
          birthDate: userData.birthday || "",
          gender: userData.gender || null,
        };

        // Auto-select document if available
        if (userData.passport_number) {
          this.selectedDocuments[index] = "passport_rf";
        }

        // Prefill contact data
        if (this.contactData[index]) {
          if (userData.phone) {
            this.contactData[index].phone = userData.phone;
          }
          if (userData.email) {
            this.contactData[index].email = userData.email;
          }
        }

        // Log select_passenger event for saved passenger
        _logActivity(this, {
          type: "select_passenger",
          direction: this.isReturnTrip ? "return" : "outbound",
          passenger_index: index + 1,
          passenger_type: value.startsWith("saved_") ? "saved" : (value.startsWith("config_user_") ? "config" : value),
          passenger_config_index: value.startsWith("config_user_") ? parseInt(value.replace("config_user_", "")) : null,
          passenger_name: userData.name || null,
          birth_date: userData.birthday || null,
          gender: userData.gender || null,
        });
      }
    },
    goToAdditionalTrips() {
      // Save current ticket first
      this.saveTicketToBasket();

      // Navigate back to search for additional trips
      this.$router.push({
        name: "bench_rail_search",
        params: {
          track_id: this.$route.params.track_id,
          state_id: this.$route.params.state_id,
        },
        query: {
          ticketAdded: 'true'
        }
      });
    },
    submitOrder() {
      if (!this.isFormValid) return;

      this.saveTicketToBasket();

      // Log basket_add event with all booking details
      const passengersData = this.passengers.map((p, idx) => {
        if (p === 'new') {
          const data = this.passengerData[idx];
          return {
            type: 'new',
            name: `${data.lastName} ${data.firstName} ${data.middleName}`.trim(),
            birth_date: data.birthDate,
            gender: data.gender,
            document_type: data.documentType,
            tariff: this.passengerTariffs[idx],
          };
        } else if (p) {
          const option = this.passengerOptions.find(opt => opt.value === p);
          return {
            type: p.startsWith('saved_') ? 'saved' : p,
            name: option?.userData?.name || null,
            birth_date: option?.userData?.birthday || null,
            gender: option?.userData?.gender || null,
            tariff: this.passengerTariffs[idx],
          };
        }
        return null;
      }).filter(Boolean);

      _logActivity(this, {
        type: "basket_add",
        train_id: this.train.id,
        train_number: this.train.number,
        train_name: this.train.name,
        from_station: this.train.fromStation,
        to_station: this.train.toStation,
        departure_date: this.departureDate,
        departure_time: this.train.departureTime,
        tariff_name: this.selectedClassName,
        tariff_code: this.selectedClassCode,
        seats: this.selectedSeats.map(seat => ({
          carriage_number: seat.carriageNumber,
          seat_number: seat.seatNumber,
          price: seat.price,
        })),
        passengers: passengersData,
        total_price: this.totalPrice,
        direction: this.isReturnTrip ? "return" : "outbound",
      });

      // Navigate to checkout page
      this.$router.push({
        name: "bench_rail_tickets_checkout",
        params: {
          track_id: this.$route.params.track_id,
          state_id: this.$route.params.state_id,
        },
      });
    },
  },
  watch: {
    selectedSeats: {
      handler() {
        this.initializePassengerData();
      },
      immediate: true
    }
  },
  mounted() {
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
    } else {
      const kvPath = this.testData.kv_store_path || "";
      if (kvPath) {
        this.$store.dispatch(GET_KV_STORE, { kvPath });
      }
      this.applyStateDelay();
    }
    this.loggedIn = syncRailTicketLoggedInFromTrack(this.trackConfig);

    // Check if we have a booking session with selected seats
    const session = getRailBookingSession();
    if (!session || !session.selectedSeats || session.selectedSeats.length === 0) {
      // No booking session, redirect back to seat selection
      this.$router.push({
        name: "bench_rail_seat_selection",
        params: {
          track_id: this.$route.params.track_id,
          state_id: this.$route.params.state_id,
        }
      });
    }
  }
});
</script>

<style src="@/assets/rail.css"></style>
<style scoped>
.bench-rail.rail-booking-page {
  background: #e9eaed;
  min-height: 100vh;
}

.rail-booking-page :deep(.rail-header) {
  width: 100vw;
  margin-left: calc(50% - 50vw);
}

.rail-booking-page :deep(.header-inner) {
  max-width: 1600px;
  margin: 0 auto;
}

.booking-content {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

.booking-container {
  background: transparent;
}

.top-card {
  background: var(--bench-surface-elevated, #fff);
  padding: 20px;
  margin-bottom: 16px;
}

.booking-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 5px;
}

.back-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  color: #333;
}

.back-btn:hover {
  background: var(--bench-primary-light, #f0f0f0);
}

.steps-indicator {
  display: flex;
  gap: 8px;
}

.step {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #d7d7d7;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 500;
}

.step.active,
.step.completed {
  background: #e21a1a;
  color: #fff;
}

.booking-title {
  font-size: 24px;
  font-weight: 300;
  margin: 0 0 16px;
  color: #000;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
  padding-left: 10px;
}

.train-info-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #333;
  flex-wrap: wrap;
  padding-left: 10px;
}

.train-info-content {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.train-number {
  font-weight: 600;
  color: #e21a1a;
}

.train-name {
  color: #e21a1a;
}

.train-route {
  color: #333;
}

.train-departure {
  color: #666;
}

.qr-icon {
  color: #999;
  cursor: pointer;
}

.qr-icon:hover {
  color: #666;
}

/* Passenger Cards */
.passenger-cards-block {
  background: var(--bench-surface-elevated, #fff);
  padding: 20px 30px;
}

.passenger-cards {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
}

.passenger-card {
  border-radius: 4px;
  background: var(--bench-surface-elevated, #fff);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 8px;
}

.passenger-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.passenger-price {
  font-size: 24px;
  font-weight: 400;
  color: #333;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
}

.passenger-price::after {
  content: "";
}

.seat-details {
  margin-bottom: 30px;
  margin-top: 20px;
}

.seat-info-row {
  display: flex;
  gap: 8px;
  margin-bottom: 2px;
  color: #000;
}

.seat-info {
  font-size: 16px;
  color: #333;
}

.seat-type-row {
  font-size: 16px;
  color: #666;
  margin-top: 4px;
}

.passenger-selector {
  margin-bottom: 16px;
}

.passenger-select {
  max-width: 400px;
}

.placeholder-text {
  color: #e21a1a;
}

.selector-hint {
  margin-top: 8px;
  font-size: 14px;
  color: #888;
}

.selector-hint.selector-hint-inline {
  margin-top: 0;
  flex: 1 1 280px;
  line-height: 1.35;
}

/* New Passenger Form */
.new-passenger-form {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e0e0e0;
}

.form-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.form-field {
  flex: 1;
}

.form-field.small {
  flex: 0.5;
}

/* Trip Summary */
.trip-summary {
  background: transparent;
  border-top: 1px solid #e8e8e8;
  padding: 20px 0 10px 0;
  margin-bottom: 16px;
}

.summary-text {
  font-size: 16px;
  color: #888;
  margin: 0;
  text-indent: 0;
  line-height: 1.5;
}

.summary-text-accent {
  color: #000;
}

/* Bottom Bar */
.booking-bottom-bar {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 8px 0 16px;
  gap: 12px;
}

.action-buttons {
  display: flex;
  gap: 0;
}

.return-trip-btn {
  background: #e21a1a;
  color: #fff;
  border: none;
  padding: 14px 35px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  text-transform: uppercase;
}

.return-trip-btn:hover {
  background: #c91515;
}

.continue-btn {
  background: var(--bench-surface-elevated, #fff);
  color: #e21a1a;
  border: 1px solid #e21a1a;
  padding: 14px 32px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 4px;
}

.continue-btn:hover:not(:disabled) {
  background: #e21a1a;
  color: #fff;
}

.continue-btn:disabled {
  border-color: #ccc;
  color: #ccc;
  cursor: not-allowed;
}

/* When no return trip, make continue button primary */
.action-buttons:not(:has(.return-trip-btn)) .continue-btn {
  background: #e21a1a;
  color: #fff;
  border: none;
}

.action-buttons:not(:has(.return-trip-btn)) .continue-btn:hover:not(:disabled) {
  background: #c91515;
}

.action-buttons:not(:has(.return-trip-btn)) .continue-btn:disabled {
  background: #ccc;
  color: #fff;
}

/* New button styles */
.additional-trips-btn {
  background: var(--bench-surface-elevated, #fff);
  color: #e21a1a;
  border: 1px solid #e21a1a;
  padding: 14px 35px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  text-transform: uppercase;
  margin-right: 10px;
}

.additional-trips-btn:hover {
  background: #fef5f5;
}

.submit-order-btn {
  background: #e21a1a;
  color: #fff;
  border: none;
  padding: 14px 35px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  text-transform: uppercase;
}

.submit-order-btn:hover:not(:disabled) {
  background: #c91515;
  border-color: #c91515;
}

.submit-order-btn:disabled {
  background: #ccc;
  border-color: #ccc;
  cursor: not-allowed;
}

/* Passenger option styles */
.passenger-option-selected,
.passenger-option-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.passenger-option-selected .passenger-name,
.passenger-option-item .passenger-name {
  color: #000;
  font-size: 16px;
}

.passenger-option-selected .passenger-birthdate,
.passenger-option-item .passenger-birthdate {
  font-size: 12px;
  color: #666;
  margin-top: -4px;
}

/* Selectors Row */
.selectors-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.selectors-group {
  display: flex;
  gap: 8px;
  flex: 1;
}

.selectors-group :deep(.v-field__input) {
  padding-top: 5px !important;
  padding-bottom: 5px !important;
}

.passenger-select {
  flex: 1;
  max-width: 300px;
  min-width: 350px;
}

.passenger-select :deep(.v-field__outline) {
  color: #ff5a13;
}

.passenger-select :deep(input::placeholder) {
  color: #e21a1a;
  opacity: 1;
}

.document-select {
  flex: 1;
  max-width: 240px;
}

.document-select :deep(.v-field__outline) {
  color: #ccc;
}

.document-option-selected {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.document-type {
  font-size: 16px;
  color: #000;
}

.document-number {
  font-size: 12px;
  color: #666;
  margin-top: -4px;
}

.edit-passenger-btn {
  background: var(--bench-surface-elevated, #fff);
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 12px;
  cursor: pointer;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 4px;
}

.edit-passenger-btn:hover {
  background: var(--bench-primary-light, #f5f5f5);
  border-color: #999;
  color: #333;
}

/* Tariff Section */
.tariff-section {
  margin: 16px 0;
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.tariff-select {
  max-width: 400px;
  min-width: 350px;
}

.tariff-select :deep(.v-field__outline) {
  color: #ff5a13;
}

.tariff-select :deep(input::placeholder) {
  color: #e21a1a;
  opacity: 1;
}

.tariff-name {
  color: #000;
  font-size: 16px;
}

.tariff-hint {
  margin-top: 0;
  font-size: 14px;
  color: #777;
  line-height: 1.4;
  flex: 1 1 280px;
}

/* Options Checkboxes */
.options-checkboxes {
  margin: 16px 0;
  padding: 8px 0;
}

.options-checkboxes :deep(.v-checkbox) {
  margin-bottom: 0;
}

.options-checkboxes :deep(.v-selection-control) {
  min-height: 32px;
}

.options-checkboxes :deep(.v-label) {
  font-size: 16px;
  color: #777;
  opacity: 1;
}

.options-checkboxes :deep(.v-selection-control__input > .v-icon) {
  font-size: 20px;
}

/* Expandable Sections */
.expandable-sections {
  margin: 16px 0;
  border: none;
  border-radius: 0;
}

.expandable-sections :deep(.v-expansion-panels) {
  border-radius: 0;
  background: transparent;
  gap: 25px;
}

.expandable-sections :deep(.v-expansion-panel) {
  border: none;
  background: transparent;
  margin: 0;
  border-radius: 0px;
  overflow: hidden;
  box-shadow: none;
}

.expandable-sections :deep(.v-expansion-panel-title) {
  padding: 18px 20px;
  min-height: 56px;
  font-size: 18px;
  color: var(--bench-text, #333);
  background: var(--bench-primary-light, #f3f3f3);
}

.expandable-sections :deep(.v-expansion-panel-title__icon) {
  color: #000;
}

.expandable-sections :deep(.v-expansion-panel-text__wrapper) {
  padding: 25px 20px 18px 0;
  background: var(--bench-surface-elevated, #fff);
}

.section-content {
  font-size: 14px;
  color: #222;
  margin: 0;
  text-indent: 0;
}

/* Contact Section */
.contact-section {
  margin: 25px 0 5px;
  border: none;
  border-radius: 0;
}

.contact-section :deep(.v-expansion-panels) {
  border-radius: 0;
  background: transparent;
  gap: 16px;
}

.contact-section :deep(.v-expansion-panel) {
  border: none;
  margin: 0;
  background: transparent;
  border-radius: 0px;
  overflow: hidden;
  box-shadow: none;
}

.contact-section :deep(.v-expansion-panel-title) {
  padding: 18px 20px;
  min-height: 56px;
  font-size: 18px;
  color: var(--bench-text, #333);
  background: var(--bench-primary-light, #f3f3f3);
}

.contact-section :deep(.v-expansion-panel-text__wrapper) {
  padding: 0 20px 18px 0;
  background: var(--bench-surface-elevated, #fff);
}

.contact-form {
  padding-bottom: 8px;
}

.contact-row {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  margin-top: 30px;
}

.contact-field {
  flex: 1;
  max-width: 280px;
}

.contact-field :deep(.v-field__input) {
  color: #e21a1a;
}

.contact-hint {
  font-size: 14px;
  color: #888;
  text-indent: 0;
}

/* Return trip button disabled state */
.return-trip-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* Expandable sections content */
.section-content-wrapper {
  padding: 0;
}

.section-hint {
  font-size: 14px;
  color: #666;
  line-height: 1.5;
  margin: 0 0 16px 0;
  text-indent: 0;
}

.section-field-group {
  margin-bottom: 16px;
}

.field-label {
  display: block;
  font-size: 14px;
  color: #333;
  margin-bottom: 8px;
  font-weight: 400;
}

.benefit-select,
.travel-card-select {
  max-width: 400px;
}

.field-with-button {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
}

.field-with-hint-button {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.bonus-card-field {
  max-width: 400px;
  flex-shrink: 0;
}

.hint-with-button {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
  min-width: 280px;
}

.inline-hint {
  font-size: 14px;
  color: #666;
  line-height: 1.5;
  margin: 0;
  text-indent: 0;
}

.link-button {
  background: transparent;
  border: none;
  color: #e21a1a;
  font-size: 14px;
  cursor: pointer;
  padding: 0;
  text-decoration: none;
  text-align: left;
  white-space: nowrap;
}

.link-button:hover {
  text-decoration: underline;
}

.medical-worker-checkbox {
  padding: 0;
}

.medical-worker-checkbox :deep(.v-checkbox) {
  margin: 0;
}

.medical-worker-checkbox :deep(.v-selection-control) {
  min-height: 32px;
}

.medical-worker-checkbox :deep(.v-label) {
  font-size: 16px;
  color: #333;
  opacity: 1;
}

.checkbox-label-with-icon {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-icon {
  color: #999;
  cursor: help;
}
</style>
