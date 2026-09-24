<template>
  <!-- Keep `.bench-rail` mounted immediately so app-shell styles apply from first paint (prevents width blink) -->
  <div class="bench-rail rail-search-page rail-gray-bg">
    <div v-if="!configLoaded" class="loading-box">
      <v-progress-circular indeterminate color="#e21a1a" :size="48"></v-progress-circular>
    </div>

    <template v-else>
    <!-- Header -->
    <RailSearchHeader :rail-logo="railLogo" :is-logged-in="loggedIn" :user-name="currentUserName" @open-login="openLoginDrawer" @logout="handleLogout" />

    <!-- Main Content -->
    <div class="search-content">
      <div v-if="pageLoading" class="page-loading" aria-label="Загрузка">
        <v-progress-circular indeterminate color="#e21a1a" :size="56"></v-progress-circular>
      </div>

      <template v-else>
        <!-- Filters Sidebar -->
        <div class="filters-sidebar">
          <!-- Favorites Section -->
          <div class="favorites-card">
            <div class="favorites-header">
              <h4>Избранные маршруты</h4>
              <v-icon size="20">mdi-close</v-icon>
            </div>
            <ul class="favorites-list">
              <li>быстрый выбор маршрута на главной странице</li>
              <li>фильтр для избранного маршрута автоматически сохраняется</li>
            </ul>
            <p v-if="!loggedIn" class="favorites-login">Войдите для сохранения маршрута</p>
            <button v-if="!loggedIn" class="login-btn" @click="openLoginDrawer">Войти</button>
            <button v-else class="save-route-btn">СОХРАНИТЬ МАРШРУТ</button>
          </div>

          <!-- Bonus Card -->
          <div v-if="!loggedIn" class="bonus-card">
            <div class="bonus-header">
              <h4>Билеты за баллы</h4>
              <v-icon size="20">mdi-close</v-icon>
            </div>
            <p>Если вы участник «Бонус», войдите и добавьте информацию в свой профиль.</p>
            <button class="login-btn">Войти</button>
          </div>

          <!-- Filters -->
          <div class="filter-header">
              <v-icon size="26">mdi-tune</v-icon>
              <span>Фильтр</span>
              <span class="trips-count">{{ filteredTrains.length }} рейса</span>
            </div>

          <div class="filters-section">
            <!-- PRICE FILTER -->
            <div class="filter-group">
              <div class="filter-title" @click="toggleFilter('price')">
                <span>СТОИМОСТЬ</span>
                <v-icon size="20">{{ expandedFilters.price ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
              </div>
              <div v-if="expandedFilters.price" class="filter-content">
                <div class="range-labels">
                  <span>{{ formatPrice(filters.priceMin) }}</span>
                  <span>{{ formatPrice(filters.priceMax) }}</span>
                </div>
                <v-range-slider
                  v-model="filters.priceRange"
                  :min="priceMinMax[0]"
                  :max="priceMinMax[1]"
                  :step="100"
                  :track-size="2"
                  thumb-size="12"
                  color="#e21a1a"
                  track-color="#ddd"
                  hide-details
                />
              </div>
            </div>

            <!-- DURATION FILTER -->
            <div class="filter-group">
              <div class="filter-title" @click="toggleFilter('duration')">
                <span>ВРЕМЯ В ПУТИ</span>
                <v-icon size="20">{{ expandedFilters.duration ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
              </div>
              <div v-if="expandedFilters.duration" class="filter-content">
                <div class="range-labels">
                  <span>{{ formatDuration(filters.durationMin) }}</span>
                  <span>{{ formatDuration(filters.durationMax) }}</span>
                </div>
                <v-range-slider
                  v-model="filters.durationRange"
                  :min="durationMinMax[0]"
                  :max="durationMinMax[1]"
                  :step="15"
                  :track-size="2"
                  thumb-size="12"
                  color="#e21a1a"
                  track-color="#ddd"
                  hide-details
                />
              </div>
            </div>

            <!-- Departure Filter -->
            <div class="filter-group">
              <div class="filter-title" @click="toggleFilter('departure')">
                <span>ОТПРАВЛЕНИЕ</span>
                <v-icon size="20">{{ expandedFilters.departure ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
              </div>
              <div v-if="expandedFilters.departure" class="filter-content">
                <div class="range-labels">
                  <span>{{ formatTimeMinutes(filters.departureMin) }}</span>
                  <span>{{ formatTimeMinutes(filters.departureMax) }}</span>
                </div>
                <v-range-slider
                  v-model="filters.departureRange"
                  :min="0"
                  :max="1440"
                  :step="15"
                  :track-size="2"
                  thumb-size="12"
                  color="#e21a1a"
                  track-color="#ddd"
                  hide-details
                />
              </div>
            </div>

            <!-- Arrival Filter -->
            <div class="filter-group">
              <div class="filter-title" @click="toggleFilter('arrival')">
                <span>ПРИБЫТИЕ</span>
                <v-icon size="20">{{ expandedFilters.arrival ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
              </div>
              <div v-if="expandedFilters.arrival" class="filter-content">
                <div class="range-labels">
                  <span>{{ formatTimeMinutes(filters.arrivalMin) }}</span>
                  <span>{{ formatTimeMinutes(filters.arrivalMax) }}</span>
                </div>
                <v-range-slider
                  v-model="filters.arrivalRange"
                  :min="0"
                  :max="1440"
                  :step="15"
                  :track-size="2"
                  thumb-size="12"
                  color="#e21a1a"
                  track-color="#ddd"
                  hide-details
                />
              </div>
            </div>

            <!-- Train Type Filter -->
            <div class="filter-group">
              <div class="filter-title" @click="toggleFilter('trainType')">
                <span>ТИП ПОЕЗДА</span>
                <v-icon size="20">{{ expandedFilters.trainType ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
              </div>
              <div v-if="expandedFilters.trainType" class="filter-content filter-checkboxes">
                <label class="filter-checkbox">
                  <input
                    type="checkbox"
                    v-model="filters.trainTypes.any"
                    @change="onTrainTypeAnyChange"
                  />
                  <span class="checkbox-label">Любой тип поезда</span>
                </label>
                <label class="filter-checkbox">
                  <input
                    type="checkbox"
                    v-model="filters.trainTypes.branded"
                    @change="onTrainTypeChange"
                  />
                  <span class="checkbox-label">Фирменный</span>
                  <span class="checkbox-price">{{ getMinPriceForType('branded') }}</span>
                </label>
                <label class="filter-checkbox">
                  <input
                    type="checkbox"
                    v-model="filters.trainTypes.doubleDecked"
                    @change="onTrainTypeChange"
                  />
                  <span class="checkbox-label">Двухэтажный</span>
                  <span class="checkbox-price">{{ getMinPriceForType('doubleDecked') }}</span>
                </label>
                <label class="filter-checkbox">
                  <input
                    type="checkbox"
                    v-model="filters.trainTypes.highSpeed"
                    @change="onTrainTypeChange"
                  />
                  <span class="checkbox-label">Скоростной</span>
                  <span class="checkbox-price">{{ getMinPriceForType('highSpeed') }}</span>
                </label>
              </div>
            </div>

            <!-- Train Name Filter -->
            <div class="filter-group">
              <div class="filter-title" @click="toggleFilter('trainName')">
                <span>ПО НАИМЕНОВАНИЮ</span>
                <v-icon size="20">{{ expandedFilters.trainName ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
              </div>
              <div v-if="expandedFilters.trainName" class="filter-content filter-checkboxes">
                <label class="filter-checkbox">
                  <input
                    type="checkbox"
                    v-model="filters.trainNames.any"
                    @change="onTrainNameAnyChange"
                  />
                  <span class="checkbox-label">Любое наименование</span>
                </label>
                <label class="filter-checkbox">
                  <input
                    type="checkbox"
                    v-model="filters.trainNames.noName"
                    @change="onTrainNameChange"
                  />
                  <span class="checkbox-label">Без наименования</span>
                </label>
                <label
                  v-for="trainName in availableTrainNamesInResults"
                  :key="trainName.key"
                  class="filter-checkbox"
                >
                  <input
                    type="checkbox"
                    :checked="filters.trainNames.selected.includes(trainName.key)"
                    @change="toggleTrainName(trainName.key)"
                  />
                  <span class="checkbox-label">{{ trainName.label }}</span>
                </label>
              </div>
            </div>

            <!-- Car Classes Filter -->
            <div class="filter-group">
              <div class="filter-title" @click="toggleFilter('carClasses')">
                <span>ВАГОНЫ И КЛАССЫ ОБСЛУЖИВАНИЯ</span>
                <v-icon size="20">{{ expandedFilters.carClasses ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
              </div>
              <div v-if="expandedFilters.carClasses" class="filter-content filter-checkboxes">
                <label class="filter-checkbox">
                  <input
                    type="checkbox"
                    v-model="filters.carClasses.any"
                    @change="onCarClassAnyChange"
                  />
                  <span class="checkbox-label">Любой класс обслуживания</span>
                </label>
                <label
                  v-for="carClass in availableCarClassesInResults"
                  :key="carClass.key"
                  class="filter-checkbox"
                >
                  <input
                    type="checkbox"
                    :checked="filters.carClasses.selected.includes(carClass.key)"
                    @change="toggleCarClass(carClass.key)"
                  />
                  <span class="checkbox-label">{{ carClass.label }}</span>
                </label>
              </div>
            </div>

            <!-- Services Filter -->
            <div class="filter-group">
              <div class="filter-title" @click="toggleFilter('services')">
                <span>ПО УСЛУГАМ</span>
                <v-icon size="20">{{ expandedFilters.services ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
              </div>
              <div v-if="expandedFilters.services" class="filter-content filter-checkboxes">
                <label class="filter-checkbox">
                  <input
                    type="checkbox"
                    v-model="filters.services.any"
                    @change="onServiceAnyChange"
                  />
                  <span class="checkbox-label">Любая услуга</span>
                </label>
                <label
                  v-for="service in availableServicesInResults"
                  :key="service.key"
                  class="filter-checkbox"
                >
                  <input
                    type="checkbox"
                    :checked="filters.services.selected.includes(service.key)"
                    @change="toggleService(service.key)"
                  />
                  <span class="checkbox-label">{{ service.label }}</span>
                </label>
              </div>
            </div>

            <!-- Preferential Travel Filter -->
            <div class="filter-group">
              <div class="filter-title" @click="toggleFilter('preferential')">
                <span>ЛЬГОТНЫЙ ПРОЕЗД</span>
                <v-icon size="20">{{ expandedFilters.preferential ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
              </div>
              <div v-if="expandedFilters.preferential" class="filter-content filter-checkboxes">
                <label class="filter-checkbox">
                  <input
                    type="checkbox"
                    v-model="filters.preferential.disabledSeats"
                  />
                  <span class="checkbox-label">Места для инвалидов</span>
                </label>
              </div>
            </div>

            <!-- Reset Filters -->
            <div class="filter-reset" @click="resetFilters">
              <span>СБРОСИТЬ</span>
              <v-icon size="20">mdi-close</v-icon>
            </div>
          </div>
        </div>

        <!-- Results Area -->
        <div class="results-area">
          <div class="hotel-link">
            <v-checkbox v-model="findHotel" hide-details density="compact">
              <template #label>
                Найти отель на <span class="travel-brand"> Travel</span>
              </template>
            </v-checkbox>
          </div>
          
          <div
            class="info-banner-inner"
            role="button"
            tabindex="0"
            :aria-expanded="infoExpanded"
            @click="toggleInfoBanner"
            @keydown.enter.prevent="toggleInfoBanner"
            @keydown.space.prevent="toggleInfoBanner"
          >
            <span class="info-alert-badge" aria-hidden="true">
              <v-icon size="20" class="info-alert-icon">mdi-alert-circle-outline</v-icon>
            </span>
            <div class="info-text" :class="{ 'is-collapsed': !infoExpanded }">
              <strong>Изменения в маршруте прохода к поездам на Ленинградском вокзале в Москве</strong>
              <p :class="{ 'info-text-collapsed': !infoExpanded }">Пассажирское здание Ленинградского вокзала Москвы (включая залы ожидания и бизнес-зал) закрыто на реконструкцию. Все поезда (пригородные и дальнего следования) продолжают прибывать и отправляться от его платформ по расписанию, однако маршруты прохода от метро и с привокзальной площади на платформы к поездам и обратно изменились.
Вы можете воспользоваться залами ожидания, камерами хранения, кассами и другими сервисами на соседних Ярославском и Казанском вокзалах, также расположенных на Комсомольской площади г. Москвы.
Учитывая возможное пересечение потоков пассажиров при прибытии и отправлении сразу нескольких поездов, просим прибывать на посадку заблаговременно!</p>
            </div>
            <v-icon size="20" class="info-toggle" aria-hidden="true">
              {{ infoExpanded ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
            </v-icon>
          </div>
          
          <!-- Sort Options -->
          <div class="sort-options">
            <button
              v-for="option in sortOptions"
              :key="option.value"
              :class="['sort-btn', { active: sortBy === option.value }]"
              @click="handleSortChange(option.value)"
            >
              <v-icon v-if="sortBy === option.value" size="16">mdi-arrow-right</v-icon>
              {{ option.label }}
            </button>
          </div>

        <!-- Loading -->
        <div v-if="!contentReady" class="loading-container">
          <v-progress-circular indeterminate color="#e21a1a" :size="48"></v-progress-circular>
        </div>

        <!-- Train Results -->
        <div v-if="contentReady" class="train-results">
          <div
            v-for="train in sortedTrains"
            :key="train.id"
            class="train-card"
            role="button"
            tabindex="0"
            @click="handleBuyClick(train)"
            @keydown.enter.prevent="handleBuyClick(train)"
            @keydown.space.prevent="handleBuyClick(train)"
          >
            <!-- Branded badge -->
            <div v-if="train.isBranded" class="branded-badge">Фирменный</div>

            <!-- Train Header -->
            <div class="train-header">
              <div class="train-info">
                <v-icon size="20" color="#e21a1a" v-if="train.isBranded">mdi-star</v-icon>
                <span class="train-number">{{ train.number }}</span>
                <span class="train-name">{{ train.name }}</span>
                <span class="train-route">{{ train.fromStation }} → {{ train.toStation }}</span>
                <span v-if="train.via">→ {{ train.via }}</span>
                <a href="#" class="route-link" @click.stop.prevent>Маршрут</a>
              </div>
              <v-icon size="20" color="#111" @click.stop>mdi-share-variant</v-icon>
            </div>

            <!-- Card Body: Left side (times/amenities) + Right side (tickets/buy) -->
            <div class="train-card-body">
              <div class="train-card-left">
                <!-- Train Times -->
                <div class="train-times">
                  <div class="train-times-top">
                    <div class="departure">
                      <span class="time">{{ train.departureTime }}</span>
                    </div>

                    <div class="duration">
                      <div class="duration-line" aria-hidden="true">
                        <span class="dot"></span>
                        <span class="line"></span>
                        <span class="dot"></span>
                      </div>
                      <span class="duration-text">{{ train.duration }}</span>
                    </div>

                    <div class="arrival">
                      <span class="time">{{ train.arrivalTime }}</span>
                    </div>
                  </div>

                  <div class="train-times-bottom">
                    <div class="station-info">
                      <span class="station-type">{{ train.fromStationType }}</span>
                      <span class="station-name">{{ train.fromStation }}</span>
                    </div>

                    <div class="duration-spacer" aria-hidden="true"></div>

                    <div class="station-info">
                      <span class="station-type">{{ train.toStationType }}</span>
                      <span class="station-name">{{ train.toStation }}</span>
                    </div>
                  </div>
                </div>

                <!-- Amenities -->
                <div class="train-amenities">
                  <v-icon v-for="amenity in train.amenities" :key="amenity" size="24" color="#111">{{ amenity }}</v-icon>
                </div>

                <!-- Wait List -->
                <div v-if="train.hasWaitList" class="wait-list">
                  <v-icon size="16">mdi-clock-outline</v-icon>
                  <span>Лист ожидания</span>
                </div>
              </div>

              <div class="train-card-right">
                <!-- Ticket Classes -->
                <div class="ticket-classes">
                  <div v-for="ticket in train.tickets" :key="ticket.type" class="ticket-class">
                    <div class="ticket-info">
                      <span class="ticket-type">{{ ticket.type }}</span>
                      <span class="ticket-seats">{{ ticket.seats }}</span>
                    </div>
                    <span class="ticket-price">от {{ formatPrice(ticket.calculatedPrice) }}</span>
                  </div>
                </div>

                <!-- Buy Button -->
                <button class="buy-btn" @click.stop="handleBuyClick(train)">
                  <v-icon size="24">mdi-cart-outline</v-icon>
                  Купить
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      </template>
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
import { setRailTicketLoggedIn, setRailTicketCurrentUser, setRailTicketUserData, getRailTicketUserData, clearRailTicketLogin, getRailBookingSession, setRailBookingSession, syncRailTicketLoggedInFromTrack } from "@/utils/localCache.js";
import { StateDelayMixin } from "@/common/stateDelayMixin.js";
import { benchUserContextMixin } from "@/common/benchUserContextMixin.js";
import { _logActivity } from "@/common/trackHelper";
import RailSearchHeader from "./components/RailSearchHeader.vue";
import RailLoginDrawer from "./components/RailLoginDrawer.vue";

const STATIONS = [
  { code: "2000000", name: "Москва" },
  { code: "2004000", name: "Санкт-Петербург" },
  { code: "2060600", name: "Казань" },
  { code: "2060001", name: "Нижний Новгород" },
  { code: "2030000", name: "Адлер" },
  { code: "2050000", name: "Самара" },
  { code: "2034000", name: "Сочи" },
  { code: "2010000", name: "Екатеринбург" },
  { code: "2020000", name: "Новосибирск" },
  { code: "2070000", name: "Краснодар" },
  { code: "2080000", name: "Ростов-на-Дону" },
  { code: "2090000", name: "Воронеж" },
  { code: "2100000", name: "Волгоград" },
  { code: "2110000", name: "Пермь" },
  { code: "2120000", name: "Уфа" },
  { code: "2130000", name: "Челябинск" },
  { code: "2140000", name: "Тюмень" },
  { code: "2150000", name: "Омск" },
  { code: "2160000", name: "Саратов" },
  { code: "2170000", name: "Ярославль" },
];

export default defineComponent({
  name: "RailSearch",
  mixins: [benchUserContextMixin,StateDelayMixin],
  components: { RailSearchHeader, RailLoginDrawer },
  data() {
    return {
      pageLoading: true,
      pageLoadingTimeout: null,
      loginDrawer: false,
      loggedIn: false,
      kvStoreReady: false,
      hasPerformedSearch: false,
      findHotel: false,
      infoExpanded: false,
      searchParams: {
        from: "",
        to: "",
        departureDate: null,
        returnDate: null,
        adults: 1,
        children: 0,
      },
      filters: {
        priceRange: [0, 50000],
        priceMin: 0,
        priceMax: 50000,
        durationRange: [0, 720],
        durationMin: 0,
        durationMax: 720,
        departureRange: [0, 1440],
        departureMin: 0,
        departureMax: 1440,
        arrivalRange: [0, 1440],
        arrivalMin: 0,
        arrivalMax: 1440,
        // Train type filters
        trainTypes: {
          any: true,
          branded: false,
          doubleDecked: false,
          highSpeed: false,
        },
        // Train name filters
        trainNames: {
          any: true,
          noName: false,
          selected: [], // Array of selected train names
        },
        // Car classes filter (ticket types)
        carClasses: {
          any: true,
          selected: [], // Array of selected car class keys
        },
        // Services filter (amenities)
        services: {
          any: true,
          selected: [], // Array of selected service keys
        },
        // Preferential travel filter
        preferential: {
          disabledSeats: false,
        },
      },
      // Available car classes for filter
      availableCarClasses: [
        { key: "platzkart", label: "Плацкарт", pattern: /плацкарт/i },
        { key: "kupe", label: "Купе", pattern: /^купе$/i },
        { key: "sv", label: "СВ", pattern: /^св$/i },
        { key: "lux", label: "Люкс", pattern: /люкс/i },
        { key: "seated", label: "Сидячий", pattern: /^сидячий$/i },
        { key: "seatedBusiness", label: "Сидячий (бизнес)", pattern: /сидячий.*бизнес/i },
        { key: "business", label: "Бизнес класс", pattern: /бизнес\s*класс/i },
        { key: "firstClass", label: "Первый класс", pattern: /первый\s*класс/i },
        { key: "economy", label: "Эконом", pattern: /^эконом$/i },
        { key: "economyPlus", label: "Эконом+", pattern: /эконом\+/i },
        { key: "basic", label: "Базовый", pattern: /базовый/i },
        { key: "comfort", label: "Комфорт", pattern: /комфорт/i },
        { key: "family", label: "Семейный", pattern: /семейный/i },
        { key: "bistro", label: "Вагон-бистро", pattern: /вагон.?бистро|бистро/i },
        { key: "kupeMeeting", label: "Купе-переговорная", pattern: /купе.?переговорная/i },
        { key: "kupeSuite", label: "Купе-сьют", pattern: /купе.?сьют/i },
        { key: "kupeDisabled", label: "Купе (для инвалидов)", pattern: /купе.*инвалид/i },
        { key: "economyDisabled", label: "Эконом (для инвалидов)", pattern: /эконом.*инвалид/i },
        { key: "basicDisabled", label: "Базовый (для инвалидов)", pattern: /базовый.*инвалид/i },
      ],
      // Available services for filter (based on amenities)
      availableServices: [
        { key: "food", label: "Питание", icon: "mdi-silverware-fork-knife" },
        { key: "bed", label: "Постельное бельё", icon: "mdi-bed" },
        { key: "tv", label: "ИРС (Развлечения)", icon: "mdi-television" },
        { key: "wifi", label: "Wi-Fi", icon: "mdi-wifi" },
        { key: "power", label: "Розетки", icon: "mdi-power-plug" },
        { key: "pets", label: "Перевозка животных", icon: "mdi-paw" },
        { key: "disabled", label: "Для инвалидов", icon: "mdi-wheelchair-accessibility" },
        { key: "children", label: "Для пассажиров с детьми", icon: "mdi-account-group" },
        { key: "aircon", label: "Кондиционер", icon: "mdi-air-conditioner" },
      ],
      // Available train names for filter (extracted from data)
      availableTrainNames: [
        { key: "sapsan", label: "экспресс", pattern: /экспресс/i },
        { key: "lastochka", label: "ЛАСТОЧКА", pattern: /ласточка/i },
        { key: "aurora", label: "Аврора", pattern: /аврора/i },
        { key: "arktika", label: "Арктика", pattern: /арктика/i },
        { key: "volga", label: "Волга", pattern: /волга/i },
        { key: "grandExpress", label: "Гранд-Экспресс", pattern: /гранд.?экспресс/i },
        { key: "krasnayaStrela", label: "Красная Стрела", pattern: /красная\s*стрела/i },
        { key: "nevskiyExpress", label: "Невский экспресс", pattern: /невский\s*экспресс/i },
        { key: "smenaBetankur", label: "Смена / А.Бетанкур", pattern: /смена|бетанкур/i },
        { key: "tavriya", label: "ТАВРИЯ", pattern: /таврия/i },
        { key: "express", label: "Экспресс", pattern: /^«?экспресс»?$/i },
        { key: "tversk", label: "ТВЕРСК", pattern: /тверск/i },
      ],
      expandedFilters: {
        price: true,
        duration: true,
        departure: true,
        arrival: true,
        carClasses: false,
        trainType: true,
        trainName: true,
        services: false,
        preferential: false,
      },
      sortBy: "departure",
      sortOptions: [
        { value: "departure", label: "Отправление" },
        { value: "arrival", label: "Прибытие" },
        { value: "price", label: "Подешевле" },
        { value: "duration", label: "Побыстрее" },
      ],
      stations: STATIONS,
      showFromDropdown: false,
      showToDropdown: false,
      activeSearchParams: {
        from: "",
        to: "",
        adults: 1,
        children: 0,
      },
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
      return this.railPrimaryPassenger;
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
    trainsFromKvStore() {
      const kv = this.kvStore || {};
      return Object.keys(kv)
        .filter(key => key.startsWith('train_'))
        .map(key => kv[key])
        .filter(train => train && train.id);
    },
    totalPassengers() {
      return this.activeSearchParams.adults + this.activeSearchParams.children;
    },
    filteredFromStations() {
      const query = (this.searchParams.from || '').toLowerCase();
      if (!query) return this.stations.slice(0, 6);
      return this.stations.filter(s => s.name.toLowerCase().includes(query)).slice(0, 8);
    },
    filteredToStations() {
      const query = (this.searchParams.to || '').toLowerCase();
      if (!query) return this.stations.slice(0, 6);
      return this.stations.filter(s => s.name.toLowerCase().includes(query)).slice(0, 8);
    },
    searchedTrains() {
      if (!this.hasPerformedSearch) return [];
      const from = (this.activeSearchParams.from || '').toLowerCase().trim();
      const to = (this.activeSearchParams.to || '').toLowerCase().trim();

      // Don't show results unless we have a real route
      if (!from || !to) return [];

      return this.trainsFromKvStore.filter(train => {
        // Match from station (partial, case-insensitive)
        const trainFrom = (train.fromStation || '').toLowerCase();
        const fromMatch = !from || trainFrom.includes(from) || from.includes(trainFrom.split(' ')[0]);

        // Match to station (partial, case-insensitive)
        const trainTo = (train.toStation || '').toLowerCase();
        const toMatch = !to || trainTo.includes(to) || to.includes(trainTo.split(' ')[0]);

        return fromMatch && toMatch;
      }).map(train => ({
        ...train,
        tickets: train.tickets.map(ticket => ({
          ...ticket,
          calculatedPrice: ticket.price * this.totalPassengers
        }))
      }));
    },
    railLogo() {
      return railAssets["rail_logo"] || "";
    },
    availableTrainNamesInResults() {
      // Filter available train names to only show those present in search results
      const trainNames = this.searchedTrains.map(t => (t.name || "").toLowerCase());
      return this.availableTrainNames.filter(nameObj => {
        return trainNames.some(name => nameObj.pattern.test(name));
      });
    },
    availableCarClassesInResults() {
      // Filter available car classes to only show those present in search results
      const ticketTypes = this.searchedTrains.flatMap(t => t.tickets.map(ticket => ticket.type));
      return this.availableCarClasses.filter(classObj => {
        return ticketTypes.some(type => classObj.pattern.test(type));
      });
    },
    availableServicesInResults() {
      // Filter available services to only show those present in search results
      const allAmenities = this.searchedTrains.flatMap(t => t.amenities || []);
      return this.availableServices.filter(serviceObj => {
        return allAmenities.includes(serviceObj.icon);
      });
    },
    passengersText() {
      const total = this.searchParams.adults + this.searchParams.children;
      if (total === 1) return "1 пассажир";
      if (total >= 2 && total <= 4) return `${total} пассажира`;
      return `${total} пассажиров`;
    },
    priceMinMax() {
      const trains = this.searchedTrains;
      if (!trains.length) return [0, 50000];
      const prices = trains.flatMap((t) => t.tickets.map((ticket) => ticket.calculatedPrice));
      return [Math.min(...prices), Math.max(...prices)];
    },
    durationMinMax() {
      const trains = this.searchedTrains;
      if (!trains.length) return [0, 720];
      const durations = trains.map((t) => t.durationMinutes);
      return [Math.min(...durations), Math.max(...durations)];
    },
    filteredTrains() {
      return this.searchedTrains.filter((train) => {
        // Train Type filter
        if (!this.filters.trainTypes.any) {
          const typeMatches = [];
          if (this.filters.trainTypes.branded && train.isBranded) typeMatches.push(true);
          if (this.filters.trainTypes.doubleDecked && train.isDoubleDecked) typeMatches.push(true);
          if (this.filters.trainTypes.highSpeed && train.isHighSpeed) typeMatches.push(true);

          // If any type filter is selected but train doesn't match any, exclude it
          const hasAnyTypeFilter = this.filters.trainTypes.branded || this.filters.trainTypes.doubleDecked || this.filters.trainTypes.highSpeed;
          if (hasAnyTypeFilter && typeMatches.length === 0) {
            return false;
          }
        }

        // Train Name filter
        if (!this.filters.trainNames.any) {
          const trainName = (train.name || "").trim();
          const hasNoName = !trainName || trainName === "";

          // Check if "no name" filter is selected and train has no name
          if (this.filters.trainNames.noName && hasNoName) {
            // Train matches "no name" filter, allow it
          } else if (this.filters.trainNames.selected.length > 0) {
            // Check if train name matches any selected name
            const matchesSelectedName = this.filters.trainNames.selected.some(selectedKey => {
              const nameObj = this.availableTrainNames.find(n => n.key === selectedKey);
              return nameObj && nameObj.pattern.test(trainName);
            });

            if (!matchesSelectedName && !(this.filters.trainNames.noName && hasNoName)) {
              return false;
            }
          } else if (this.filters.trainNames.noName && !hasNoName) {
            // Only "no name" is selected and train has a name
            return false;
          }
        }

        // Price filter (using calculated price based on passengers)
        const minPrice = Math.min(...train.tickets.map((t) => t.calculatedPrice));
        if (minPrice < this.filters.priceRange[0] || minPrice > this.filters.priceRange[1]) {
          return false;
        }

        // Duration filter
        if (train.durationMinutes < this.filters.durationRange[0] || train.durationMinutes > this.filters.durationRange[1]) {
          return false;
        }

        // Departure time filter
        const depMinutes = this.timeToMinutes(train.departureTime);
        if (depMinutes < this.filters.departureRange[0] || depMinutes > this.filters.departureRange[1]) {
          return false;
        }

        // Arrival time filter
        const arrMinutes = this.timeToMinutes(train.arrivalTime);
        if (arrMinutes < this.filters.arrivalRange[0] || arrMinutes > this.filters.arrivalRange[1]) {
          return false;
        }

        // Car Classes filter
        if (!this.filters.carClasses.any && this.filters.carClasses.selected.length > 0) {
          const trainTicketTypes = train.tickets.map(t => t.type);
          const hasMatchingClass = this.filters.carClasses.selected.some(selectedKey => {
            const classObj = this.availableCarClasses.find(c => c.key === selectedKey);
            return classObj && trainTicketTypes.some(type => classObj.pattern.test(type));
          });
          if (!hasMatchingClass) {
            return false;
          }
        }

        // Services filter
        if (!this.filters.services.any && this.filters.services.selected.length > 0) {
          const trainAmenities = train.amenities || [];
          const hasMatchingService = this.filters.services.selected.some(selectedKey => {
            const serviceObj = this.availableServices.find(s => s.key === selectedKey);
            return serviceObj && trainAmenities.includes(serviceObj.icon);
          });
          if (!hasMatchingService) {
            return false;
          }
        }

        // Preferential travel filter (disabled seats)
        if (this.filters.preferential.disabledSeats) {
          const hasDisabledSeats = train.tickets.some(t => /инвалид/i.test(t.type)) ||
            (train.amenities && train.amenities.includes("mdi-wheelchair-accessibility"));
          if (!hasDisabledSeats) {
            return false;
          }
        }

        return true;
      });
    },
    sortedTrains() {
      const sorted = [...this.filteredTrains];
      switch (this.sortBy) {
        case "departure":
          sorted.sort((a, b) => this.timeToMinutes(a.departureTime) - this.timeToMinutes(b.departureTime));
          break;
        case "arrival":
          sorted.sort((a, b) => this.timeToMinutes(a.arrivalTime) - this.timeToMinutes(b.arrivalTime));
          break;
        case "price":
          sorted.sort((a, b) => {
            const minA = Math.min(...a.tickets.map((t) => t.calculatedPrice));
            const minB = Math.min(...b.tickets.map((t) => t.calculatedPrice));
            return minA - minB;
          });
          break;
        case "duration":
          sorted.sort((a, b) => a.durationMinutes - b.durationMinutes);
          break;
      }
      return sorted;
    },
  },
  watch: {
    "filters.priceRange": {
      handler(val) {
        this.filters.priceMin = val[0];
        this.filters.priceMax = val[1];
        _logActivity(this, {
          type: "apply_filter",
          filter_type: "price",
          value: { min: val[0], max: val[1] },
        });
      },
    },
    "filters.durationRange": {
      handler(val) {
        this.filters.durationMin = val[0];
        this.filters.durationMax = val[1];
        _logActivity(this, {
          type: "apply_filter",
          filter_type: "duration",
          value: { min: val[0], max: val[1] },
        });
      },
    },
    "filters.departureRange": {
      handler(val) {
        this.filters.departureMin = val[0];
        this.filters.departureMax = val[1];
        _logActivity(this, {
          type: "apply_filter",
          filter_type: "departure_time",
          value: { min: val[0], max: val[1] },
        });
      },
    },
    "filters.arrivalRange": {
      handler(val) {
        this.filters.arrivalMin = val[0];
        this.filters.arrivalMax = val[1];
        _logActivity(this, {
          type: "apply_filter",
          filter_type: "arrival_time",
          value: { min: val[0], max: val[1] },
        });
      },
    },
    kvStoreReady(newVal) {
      if (newVal) {
        this.initializeFilters();
      }
    },
    "filters.preferential.disabledSeats": {
      handler(val) {
        _logActivity(this, {
          type: "apply_filter",
          filter_type: "preferential",
          value: { disabledSeats: val },
        });
      },
    },
  },
  methods: {
    startPageLoading() {
      if (this.pageLoadingTimeout) {
        clearTimeout(this.pageLoadingTimeout);
        this.pageLoadingTimeout = null;
      }
      this.pageLoading = true;
      this.pageLoadingTimeout = setTimeout(() => {
        this.pageLoading = false;
        this.pageLoadingTimeout = null;
      }, 200);
    },
    initializeFilters() {
      this.filters.priceRange = [...this.priceMinMax];
      this.filters.priceMin = this.priceMinMax[0];
      this.filters.priceMax = this.priceMinMax[1];
      this.filters.durationRange = [...this.durationMinMax];
      this.filters.durationMin = this.durationMinMax[0];
      this.filters.durationMax = this.durationMinMax[1];
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
    getTrackConfig() {
      this.$store.dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id }).then(() => {
        if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
          this.$router.push({ name: "not_found" });
          return;
        }
        const kvPath = this.testData.kv_store_path || "";
        if (kvPath) {
          this.$store.dispatch(GET_KV_STORE, { kvPath }).then(() => {
            this.kvStoreReady = true;
          });
        } else {
          this.kvStoreReady = true;
        }
        if (!this.trackConfig[this.$route.params.state_id]) {
          this.$router.push({ name: "state_not_found" });
        }
        this.applyStateDelay();
      });
    },
    parseQueryParams() {
      const query = this.$route.query;
      const hasAnyQuery =
        query.from != null ||
        query.to != null ||
        query.date != null ||
        query.returnDate != null ||
        query.adults != null ||
        query.children != null;

      // No default search params: only prefill if explicitly provided via URL query
      this.searchParams.from = query.from || "";
      this.searchParams.to = query.to || "";
      this.searchParams.departureDate = query.date || null;
      this.searchParams.returnDate = query.returnDate || null;

      const adults = Number.parseInt(query.adults);
      const children = Number.parseInt(query.children);
      this.searchParams.adults = Number.isFinite(adults) ? adults : 1;
      this.searchParams.children = Number.isFinite(children) ? children : 0;

      if (hasAnyQuery) {
        // If user navigated here with query params, treat it as an initial search state.
        this.activeSearchParams = {
          from: this.searchParams.from,
          to: this.searchParams.to,
          adults: this.searchParams.adults,
          children: this.searchParams.children,
        };
        this.hasPerformedSearch = true;
      } else {
        this.hasPerformedSearch = false;
      }
    },
    swapStations() {
      const temp = this.searchParams.from;
      this.searchParams.from = this.searchParams.to;
      this.searchParams.to = temp;
    },
    closeAllDropdowns() {
      this.showFromDropdown = false;
      this.showToDropdown = false;
    },
    handleOutsideClick(e) {
      if (this.$el && !this.$el.contains(e.target)) {
        this.closeAllDropdowns();
      }
    },
    onFromInput() {
      this.showFromDropdown = true;
      this.showToDropdown = false;
    },
    onToInput() {
      this.showToDropdown = true;
      this.showFromDropdown = false;
    },
    selectFromStation(station) {
      this.searchParams.from = station.name;
      this.showFromDropdown = false;
      this.showToDropdown = true;
      this.$refs.toInput?.focus();
    },
    selectToStation(station) {
      this.searchParams.to = station.name;
      this.showToDropdown = false;
    },
    performSearch() {
      // Imitate loading when submitting search
      this.startPageLoading();

      // Copy searchParams to activeSearchParams to trigger the search
      this.activeSearchParams = {
        from: this.searchParams.from,
        to: this.searchParams.to,
        adults: this.searchParams.adults,
        children: this.searchParams.children,
      };
      this.hasPerformedSearch = true;
      // Reinitialize filters based on new search
      this.initializeFilters();
      // Update URL with new search params
      this.$router.push({
        name: "bench_rail_search",
        params: {
          track_id: this.$route.params.track_id,
          state_id: this.$route.params.state_id,
        },
        query: {
          from: this.searchParams.from,
          to: this.searchParams.to,
          date: this.searchParams.departureDate,
          returnDate: this.searchParams.returnDate,
          adults: this.searchParams.adults,
          children: this.searchParams.children,
        },
      });
    },
    handleBuyClick(train) {
      // Get existing session to check if it's a return trip
      const existingSession = getRailBookingSession() || {};
      const isReturnTrip = !!existingSession.isReturnTrip;

      // Set up booking session
      const bookingSession = {
        train: {
          id: train.id,
          number: train.number,
          name: train.name,
          fromStation: train.fromStation,
          toStation: train.toStation,
          fromStationType: train.fromStationType,
          toStationType: train.toStationType,
          departureTime: train.departureTime,
          arrivalTime: train.arrivalTime,
          duration: train.duration,
          durationMinutes: train.durationMinutes,
          tickets: train.tickets,
          amenities: train.amenities,
          isBranded: train.isBranded,
        },
        from: this.activeSearchParams.from,
        to: this.activeSearchParams.to,
        departureDate: this.searchParams.departureDate,
        returnDate: this.searchParams.returnDate,
        adults: this.activeSearchParams.adults,
        children: this.activeSearchParams.children,
        isReturnTrip: isReturnTrip,
      };
      setRailBookingSession(bookingSession);

      // Log select_train event
      _logActivity(this, {
        type: "select_train",
        direction: isReturnTrip ? "return" : "outbound",
        train_id: train.id,
        train_number: train.number,
        train_name: train.name,
        from_station: train.fromStation,
        to_station: train.toStation,
        departure_time: train.departureTime,
        arrival_time: train.arrivalTime,
        duration: train.duration,
        is_branded: train.isBranded,
      });

      // Navigate to tariff selection
      this.$router.push({
        name: "bench_rail_tarif_selection",
        params: {
          track_id: this.$route.params.track_id,
          state_id: this.$route.params.state_id,
        }
      });
    },
    toggleFilter(filterName) {
      this.expandedFilters[filterName] = !this.expandedFilters[filterName];
    },
    handleSortChange(sortValue) {
      this.sortBy = sortValue;
      _logActivity(this, {
        type: "apply_sort",
        sort_type: sortValue,
      });
    },
    // Train Type filter methods
    onTrainTypeAnyChange() {
      if (this.filters.trainTypes.any) {
        // Reset all other type filters when "any" is selected
        this.filters.trainTypes.branded = false;
        this.filters.trainTypes.doubleDecked = false;
        this.filters.trainTypes.highSpeed = false;
      }
      _logActivity(this, {
        type: "apply_filter",
        filter_type: "train_type",
        value: "any",
      });
    },
    onTrainTypeChange() {
      // If any specific type is selected, uncheck "any"
      const hasSpecificType = this.filters.trainTypes.branded || this.filters.trainTypes.doubleDecked || this.filters.trainTypes.highSpeed;
      if (hasSpecificType) {
        this.filters.trainTypes.any = false;
      } else {
        // If all specific types are unchecked, check "any"
        this.filters.trainTypes.any = true;
      }
      const selectedTypes = [];
      if (this.filters.trainTypes.branded) selectedTypes.push("branded");
      if (this.filters.trainTypes.doubleDecked) selectedTypes.push("doubleDecked");
      if (this.filters.trainTypes.highSpeed) selectedTypes.push("highSpeed");
      _logActivity(this, {
        type: "apply_filter",
        filter_type: "train_type",
        value: selectedTypes,
      });
    },
    // Train Name filter methods
    onTrainNameAnyChange() {
      if (this.filters.trainNames.any) {
        // Reset all other name filters when "any" is selected
        this.filters.trainNames.noName = false;
        this.filters.trainNames.selected = [];
      }
      _logActivity(this, {
        type: "apply_filter",
        filter_type: "train_name",
        value: "any",
      });
    },
    onTrainNameChange() {
      // If any specific name filter is active, uncheck "any"
      const hasSpecificFilter = this.filters.trainNames.noName || this.filters.trainNames.selected.length > 0;
      if (hasSpecificFilter) {
        this.filters.trainNames.any = false;
      } else {
        this.filters.trainNames.any = true;
      }
      const selectedNames = [...this.filters.trainNames.selected];
      if (this.filters.trainNames.noName) selectedNames.push("noName");
      _logActivity(this, {
        type: "apply_filter",
        filter_type: "train_name",
        value: selectedNames,
      });
    },
    toggleTrainName(nameKey) {
      const index = this.filters.trainNames.selected.indexOf(nameKey);
      if (index === -1) {
        this.filters.trainNames.selected.push(nameKey);
      } else {
        this.filters.trainNames.selected.splice(index, 1);
      }
      this.onTrainNameChange();
    },
    getMinPriceForType(type) {
      const trains = this.searchedTrains.filter(train => {
        if (type === 'branded') return train.isBranded;
        if (type === 'doubleDecked') return train.isDoubleDecked;
        if (type === 'highSpeed') return train.isHighSpeed;
        return false;
      });
      if (trains.length === 0) return "";
      const minPrice = Math.min(...trains.flatMap(t => t.tickets.map(ticket => ticket.calculatedPrice)));
      return `от ${this.formatPrice(minPrice)}`;
    },
    // Car Classes filter methods
    onCarClassAnyChange() {
      if (this.filters.carClasses.any) {
        this.filters.carClasses.selected = [];
      }
      _logActivity(this, {
        type: "apply_filter",
        filter_type: "car_class",
        value: "any",
      });
    },
    toggleCarClass(classKey) {
      const index = this.filters.carClasses.selected.indexOf(classKey);
      if (index === -1) {
        this.filters.carClasses.selected.push(classKey);
      } else {
        this.filters.carClasses.selected.splice(index, 1);
      }
      // Update "any" checkbox based on selection
      if (this.filters.carClasses.selected.length > 0) {
        this.filters.carClasses.any = false;
      } else {
        this.filters.carClasses.any = true;
      }
      _logActivity(this, {
        type: "apply_filter",
        filter_type: "car_class",
        value: [...this.filters.carClasses.selected],
      });
    },
    // Services filter methods
    onServiceAnyChange() {
      if (this.filters.services.any) {
        this.filters.services.selected = [];
      }
      _logActivity(this, {
        type: "apply_filter",
        filter_type: "services",
        value: "any",
      });
    },
    toggleService(serviceKey) {
      const index = this.filters.services.selected.indexOf(serviceKey);
      if (index === -1) {
        this.filters.services.selected.push(serviceKey);
      } else {
        this.filters.services.selected.splice(index, 1);
      }
      // Update "any" checkbox based on selection
      if (this.filters.services.selected.length > 0) {
        this.filters.services.any = false;
      } else {
        this.filters.services.any = true;
      }
      _logActivity(this, {
        type: "apply_filter",
        filter_type: "services",
        value: [...this.filters.services.selected],
      });
    },
    // Reset all filters
    resetFilters() {
      // Reset price filter
      this.filters.priceRange = [...this.priceMinMax];
      this.filters.priceMin = this.priceMinMax[0];
      this.filters.priceMax = this.priceMinMax[1];
      // Reset duration filter
      this.filters.durationRange = [...this.durationMinMax];
      this.filters.durationMin = this.durationMinMax[0];
      this.filters.durationMax = this.durationMinMax[1];
      // Reset time filters
      this.filters.departureRange = [0, 1440];
      this.filters.departureMin = 0;
      this.filters.departureMax = 1440;
      this.filters.arrivalRange = [0, 1440];
      this.filters.arrivalMin = 0;
      this.filters.arrivalMax = 1440;
      // Reset train type filters
      this.filters.trainTypes.any = true;
      this.filters.trainTypes.branded = false;
      this.filters.trainTypes.doubleDecked = false;
      this.filters.trainTypes.highSpeed = false;
      // Reset train name filters
      this.filters.trainNames.any = true;
      this.filters.trainNames.noName = false;
      this.filters.trainNames.selected = [];
      // Reset car classes filter
      this.filters.carClasses.any = true;
      this.filters.carClasses.selected = [];
      // Reset services filter
      this.filters.services.any = true;
      this.filters.services.selected = [];
      // Reset preferential filter
      this.filters.preferential.disabledSeats = false;
      _logActivity(this, {
        type: "apply_filter",
        filter_type: "reset",
        value: "all",
      });
    },
    toggleInfoBanner() {
      this.infoExpanded = !this.infoExpanded;
    },
    formatDateShort(date) {
      if (!date) return "";
      const d = new Date(date);
      const day = d.getDate();
      const months = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"];
      const weekdays = ["вс", "пн", "вт", "ср", "чт", "пт", "сб"];
      return `${day} ${months[d.getMonth()]}, ${weekdays[d.getDay()]}`;
    },
    formatPrice(price) {
      return price.toLocaleString("ru-RU") + " ₽";
    },
    formatDuration(minutes) {
      const hours = Math.floor(minutes / 60);
      const mins = minutes % 60;
      return `${String(hours).padStart(2, "0")}ч ${String(mins).padStart(2, "0")}м`;
    },
    formatTimeMinutes(minutes) {
      const hours = Math.floor(minutes / 60) % 24;
      const mins = minutes % 60;
      return `${String(hours).padStart(2, "0")}ч ${String(mins).padStart(2, "0")}м`;
    },
    timeToMinutes(timeStr) {
      const [hours, minutes] = timeStr.split(":").map(Number);
      return hours * 60 + minutes;
    },
  },
  mounted() {
    // Imitate page loading in main content area
    this.startPageLoading();

    this.parseQueryParams();
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
    } else {
      const kvPath = this.testData.kv_store_path || "";
      if (kvPath && !this.kvStoreReady) {
        this.$store.dispatch(GET_KV_STORE, { kvPath }).then(() => {
          this.kvStoreReady = true;
        });
      } else if (!kvPath) {
        this.kvStoreReady = true;
      }
      this.applyStateDelay();
    }
    this.loggedIn = syncRailTicketLoggedInFromTrack(this.trackConfig);
    document.addEventListener("click", this.handleOutsideClick);
  },
  beforeUnmount() {
    if (this.pageLoadingTimeout) {
      clearTimeout(this.pageLoadingTimeout);
      this.pageLoadingTimeout = null;
    }
    document.removeEventListener("click", this.handleOutsideClick);
  },
});
</script>

<style src="@/assets/rail.css"></style>
<style scoped>
.bench-rail.rail-search-page {
  background: var(--bench-surface, #e9eaed);
  min-height: 100vh;
}

/* Make the ЖД search header full viewport width on this page only */
.rail-search-page :deep(.rail-header) {
  width: 100vw;
  margin-left: calc(50% - 50vw);
}

/* Constrain header inner content to 1600px on this page */
.rail-search-page :deep(.header-inner) {
  max-width: 1600px;
  margin: 0 auto;
}


/* Search Bar Section */
.search-bar-section {
  background: var(--bench-surface-elevated, #fff);
  max-width: 1260px;
  margin: 0 auto;
  margin-top: 20px;
}

.search-bar-inner {
  margin: 0 auto;
  padding: 12px 20px;
  background: var(--bench-surface, #e9eaed);
}

.search-bar-form {
  display: flex;
  align-items: center;
  gap: 0;
  background: var(--bench-surface-elevated, #fff);
}

.stations-group {
  position: relative;
  display: flex;
  flex: 3;
  min-width: 0;
}

.stations-group .search-field.station-field {
  flex: 1;
}

.stations-group .search-field.station-field:first-child {
  padding-right: 20px;
}

/* Override `.search-field:last-of-type` inside the stations group */
.stations-group .search-field.station-field:last-of-type {
  padding-left: 20px;
  border-right: 1px solid #e0e0e0;
}

.search-field {
  display: flex;
  align-items: center;
  padding: 18px 16px;
  border-right: 1px solid #e0e0e0;
  position: relative;
}

.search-field:last-of-type {
  border-right: none;
}

.search-field.station-field {
  flex: 1.5;
}

.search-field.date-field {
  flex: 1;
}

.search-field.passengers-field {
  flex: 1;
  gap: 8px;
  cursor: pointer;
}

.search-field input {
  border: none;
  outline: none;
  font-size: 18px;
  flex: 1;
  background: transparent;
  font-weight: 500;
}

.search-field .date-value {
  font-size: 18px;
  color: #000;
  font-weight: 500;
}

.search-field .passengers-text {
  font-size: 18px;
  color: #000;
  flex: 1;
  font-weight: 500;
}

.swap-btn {
  background: var(--bench-surface-elevated, #fff);
  border: none;
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  z-index: 5;
  width: 40px;
  height: 40px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #999;
}

.swap-btn:hover {
  color: #e21a1a;
}

.clear-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
  padding: 4px;
}

.search-field.date-field .clear-btn {
  margin-left: auto;
}

/* Station Dropdown */
.station-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--bench-surface-elevated, #fff);
  border: 1px solid #e0e0e0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 100;
  padding-bottom: 10px;
}

.dropdown-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 15px 10px 10px 10px;
  color: #999;
  font-size: 14px;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  cursor: pointer;
  font-size: 15px;
}

.dropdown-item:hover {
  background: var(--bench-primary-light, #f5f5f5);
}

.dropdown-item span {
  color: var(--bench-text, #333);
}

.search-btn {
  background: var(--bench-surface-elevated, #fff);
  border: none;
  border-left: 1px solid #e0e0e0;
  color: #e21a1a;
  font-size: 15px;
  font-weight: 600;
  padding: 22px 45px;
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.search-btn:hover {
  background: #e21a1a;
  color: #fff;
}

.hotel-link {
  margin-top: 0px;
  display: flex;
  justify-content: flex-end;
}

.hotel-link .travel-brand {
  color: var(--rail-red, #e21a1a);
  padding-left: 5px;
  font-weight: 500;
}

/* Info Banner */
.info-banner {
  background: var(--bench-primary-light, #fff3cd);
  border-bottom: 1px solid #e0e0e0;
}

.info-banner-inner {
  padding: 14px 20px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: var(--bench-surface-elevated, #fff);
  margin-bottom: 12px;
  cursor: pointer;
}

.info-banner-inner:focus-visible {
  outline: 2px solid rgba(226, 26, 26, 0.35);
  outline-offset: 2px;
}

.info-alert-badge {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--bench-surface-elevated, #fff);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.info-alert-icon {
  color: #ff7a00;
}

.info-banner-inner .info-text {
  flex: 1;
  position: relative;
}

.info-banner-inner .info-text strong {
  display: block;
  color: var(--bench-text, #000);
  margin-bottom: 4px;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
  font-size: 20px;
  font-weight: 500;
}

.info-banner-inner .info-text p {
  color: var(--bench-text-muted, #666);
  font-size: 14px;
  margin: 0;
  text-indent: 0;
}

.info-banner-inner .info-text.is-collapsed::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 18px;
  pointer-events: none;
  background: linear-gradient(to bottom, rgba(255, 255, 255, 0) 0%, var(--bench-surface-elevated, #fff) 85%);
}

.info-banner-inner .info-text p.info-text-collapsed {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
  line-clamp: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}

.info-banner-inner .info-toggle {
  cursor: pointer;
  user-select: none;
}

/* Main Content */
.search-content {
  max-width: 1260px;
  margin: 0 auto;
  padding: 20px;
  display: flex;
  gap: 20px;
}

.page-loading {
  flex: 1;
  width: 100%;
  min-height: 420px;
  background: var(--bench-surface, #e9eaed);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Filters Sidebar */
.filters-sidebar {
  width: 280px;
  flex-shrink: 0;
}

.favorites-card,
.bonus-card {
  background: var(--bench-surface-elevated, #fff);
  padding: 16px;
  margin-bottom: 16px;
  border-radius: 0;
}

.favorites-header,
.bonus-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.favorites-header h4,
.bonus-header h4 {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
  color: #000;
}

.favorites-list {
  list-style: disc;
  padding-left: 20px;
  margin: 0 0 12px;
  font-size: 14px;
  color: #666;
}

.favorites-list li {
  margin-bottom: 4px;
}

.favorites-login {
  font-size: 13px;
  color: #666;
  margin-bottom: 12px;
}

.bonus-card p {
  font-size: 13px;
  color: #666;
  margin: 0 0 12px;
  text-indent: 0;
}

.login-btn {
  background: var(--bench-surface-elevated, #fff);
  border: 1px solid #e21a1a;
  color: #e21a1a;
  padding: 8px 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 20px;
}

.login-btn:hover {
  background: #e21a1a;
  color: #fff;
}

.save-route-btn {
  background: var(--bench-primary-light, #f5f5f5);
  border: none;
  color: #e21a1a;
  padding: 12px 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
}

.save-route-btn:hover {
  background: var(--bench-border, #ededed);
}

/* Filters Section */
.filters-section {
  background: var(--bench-surface-elevated, #fff);
  padding: 0px;
}

.filter-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 15px;
  font-size: 14px;
  color: #111;
  font-weight: 500;
}

.filter-header .trips-count {
  color: #777;
}

.filter-group {
  border-top: 1px solid #e0e0e0;
  padding: 25px 25px;
}

.filter-group:first-child {
  border-top: none;
}

.filter-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  letter-spacing: 0.5px;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
}

.filter-content {
  padding-top: 12px;
}

/* Filter Checkboxes */
.filter-checkboxes {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-checkbox {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
}

.filter-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: #e21a1a;
  cursor: pointer;
  flex-shrink: 0;
}

.filter-checkbox .checkbox-label {
  flex: 1;
}

.filter-checkbox .checkbox-price {
  color: #999;
  font-size: 13px;
  white-space: nowrap;
}

/* Filter Reset Button */
.filter-reset {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0;
  border-top: 1px solid #e0e0e0;
  margin-top: 8px;
  cursor: pointer;
  color: #e21a1a;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.filter-reset:hover {
  color: #b01515;
}

.range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 16px;
  color: #666;
  margin-bottom: 10px;
  margin-top: 5px;
}

/* Results Area */
.results-area {
  flex: 1;
}

.sort-options {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.sort-btn {
  background: none;
  padding: 8px 16px;
  font-size: 14px;
  color: #000;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  border-radius: 20px;
}

.sort-btn.active {
  color: var(--bench-primary, #e21a1a);
  background: var(--bench-surface-elevated, #fff);
}

.sort-btn:hover {
  color: #e21a1a;
}

/* Loading */
.loading-container {
  display: flex;
  justify-content: center;
  padding: 60px;
}

/* Train Card */
.train-card {
  background: var(--bench-surface-elevated, #fff);
  padding: 20px 30px;
  margin-bottom: 20px;
  position: relative;
  cursor: pointer;
  transition: box-shadow 160ms ease, transform 160ms ease;
  will-change: box-shadow, transform;
}

.train-card:hover {
  box-shadow: 0 10px 26px rgba(0, 0, 0, 0.12);
}

.train-card:focus-visible {
  outline: 2px solid rgba(226, 26, 26, 0.35);
  outline-offset: 2px;
  box-shadow: 0 10px 26px rgba(0, 0, 0, 0.12);
}

.branded-badge {
  display: inline-block;
  position: relative;
  margin-bottom: 10px;
  border-radius: 5px;
  background: #e21a1a;
  color: #fff;
  font-size: 12px;
  font-weight: 400;
  padding: 4px 4px;
}

.train-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  padding-top: 8px;
}

.train-info {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 14px;
  color: #666;
}

.train-number {
  font-weight: 600;
  color: #000;
}

.train-name {
  color: #666;
}

.train-route {
  color: #666;
}

.route-link {
  color: #e21a1a;
  text-decoration: none;
  margin-left: 8px;
}

.route-link:hover {
  text-decoration: underline;
}

/* Train Card Body - Two Column Layout */
.train-card-body {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding-top: 15px;
}

.train-card-left {
  flex: 1;
  min-width: 0;
}

.train-card-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 16px;
  flex-shrink: 0;
  border-left: 1px solid #e0e0e0;
  padding-left: 24px;
}

/* Train Times */
.train-times {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 16px;
}

.train-times-top {
  display: flex;
  align-items: end;
  gap: 15px;
  justify-content: space-between;
}

.train-times-bottom {
  display: flex;
  align-items: flex-start;
  gap: 24px;
}

.departure,
.arrival {
  display: flex;
  flex-direction: column;
}

.arrival {
  align-items: flex-end;
}

.departure .time,
.arrival .time {
  font-size: 32px;
  font-weight: 500;
  color: #000;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
}

.station-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.train-times-bottom .station-info:last-child {
  align-items: flex-end;
}

.station-type {
  font-size: 12px;
  color: #999;
}

.station-name {
  font-size: 12px;
  color: #111;
  font-weight: 600;
}

.duration {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 260px;
  min-width: 120px;
}

.duration-line {
  display: flex;
  align-items: center;
  width: 100%;
}

.duration-line .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #e21a1a;
}

.duration-line .line {
  flex: 1;
  height: 2px;
  background: #e21a1a;
}

.duration-spacer {
  flex: 1;
  max-width: 200px;
  min-width: 120px;
}

.duration-text {
  font-size: 12px;
  color: #999;
  text-align: center;
  white-space: nowrap;
  line-height: 1.2;
  margin-top: 2px;
}

/* Amenities */
.train-amenities {
  display: flex;
  gap: 15px;
  margin-bottom: 16px;
}

/* Ticket Classes - Right Side */
.ticket-classes {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ticket-class {
  display: flex;
  align-items: center;
  gap: 24px;
  min-width: 320px;
  justify-content: space-between;
}

.ticket-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ticket-type {
  font-size: 14px;
  color: #333;
}

.ticket-seats {
  font-size: 14px;
  color: #999;
}

.ticket-price {
  font-size: 14px;
  font-weight: 500;
  color: #e21a1a;
  white-space: nowrap;
}

/* Wait List */
.wait-list {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--bench-text-muted, #666);
  padding: 8px 12px;
  background: var(--bench-surface-elevated, #f5f5f5);
  width: fit-content;
  border-radius: 4px;
}

/* Buy Button */
.buy-btn {
  background: var(--bench-surface-elevated, #fff);
  border: 1px solid #e21a1a;
  color: #e21a1a;
  padding: 6px 15px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  border-radius: 20px;

}

.buy-btn:hover {
  background: #e21a1a;
  color: #fff;
}
</style>
