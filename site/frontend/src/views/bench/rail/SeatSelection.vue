<template>
  <div class="bench-rail rail-seat-page rail-gray-bg">
    <div v-if="!configLoaded" class="loading-box">
      <v-progress-circular indeterminate color="#e21a1a" :size="48"></v-progress-circular>
    </div>

    <template v-else>
      <!-- Header -->
      <RailSearchHeader :rail-logo="railLogo" :is-logged-in="loggedIn" :user-name="currentUserName" @open-login="openLoginDrawer" @logout="handleLogout" />

      <!-- Main Content -->
      <main class="seat-main">
        <div class="seat-container">
          <div class="top-card">
            <!-- Back button and steps -->
            <div class="booking-header">
              <button class="back-btn" @click="goBack">
                <v-icon size="24">mdi-arrow-left</v-icon>
              </button>
              <div class="steps-indicator">
                <span v-for="step in 7" :key="step" class="step" :class="getStepClass(step)">{{ step }}</span>
              </div>
            </div>

            <!-- Title -->
            <h2 class="seat-title">
              Выберите до {{ maxSeats }} мест или <a href="#" class="params-link">задайте параметры</a>
            </h2>

            <!-- Train Info -->
            <div class="train-info">
              <img :src="sapsanLogo" alt="экспресс" class="sapsan-logo" />
              <span class="train-number">{{ train.number }}</span>
              <span class="train-name">{{ train.name }}</span>
              <span class="train-route">{{ train.fromStation }} — {{ train.toStation }}</span>
              <span class="train-departure">, отпр. {{ train.departureTime }}, {{ formatDateShort(departureDate) }}</span>
            </div>
          </div>

          <!-- Carriage Section -->
          <div class="carriage-card">
            <!-- Carriage Header -->
            <div class="carriage-header">
              <div class="carriage-info">
                <span class="carriage-title">Вагон {{ activeCarriage.number }}</span>
                <span class="carriage-subtitle">Нумерация вагонов с головы поезда</span>
              </div>
              <div class="direction-indicator">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M19 12H5M5 12L11 6M5 12L11 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span>Направление движения</span>
              </div>
              <div class="carriage-actions">
                <button class="action-btn" title="QR код">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <rect x="3" y="3" width="7" height="7" stroke="currentColor" stroke-width="2"/>
                    <rect x="14" y="3" width="7" height="7" stroke="currentColor" stroke-width="2"/>
                    <rect x="3" y="14" width="7" height="7" stroke="currentColor" stroke-width="2"/>
                    <rect x="14" y="14" width="3" height="3" fill="currentColor"/>
                    <rect x="18" y="18" width="3" height="3" fill="currentColor"/>
                  </svg>
                </button>
                <button class="action-btn" title="Список">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path d="M8 6H21M8 12H21M8 18H21M3 6H3.01M3 12H3.01M3 18H3.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                </button>
                <button class="action-btn" title="Развернуть">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path d="M15 3H21V9M9 21H3V15M21 3L14 10M3 21L10 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button>
              </div>
            </div>

            <!-- Seat Diagram - SVG Carriage Layout -->
            <div class="seat-diagram-wrapper">
              <svg class="carriage-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2420 336" preserveAspectRatio="xMidYMid meet">
                <!-- Background -->
                <path class="carriage-bg" d="M9.301,326.753C10.106,327.546,11.165,328,12.3,328H2407.7c1.143,0,2.21-0.459,3.017-1.265l0.017-0.016c0.806-0.806,1.266-1.872,1.266-3.014V12.296c0-1.143-0.46-2.208-1.266-3.014l-0.017-0.016c-0.806-0.806-1.874-1.265-3.017-1.265H12.3c-1.145,0-2.213,0.462-2.968,1.216L9.316,9.233C8.503,10.059,8,11.128,8,12.296v311.408C8,324.866,8.497,325.928,9.301,326.753z"/>

                <!-- Color zones for special compartments -->
                <rect x="402" y="8" class="color-zone" width="113" height="116"/>
                <rect x="1890" y="8" class="color-zone" width="215" height="320"/>

                <!-- Carriage outline -->
                <path class="carriage-outline" d="M2416.391,3.625l-0.017-0.016c-2.228-2.225-5.298-3.608-8.673-3.608L12.3,0C8.924,0,5.853,1.384,3.626,3.608L3.61,3.625C1.384,5.852,0,8.921,0,12.296l0,311.408c0,3.375,1.384,6.444,3.61,8.671l0.016,0.016C5.853,334.616,8.924,336,12.299,336H2407.7c3.376,0,6.446-1.384,8.674-3.609l0.017-0.016c2.225-2.227,3.609-5.297,3.609-8.671V12.296C2420,8.921,2418.616,5.852,2416.391,3.625z M2412,323.704c0,1.143-0.46,2.208-1.266,3.014l-0.016,0.016c-0.806,0.806-1.874,1.265-3.017,1.265H12.299c-1.135,0-2.193-0.454-2.999-1.247C8.497,325.928,8,324.865,8,323.704V12.296c0-1.169,0.503-2.237,1.316-3.064l0.016-0.016C10.087,8.462,11.155,8,12.3,8l2395.401,0c1.143,0,2.21,0.459,3.017,1.265l0.016,0.016c0.806,0.806,1.266,1.872,1.266,3.014V323.704z"/>

                <!-- Compartment dividers -->
                <path class="compartment-dividers" d="M2264,208h6v120h-6V208z M2264,8v114h-152V8h-6v112v8v0h164v0v-8V8H2264z M396,8.001v110H156v-110h-6v108v8h8h236h8v-8v-108H396z M372.494,218.825l-1.976,5.637c8.057,3.968,17.425,9.49,25.482,14.537v89h6v-82.92l0.007-9.52C392.205,229.216,382.368,223.643,372.494,218.825z M186.927,216.188c-12.253,5.381-24.558,11.837-36.913,19.371H150V328h6v-88.666c10.54-6.239,22.506-12.526,33.021-17.174L186.927,216.188z M283.173,196l-6,0.01c0,0-22.139,1.02-32.768,2.772l1.898,5.414c9.699-1.529,21.183-2.082,30.87-2.169V328h6V202.118c9.606,0.313,20.937,1.265,30.534,3.036l1.949-5.559C305.201,197.601,283.173,196,283.173,196z"/>

                <!-- Interactive Seats -->
                <g class="seats-group">
                  <g v-for="seat in activeCarriage.seats" :key="seat.number"
                     class="seat-wrapper"
                     :class="getSeatClass(seat)"
                     @click="toggleSeat(seat)"
                     :transform="getSeatTransform(seat.number)">
                    <path class="seat-path" :d="getSeatPath(seat.number)"/>
                    <text class="seat-number" :x="getSeatTextX(seat.number)" :y="getSeatTextY(seat.number)">{{ seat.number }}</text>
                  </g>
                </g>

                <!-- Tables -->
                <g class="tables-group">
                  <path class="table" d="M581,13h48v72c0,8.8-7.2,16-16,16h-16c-8.8,0-16-7.2-16-16V13z"/>
                  <path class="table" d="M581,328h48v-72c0-8.8-7.2-16-16-16h-16c-8.8,0-16,7.2-16,16V328z"/>
                  <path class="table" d="M1561,323h48v-72c0-8.8-7.2-16-16-16h-16c-8.8,0-16,7.2-16,16V323z"/>
                  <path class="table" d="M1561,13h48v72c0,8.8-7.2,16-16,16h-16c-8.8,0-16-7.2-16-16V13z"/>
                  <rect x="880" y="235" class="table" width="160" height="88"/>
                  <rect x="2106" y="213" class="table" width="153" height="110"/>
                </g>

                <!-- Windows -->
                <g class="windows-group">
                  <line x1="2388" y1="4" x2="2294" y2="4"/>
                  <line x1="126" y1="4" x2="32" y2="4"/>
                  <line x1="613" y1="4" x2="467" y2="4"/>
                  <line x1="857" y1="4" x2="711" y2="4"/>
                  <line x1="1239" y1="4" x2="1093" y2="4"/>
                  <line x1="1660" y1="4" x2="1514" y2="4"/>
                  <line x1="1439" y1="4" x2="1293" y2="4"/>
                  <line x1="1873" y1="4" x2="1727" y2="4"/>
                  <line x1="2088" y1="4" x2="1942" y2="4"/>
                  <line x1="2388" y1="332" x2="2294" y2="332"/>
                  <line x1="126" y1="332" x2="32" y2="332"/>
                  <line x1="674" y1="332" x2="528" y2="332"/>
                  <line x1="868" y1="332" x2="722" y2="332"/>
                  <line x1="1239" y1="332" x2="1093" y2="332"/>
                  <line x1="1660" y1="332" x2="1514" y2="332"/>
                  <line x1="1439" y1="332" x2="1293" y2="332"/>
                  <line x1="1873" y1="332" x2="1727" y2="332"/>
                  <line x1="2088" y1="332" x2="1942" y2="332"/>
                </g>

                <!-- Service Icons -->
                <g class="icons-group">
                  <!-- Exit icons -->
                  <path class="icon exit" d="M84.232,22.861v19.712L92.962,48V18.308L84.232,22.861z M73.847,22.656c1.282-0.031,2.302-1.097,2.271-2.381c-0.032-1.288-1.101-2.304-2.384-2.274c-1.283,0.031-2.301,1.097-2.27,2.385C71.496,21.67,72.563,22.687,73.847,22.656z M67.453,26.804l-2.235,5.53c-0.406,0.922-0.14,1.841,0.948,2.185l0.586,0.129l2.66-6.449h0.003c0.237-0.496,0.614-0.908,1.068-1.232l-0.495,6.886l-0.007,0.003l-1.016,7.028l-3.026,4.293c0,0-0.374,0.587-0.004,1.303c0.254,0.49,1.285,1.222,1.285,1.222l4.686-6.262l1.108-6.596c0.063-0.004,0.127-0.008,0.195-0.014l-0.01,0.009l3.272,11.575c0,0,0.123,0.728,0.508,1.071c0.435,0.397,1.082,0.408,1.082,0.408l1.404-0.211L75.888,33.41c0-1.499,0.009-4.972,0.009-6.506c0-2.055-0.54-3.172-3.09-3.39C72.205,23.468,69.084,22.866,67.453,26.804z M80.699,33.234l0.147-0.296l-3.995-2.758l-0.103,2.58l1.995,1.184C79.579,34.328,80.214,34.214,80.699,33.234z"/>
                  <path class="icon exit" d="M37.194,157.861v19.712l8.73,5.427v-29.692L37.194,157.861z M26.809,157.656c1.282-0.031,2.302-1.097,2.271-2.381c-0.032-1.288-1.101-2.304-2.384-2.274c-1.283,0.031-2.301,1.097-2.27,2.385C24.457,156.67,25.524,157.687,26.809,157.656z M20.415,161.804l-2.235,5.53c-0.406,0.922-0.14,1.841,0.948,2.185l0.586,0.129l2.66-6.449h0.003c0.237-0.496,0.614-0.908,1.068-1.232l-0.495,6.886l-0.007,0.003l-1.016,7.028l-3.026,4.293c0,0-0.374,0.587-0.004,1.303c0.254,0.49,1.285,1.222,1.285,1.222l4.686-6.262l1.108-6.596c0.063-0.004,0.127-0.008,0.195-0.014l-0.01,0.009l3.272,11.575c0,0,0.123,0.728,0.508,1.071c0.435,0.397,1.082,0.408,1.082,0.408l1.404-0.211l-3.576-14.272c0-1.499,0.009-4.972,0.009-6.506c0-2.055-0.54-3.172-3.09-3.39C25.166,158.468,22.045,157.866,20.415,161.804z M33.661,168.234l0.147-0.296l-3.995-2.758l-0.103,2.58l1.995,1.184C32.54,169.328,33.175,169.214,33.661,168.234z"/>
                  <path class="icon exit" d="M84.232,292.861v19.712l8.73,5.427v-29.692L84.232,292.861z M73.847,292.656c1.282-0.031,2.302-1.097,2.271-2.381c-0.032-1.288-1.101-2.304-2.384-2.274c-1.283,0.031-2.301,1.097-2.27,2.385C71.496,291.67,72.563,292.687,73.847,292.656z M67.453,296.804l-2.235,5.53c-0.406,0.922-0.14,1.841,0.948,2.185l0.586,0.129l2.66-6.449h0.003c0.237-0.496,0.614-0.908,1.068-1.232l-0.495,6.886l-0.007,0.003l-1.016,7.028l-3.026,4.293c0,0-0.374,0.587-0.004,1.303c0.254,0.49,1.285,1.222,1.285,1.222l4.686-6.262l1.108-6.596c0.063-0.004,0.127-0.008,0.195-0.014l-0.01,0.009l3.272,11.575c0,0,0.123,0.728,0.508,1.071c0.435,0.397,1.082,0.408,1.082,0.408l1.404-0.211l-3.576-14.272c0-1.499,0.009-4.972,0.009-6.506c0-2.055-0.54-3.172-3.09-3.39C72.205,293.468,69.084,292.866,67.453,296.804z M80.699,303.234l0.147-0.296l-3.995-2.758l-0.103,2.58l1.995,1.184C79.579,304.328,80.214,304.214,80.699,303.234z"/>
                  <path class="icon exit" d="M2393.271,157.861v19.712L2402,183v-29.692L2393.271,157.861z M2382.885,157.656c1.282-0.031,2.302-1.097,2.271-2.381c-0.032-1.288-1.101-2.304-2.384-2.274c-1.283,0.031-2.301,1.097-2.27,2.385C2380.534,156.67,2381.601,157.687,2382.885,157.656z M2376.491,161.804l-2.235,5.53c-0.406,0.922-0.139,1.841,0.948,2.185l0.586,0.129l2.66-6.449h0.003c0.237-0.496,0.614-0.908,1.068-1.232l-0.495,6.886l-0.007,0.003l-1.016,7.028l-3.026,4.293c0,0-0.374,0.587-0.004,1.303c0.254,0.49,1.285,1.222,1.285,1.222l4.686-6.262l1.107-6.596c0.063-0.004,0.127-0.008,0.196-0.014l-0.01,0.009l3.272,11.575c0,0,0.123,0.728,0.508,1.071c0.435,0.397,1.082,0.408,1.082,0.408l1.404-0.211l-3.576-14.272c0-1.499,0.009-4.972,0.009-6.506c0-2.055-0.54-3.172-3.09-3.39C2381.243,158.468,2378.122,157.866,2376.491,161.804z M2389.738,168.234l0.146-0.296l-3.995-2.758l-0.103,2.58l1.995,1.184C2388.617,169.328,2389.252,169.214,2389.738,168.234z"/>

                  <!-- WC labels -->
                  <text class="wc-text" x="225" y="276">WC</text>
                  <text class="wc-text" x="347" y="276">WC</text>

                  <!-- Baggage icons -->
                  <path class="icon baggage" d="M444.634,38.443c-0.687,0.683-0.941,1.477-1.036,2.248c-0.054,0.447-0.054,0.888-0.054,1.298v15.438c0,0.403,0,0.844,0.054,1.297c0.095,0.765,0.349,1.56,1.036,2.244c1.085,1.099,2.451,1.099,3.544,1.099h0.64V37.348h-0.64C447.085,37.348,445.719,37.348,444.634,38.443z M473.402,40.69c-0.095-0.77-0.347-1.565-1.033-2.248c-1.088-1.094-2.454-1.094-3.545-1.094h-0.64v24.718h0.64c1.09,0,2.456,0,3.545-1.099c0.687-0.684,0.938-1.478,1.033-2.244c0.053-0.453,0.053-0.894,0.053-1.297V41.988C473.456,41.578,473.456,41.137,473.402,40.69z M462.907,34.18c0-1.164-0.95-2.114-2.117-2.114h-4.585c-1.158,0-2.109,0.949-2.109,2.114v3.168h-3.517v24.711h15.835V37.348h-3.508V34.18z M461.033,37.351h-5.069v-3.359h5.069V37.351z"/>
                  <path class="icon baggage" d="M2167.634,259.376c-0.687,0.683-0.941,1.477-1.036,2.248c-0.054,0.447-0.054,0.888-0.054,1.298v15.438c0,0.403,0,0.844,0.054,1.297c0.095,0.765,0.349,1.56,1.036,2.244c1.085,1.099,2.451,1.099,3.544,1.099h0.639v-24.718h-0.639C2170.084,258.282,2168.719,258.282,2167.634,259.376z M2196.402,261.624c-0.095-0.77-0.346-1.565-1.033-2.248c-1.088-1.095-2.454-1.095-3.545-1.095h-0.64V283h0.64c1.091,0,2.456,0,3.545-1.099c0.687-0.684,0.938-1.478,1.033-2.244c0.053-0.453,0.053-0.894,0.053-1.297v-15.438C2196.456,262.512,2196.456,262.071,2196.402,261.624z M2185.906,255.113c0-1.164-0.95-2.114-2.117-2.114h-4.584c-1.158,0-2.109,0.949-2.109,2.114v3.168h-3.517v24.711h15.835v-24.711h-3.508V255.113z M2184.033,258.285h-5.069v-3.359h5.069V258.285z"/>

                  <!-- Settings icons -->
                  <path class="icon settings" d="M287.148,63.455c0.06-0.48,0.105-0.96,0.105-1.455c0-0.495-0.045-0.99-0.105-1.5l3.165-2.445c0.285-0.225,0.36-0.63,0.18-0.96l-3-5.19c-0.18-0.33-0.585-0.465-0.915-0.33l-3.735,1.5c-0.78-0.585-1.59-1.095-2.535-1.47l-0.555-3.975c-0.06-0.36-0.375-0.63-0.75-0.63h-6c-0.375,0-0.69,0.27-0.75,0.63l-0.555,3.975c-0.945,0.375-1.755,0.885-2.535,1.47l-3.735-1.5c-0.33-0.135-0.735,0-0.915,0.33l-3,5.19c-0.195,0.33-0.105,0.735,0.18,0.96l3.165,2.445c-0.06,0.51-0.105,1.005-0.105,1.5c0,0.495,0.045,0.975,0.105,1.455l-3.165,2.49c-0.285,0.225-0.375,0.63-0.18,0.96l3,5.19c0.18,0.33,0.585,0.45,0.915,0.33l3.735-1.515c0.78,0.6,1.59,1.11,2.535,1.485l0.555,3.975c0.06,0.36,0.375,0.63,0.75,0.63h6c0.375,0,0.69-0.27,0.75-0.63l0.555-3.975c0.945-0.39,1.755-0.885,2.535-1.485l3.735,1.515c0.33,0.12,0.735,0,0.915-0.33l3-5.19c0.18-0.33,0.105-0.735-0.18-0.96L287.148,63.455z M276.003,67.25c-2.899,0-5.25-2.351-5.25-5.25c0-2.899,2.351-5.25,5.25-5.25s5.25,2.351,5.25,5.25C281.253,64.899,278.903,67.25,276.003,67.25z"/>
                  <path class="icon settings" d="M2199.148,65.454c0.06-0.48,0.105-0.96,0.105-1.455c0-0.495-0.045-0.99-0.105-1.5l3.165-2.445c0.285-0.225,0.36-0.63,0.18-0.96l-3-5.19c-0.18-0.33-0.585-0.465-0.915-0.33l-3.735,1.5c-0.78-0.585-1.59-1.095-2.535-1.47l-0.555-3.975c-0.06-0.36-0.375-0.63-0.75-0.63h-6c-0.375,0-0.69,0.27-0.75,0.63l-0.555,3.975c-0.945,0.375-1.755,0.885-2.535,1.47l-3.735-1.5c-0.33-0.135-0.735,0-0.915,0.33l-3,5.19c-0.195,0.33-0.105,0.735,0.18,0.96l3.165,2.445c-0.06,0.51-0.105,1.005-0.105,1.5c0,0.495,0.045,0.975,0.105,1.455l-3.165,2.49c-0.285,0.225-0.375,0.63-0.18,0.96l3,5.19c0.18,0.33,0.585,0.45,0.915,0.33l3.735-1.515c0.78,0.6,1.59,1.11,2.535,1.485l0.555,3.975c0.06,0.36,0.375,0.63,0.75,0.63h6c0.375,0,0.69-0.27,0.75-0.63l0.555-3.975c0.945-0.39,1.755-0.885,2.535-1.485l3.735,1.515c0.33,0.12,0.735,0,0.915-0.33l3-5.19c0.18-0.33,0.105-0.735-0.18-0.96L2199.148,65.454z M2188.003,69.249c-2.899,0-5.25-2.351-5.25-5.25s2.351-5.25,5.25-5.25s5.25,2.351,5.25,5.25S2190.902,69.249,2188.003,69.249z"/>
                </g>
              </svg>
            </div>

            <!-- Carriage Tabs -->
            <div class="carriage-tabs">
              <button
                v-for="carriage in carriages"
                :key="carriage.id"
                class="carriage-tab"
                :class="{ active: activeCarriageId === carriage.id }"
                @click="selectCarriage(carriage.id)"
              >
                <span class="tab-label">ВАГОН {{ carriage.number }}</span>
                <span class="tab-seats">{{ carriage.availableSeats }} {{ getSeatsLabel(carriage.availableSeats) }}</span>
                <span v-if="getSelectedSeatsInCarriage(carriage.id).length > 0" class="tab-badge">
                  {{ getSelectedSeatsInCarriage(carriage.id).length }}
                </span>
              </button>
            </div>

            <!-- Legend -->
            <div class="seat-legend">
              <div class="legend-items">
                <div class="legend-item">
                  <span class="legend-color free"></span>
                  <span class="legend-text">Свободное</span>
                </div>
                <div class="legend-item">
                  <span class="legend-color occupied"></span>
                  <span class="legend-text">Занятое место</span>
                </div>
                <div class="legend-item">
                  <span class="legend-color selected"></span>
                  <span class="legend-text">Выбранное</span>
                </div>
                <div class="legend-item">
                  <span class="legend-color filtered"></span>
                  <span class="legend-text">Не соответствует фильтру</span>
                </div>
                <div class="legend-item">
                  <span class="legend-color pet"></span>
                  <span class="legend-text">Место с животным</span>
                </div>
                <!-- <div class="legend-item">
                  <span class="legend-color non-refundable"></span>
                  <span class="legend-text">Невозвратный билет</span>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" class="info-icon">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
                  </svg>
                </div> -->
              </div>
              <button class="all-marks-btn">Все обозначения</button>
            </div>

            <!-- Carriage Details -->
            <div class="carriage-details">
              <div class="details-header">
                <span class="details-carriage">Вагон {{ activeCarriage.number }}</span>
                <span class="details-separator">·</span>
                <span class="details-class">{{ selectedClassName }} {{ selectedClassCode }}</span>
                <span class="details-separator">·</span>
                <span class="details-type">{{ activeCarriage.type }}</span>
              </div>

              <div class="amenities">
                <div v-for="amenity in carriageAmenities" :key="amenity.icon" class="amenity" :title="amenity.name">
                  <v-icon size="26">{{ amenity.icon }}</v-icon>
                </div>
              </div>

              <div class="carriage-photos">
                <img
                  v-for="(photo, idx) in carriagePhotos.slice(0, 7)"
                  :key="idx"
                  :src="photo"
                  class="carriage-photo"
                  :class="{ active: idx === 0 }"
                  :alt="'Фото ' + (idx + 1)"
                />
                <button v-if="carriagePhotos.length > 9" class="more-photos-btn">
                  Ещё {{ carriagePhotos.length - 9 }} фото
                </button>
              </div>
            </div>

            <!-- Continue Button -->
            <div class="seat-continue-bar">
              <div class="seat-continue-info">
                <span>Выбрано </span>
                <span class="seat-continue-accent">{{ selectedSeats.length }}</span>
                <span> {{ getSeatsLabel(selectedSeats.length) }} </span>
                <span class="seat-continue-accent">{{ formatPrice(totalPrice) }}</span>
              </div>
              <button class="continue-btn" :disabled="selectedSeats.length === 0" @click="continueBooking">
                Продолжить
              </button>
            </div>
          </div>
        </div>
      </main>

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

export default defineComponent({
  name: "RailSeatSelection",
  mixins: [benchUserContextMixin,StateDelayMixin],
  components: { RailSearchHeader, RailLoginDrawer },
  data() {
    return {
      loginDrawer: false,
      loggedIn: false,
      maxSeats: 9,
      activeCarriageId: "car_03",
      selectedSeats: [],
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
    railLogo() {
      return railAssets["rail_logo"] || "";
    },
    sapsanLogo() {
      return railAssets["sapsan_logo"] || "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='20' viewBox='0 0 60 20'%3E%3Ctext x='0' y='15' fill='%23e21a1a' font-family='Arial' font-weight='bold' font-size='12'%3Eэкспресс%3C/text%3E%3C/svg%3E";
    },
    bookingSession() {
      return getRailBookingSession() || {};
    },
    train() {
      return this.bookingSession.train || {
        id: "train_754",
        number: "754",
        name: "«экспресс»",
        fromStation: "Москва Октябрьская",
        toStation: "Санкт-Петербург-Главный",
        departureTime: "05:45",
      };
    },
    departureDate() {
      return this.bookingSession.departureDate || new Date().toISOString().split('T')[0];
    },
    selectedClass() {
      return this.bookingSession.selectedClass || { type: "econom", name: "Эконом" };
    },
    selectedClassName() {
      return this.selectedClass.name || "Эконом";
    },
    selectedClassCode() {
      return "2С 2Ж";
    },
    pricePerSeat() {
      return this.selectedClass.price || 3500;
    },
    totalPrice() {
      return this.selectedSeats.length * this.pricePerSeat;
    },
    carriages() {
      return [
        { id: "car_03", number: "03", availableSeats: 62, type: "ДОСС" },
        { id: "car_06", number: "06", availableSeats: 52, type: "ДОСС" },
        { id: "car_07", number: "07", availableSeats: 62, type: "ДОСС" },
        { id: "car_08", number: "08", availableSeats: 64, type: "ДОСС" },
        { id: "car_09", number: "09", availableSeats: 64, type: "ДОСС" },
      ];
    },
    activeCarriage() {
      const carriage = this.carriages.find(c => c.id === this.activeCarriageId) || this.carriages[0];
      const occupiedSeats = this.generateOccupiedSeats(carriage.id, 66 - carriage.availableSeats);

      // Generate flat list of seats for SVG compartment layout
      const createSeat = (number) => ({
        number,
        carriageId: carriage.id,
        isOccupied: occupiedSeats.includes(number),
        isNonRefundable: number % 11 === 0,
        hasPet: number === 41 || number === 42,
        price: this.pricePerSeat
      });

      // Create all 66 seats
      const seats = [];
      for (let i = 1; i <= 66; i++) {
        seats.push(createSeat(i));
      }

      return {
        ...carriage,
        seats,
      };
    },
    // Seat position data for SVG layout
    seatPositions() {
      // Map seat numbers to their SVG coordinates (x, y positions for rendering)
      // Based on the original SVG seat paths
      return {
        1: { x: 2071, y: 304, row: 'bottom', facing: 'right' },
        2: { x: 2071, y: 254, row: 'bottom', facing: 'right' },
        3: { x: 2071, y: 44, row: 'top', facing: 'right' },
        4: { x: 2071, y: 94, row: 'top', facing: 'right' },
        5: { x: 1965, y: 304, row: 'bottom', facing: 'right' },
        6: { x: 1965, y: 254, row: 'bottom', facing: 'right' },
        7: { x: 1965, y: 44, row: 'top', facing: 'right' },
        8: { x: 1965, y: 94, row: 'top', facing: 'right' },
        9: { x: 1858, y: 304, row: 'bottom', facing: 'right' },
        10: { x: 1853, y: 254, row: 'bottom', facing: 'right' },
        11: { x: 1853, y: 44, row: 'top', facing: 'right' },
        12: { x: 1853, y: 94, row: 'top', facing: 'right' },
        13: { x: 1746, y: 304, row: 'bottom', facing: 'right' },
        14: { x: 1746, y: 254, row: 'bottom', facing: 'right' },
        15: { x: 1746, y: 44, row: 'top', facing: 'right' },
        16: { x: 1746, y: 94, row: 'top', facing: 'right' },
        17: { x: 1640, y: 304, row: 'bottom', facing: 'right' },
        18: { x: 1640, y: 254, row: 'bottom', facing: 'right' },
        19: { x: 1508, y: 304, row: 'bottom', facing: 'left' },
        20: { x: 1508, y: 254, row: 'bottom', facing: 'left' },
        21: { x: 1640, y: 44, row: 'top', facing: 'right' },
        22: { x: 1640, y: 94, row: 'top', facing: 'right' },
        23: { x: 1508, y: 44, row: 'top', facing: 'left' },
        24: { x: 1508, y: 94, row: 'top', facing: 'left' },
        25: { x: 1418, y: 304, row: 'bottom', facing: 'left' },
        26: { x: 1418, y: 254, row: 'bottom', facing: 'left' },
        27: { x: 1418, y: 44, row: 'top', facing: 'left' },
        28: { x: 1418, y: 94, row: 'top', facing: 'left' },
        29: { x: 1328, y: 304, row: 'bottom', facing: 'left' },
        30: { x: 1328, y: 254, row: 'bottom', facing: 'left' },
        31: { x: 1328, y: 44, row: 'top', facing: 'left' },
        32: { x: 1328, y: 94, row: 'top', facing: 'left' },
        33: { x: 1238, y: 304, row: 'bottom', facing: 'left' },
        34: { x: 1238, y: 254, row: 'bottom', facing: 'left' },
        35: { x: 1238, y: 44, row: 'top', facing: 'left' },
        36: { x: 1238, y: 94, row: 'top', facing: 'left' },
        37: { x: 1148, y: 304, row: 'bottom', facing: 'left' },
        38: { x: 1148, y: 254, row: 'bottom', facing: 'left' },
        39: { x: 1148, y: 44, row: 'top', facing: 'left' },
        40: { x: 1148, y: 94, row: 'top', facing: 'left' },
        41: { x: 1058, y: 304, row: 'bottom', facing: 'left' },
        42: { x: 1058, y: 254, row: 'bottom', facing: 'left' },
        43: { x: 1058, y: 44, row: 'top', facing: 'left' },
        44: { x: 1058, y: 94, row: 'top', facing: 'left' },
        45: { x: 975, y: 44, row: 'top', facing: 'left' },
        46: { x: 975, y: 94, row: 'top', facing: 'left' },
        47: { x: 893, y: 44, row: 'top', facing: 'left' },
        48: { x: 893, y: 94, row: 'top', facing: 'left' },
        49: { x: 840, y: 304, row: 'bottom', facing: 'right' },
        50: { x: 840, y: 254, row: 'bottom', facing: 'right' },
        51: { x: 840, y: 44, row: 'top', facing: 'right' },
        52: { x: 840, y: 94, row: 'top', facing: 'right' },
        53: { x: 750, y: 304, row: 'bottom', facing: 'right' },
        54: { x: 750, y: 254, row: 'bottom', facing: 'right' },
        55: { x: 750, y: 44, row: 'top', facing: 'right' },
        56: { x: 750, y: 94, row: 'top', facing: 'right' },
        57: { x: 660, y: 304, row: 'bottom', facing: 'right' },
        58: { x: 660, y: 254, row: 'bottom', facing: 'right' },
        59: { x: 528, y: 304, row: 'bottom', facing: 'left' },
        60: { x: 528, y: 254, row: 'bottom', facing: 'left' },
        61: { x: 660, y: 44, row: 'top', facing: 'right' },
        62: { x: 660, y: 94, row: 'top', facing: 'right' },
        63: { x: 528, y: 44, row: 'top', facing: 'left' },
        64: { x: 528, y: 94, row: 'top', facing: 'left' },
        65: { x: 446, y: 304, row: 'bottom', facing: 'left' },
        66: { x: 446, y: 254, row: 'bottom', facing: 'left' },
      };
    },
    carriageAmenities() {
      return [
        { icon: "mdi-silverware-fork-knife", name: "Вагон-ресторан или буфет" },
        { icon: "mdi-toilet", name: "Биотуалет" },
        { icon: "mdi-snowflake", name: "Кондиционер" },
        { icon: "mdi-play-circle-outline", name: "ИРС (Информационно-развлекательный сервис)" },
        { icon: "mdi-paw", name: "Вагон с услугой перевозки животных" },
        { icon: "mdi-sale", name: "Специальные тарифы" },
      ];
    },
    carriagePhotos() {
      const placeholder = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='72' height='54' viewBox='0 0 72 54'%3E%3Crect fill='%23e8e8e8' width='72' height='54'/%3E%3Crect fill='%23d0d0d0' x='20' y='15' width='32' height='24' rx='2'/%3E%3Cpath fill='%23a0a0a0' d='M30 22h12v2H30zM30 26h8v2h-8zM30 30h10v2H30z'/%3E%3C/svg%3E";
      return [
        railAssets["sapsan_interior_1"] || placeholder,
        railAssets["sapsan_interior_2"] || placeholder,
        railAssets["sapsan_interior_3"] || placeholder,
        railAssets["sapsan_interior_4"] || placeholder,
        railAssets["sapsan_interior_5"] || placeholder,
        railAssets["sapsan_interior_6"] || placeholder,
        railAssets["sapsan_interior_7"] || placeholder,
        railAssets["sapsan_interior_8"] || placeholder,
        railAssets["sapsan_interior_9"] || placeholder,
        railAssets["sapsan_interior_10"] || placeholder,
        railAssets["sapsan_interior_11"] || placeholder,
        railAssets["sapsan_interior_12"] || placeholder,
      ];
    },
    currentStep() {
      const session = this.bookingSession;
      return session.isReturnTrip ? 5 : 2;
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
    generateOccupiedSeats(carriageId, count) {
      const seed = carriageId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
      const occupied = [];
      for (let i = 0; i < count; i++) {
        const seatNum = ((seed * (i + 1) * 7) % 66) + 1;
        if (!occupied.includes(seatNum)) {
          occupied.push(seatNum);
        }
      }
      return occupied;
    },
    getSeatClass(seat) {
      const classes = [];
      if (this.isSeatSelected(seat)) classes.push('selected');
      else if (seat.isOccupied) classes.push('occupied');
      else if (seat.hasPet) classes.push('pet');
      else if (seat.isNonRefundable) classes.push('non-refundable');
      else classes.push('free');
      return classes.join(' ');
    },
    getSeatTransform(seatNumber) {
      // No transform needed - seats are positioned via their path coordinates
      return '';
    },
    getSeatPath(seatNumber) {
      // Simplified seat path - a rounded rectangle with armrest detail
      const pos = this.seatPositions[seatNumber];
      if (!pos) return '';

      const w = 42; // seat width
      const h = 50; // seat height
      const x = pos.x - w/2;
      const y = pos.y - h/2;
      const r = 8; // corner radius

      // Simple rounded rectangle path for seat
      return `M${x + r},${y}
              h${w - 2*r}
              a${r},${r} 0 0 1 ${r},${r}
              v${h - 2*r}
              a${r},${r} 0 0 1 -${r},${r}
              h-${w - 2*r}
              a${r},${r} 0 0 1 -${r},-${r}
              v-${h - 2*r}
              a${r},${r} 0 0 1 ${r},-${r} z`;
    },
    getSeatTextX(seatNumber) {
      const pos = this.seatPositions[seatNumber];
      return pos ? pos.x : 0;
    },
    getSeatTextY(seatNumber) {
      const pos = this.seatPositions[seatNumber];
      return pos ? pos.y + 5 : 0;
    },
    isSeatSelected(seat) {
      return this.selectedSeats.some(s => s.carriageId === seat.carriageId && s.number === seat.number);
    },
    toggleSeat(seat) {
      if (seat.isOccupied) return;
      const idx = this.selectedSeats.findIndex(s => s.carriageId === seat.carriageId && s.number === seat.number);
      if (idx !== -1) {
        this.selectedSeats.splice(idx, 1);
      } else if (this.selectedSeats.length < this.maxSeats) {
        this.selectedSeats.push({ ...seat });
      }
    },
    selectCarriage(carriageId) {
      this.activeCarriageId = carriageId;
    },
    getSelectedSeatsInCarriage(carriageId) {
      return this.selectedSeats.filter(s => s.carriageId === carriageId);
    },
    continueBooking() {
      if (this.selectedSeats.length === 0) return;
      const session = getRailBookingSession() || {};
      const isReturnTrip = !!session.isReturnTrip;
      session.selectedSeats = this.selectedSeats.map(seat => ({
        carriageId: seat.carriageId,
        carriageNumber: this.carriages.find(c => c.id === seat.carriageId)?.number || "03",
        seatNumber: seat.number,
        price: seat.price,
        isNonRefundable: seat.isNonRefundable
      }));
      session.totalPrice = this.totalPrice;
      setRailBookingSession(session);

      // Log select_seat event for each selected seat
      this.selectedSeats.forEach(seat => {
        const carNumber = this.carriages.find(c => c.id === seat.carriageId)?.number || "03";
        const seatPos = this.seatPositions[seat.number];
        // In this carriage layout, top row seats (odd positions in pairs) are near windows
        const nearWindow = seatPos ? (seatPos.row === 'top' || seatPos.row === 'bottom') : false;
        _logActivity(this, {
          type: "select_seat",
          direction: isReturnTrip ? "return" : "outbound",
          car_number: carNumber,
          seat_number: seat.number,
          near_window: nearWindow,
          seats_amount: this.selectedSeats.length,
          total_price: this.totalPrice,
        });
      });

      this.$router.push({
        name: "bench_rail_passenger_selection",
        params: {
          track_id: this.$route.params.track_id,
          state_id: this.$route.params.state_id,
        }
      });
    },
    formatPrice(price) {
      return price.toLocaleString("ru-RU") + " ₽";
    },
    formatDateShort(date) {
      if (!date) return "";
      const d = new Date(date);
      const day = d.getDate();
      const months = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"];
      const weekdays = ["вс", "пн", "вт", "ср", "чт", "пт", "сб"];
      return `${day} ${months[d.getMonth()]}., ${weekdays[d.getDay()]}`;
    },
    getSeatsLabel(count) {
      if (count === 0) return "мест";
      if (count === 1) return "место";
      if (count >= 2 && count <= 4) return "места";
      if (count % 10 === 1 && count % 100 !== 11) return "место";
      if (count % 10 >= 2 && count % 10 <= 4 && (count % 100 < 10 || count % 100 >= 20)) return "места";
      return "мест";
    },
    getStepClass(step) {
      const current = this.currentStep;
      if (step === current) return "active";
      if (step < current) return "completed";
      return "";
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
  }
});
</script>

<style src="@/assets/rail.css"></style>
<style scoped>
.bench-rail.rail-seat-page {
  background: #e9eaed;
  min-height: 100vh;
}

.rail-seat-page :deep(.rail-header) {
  width: 100vw;
  margin-left: calc(50% - 50vw);
}

.rail-seat-page :deep(.header-inner) {
  max-width: 1600px;
  margin: 0 auto;
}

.seat-main {
  max-width: 1280px;
  margin: 0 auto;
  padding: 24px 20px;
}

.seat-container {
  background: transparent;
}

.top-card {
  background: var(--bench-surface-elevated, #fff);
  padding: 20px;
  margin-bottom: 16px;
}

/* Navigation */
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

/* Title */
.seat-title {
  font-size: 24px;
  font-weight: 300;
  color: #000;
  margin: 0 0 16px;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
  padding-left: 10px;
}

.params-link {
  color: #e21a1a;
  text-decoration: none;
}

.params-link:hover {
  text-decoration: underline;
}

/* Train Info */
.train-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #333;
  flex-wrap: wrap;
  padding-left: 10px;
}

.sapsan-logo {
  height: 20px;
  margin-right: 4px;
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

/* Carriage Card */
.carriage-card {
  background: var(--bench-surface-elevated, #fff);
  padding: 20px 30px;
}

/* Carriage Header */
.carriage-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.carriage-info {
  display: flex;
  flex-direction: column;
}

.carriage-title {
  font-size: 24px;
  font-weight: 400;
  color: #000;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
}

.carriage-subtitle {
  font-size: 13px;
  color: #000;
  margin-top: 2px;
}

.direction-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #000;
  font-size: 14px;
}

.direction-indicator svg {
  color: #000;
}

.carriage-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  background: var(--bench-surface-elevated, #fff);
  border: 1px solid var(--bench-border, #e0e0e0);
  border-radius: 4px;
  padding: 8px;
  cursor: pointer;
  color: var(--bench-text-muted, #666);
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btn:hover {
  background: var(--bench-primary-light, #f5f5f5);
  border-color: var(--bench-border, #ccc);
}

/* Seat Diagram - SVG Carriage Layout */
.seat-diagram-wrapper {
  background: var(--bench-primary-light, #f5f7f9);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 16px;
  overflow-x: auto;
}

.carriage-svg {
  width: 100%;
  min-width: 900px;
  height: auto;
  display: block;
}

/* SVG Carriage Styles */
.carriage-bg {
  fill: #ffffff;
}

.color-zone {
  fill: #ecfcf1;
}

.carriage-outline {
  fill: #a9aeba;
}

.compartment-dividers {
  fill: #a9aeba;
}

/* Tables */
.tables-group .table {
  fill: #e6e6e6;
}

/* Windows */
.windows-group line {
  stroke: #bbddff;
  stroke-width: 6;
  stroke-miterlimit: 22.9256;
  fill: none;
}

/* Icons */
.icons-group .icon {
  fill: #868d98;
}

.icons-group .wc-text {
  fill: #868d98;
  font-family: 'Roboto', 'Helvetica Neue', sans-serif;
  font-size: 20px;
}

/* Seats */
.seats-group .seat-wrapper {
  cursor: pointer;
  transition: all 0.15s ease;
}

.seats-group .seat-path {
  fill: #e2e4e7;
  stroke: #d2d7db;
  stroke-miterlimit: 22.9256;
  transition: fill 0.15s ease;
}

.seats-group .seat-number {
  fill: #ffffff;
  font-family: 'Roboto', 'Helvetica Neue', sans-serif;
  font-size: 20px;
  text-anchor: middle;
  dominant-baseline: middle;
  pointer-events: none;
}

/* Seat states */
.seats-group .seat-wrapper.free .seat-path {
  fill: #8fcfff;
  stroke: #7ac0f0;
}

.seats-group .seat-wrapper.free:hover .seat-path {
  fill: #5bb8f7;
}

.seats-group .seat-wrapper.occupied .seat-path {
  fill: #e0e0e0;
  stroke: #d0d0d0;
}

.seats-group .seat-wrapper.occupied {
  cursor: not-allowed;
}

.seats-group .seat-wrapper.selected .seat-path {
  fill: #e21a1a;
  stroke: #c91515;
}

.seats-group .seat-wrapper.pet .seat-path {
  fill: #a0a0a0;
  stroke: #909090;
}

.seats-group .seat-wrapper.non-refundable .seat-path {
  fill: #b8e0ff;
  stroke: #a0d0f0;
}

/* Carriage Tabs */
.carriage-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.carriage-tab {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 12px 40px 12px 25px;
  background: var(--bench-surface-elevated, #f3f3f3);
  color: var(--bench-text, inherit);
  cursor: pointer;
  min-width: 100px;
  position: relative;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
}

.carriage-tab:hover {
  border-color: #ccc;
}

.carriage-tab.active {
  background: var(--bench-primary, #e21a1a);
  border-color: var(--bench-primary, #e21a1a);
  color: #fff;
}

.tab-label {
  font-size: 14px;
  text-transform: uppercase;
}

.tab-seats {
  font-size: 11px;
  color: var(--bench-text-muted, #666);
  margin-top: 2px;
}

.carriage-tab.active .tab-seats {
  color: #fff;
}

.tab-badge {
  position: absolute;
  top: 5px;
  right: 5px;
  background: #e21a1a;
  color: #fff;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
}

.carriage-tab.active .tab-badge {
  background: var(--bench-surface-elevated, #fff);
  color: #e21a1a;
}

/* Legend */
.seat-legend {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  padding: 12px 0;
  flex-wrap: wrap;
  gap: 12px;
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 50px;
  align-items: center;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #000;
}

.legend-color {
  width: 24px;
  height: 24px;
  border-radius: 3px;
}

.legend-color.free {
  background: #8fcfff;
}

.legend-color.occupied {
  background: #e0e0e0;
}

.legend-color.selected {
  background: #e21a1a;
}

.legend-color.filtered {
  background: #d8c8e8;
}

.legend-color.pet {
  background: #a0a0a0;
}

.legend-color.non-refundable {
  background: #b8e0ff;
}

.info-icon {
  color: #999;
  margin-left: 2px;
}

.all-marks-btn {
  background: var(--bench-surface-elevated, #fff);
  border: 1px solid #e21a1a;
  color: #e21a1a;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
}

.all-marks-btn:hover {
  background: #e21a1a;
  color: #fff;
}

/* Carriage Details */
.carriage-details {
  padding-top: 16px;
}

.details-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  font-size: 24px;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
  flex-wrap: wrap;
}

.details-carriage {
  color: #111;
}

.details-separator {
  color: #ccc;
}

.details-class,
.details-type {
  color: #000;
}

.amenities {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 20px;
}

.amenity {
  color: #000;
}

.carriage-photos {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  align-items: center;
}

.carriage-photo {
  width: 100px;
  height: 80px;
  object-fit: cover;
  border-radius: 4px;
  border: 2px solid transparent;
  cursor: pointer;
}

.carriage-photo.active {
  border-color: #e21a1a;
}

.carriage-photo:hover {
  border-color: #e21a1a;
}

.more-photos-btn {
  background: var(--bench-surface-elevated, #fff);
  border: 1px solid #e21a1a;
  color: #e21a1a;
  padding: 8px 12px;
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
  white-space: nowrap;
  margin-left: auto;
}

.more-photos-btn:hover {
  background: #e21a1a;
  color: #fff;
}

/* Continue Button */
.seat-continue-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-top: 40px;
  padding: 16px 0px 0;
  background: var(--bench-surface-elevated, #fff);
  border-top: 1px solid #e0e0e0;
  font-family: 'RussianRail G Pro Extended', Arial, Helvetica, sans-serif;
}

.seat-continue-info {
  font-size: 24px;
  color: #000;
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
}

.seat-continue-accent {
  color: #e21a1a;
}

.continue-btn {
  padding: 14px 45px;
  background: #e21a1a;
  color: #fff;
  border: none;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  text-transform: uppercase;
}

.continue-btn:hover:not(:disabled) {
  background: #c91515;
}

.continue-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* Responsive */
@media (max-width: 768px) {
  .seat-title {
    font-size: 22px;
  }

  .carriage-header {
    flex-direction: column;
  }

  .direction-indicator {
    order: -1;
  }

  .seat {
    width: 28px;
    height: 28px;
  }

  .seat-num {
    font-size: 9px;
  }
}
</style>
