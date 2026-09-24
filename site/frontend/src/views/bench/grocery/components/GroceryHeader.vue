<template>
  <div>
    <!-- Global overlay for Login/Profile Drawer -->
    <div v-if="drawerOpen" class="drawer-overlay" @click="closeDrawer"></div>
    
    <!-- Login Drawer (shown when not logged in) -->
    <div v-if="!isLoggedIn" class="login-drawer" :class="{ open: drawerOpen }" role="dialog" aria-modal="true">
      <div class="drawer-header">
        <v-btn class="drawer-close" variant="flat" @click="closeDrawer">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 16 16">
            <path fill="currentColor" d="M13.707 2.293a1 1 0 0 1 0 1.414l-3.515 3.515a1.1 1.1 0 0 0 0 1.555l3.515 3.516a1 1 0 0 1-1.414 1.414l-3.515-3.515a1.1 1.1 0 0 0-1.556 0l-1.515 1.515v.001l-2 2a1 1 0 0 1-1.414-1.415l3.515-3.515v-.001a1.1 1.1 0 0 0 0-1.555L2.293 3.707a1 1 0 0 1 1.414-1.414l2 2 1.515 1.515a1.1 1.1 0 0 0 1.555 0l3.516-3.515a1 1 0 0 1 1.414 0"></path>
          </svg>
        </v-btn>
      </div>
      <div class="drawer-content">
        <div class="login-section">
          <div class="sber-card">
            <div class="sber-logo">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24">
                <path fill="url(#paint0_linear_17248_53654)" d="M12 2C6.5 2 2 6.5 2 12v10h10c5.5 0 10-4.5 10-10S17.5 2 12 2m.083 15.333c-2.916 0-5.333-2.417-5.333-5.333s2.417-5.333 5.333-5.333c1.667 0 3.166.75 4.167 2l-2.167 1.75a2.54 2.54 0 0 0-2-.917c-1.417 0-2.5 1.166-2.5 2.5 0 1.416 1.166 2.5 2.5 2.5.75 0 1.5-.333 2-1l2.25 1.75c-1 1.333-2.583 2.083-4.25 2.083"></path>
                <defs>
                  <linearGradient id="paint0_linear_17248_53654" x1="21.866" x2="-0.818" y1="2" y2="5.995" gradientUnits="userSpaceOnUse">
                    <stop stop-color="#0BADBF"></stop>
                    <stop offset="0.51" stop-color="#34C61A"></stop>
                    <stop offset="1" stop-color="#E1EE05"></stop>
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <div class="sber-text">
              <div class="sber-title">Бонусы</div>
              <div class="sber-desc">Войдите, чтобы получать и списывать бонусы</div>
            </div>
          </div>
          <v-btn class="sber-green-btn" color="#21A038" variant="flat" @click="handleSberLogin">
            <span class="sber-green-btn-content">
              <svg style="display: block" viewBox="0 0 26 26" fill="none" xmlns="http://www.w3.org/2000/svg" width="20" height="20">
                <path fill-rule="evenodd" clip-rule="evenodd" d="M13 0C16.0927 0 18.9337 1.08103 21.1657 2.88421L18.6371 4.74793C17.0315 3.64848 15.0899 3.00354 13 3.00354C7.48924 3.00354 3.00587 7.48999 3.00587 13.0013C3.00587 18.5126 7.48924 22.9965 13 22.9965C18.5134 22.9965 22.9968 18.5126 22.9968 13.0013C22.9968 12.9118 22.9941 12.8223 22.9924 12.7328L25.7912 10.6699C25.9289 11.4245 26 12.2055 26 13.0013C26 20.1807 20.1795 26 13 26C5.82135 26 0 20.1807 0 13.0013C0 5.81931 5.82135 0 13 0ZM23.2856 5.05241C23.9006 5.84651 24.4262 6.71169 24.8456 7.63565L13.0002 16.3673L8.05093 13.2628V9.52921L13.0002 12.6337L23.2856 5.05241Z" fill="#ffffff"></path>
              </svg>
              Войти как {{ displayShortName }}
            </span>
          </v-btn>
          <v-btn class="phone-btn" variant="flat">Войти по номеру телефона</v-btn>
        </div>
        
        <div class="consents-section">
          <div class="consents">
          <div class="consent-item">
            <button 
              class="checkbox" 
              :class="{ checked: consent1 }" 
              :aria-checked="consent1" 
              type="button" 
              role="checkbox"
              @click="consent1 = !consent1"
            >
              <svg v-if="consent1" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path d="M20 6L9 17L4 12" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
            <span class="consent-text"><span>Получать </span><a href="#" target="_blank">предложения об акциях и скидках</a></span>
          </div>
          <div class="consent-item">
            <button 
              class="checkbox" 
              :class="{ checked: consent2 }" 
              :aria-checked="consent2" 
              type="button" 
              role="checkbox"
              @click="consent2 = !consent2"
            >
              <svg v-if="consent2" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path d="M20 6L9 17L4 12" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
            <span class="consent-text"><span>Делиться </span><a href="#" target="_blank">данными с партнёрами доставки</a></span>
          </div>
          </div>
          <div class="agreement">
            Продолжая авторизацию, вы соглашаетесь с <a href="#" target="_blank">политикой конфиденциальности</a>, <a href="#" target="_blank">условиями сервиса</a> и <a href="#" target="_blank">условиями продажи товаров</a>
          </div>
        </div>
      </div>
    </div>

    <!-- Profile View -->
    <div v-if="isLoggedIn" class="login-drawer profile-drawer" :class="{ open: drawerOpen }" role="dialog" aria-modal="true">
      <div class="drawer-header">
        <v-btn v-if="showLogoutConfirm" class="drawer-back" variant="flat" @click="cancelLogout">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 16 16" color="#404040" style="min-width: 16px; min-height: 16px;"><path fill="currentColor" d="M8.707 14.707a1 1 0 0 1-1.414 0L1.328 8.742l-.016-.018a.996.996 0 0 1 0-1.448q.008-.01.016-.018l5.965-5.965a1 1 0 0 1 1.414 1.414L4.755 6.658A.2.2 0 0 0 4.897 7H14a1 1 0 0 1 0 2H4.897a.2.2 0 0 0-.142.341l3.952 3.952a1 1 0 0 1 0 1.414"></path></svg>
        </v-btn>
        <v-btn class="drawer-close" variant="flat" @click="closeDrawer">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 16 16">
            <path fill="currentColor" d="M13.707 2.293a1 1 0 0 1 0 1.414l-3.515 3.515a1.1 1.1 0 0 0 0 1.555l3.515 3.516a1 1 0 0 1-1.414 1.414l-3.515-3.515a1.1 1.1 0 0 0-1.556 0l-1.515 1.515v.001l-2 2a1 1 0 0 1-1.414-1.415l3.515-3.515v-.001a1.1 1.1 0 0 0 0-1.555L2.293 3.707a1 1 0 0 1 1.414-1.414l2 2 1.515 1.515a1.1 1.1 0 0 0 1.555 0l3.516-3.515a1 1 0 0 1 1.414 0"></path>
          </svg>
        </v-btn>
      </div>
      <div class="drawer-content profile-content" :class="{ 'logout-confirm-content': showLogoutConfirm }">
        <!-- Logout Confirmation View -->
        <div v-if="showLogoutConfirm" class="logout-confirm-section">
          <h2 class="logout-confirm-title">Уходите?</h2>
          <v-btn class="logout-confirm-yes-btn" variant="flat" @click="confirmLogout">
            Ухожу
          </v-btn>
          <v-btn class="logout-confirm-no-btn" variant="flat" @click="cancelLogout">
            Нет
          </v-btn>
        </div>

        <!-- Profile View -->
        <div v-else class="profile-section">
          <div class="profile-info">
            <bench-profile-info-card :info="personalInfo" variant="inline" />
          </div>

          <div class="profile-menu">
            <div class="profile-menu-item" @click="handleMenuClick('orders')">
              <div class="menu-item-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" fill="none" viewBox="0 0 64 64" style="min-width: 64px; min-height: 64px;"><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="M36.822 14.912c0 1.206-.026 2.428-.08 2.996-.097 1.055-.676 2.033-1.691 2.428-.903.347-1.859.189-2.696-.25-.838-.44-1.798-1.688-2.38-2.796-1.114 0-1.915-.836-2.033-1.914a1.42 1.42 0 0 1 .277-1.076M36.824 11.893v1.8"></path><path fill="#404040" d="M28.202 14.25a74 74 0 0 1-.394-3.42 2.24 2.24 0 0 1 1.004-2.095 2.79 2.79 0 0 1 2.595-.204c.346-.831.952-1.553 1.9-1.543.908 0 1.512.52 1.878 1.336a2.03 2.03 0 0 1 1.617.012 1.73 1.73 0 0 1 .931 1.484c.063.753-.488 1.493-.854 2.125v-.028a1.42 1.42 0 0 1-.956-.63l-.034-.04a2.05 2.05 0 0 1-1.424.57 2.08 2.08 0 0 1-1.452-.528 1.86 1.86 0 0 1-1.102 1.081 3.2 3.2 0 0 1-1.57.149l-.06.037v2.301c-.167-.61-.814-1.136-1.463-.943-.233.065-.442.2-.597.386"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="M28.202 14.25a74 74 0 0 1-.394-3.42 2.24 2.24 0 0 1 1.004-2.095 2.79 2.79 0 0 1 2.595-.204c.346-.831.952-1.553 1.9-1.543.908 0 1.512.52 1.878 1.336a2.03 2.03 0 0 1 1.617.012 1.73 1.73 0 0 1 .931 1.484c.063.753-.488 1.493-.854 2.125v-.028a1.42 1.42 0 0 1-.956-.63l-.034-.04a2.05 2.05 0 0 1-1.424.57 2.08 2.08 0 0 1-1.452-.528 1.86 1.86 0 0 1-1.102 1.081 3.2 3.2 0 0 1-1.57.149l-.06.037v2.301c-.167-.61-.814-1.136-1.463-.943-.233.065-.442.2-.597.386"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="M33.087 15.61a1.23 1.23 0 1 0 0-2.46 1.23 1.23 0 0 0 0 2.46"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="M36.985 14.3a1.23 1.23 0 1 1-1.23-1.23 1.22 1.22 0 0 1 1.23 1.23M35.05 20.336l.003 1.54-1.964 4.007-3.303-4.403v-4.067"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="M27.796 39.54c-1.06.843-2.56 1.986-3.679 2.755-.931.638-1.745 1.232-2.93 1.116-1.881-.18-2.985-2.064-3.05-3.809-.06-1.793 2.255-7.804 2.735-9.122.659-1.567 1.1-3.611 2.29-4.868.872-.907 2.116-1.663 3.21-2.26l3.416-1.874"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="M29.494 34.96c.299.313.502.704.585 1.129.262 1.338-.36 3.05-1.806 3.385-1.445.336-3.078-.628-3.253-2.14a3.01 3.01 0 0 1 1.372-2.799 2.48 2.48 0 0 1 3.102.425M19.715 39l5.968-3.816"></path><path fill="#404040" d="M28.23 34.24a2.35 2.35 0 0 0-1.83.301l-.028-11.19 1.86-1.017v11.841"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="M28.23 34.24a2.35 2.35 0 0 0-1.83.301l-.028-11.19 1.86-1.017v11.841"></path><path fill="#404040" d="M27.796 39.54c-1.06.843-2.56 1.986-3.679 2.755-.931.638-1.745 1.232-2.93 1.116-1.881-.18-2.985-2.064-3.05-3.808v18.545H32.41V39.542h-4.503"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="M27.796 39.54c-1.06.843-2.56 1.986-3.679 2.755-.931.638-1.745 1.232-2.93 1.116-1.881-.18-2.985-2.064-3.05-3.808v18.545H32.41V39.542h-4.503"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="M31.856 49.05h8.063l-.581-20.687"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="M47.906 52.804c-.437-1.845-3.816-17.236-5.61-22.903-.571-1.806-1.346-3.693-2.847-4.923a44 44 0 0 0-4.39-3.101M47.906 52.804h-6.084M18.362 38.106l-3.253-9.38a1.962 1.962 0 1 1 3.707-1.29l1.543 4.456M38.174 49.05l3.648 10.604M43.581 52.822a3.19 3.19 0 0 0 .242 3.05 2.44 2.44 0 0 0 3.555.582c.97-.745 1.017-2.575.496-3.596M41.822 59.654l1.483-5.138M47.707 56.112l1.104 3.46"></path></svg>
              </div>
              <span>Заказы</span>
            </div>
            <div class="profile-menu-item" @click="handleMenuClick('addresses')">
              <div class="menu-item-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" fill="none" viewBox="0 0 168 168" style="min-width: 64px; min-height: 64px;"><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="M99.477 35.632c-2.945-.101-6.12-.176-8.808 1.163a16.33 16.33 0 0 1-14.165 0c-2.667-1.339-5.868-1.264-8.808-1.163l-.048-.304c0-9.395 7.133-17.008 15.936-17.008s15.935 7.613 15.935 17.008"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="M73.444 50.17a106 106 0 0 1-1.665-14.261M94.45 49.086a54 54 0 0 1-.983 4.306c-1.093 3.996-5.222 7.751-9.63 7.751-4.406 0-8.535-3.734-9.602-7.751a52 52 0 0 1-.768-3.201M95.903 35.909a114 114 0 0 1-1.446 13.177"></path><path fill="#404040" d="M80.93 42.792a.97.97 0 0 1-.763.704 1.01 1.01 0 0 1-.934-.421c-.49-.662-.453-3.505.902-3.201a1.17 1.17 0 0 1 .79.827c.203.68.203 1.405 0 2.086M88.393 42.792a.97.97 0 0 1-.763.704 1.01 1.01 0 0 1-.934-.421c-.49-.662-.453-3.505.902-3.201a1.17 1.17 0 0 1 .79.827c.203.68.203 1.405 0 2.086"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="M73.36 50.202c-3.853 1.238-6.04-3.59-4.871-6.695.613-1.627 2.085-2.134 3.665-1.504M94.65 49.258c3.852 1.237 6.04-3.596 4.871-6.701-.613-1.6-2.086-2.134-3.67-1.5"></path><path fill="#404040" d="m74.723 36.123-2.571 5.863-4.455-6.354"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="m74.723 36.123-2.571 5.863-4.455-6.354"></path><path fill="#404040" d="m92.725 36.523 3.126 4.534 3.628-5.425"></path><path fill="#404040" d="m92.725 36.523 3.126 4.534 3.628-5.425"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="m92.725 36.523 3.126 4.534 3.628-5.425M75.982 65.3c-4.583 1.29-11.838 2.667-16.005 5.015-3.734 2.134-6.562 5.756-8.477 9.544M108.706 94.882a8.2 8.2 0 0 1-8.2 8.199c-3.772 0-6.962-2.843-8.002-6.402a8.62 8.62 0 0 1 1.798-7.9c2.294-2.465 6.642-2.807 9.688-1.868 3.308 1.025 4.716 4.764 4.716 7.97M108.682 93.046l10.787 25.251M60.625 93.046v56.716M107.08 128.001v22.321"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="M38.484 79.608a7.565 7.565 0 0 0-1.328 9.352c1.888 3.415 6.199 4.418 9.736 3.255a7.73 7.73 0 0 0 4.193-3.148c2.043-3.313 1.302-9.896-3.334-11.091.117-2.577.613-5.495.73-8.072.06-1.286.62-4.62-1.008-5.233-3.873-1.457-3.633 5.74-3.782 7.853l-.336 4.732c-.72-2.545-1.297-5.149-2.033-7.581a13.6 13.6 0 0 0-1.366-3.5 1.756 1.756 0 0 0-2.87-.304c-1.248 1.398-.16 4.412.197 5.97l1.692 7.33"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="m51.495 82.744-6.877-1.456a3 3 0 0 0-1.6.096 2.02 2.02 0 0 0-1.286 2.72c.576 1.697 2.54 1.89 4.07 2.263 1.948.475 3.922.885 5.901 1.173M37.156 88.96c.032 3.452.059 7.97.086 11.422.032 4.119-.14 8.237 0 12.35.144 3.847.304 8.243 2.134 11.663 2.464 4.662 6.674 7.319 12.1 6.402 4.267-.721 7.116-4.071 9.149-8.318M51.703 87.552v29.822"></path><path fill="#404040" d="m59.625 70.96.934 37.451a72.2 72.2 0 0 0 4.492-22.3c.272-5.895.832-12.185.666-18.096"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="m59.625 70.96.934 37.451a72.2 72.2 0 0 0 4.492-22.3c.272-5.895.832-12.185.666-18.096"></path><path fill="#404040" d="m101.896 68.624-2.374 17.808v.048c1.493-.14 3 .006 4.438.432a5.6 5.6 0 0 1 2.134 1.221l-.053-.586 2.214-16.597"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="m101.896 68.624-2.374 17.808v.048c1.493-.14 3 .006 4.438.432a5.6 5.6 0 0 1 2.134 1.221l-.053-.586 2.214-16.597"></path><path fill="#404040" d="M72.845 23.81c-.064 2.043-.08 4.086-.032 6.13 1.227-2.412 1.969-5.896 2.23-8.59"></path><path fill="#404040" d="M72.845 23.81c-.064 2.043-.08 4.086-.032 6.13 1.227-2.412 1.969-5.896 2.23-8.59"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="M72.845 23.81c-.064 2.043-.08 4.086-.032 6.13 1.227-2.412 1.969-5.896 2.23-8.59"></path><path fill="#404040" d="M85.457 19.04a35 35 0 0 1-1.92 8.44h-.214a34.4 34.4 0 0 1-1.92-8.44"></path><path fill="#404040" d="M85.457 19.04a35 35 0 0 1-1.92 8.44h-.214a34.4 34.4 0 0 1-1.92-8.44"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="M85.457 19.04a35 35 0 0 1-1.92 8.44h-.214a34.4 34.4 0 0 1-1.92-8.44"></path><path fill="#404040" d="M93.958 23.276q.102 3.062.038 6.13c-1.227-2.412-1.969-5.895-2.23-8.59"></path><path fill="#404040" d="M93.958 23.276q.102 3.062.038 6.13c-1.227-2.412-1.969-5.895-2.23-8.59"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="M93.958 23.276q.102 3.062.038 6.13c-1.227-2.412-1.969-5.895-2.23-8.59M91.902 65.3c4.583 1.29 11.7 2.667 15.856 5.015 5.452 3.11 8.12 8.824 10.136 14.5 2.497 7.026 5.367 13.962 7.57 21.153 1.996 6.514 5.944 14.623 2.332 21.292-2.187 4.033-6.525 7.058-11.241 6.674-5.287-.432-8.733-3.975-10.974-8.536-2.945-5.949-8.077-17.765-10.21-24.061"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M75.984 57.164V65.3c2.487 4.561 11.492 6.605 15.92 0l-.028-8.425"></path><path fill="#404040" d="M75.983 65.3c-4.582 1.29-11.838 2.667-16.004 5.015a18.5 18.5 0 0 0-4.322 3.478l-2.87 3.783v-20.38l23.186-.032"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="M75.983 65.3c-4.582 1.29-11.838 2.667-16.004 5.015a18.5 18.5 0 0 0-4.322 3.478l-2.87 3.783v-20.38l23.186-.032"></path><path fill="#404040" d="M91.904 65.3c4.583 1.29 11.7 2.667 15.856 5.015a24.1 24.1 0 0 1 5.276 4.177l3.105 5.367-.043-22.695H91.766"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="M91.904 65.3c4.583 1.29 11.7 2.667 15.856 5.015a24.1 24.1 0 0 1 5.276 4.177l3.105 5.367-.043-22.695H91.766"></path></svg>
              </div>
              <span>Адреса</span>
            </div>
            <div class="profile-menu-item" @click="handleMenuClick('settings')">
              <div class="menu-item-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" fill="none" viewBox="0 0 64 64" style="min-width: 64px; min-height: 64px;"><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="M25.61 13.624c1.3 2.905 3.384 8.055 7.013 6.294a3.57 3.57 0 0 0 1.605-1.628"></path><path fill="#404040" d="M25.61 13.624a3.8 3.8 0 0 1-.3-1.418c-.088-1.666.777-3.16 2.115-4.148 1.608-1.19 4.006-1.39 5.808-.53 2.168 1.037 2.735 3.764 3.582 5.819l-.058-.072c.362.822.658 1.643.956 2.465.193.537.793.73 1.041 1.219.27.53-.026 1.136.089 1.689s.664.752 1.027 1.107c.643.617.226 1.135.082 1.87-.11.57.453.884.785 1.233a1.6 1.6 0 0 1 .206 1.85c-.362.7-1.438.616-2.012.266-.573-.349-.682-1.216-.59-1.828.056-.358.111-.495-.164-.804-.218-.244-.737-.458-.85-.772-.224-.635.497-1.305-.062-1.965-.3-.353-.947-.31-1.028-.89-.06-.466.206-.893.066-1.407-.205-.709-.974-.842-1.41-1.379v-.086c.987-.263 1.496-1.385 1.303-2.347-.254-1.27-1.839-2.054-2.465-.577a3.9 3.9 0 0 0-.284 1.184l-.08-.142-2.692-4.34c-.939 1.352-3.329 3.126-4.849 3.752"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="M25.61 13.624a3.8 3.8 0 0 1-.3-1.418c-.088-1.666.777-3.16 2.115-4.148 1.608-1.19 4.006-1.39 5.808-.53 2.168 1.037 2.735 3.764 3.582 5.819l-.058-.072c.362.822.658 1.643.956 2.465.193.537.793.73 1.041 1.219.27.53-.026 1.136.089 1.689s.664.752 1.027 1.107c.643.617.226 1.135.082 1.87-.11.57.453.884.785 1.233a1.6 1.6 0 0 1 .206 1.85c-.362.7-1.438.616-2.012.266-.573-.349-.682-1.216-.59-1.828.056-.358.111-.495-.164-.804-.218-.244-.737-.458-.85-.772-.224-.635.497-1.305-.062-1.965-.3-.353-.947-.31-1.028-.89-.06-.466.206-.893.066-1.407-.205-.709-.974-.842-1.41-1.379v-.086c.987-.263 1.496-1.385 1.303-2.347-.254-1.27-1.839-2.054-2.465-.577a3.9 3.9 0 0 0-.284 1.184l-.08-.142-2.692-4.34c-.939 1.352-3.329 3.126-4.849 3.752"></path><path fill="#404040" d="M27.955 14.927a.38.38 0 0 1-.117.382.39.39 0 0 1-.395.041c-.29-.125-.822-1.077-.32-1.233a.46.46 0 0 1 .423.121c.201.187.344.428.41.695M30.657 13.98a.38.38 0 0 1-.115.382.4.4 0 0 1-.395.04c-.292-.124-.832-1.076-.322-1.232a.46.46 0 0 1 .423.121c.201.187.344.428.41.695"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="m24.162 33.754-10.313-5.036c-1.126-.549-2.708-.87-3.699.128-1.498 1.516-.398 4.121 1.669 4.224a3.06 3.06 0 0 0 2.973-1.777"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="M29.919 20.396h-.559a5.4 5.4 0 0 0-4.171 1.889c-.787.961-.99 2.188-1.027 3.398-.074 2.702 0 5.365 0 8.078M40.949 35.332l2.657 2.145c1.57 1.268 4.07 3.613 6.174 2.13 1.728-1.217.553-3.61-.084-5.107l-3.082-7.233c-.923-2.163-2.026-5.178-4.294-6.27-1.028-.5-2.17-.59-3.31-.58"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="M39.447 33.652c-.54-.892-.323-2.373.353-3.128a2.76 2.76 0 0 1 1.776-.822c1.915-.184 3.193 1.944 2.687 3.637a2.71 2.71 0 0 1-3.86 1.704M43.608 30.543l6.606 5.18M11.827 33.072c1.077 3.61 2.016 7.262 3.125 10.864.98 3.18 1.956 6.82 4.332 9.273 2.823 2.914 7.124 3.417 10.857 2.155"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="M41.155 32.045q-1.104 4.02-2.203 8.04c-.5 1.819-.95 3.658-1.496 5.462-1.124 3.698-2.525 6.986-5.795 9.246M41.155 32.045l-5.569 5.486c-1.964 1.936-3.99 3.886-6.407 5.254-3.634 2.055-7.53 1.819-10.654-.91-2.683-2.347-4.273-5.684-5.726-8.903M29.92 20.396c1.4 3.549 5.857 4.073 9.09.243M44.376 38.098l.07 7.985"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="M28.154 26.567c-.102 1.939.11 3.882.629 5.753a31.9 31.9 0 0 1 1.136 9.832"></path><path fill="#404040" d="M37.345 54.041c0 2.125-1.656 3.847-3.699 3.847-2.042 0-3.698-1.722-3.698-3.847s1.656-3.846 3.698-3.846c2.043 0 3.699 1.722 3.699 3.846"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="M33.642 57.888c2.045 0 3.703-1.722 3.703-3.847s-1.658-3.846-3.703-3.846-3.702 1.722-3.702 3.846 1.657 3.847 3.702 3.847M52.723 46.137H39.889v8.866h12.834z"></path><path fill="#404040" d="M14.295 32.36c1.089.95 2.26 1.966 2.876 3.306.557 1.212.442 2.985-.865 3.686l-.033.024a15 15 0 0 0 2.26 2.499c2.99 2.612 6.69 2.942 10.192 1.159l-.024-.045-13.9-11.696"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="M14.295 32.36c1.089.95 2.26 1.966 2.876 3.306.557 1.212.442 2.985-.865 3.686l-.033.024a15 15 0 0 0 2.26 2.499c2.99 2.612 6.69 2.942 10.192 1.159l-.024-.045-13.9-11.696M28.95 14.99c.24.617.205 1.326.182 1.969.469 0 .908.333 1.26.643"></path></svg>
              </div>
              <span>Настройки</span>
            </div>
            <div class="profile-menu-item bonus-item">
              <div class="menu-item-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" fill="none" viewBox="0 0 64 64" style="min-width: 64px; min-height: 64px;"><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="M34.799 15.361c-.054 1.175-.279 2.267-.846 3.176-.956 1.53-3.037 1.917-4.569 1.051-1.696-.958-2.549-3.015-3.478-4.625"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="M30.011 17.715a2.34 2.34 0 0 0 2.14-.81M20.172 36.51c.206 1.11 1.018 2.107 2.187 2.268 2.35.331 3.55-2.509 4.424-4.186 1.078-2.061 1.983-4.231 3.166-6.247.544-.925.853-1.743.575-2.805-.194-.74-.715-1.236-1.488-1.183-1.49.1-1.94 1.103-2.62 2.267-.999 1.703-1.89 3.47-2.984 5.115s-2.15 3.246-3.237 4.868"></path><path fill="#404040" d="m34.696 16.417-.017 5.047h.284c2.424-.097 4.852-2.156 4.675-4.563-.165-2.292-2.218-4.557-3.516-6.344-1.876-2.576-4.495-5.44-8.003-4.299a5.6 5.6 0 0 0-3.415 3.069c-.824 1.945.34 4.033 1.257 5.704v-.09l-.084-5.73 8.472 2.842h.124c.398-.661 1.22-.919 1.764-.276.975 1.15.429 3.205-1.084 3.558"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="m34.696 16.417-.017 5.047h.284c2.424-.097 4.852-2.156 4.675-4.563-.165-2.292-2.218-4.557-3.516-6.344-1.876-2.576-4.495-5.44-8.003-4.299a5.6 5.6 0 0 0-3.415 3.069c-.824 1.945.34 4.033 1.257 5.704v-.09l-.084-5.73 8.472 2.842h.124c.398-.661 1.22-.919 1.764-.276.975 1.15.429 3.205-1.084 3.558M25.081 58.907V45.203h12.55v13.703M24.374 29.495l-4.348-7.55a4.262 4.262 0 0 1 7.382-4.261l7.477 12.94a4.262 4.262 0 1 1-7.382 4.262l-.464-.78"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="M44.409 33.978c.197.811.17 1.66-.077 2.458-.554 1.616-2.234 1.997-3.816 1.997h-8.073c-1.709 0-3.273-1.21-4.254-2.411M27.297 14.23a1.34 1.34 0 0 0 1.187-.602M30.736 12.958a1.35 1.35 0 0 0 1.19-.602"></path><path fill="#404040" d="m24.426 29.777-2.267-4.122c-.707 1.544-.787 3.166-1.218 4.932s-.825 3.56-.825 5.371q.003.287.056.569"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="m24.426 29.777-2.267-4.122c-.707 1.544-.787 3.166-1.218 4.932s-.825 3.56-.825 5.371q.003.287.056.569"></path><path fill="#404040" d="M27.23 33.714q-.218.443-.447.882c-.447.86-.98 2.022-1.708 2.908v7.7l14.633.061-.893-6.832h-6.372c-1.709 0-3.273-1.21-4.254-2.41"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="M27.23 33.714q-.218.443-.447.882c-.447.86-.98 2.022-1.708 2.908v7.7l14.633.061-.893-6.832h-6.372c-1.709 0-3.273-1.21-4.254-2.41"></path><path fill="#404040" d="M34.568 21.664a4.03 4.03 0 0 1-3.504 1.665l-.433-.047 4.666 7.343a4.25 4.25 0 0 1 .357 3.466h8.783l-.022-.12a15.4 15.4 0 0 0-1.018-2.885c-.711-1.648-1.484-3.279-2.232-4.915a10.9 10.9 0 0 0-2.107-3.184c-1.03-1.092-2.648-1.569-4.121-1.527"></path><path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.8" d="M34.568 21.664a4.03 4.03 0 0 1-3.504 1.665l-.433-.047 4.666 7.343a4.25 4.25 0 0 1 .357 3.466v0h8.783l-.022-.12a15.4 15.4 0 0 0-1.018-2.885c-.711-1.648-1.484-3.279-2.232-4.915a10.9 10.9 0 0 0-2.107-3.184c-1.03-1.092-2.648-1.569-4.121-1.527M25.092 18.63q-.825 1.815-1.662 3.63M26.753 21.468a777 777 0 0 1-1.662 3.63M31.872 29.778l-1.661 3.629M31.072 49.173l-.03 9.734M42.383 13.884c.84-.878 3.112-3.277 1.236-4.339-.81-.46-1.527.46-1.81 1.163h-.053c-.503-.567-1.486-1.194-2.096-.489-1.395 1.628 1.55 3.12 2.644 3.665"></path></svg>
              </div>
              <span>Бонусы</span>
              <div class="bonus-badge">{{ bonusPoints }}
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="none" viewBox="0 0 24 24" color="#ffffff" style="min-width: 12px; min-height: 12px;"><path fill="currentColor" d="M12.088 2q2.259 0 4.09.762 1.832.763 3.112 2.11a9.3 9.3 0 0 1 2.007 3.176q.703 1.83.703 3.94t-.703 3.938a9.3 9.3 0 0 1-2.007 3.177q-1.28 1.347-3.112 2.135-1.832.762-4.09.762H2V11.987q0-2.109.703-3.939a9.6 9.6 0 0 1 2.032-3.176q1.331-1.347 3.187-2.11Q9.78 2 12.088 2m3.739 11.385q-.377.636-1.205 1.067-.803.432-2.082.432-1.28 0-2.033-.66-.728-.687-.728-2.135 0-1.449.678-2.11.677-.66 2.057-.66 1.18 0 1.933.508.777.483 1.28 1.245V7.54q-.503-.381-1.356-.635a7.1 7.1 0 0 0-1.857-.28Q9.854 6.6 8.248 7.997q-1.58 1.398-1.58 4.092 0 1.373.426 2.414T8.3 16.231t1.832 1.042q1.054.33 2.308.33.578 0 1.104-.101a7 7 0 0 0 1.004-.305q.451-.204.778-.407.352-.202.502-.406z"></path></svg>
              </div>
            </div>
          </div>

          <div class="profile-actions">
            <v-btn class="contact-btn" variant="flat">
              Связаться с нами
            </v-btn>
            <v-btn class="logout-btn" variant="flat" @click="handleLogout">
              Выйти
            </v-btn>
          </div>
        </div>
      </div>
    </div>

    <!-- Header -->
    <div class="grocery-header">
      <div class="header-content">
        <div class="logo" @click="goHome">
          <img :src="assets.logo" alt="" />
        </div>
        <!-- overlay -->
        <div
          v-if="searchFocused"
          class="grocery-overlay"
          @click="searchFocused = false"
        ></div>
        <div class="search-box" :class="{ focused: searchFocused }">
          <v-icon class="search-icon">mdi-magnify</v-icon>
          <input
            type="text"
            v-model="localSearchQuery"
            :placeholder="header && header.searchPlaceholder"
            @focus="searchFocused = true"
            @blur="onSearchBlur"
            @input="onSearchInput"
          />
        </div>
        <div class="login-btn">
          <v-btn variant="flat" @click="onLoginButtonClick">
            <span class="login-button-content">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" class="login-icon">
                <path fill="currentColor" d="M15.543 13.703c.36-.324.865-.462 1.314-.283C18.534 14.092 20 14.972 20 16c0 2.4-2.4 5.6-8 5.6S4 18.4 4 16c0-1.028 1.466-1.908 3.143-2.58.45-.18.954-.04 1.314.283.967.867 2.182 1.497 3.543 1.497 1.36 0 2.576-.63 3.543-1.497M12 2.4c2.65 0 4.8 1.808 4.8 4.9s-2.4 6.3-4.8 6.3-4.8-3.207-4.8-6.3S9.35 2.4 12 2.4"></path>
              </svg>
              <span>
                {{ loginButtonText }}
              </span>
            </span>
          </v-btn>
        </div>
        <div class="chat-btn">
          <v-btn variant="flat">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" class="chat-icon">
              <path fill="currentColor" fill-rule="evenodd" d="M12 2c5.523 0 10 4.477 10 10s-4.477 10-10 10a10 10 0 0 1-3.323-.565l-.44-.167-.08-.038c-.983-.504-1.958-.396-2.75-.119a5.2 5.2 0 0 0-1.217.621l-.058.043-.008.005-.003.003h.002a1 1 0 0 1-1.545-1.17l.007-.017.03-.08c.027-.072.067-.184.113-.326.09-.288.203-.696.286-1.172.158-.915.189-1.987-.156-2.94l-.073-.188A10 10 0 0 1 2 12C2 6.477 6.477 2 12 2m-4.5 8.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3m4.5 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3m4.5 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3" clip-rule="evenodd"></path>
            </svg>
          </v-btn>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent } from "vue";
import { mapGetters } from "vuex";
import { assets } from "@/assets/grocery-assets.js";
import { isGroceryLoggedIn, clearGroceryLogin } from "@/utils/localCache.js";
import { _logActivity } from "@/common/trackHelper";
import { isUnifiedBench } from "@/common/benchTheme";
import { pushBenchRoute } from "@/common/benchNavigation";
import BenchProfileInfoCard from "@/views/ui/BenchProfileInfoCard.vue";
import { getBenchPersonalInfo } from "@/common/benchPersonalInfo.js";

export default defineComponent({
  name: "GroceryHeader",
  components: { BenchProfileInfoCard },
  props: {
    header: {
      type: Object,
      default: () => ({}),
    },
    userShortName: {
      type: String,
      default: "",
    },
    isUserLoggedIn: {
      type: Boolean,
      default: false,
    },
    searchQuery: {
      type: String,
      default: "",
    },
  },
  data() {
    return {
      assets,
      searchFocused: false,
      drawerOpen: false,
      consent1: true,
      consent2: true,
      isLoggedIn: false,
      showLogoutConfirm: false,
      localSearchQuery: '',
      searchDebounceTimer: null,
    };
  },
  computed: {
    ...mapGetters(["trackConfig"]),
    loginButtonText() {
      return this.isLoggedIn ? this.displayShortName : (this.header && this.header.loginButton && this.header.loginButton.label) || 'Войти';
    },
    testData() {
      return (this.trackConfig && this.trackConfig.test_data) || {};
    },
    personalInfo() {
      return getBenchPersonalInfo(this.trackConfig);
    },
    displayShortName() {
      return this.personalInfo.shortName || this.userShortName || 'Пользователь';
    },
    userData() {
      return (this.testData && this.testData.user_data) || {};
    },
    loginData() {
      return (this.testData && this.testData.login_data) || {};
    },
    fullUserName() {
      return this.personalInfo.fullName;
    },
    userPhone() {
      return this.personalInfo.phone || '';
    },
    bonusPoints() {
      return this.userData.bonus_points || 0;
    },
  },
  methods: {
    checkLoginState() {
      this.isLoggedIn = isGroceryLoggedIn();
    },
    onLoginButtonClick() {
      if (this.isLoggedIn) {
        pushBenchRoute(this.$router, {
          name: 'bench_grocery_profile',
          stateId: 'state_profile',
          trackId: this.$route.params.track_id,
        });
        return;
      }
      this.drawerOpen = true;
    },
    closeDrawer() {
      this.drawerOpen = false;
      this.showLogoutConfirm = false;
    },
    handleSberLogin() {
      this.closeDrawer();
      
      try {
        const username = this.displayShortName || '';
        _logActivity(this, { type: 'authorize_sber_id', username });
      } catch (e) {console.error(e);}
      setTimeout(() => {
        const authState = isUnifiedBench(this.trackConfig)
          ? 'state_grocery_authorization'
          : 'state_authorization';
        const routeName = isUnifiedBench(this.trackConfig)
          ? 'bench_grocery_authorization'
          : 'bench_grocery_authorization';
        pushBenchRoute(this.$router, {
          name: routeName,
          stateId: authState,
          trackId: this.$route.params.track_id,
        });
      }, 500);
    },
    handleLogout() {
      this.showLogoutConfirm = true;
    },
    confirmLogout() {
      clearGroceryLogin();
      this.isLoggedIn = false;
      this.showLogoutConfirm = false;
      this.drawerOpen = false;
      try {
        const username = this.displayShortName || '';
        _logActivity(this, { type: 'logout', username });
      } catch (e) { console.error(e); }
      this.$emit('logout');
    },
    cancelLogout() {
      // Return to profile view in the same drawer
      this.showLogoutConfirm = false;
    },
    handleMenuClick(menuType) {
      // Handle menu item clicks (can be extended later)
      console.log('Menu clicked:', menuType);
    },
    goHome() {
      const mainState = isUnifiedBench(this.trackConfig)
        ? 'state_grocery_main'
        : 'state_main';
      const routeName = isUnifiedBench(this.trackConfig)
        ? 'bench_grocery_main'
        : 'bench_grocery_main';
      pushBenchRoute(this.$router, {
        name: routeName,
        stateId: mainState,
        trackId: this.$route.params.track_id,
      });
    },
    onSearchInput() {
      // Debounce search input
      if (this.searchDebounceTimer) {
        clearTimeout(this.searchDebounceTimer);
      }
      
      this.searchDebounceTimer = setTimeout(() => {
        const query = this.localSearchQuery.trim();
        if (query.length >= 3) {
          this.$emit('search', query);
        } else if (query.length === 0) {
          this.$emit('search', '');
        }
      }, 300);
    },
    onSearchBlur() {
      // Delay blur to allow click events
      setTimeout(() => {
        this.searchFocused = false;
      }, 150);
    },
  },
  watch: {
    isUserLoggedIn: {
      handler(newVal) {
        this.isLoggedIn = newVal;
      },
      immediate: true,
    },
    searchQuery: {
      handler(newVal) {
        this.localSearchQuery = newVal || '';
      },
      immediate: true,
    },
  },
  mounted() {
    this.checkLoginState();
  },
  activated() {
    this.checkLoginState();
  },
});
</script>

<style scoped>
/* Profile-specific drawer styles */
.profile-drawer .drawer-content {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 100%;
}

.profile-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.profile-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 20px 0 32px;
}

.profile-avatar {
  margin-bottom: 16px;
}

.profile-name {
  font-size: 24px;
  font-weight: 700;
  color: #333;
  margin-bottom: 3px;
}

.profile-phone {
  font-size: 14px;
  color: #aaa;
  font-weight: 600;
}

.profile-menu {
  margin-top: 0;
  border-top: 1px solid #e8e8e8;
}

.profile-menu-item {
  display: flex;
  align-items: center;
  padding: 16px 0;
  cursor: pointer;
  transition: background-color 0.2s;
  border-radius: 0px;
  border-bottom: 1px solid #e8e8e8;
}

/* .profile-menu-item:hover {
  background-color: #f8f8f8;
} */

.menu-item-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  flex-shrink: 0;
}

.menu-item-icon svg {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
}

.profile-menu-item span {
  font-size: 17px;
  color: #333;
  font-weight: 600;
  flex: 1;
}

.bonus-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.bonus-badge {
  background-color: var(--grocery-bg, var(--bench-surface-elevated, #f2f2f2));
  color: var(--grocery-text, var(--bench-text, #333));
  padding: 3px 6px;
  font-size: 14px;
  font-weight: 600;
  margin-left: auto;
  background: var(--grocery-bg, var(--bench-surface-elevated, #f2f2f2));
  border-radius: 14px 16px 16px 0;
}

.profile-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-top: 20px;
  margin-top: auto;
  width: 300px;
  align-self: center;
}

.contact-btn {
  width: 100%;
  height: 52px !important;
  background-color: var(--bench-primary-light, #f2f2f2) !important;
  color: var(--bench-text, #333) !important;
  font-size: 16px !important;
  font-weight: 500 !important;
  border-radius: 30px !important;
  text-transform: none !important;
  letter-spacing: normal !important;
}

.logout-btn {
  width: 100%;
  height: 52px !important;
  background-color: var(--bench-primary-light, #f2f2f2) !important;
  color: var(--bench-text, #333) !important;
  font-size: 16px !important;
  font-weight: 500 !important;
  border-radius: 30px !important;
  text-transform: none !important;
  letter-spacing: normal !important;
}

/* Logout confirmation content styles (shown in same drawer) */
.logout-confirm-content {
  justify-content: center !important;
  align-items: center;
}

.logout-confirm-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  gap: 16px;
  padding: 40px 24px;
}

.logout-confirm-title {
  font-size: 28px;
  font-weight: 600;
  color: #333;
  margin: 0 0 24px 0;
  text-align: center;
}

.logout-confirm-yes-btn {
  width: 100%;
  max-width: 300px;
  height: 52px !important;
  background-color: #f3345c !important;
  color: white !important;
  font-size: 16px !important;
  font-weight: 500 !important;
  border-radius: 26px !important;
  text-transform: none !important;
  letter-spacing: normal !important;
  box-shadow: none !important;
}

.logout-confirm-yes-btn:hover {
  background-color: #d92e50 !important;
}

.logout-confirm-no-btn {
  width: 100%;
  max-width: 300px;
  height: 52px !important;
  background-color: var(--bench-primary-light, #f2f2f2) !important;
  color: var(--bench-text, #333) !important;
  font-size: 16px !important;
  font-weight: 500 !important;
  border-radius: 26px !important;
  text-transform: none !important;
  letter-spacing: normal !important;
  box-shadow: none !important;
}

.logout-confirm-no-btn:hover {
  background-color: #e8e8e8 !important;
}

.logo {
  cursor: pointer;
}
</style>
