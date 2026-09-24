<template>
  <div>
    <!-- Overlay -->
    <div v-if="isOpen" class="checkout-overlay" @click="close"></div>
    
    <!-- Drawer -->
    <div class="checkout-drawer" :class="{ open: isOpen, 'payment-step': isPaymentStep }" role="dialog" aria-modal="true">
      <div class="drawer-header">
        <v-btn v-if="isPaymentStep" class="drawer-back" variant="flat" @click="backToBasket">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 16 16" color="#404040" style="min-width: 16px; min-height: 16px;"><path fill="currentColor" d="M8.707 14.707a1 1 0 0 1-1.414 0L1.328 8.742l-.016-.018a.996.996 0 0 1 0-1.448q.008-.01.016-.018l5.965-5.965a1 1 0 0 1 1.414 1.414L4.755 6.658A.2.2 0 0 0 4.897 7H14a1 1 0 0 1 0 2H4.897a.2.2 0 0 0-.142.341l3.952 3.952a1 1 0 0 1 0 1.414"></path></svg>
        </v-btn>
        <div class="checkout-address-header">
          <h2 v-if="!isPaymentStep">{{ deliveryAddress }}</h2>
          <h2 v-else>Адрес и оплата</h2>
        </div>
        <v-btn class="drawer-close" variant="flat" @click="close">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 16 16">
            <path fill="currentColor" d="M13.707 2.293a1 1 0 0 1 0 1.414l-3.515 3.515a1.1 1.1 0 0 0 0 1.555l3.515 3.516a1 1 0 0 1-1.414 1.414l-3.515-3.515a1.1 1.1 0 0 0-1.556 0l-1.515 1.515v.001l-2 2a1 1 0 0 1-1.414-1.415l3.515-3.515v-.001a1.1 1.1 0 0 0 0-1.555L2.293 3.707a1 1 0 0 1 1.414-1.414l2 2 1.515 1.515a1.1 1.1 0 0 0 1.555 0l3.516-3.515a1 1 0 0 1 1.414 0"></path>
          </svg>
        </v-btn>
      </div>

      <div class="drawer-content">
        <div v-if="!isPaymentStep" class="checkout-main">
          <!-- Left column -->
          <div class="checkout-left">
            <!-- Address header moved to drawer header -->

            <!-- Basket items -->
            <div class="checkout-basket-section">
              <div class="checkout-basket-title">
                <span class="delivery-time">Доставка 15 минут</span>
              </div>
              <div class="basket-items-list">
                <div
                  v-for="(item, idx) in displayedBasketItems"
                  :key="idx"
                  class="checkout-basket-item"
                >
                  <div class="checkout-item-image">
                    <img :src="groceryImageSrc(item)" :alt="item.title" />
                  </div>
                  <div class="checkout-item-info">
                    <div class="checkout-item-title">{{ item.title }}</div>
                    <div class="checkout-item-amount">{{ item.amount }}</div>
                    <div class="checkout-item-footer">
                      <div class="checkout-item-controls">
                        <div class="control-btn" @click="decrementItem(item.item_id)">
                          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24">
                            <path fill="currentColor" d="M0 12a1 1 0 0 1 1-1h22a1 1 0 1 1 0 2H1a1 1 0 0 1-1-1"></path>
                          </svg>
                        </div>
                        <span class="item-quantity">{{ item.quantity }}</span>
                        <div class="control-btn" @click="incrementItem(item.item_id)">
                          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24">
                            <g clip-path="url(#clip0_checkout)">
                              <path fill="currentColor" d="M12 0a1 1 0 0 1 1 1v8.5a1.5 1.5 0 0 0 1.5 1.5H23a1 1 0 1 1 0 2h-8.5a1.5 1.5 0 0 0-1.5 1.5V23a1 1 0 1 1-2 0v-8.5A1.5 1.5 0 0 0 9.5 13H1a1 1 0 1 1 0-2h8.5A1.5 1.5 0 0 0 11 9.5V1a1 1 0 0 1 1-1"></path>
                            </g>
                            <defs>
                              <clipPath id="clip0_checkout">
                                <path fill="#fff" d="M0 0h24v24H0z"></path>
                              </clipPath>
                            </defs>
                          </svg>
                        </div>
                      </div>
                      <div class="checkout-item-prices">
                        <span v-if="item.old_price" class="checkout-old-price">{{ Math.round(parseFloat(item.old_price) * item.quantity) }}</span>
                        <span class="checkout-item-price">{{ Math.round(parseFloat(item.price) * item.quantity) }} ₽</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div v-if="basketItems.length > 3" class="show-more-section">
                <button class="show-more-btn" @click="toggleShowAll">
                  {{ showAllItems ? 'Свернуть' : `Показать еще ${basketItems.length - 3}` }}
                </button>
              </div>
            </div>

            <!-- Add to order section -->
            <div class="add-to-order-section">
              <h3>Добавить к заказу?</h3>
              <div class="add-items-grid">
                <div
                  v-for="(item, idx) in randomItems"
                  :key="idx"
                  class="add-item-card"
                >
                  <div class="add-item-image-container">
                    <div v-if="item.old_price" class="add-item-discount">
                      −{{ calculateDiscount(item.price, item.old_price) }}%
                    </div>
                    <img :src="groceryImageSrc(item)" :alt="item.title" />
                    <div v-if="getItemQuantity(item.item_id) > 0" class="add-item-overlay">
                      <span class="add-overlay-quantity">{{ getItemQuantity(item.item_id) }}</span>
                    </div>
                  </div>
                  <div class="add-item-info">
                    <div class="add-item-title">{{ item.title }}</div>
                    <div class="add-item-meta">
                      <span v-if="item.amount" class="add-item-amount">{{ item.amount }}</span>
                    </div>
                    <div class="add-item-actions" :class="{ 'in-basket': getItemQuantity(item.item_id) > 0 }">
                      <div v-if="getItemQuantity(item.item_id) > 0" class="add-action-btn" @click="decrementItem(item.item_id)">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="none" viewBox="0 0 24 24">
                          <path fill="currentColor" d="M0 12a1 1 0 0 1 1-1h22a1 1 0 1 1 0 2H1a1 1 0 0 1-1-1"></path>
                        </svg>
                      </div>
                      <div class="add-price-container">
                        <span v-if="item.old_price && getItemQuantity(item.item_id) === 0" class="add-old-price">{{ item.old_price }}</span>
                        <span class="add-current-price">{{ item.price }} ₽</span>
                      </div>
                      <div class="add-action-btn" @click="incrementItem(item.item_id)">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="none" viewBox="0 0 24 24">
                          <g clip-path="url(#clip0_add)">
                            <path fill="currentColor" d="M12 0a1 1 0 0 1 1 1v8.5a1.5 1.5 0 0 0 1.5 1.5H23a1 1 0 1 1 0 2h-8.5a1.5 1.5 0 0 0-1.5 1.5V23a1 1 0 1 1-2 0v-8.5A1.5 1.5 0 0 0 9.5 13H1a1 1 0 1 1 0-2h8.5A1.5 1.5 0 0 0 11 9.5V1a1 1 0 0 1 1-1"></path>
                          </g>
                          <defs>
                            <clipPath id="clip0_add">
                              <path fill="#fff" d="M0 0h24v24H0z"></path>
                            </clipPath>
                          </defs>
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Right column -->
          <div class="checkout-right">
            <!-- Benefits section -->
            <div class="benefits-section">
              <h3 class="benefits-title">Скидки и выгода</h3>
              
              <!-- Promo code / discount -->
              <div class="benefit-item" style="padding-top: 15px;">
                <div class="benefit-header">
                  <div class="benefit-label">
                    <span>Скидка или промокод</span>
                    <div class="benefit-dot"></div>
                  </div>
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" class="benefit-icon" color="#A6A6A6" style="min-width: 24px; min-height: 24px;"><path fill="currentColor" d="M8.293 4.293a1 1 0 0 0 0 1.414L14.586 12l-6.293 6.293a1 1 0 1 0 1.414 1.414l7-7a1 1 0 0 0 0-1.414l-7-7a1 1 0 0 0-1.414 0"></path></svg>
                </div>
              </div>

              <!-- SberSpasibo -->
              <div class="benefit-item">
                <div class="benefit-header">
                  <div class="benefit-label">
                    <span>Бонусы</span>
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="none" viewBox="0 0 14 14"><path fill="#fff" d="M7 0C3.15 0 0 3.15 0 7v7h7c3.85 0 7-3.15 7-7s-3.15-7-7-7m.058 10.733c-2.041 0-3.733-1.692-3.733-3.733s1.692-3.733 3.733-3.733c1.167 0 2.216.525 2.917 1.4L8.458 5.89a1.78 1.78 0 0 0-1.4-.641c-.992 0-1.75.816-1.75 1.75 0 .992.817 1.75 1.75 1.75.525 0 1.05-.233 1.4-.7l1.575 1.224c-.7.934-1.808 1.46-2.975 1.46"></path><path fill="url(#paint0_linear_18722_348)" d="M7 0C3.15 0 0 3.15 0 7v7h7c3.85 0 7-3.15 7-7s-3.15-7-7-7m.058 10.733c-2.041 0-3.733-1.692-3.733-3.733s1.692-3.733 3.733-3.733c1.167 0 2.216.525 2.917 1.4L8.458 5.89a1.78 1.78 0 0 0-1.4-.641c-.992 0-1.75.816-1.75 1.75 0 .992.817 1.75 1.75 1.75.525 0 1.05-.233 1.4-.7l1.575 1.224c-.7.934-1.808 1.46-2.975 1.46"></path><defs><linearGradient id="paint0_linear_18722_348" x1="13.906" x2="-1.973" y1="0" y2="2.796" gradientUnits="userSpaceOnUse"><stop stop-color="#0BADBF"></stop><stop offset="0.51" stop-color="#34C61A"></stop><stop offset="1" stop-color="#E1EE05"></stop></linearGradient></defs></svg>
                  </div>
                </div>
                <div class="benefit-right-control">
                  <v-switch v-model="sberSpasiboEnabled" color="#21A038" hide-details density="compact"></v-switch>
                </div>
                <div class="benefit-info">
                  У вас {{ bonusPoints }} бонус{{ bonusText }} — спишем {{ Math.min(bonusPoints, Math.floor(basketTotal * 0.99)) }}
                </div>
              </div>

              <!-- SberPrime -->
              <div class="benefit-item">
                <div class="benefit-header">
                  <div class="benefit-label">
                    <span>Подписка</span>
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 16 16"><path fill="url(#paint0_linear_4249_2757)" d="M15 1.626 1 2.95v11.347l14-1.324-2.535-5.531z"></path><path fill="#fff" d="M9.413 6.065q.219.293.369.633l-2.806 2.14-1.172-.761v-.914l1.172.76zm.642 1.948a3.3 3.3 0 0 0-.049-.571l-.663.505v.065c0 1.35-1.061 2.45-2.367 2.45-1.305 0-2.368-1.099-2.368-2.45 0-1.35 1.062-2.45 2.368-2.45a2.3 2.3 0 0 1 1.335.428l.598-.456a3 3 0 0 0-1.933-.707c-1.7 0-3.08 1.426-3.08 3.185s1.38 3.185 3.08 3.185 3.08-1.425 3.08-3.184"></path><defs><linearGradient id="paint0_linear_4249_2757" x1="14.906" x2="-0.868" y1="1.626" y2="4.695" gradientUnits="userSpaceOnUse"><stop stop-color="#0BADBF"></stop><stop offset="0.51" stop-color="#34C61A"></stop><stop offset="1" stop-color="#E1EE05"></stop></linearGradient></defs></svg>
                  </div>
                </div>
                <svg class="benefit-close-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 16 16" color="#A6A6A6" style="min-width: 16px; min-height: 16px;"><path fill="currentColor" d="M11.652 3.231a.79.79 0 1 1 1.117 1.117L9.823 7.293a1 1 0 0 0 0 1.414l2.946 2.945.054.06a.79.79 0 0 1-1.111 1.111l-.06-.054-2.945-2.946a1 1 0 0 0-1.414 0L4.348 12.77l-.06.054a.79.79 0 0 1-1.111-1.111l.054-.06 2.946-2.945a1 1 0 0 0 0-1.414L3.23 4.348A.79.79 0 0 1 4.348 3.23l2.945 2.946a1 1 0 0 0 1.414 0z"></path></svg>
                <div class="benefit-info" style="padding-right:20px;">
                  С подпиской вы получите 22 бонуса за этот заказ и до 9% за следующие
                </div>
              </div>
            </div>

            <!-- Summary section -->
            <div class="checkout-summary">
              <div class="summary-row">
                <div class="summary-label">Итого</div>
                <div class="summary-total">{{ basketTotal }} ₽</div>
              </div>
              <v-btn class="checkout-continue-btn" color="primary" block @click="continueToPayment">
                <span class="btn-title">Продолжить</span>
                <span class="btn-subtitle">К адресу и оплате</span>
              </v-btn>
            </div>
          </div>
        </div>
        
        <!-- Address and payment step -->
        <div v-else class="checkout-details">
          <!-- Details rows view -->
          <div v-if="!isChoosingPayment" class="details-list">
            <!-- Address -->
            <div class="detail-row">
              <div class="detail-text">
                <div class="detail-title">{{ addressLine }}</div>
                <div v-if="addressDetails" class="detail-subtitle">{{ addressDetails }}</div>
              </div>
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" class="detail-arrow" color="#404040"><path fill="currentColor" d="M8.293 4.293a1 1 0 0 0 0 1.414L14.586 12l-6.293 6.293a1 1 0 1 0 1.414 1.414l7-7a1 1 0 0 0 0-1.414l-7-7a1 1 0 0 0-1.414 0"></path></svg>
            </div>

            <!-- Leave at door switch -->
            <div class="detail-row">
              <div class="detail-text-only">Оставить у двери</div>
              <div class="detail-control">
                <v-switch v-model="leaveAtDoor" color="#21A038" hide-details density="compact"></v-switch>
              </div>
            </div>

            <!-- Payment method -->
            <div class="detail-row" @click="openPaymentSelection">
              <div class="detail-icon">
                <!-- Card icon or SberPay icon based on method -->
                <template v-if="selectedPaymentMethod === 'card'">
                  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="none" viewBox="0 0 24 24" style="min-width: 32px; min-height: 32px;"><rect width="19.5" height="13.5" x="2.25" y="5.25" fill="#E0E0E0" rx="3"></rect><g clip-path="url(#clip0_1_1104)"><path fill="#FF5F00" d="M13.798 9.086h-3.555v5.816h3.555z"></path><path fill="#EB001B" d="M10.61 11.995a3.7 3.7 0 0 1 1.41-2.908 3.69 3.69 0 0 0-5.412.946 3.703 3.703 0 0 0 1.516 5.29 3.69 3.69 0 0 0 3.896-.42 3.69 3.69 0 0 1-1.41-2.908"></path><path fill="#F79E1B" d="M17.641 14.287v-.12h.051v-.024h-.122v.025h.049v.119zm.237 0v-.144h-.037l-.043.103-.043-.103h-.037v.144h.027v-.109l.04.094h.027l.04-.094v.109zM17.994 11.994a3.7 3.7 0 0 1-2.079 3.327 3.69 3.69 0 0 1-3.895-.42 3.7 3.7 0 0 0 1.41-2.907 3.7 3.7 0 0 0-1.41-2.908 3.69 3.69 0 0 1 5.974 2.907z"></path></g><defs><clipPath id="clip0_1_1104"><path fill="#fff" d="M6 8.25h12v7.5H6z"></path></clipPath></defs></svg>
                </template>
                <template v-else>
                  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="none" viewBox="0 0 24 24" style="min-width: 32px; min-height: 32px;"><path fill="#0C9C0C" d="M1.5 12c0-2.9 2.35-5.25 5.25-5.25h10.5a5.25 5.25 0 1 1 0 10.5H6.75A5.25 5.25 0 0 1 1.5 12"></path><path fill="url(#paint0_radial_1_1128)" d="M1.5 12c0-2.9 2.35-5.25 5.25-5.25h10.5a5.25 5.25 0 1 1 0 10.5H6.75A5.25 5.25 0 0 1 1.5 12"></path><path fill="url(#paint1_radial_1_1128)" d="M1.5 12c0-2.9 2.35-5.25 5.25-5.25h10.5a5.25 5.25 0 1 1 0 10.5H6.75A5.25 5.25 0 0 1 1.5 12"></path><path fill="url(#paint2_radial_1_1128)" d="M1.5 12c0-2.9 2.35-5.25 5.25-5.25h10.5a5.25 5.25 0 1 1 0 10.5H6.75A5.25 5.25 0 0 1 1.5 12"></path><path fill="url(#paint3_radial_1_1128)" d="M1.5 12c0-2.9 2.35-5.25 5.25-5.25h10.5a5.25 5.25 0 1 1 0 10.5H6.75A5.25 5.25 0 0 1 1.5 12"></path><path fill="#fff" d="M11.973 12.57v1.198h-.687V9.921h1.28c1.214 0 1.73.435 1.73 1.303 0 .896-.604 1.346-1.73 1.346zm0-2.016v1.383h.645c.637 0 .967-.208.967-.73 0-.473-.287-.654-.955-.654zM14.66 11.213c.18-.135.51-.247.983-.247.802 0 1.198.275 1.198.99v1.813h-.605v-.495c-.132.318-.466.539-.907.539-.554 0-.883-.314-.883-.852 0-.627.456-.803 1.13-.803h.622v-.12c0-.39-.187-.511-.555-.511-.506 0-.797.197-.983.489zm1.537 1.586v-.223h-.543c-.38 0-.561.072-.561.319 0 .208.153.34.44.34.433 0 .637-.247.664-.436M17.158 11.02h.717l.753 1.885.615-1.884h.681l-1.098 3.039c-.243.659-.49.807-.852.807-.17 0-.358-.05-.44-.12v-.6a.49.49 0 0 0 .33.138c.197 0 .346-.132.45-.502zM5.632 11.216v.844l1.118.701 2.678-1.97a3 3 0 0 0-.353-.585L6.75 11.917z"></path><path fill="#fff" d="M9.01 11.938v.06a2.262 2.262 0 1 1-.987-1.864l.574-.42a2.939 2.939 0 1 0 1.044 1.759z"></path><defs><radialGradient id="paint0_radial_1_1128" cx="0" cy="0" r="1" gradientTransform="matrix(11.273 0 0 10.6132 1.5 6.75)" gradientUnits="userSpaceOnUse"><stop stop-color="#15D015"></stop><stop offset="1" stop-color="#15D015" stop-opacity="0"></stop></radialGradient><radialGradient id="paint1_radial_1_1128" cx="0" cy="0" r="1" gradientTransform="matrix(11.4018 0 0 18.512 .598 6.75)" gradientUnits="userSpaceOnUse"><stop stop-color="#FAED05"></stop><stop offset="1" stop-color="#0C9C0C" stop-opacity="0"></stop></radialGradient><radialGradient id="paint2_radial_1_1128" cx="0" cy="0" r="1" gradientTransform="matrix(-8.11657 0 0 -7.20371 23.305 6.75)" gradientUnits="userSpaceOnUse"><stop stop-color="#42E3B4"></stop><stop offset="1" stop-color="#15D015" stop-opacity="0"></stop></radialGradient><radialGradient id="paint3_radial_1_1128" cx="0" cy="0" r="1" gradientTransform="matrix(-20.6135 0 0 -19.33 22.5 17.25)" gradientUnits="userSpaceOnUse"><stop stop-color="#129DFA"></stop><stop offset="1" stop-color="#15D015" stop-opacity="0"></stop></radialGradient></defs></svg>
                </template>
              </div>
              <div class="detail-text">
                <template v-if="selectedPaymentMethod === 'card'">
                  <span class="detail-title">Оплата картой&nbsp; {{ maskedLast4 }}</span>
                </template>
                <template v-else>
                  <div class="detail-title">Оплата co SberPay <template v-if="last4">&nbsp;{{ maskedLast4 }}</template></div>
                  <div v-if="!last4" class="detail-subtitle">Если есть аккаунт с тем же телефоном</div>
                </template>
              </div>
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" class="detail-arrow" color="#404040"><path fill="currentColor" d="M8.293 4.293a1 1 0 0 0 0 1.414L14.586 12l-6.293 6.293a1 1 0 1 0 1.414 1.414l7-7a1 1 0 0 0 0-1.414l-7-7a1 1 0 0 0-1.414 0"></path></svg>
            </div>
          </div>

          <!-- Summary section identical to previous step -->
          <div v-if="!isChoosingPayment" class="checkout-summary">
            <div class="summary-row">
              <div class="summary-label">Итого</div>
              <div class="summary-total">{{ basketTotal }} ₽</div>
            </div>
            <v-btn class="checkout-continue-btn" :loading="isSubmitting" :disabled="isSubmitting" color="primary" block @click="submitPayment" style="height: 56px !important;">
              <template v-if="!isSubmitting">Оплатить</template>
              <template v-else>
                <v-progress-circular indeterminate size="22" width="3" color="white"></v-progress-circular>
              </template>
            </v-btn>
          </div>

          <!-- Payment choosing view -->
          <div v-else class="payment-choose">
            <div class="payment-grid">
              <!-- New card tile -->
              <div class="pm-card pm-new" :class="{ 'pm-active': selectedPaymentTile === 'new_card' }" @click="onTileClick('new_card')">
                <span class="pm-title">Новая карта</span>
                <div class="pm-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="none" viewBox="0 0 24 24" style="min-width: 32px; min-height: 32px;"><rect width="19.5" height="13.5" x="2.25" y="5.25" fill="#E0E0E0" rx="3"></rect><path fill="#BFBFBF" fill-rule="evenodd" d="M12 7.95a.613.613 0 0 0-.612.613v2.656a.17.17 0 0 1-.17.168H8.564a.613.613 0 0 0 0 1.226h2.662c.09.003.163.077.163.168v2.657a.613.613 0 0 0 1.225 0V12.78c0-.09.072-.165.162-.168h2.663a.612.612 0 1 0 0-1.225H12.78a.17.17 0 0 1-.168-.17V8.564A.61.61 0 0 0 12 7.95" clip-rule="evenodd"></path></svg>
                </div>
              </div>

              <!-- Existing method with last4 if provided -->
              <div v-if="last4" class="pm-card pm-active" :class="{ 'pm-active': selectedPaymentTile === 'existing' }" @click="onTileClick('existing')">
                <span class="pm-title">{{ selectedPaymentMethod === 'card' ? 'Карта' : 'SberPay' }} {{ maskedLast4 }}</span>
                <div class="pm-icon">
                  <div class="pm-bank">
                    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="none" viewBox="0 0 24 24" style="min-width: 32px; min-height: 32px;"><path fill="#0C9C0C" d="M1.5 12c0-2.9 2.35-5.25 5.25-5.25h10.5a5.25 5.25 0 1 1 0 10.5H6.75A5.25 5.25 0 0 1 1.5 12"></path><path fill="url(#paint0_radial_pm)" d="M1.5 12c0-2.9 2.35-5.25 5.25-5.25h10.5a5.25 5.25 0 1 1 0 10.5H6.75A5.25 5.25 0 0 1 1.5 12"></path><path fill="url(#paint1_radial_pm)" d="M1.5 12c0-2.9 2.35-5.25 5.25-5.25h10.5a5.25 5.25 0 1 1 0 10.5H6.75A5.25 5.25 0 0 1 1.5 12"></path><path fill="url(#paint2_radial_pm)" d="M1.5 12c0-2.9 2.35-5.25 5.25-5.25h10.5a5.25 5.25 0 1 1 0 10.5H6.75A5.25 5.25 0 0 1 1.5 12"></path><path fill="url(#paint3_radial_pm)" d="M1.5 12c0-2.9 2.35-5.25 5.25-5.25h10.5a5.25 5.25 0 1 1 0 10.5H6.75A5.25 5.25 0 0 1 1.5 12"></path><path fill="#fff" d="M11.973 12.57v1.198h-.687V9.921h1.28c1.214 0 1.73.435 1.73 1.303 0 .896-.604 1.346-1.73 1.346zm0-2.016v1.383h.645c.637 0 .967-.208.967-.73 0-.473-.287-.654-.955-.654zM14.66 11.213c.18-.135.51-.247.983-.247.802 0 1.198.275 1.198.99v1.813h-.605v-.495c-.132.318-.466.539-.907.539-.554 0-.883-.314-.883-.852 0-.627.456-.803 1.13-.803h.622v-.12c0-.39-.187-.511-.555-.511-.506 0-.797.197-.983.489zm1.537 1.586v-.223h-.543c-.38 0-.561.072-.561.319 0 .208.153.34.44.34.433 0 .637-.247.664-.436M17.158 11.02h.717l.753 1.885.615-1.884h.681l-1.098 3.039c-.243.659-.49.807-.852.807-.17 0-.358-.05-.44-.12v-.6a.49.49 0 0 0 .33.138c.197 0 .346-.132.45-.502zM5.632 11.216v.844l1.118.701 2.678-1.97a3 3 0 0 0-.353-.585L6.75 11.917z"></path><path fill="#fff" d="M9.01 11.938v.06a2.262 2.262 0 1 1-.987-1.864l.574-.42a2.939 2.939 0 1 0 1.044 1.759z"></path><defs><radialGradient id="paint0_radial_pm" cx="0" cy="0" r="1" gradientTransform="matrix(11.273 0 0 10.6132 1.5 6.75)" gradientUnits="userSpaceOnUse"><stop stop-color="#15D015"></stop><stop offset="1" stop-color="#15D015" stop-opacity="0"></stop></radialGradient><radialGradient id="paint1_radial_pm" cx="0" cy="0" r="1" gradientTransform="matrix(11.4018 0 0 18.512 .598 6.75)" gradientUnits="userSpaceOnUse"><stop stop-color="#FAED05"></stop><stop offset="1" stop-color="#0C9C0C" stop-opacity="0"></stop></radialGradient><radialGradient id="paint2_radial_pm" cx="0" cy="0" r="1" gradientTransform="matrix(-8.11657 0 0 -7.20371 23.305 6.75)" gradientUnits="userSpaceOnUse"><stop stop-color="#42E3B4"></stop><stop offset="1" stop-color="#15D015" stop-opacity="0"></stop></radialGradient><radialGradient id="paint3_radial_pm" cx="0" cy="0" r="1" gradientTransform="matrix(-20.6135 0 0 -19.33 22.5 17.25)" gradientUnits="userSpaceOnUse"><stop stop-color="#129DFA"></stop><stop offset="1" stop-color="#15D015" stop-opacity="0"></stop></radialGradient></defs></svg>
                    <span class="pm-bank-name">Банк</span>
                  </div>
                </div>
              </div>

              <!-- SberPay tile (no card) -->
              <div class="pm-card pm-new" :class="{ 'pm-active': selectedPaymentTile === 'sberpay' }" @click="onTileClick('sberpay')">
                <span class="pm-title">SberPay</span>
                <div class="pm-icon">
                  <div class="pm-bank">
                    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="none" viewBox="0 0 24 24" style="min-width: 32px; min-height: 32px;"><path fill="#0C9C0C" d="M1.5 12c0-2.9 2.35-5.25 5.25-5.25h10.5a5.25 5.25 0 1 1 0 10.5H6.75A5.25 5.25 0 0 1 1.5 12"></path><path fill="url(#paint0_radial_pm)" d="M1.5 12c0-2.9 2.35-5.25 5.25-5.25h10.5a5.25 5.25 0 1 1 0 10.5H6.75A5.25 5.25 0 0 1 1.5 12"></path><path fill="url(#paint1_radial_pm)" d="M1.5 12c0-2.9 2.35-5.25 5.25-5.25h10.5a5.25 5.25 0 1 1 0 10.5H6.75A5.25 5.25 0 0 1 1.5 12"></path><path fill="url(#paint2_radial_pm)" d="M1.5 12c0-2.9 2.35-5.25 5.25-5.25h10.5a5.25 5.25 0 1 1 0 10.5H6.75A5.25 5.25 0 0 1 1.5 12"></path><path fill="url(#paint3_radial_pm)" d="M1.5 12c0-2.9 2.35-5.25 5.25-5.25h10.5a5.25 5.25 0 1 1 0 10.5H6.75A5.25 5.25 0 0 1 1.5 12"></path></svg>
                  </div>
                </div>
              </div>
            </div>

            <div class="checkout-summary">
              <div class="summary-row">
                <div class="summary-label">Сохранить</div>
                <div class="summary-total">{{ basketTotal }} ₽</div>
              </div>
              <v-btn class="checkout-continue-btn" :loading="savingPayment" color="primary" block @click="savePaymentSelection" style="height: 56px !important;">
                <template v-if="!savingPayment">Сохранить</template>
                <template v-else>
                  <v-progress-circular indeterminate size="22" width="3" color="white"></v-progress-circular>
                </template>
              </v-btn>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent } from "vue";
import { getGroceryBasket, incrementGroceryBasketItem, getGroceryCurrentUser } from "@/utils/localCache.js";
import { groceryImageSrc } from "@/common/groceryImages";

export default defineComponent({
  name: "CheckoutDrawer",
  props: {
    isOpen: {
      type: Boolean,
      default: false
    },
    deliveryAddress: {
      type: String,
      default: ''
    },
    bonusPoints: {
      type: Number,
      default: 0
    },
    kvStore: {
      type: Object,
      default: () => ({})
    },
    userData: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      showAllItems: false,
      sberSpasiboEnabled: true,
      sberPrimeEnabled: false,
      basket: {},
      basketRefreshKey: 0,
      isPaymentStep: false,
      leaveAtDoor: false,
      selectedPaymentMethod: 'card',
      cardNumber: '',
      isChoosingPayment: false,
      savingPayment: false,
      selectedPaymentTile: null,
      isSubmitting: false
    };
  },
  computed: {
    basketItems() {
      this.basketRefreshKey; // eslint-disable-line no-unused-expressions
      const basketMap = getGroceryBasket();
      const items = [];
      
      for (const [itemId, quantity] of Object.entries(basketMap)) {
        if (quantity > 0 && this.kvStore[itemId]) {
          const kvItem = this.kvStore[itemId];
          items.push({
            ...kvItem,
            quantity
          });
        }
      }
      
      return items;
    },
    displayedBasketItems() {
      if (this.showAllItems) {
        return this.basketItems;
      }
      return this.basketItems.slice(0, 3);
    },
    basketTotal() {
      return this.basketItems.reduce((sum, item) => {
        const price = parseFloat(item.price) || 0;
        return sum + (price * item.quantity);
      }, 0);
    },
    bonusText() {
      const count = this.bonusPoints;
      if (count % 10 === 1 && count % 100 !== 11) return '';
      if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) 'а';
      return 'ов';
    },
    randomItems() {
      const allItems = Object.values(this.kvStore || {});
      if (allItems.length === 0) return [];
      
      // Shuffle and take 20 items
      const shuffled = [...allItems].sort(() => Math.random() - 0.5);
      return shuffled.slice(0, 20);
    },
    addressLine() {
      return (this.userData && this.userData.address) || this.deliveryAddress || '';
    },
    addressDetails() {
      return (this.userData && this.userData.address_details) || '';
    },
    last4() {
      const num = String(this.cardNumber || '').replace(/\D/g, '');
      return num ? num.slice(-4) : '';
    },
    maskedLast4() {
      return this.last4 ? `••• ${this.last4}` : '';
    }
  },
  methods: {
    groceryImageSrc,
    close() {
      this.$emit('close');
    },
    toggleShowAll() {
      this.showAllItems = !this.showAllItems;
    },
    calculateDiscount(currentPrice, oldPrice) {
      const current = parseFloat(currentPrice);
      const old = parseFloat(oldPrice);
      if (!old || old === 0) return 0;
      const discount = Math.round(((old - current) / old) * 100);
      return discount > 0 ? discount : 0;
    },
    getItemQuantity(itemId) {
      this.basketRefreshKey; // eslint-disable-line no-unused-expressions
      const basketMap = getGroceryBasket();
      return basketMap[itemId] || 0;
    },
    loadBasket() {
      const username = getGroceryCurrentUser() || 'guest';
      this.basket = getGroceryBasket(username);
      this.basketRefreshKey++;
    },
    incrementItem(itemId) {
      const username = getGroceryCurrentUser() || 'guest';
      incrementGroceryBasketItem(username, itemId, 1);
      this.loadBasket();
      this.$emit('basket-updated');
    },
    decrementItem(itemId) {
      const username = getGroceryCurrentUser() || 'guest';
      incrementGroceryBasketItem(username, itemId, -1);
      this.loadBasket();
      this.$emit('basket-updated');
    },
    continueToPayment() {
      this.isPaymentStep = true;
      this.leaveAtDoor = !!(this.userData && this.userData.on_door);
      this.selectedPaymentMethod = (this.userData && this.userData.payment_method) || 'card';
      this.cardNumber = (this.userData && this.userData.card_number) || '';
    },
    backToBasket() {
      if (this.isChoosingPayment) {
        this.isChoosingPayment = false;
        return;
      }
      this.isPaymentStep = false;
    },
    submitPayment() {
      this.isSubmitting = true;
      setTimeout(() => {
        this.isSubmitting = false;
        this.$emit('proceed-payment', { basketTotal: this.basketTotal });
      }, 200);
    },
    openPaymentSelection() {
      this.isChoosingPayment = true;
    },
    onTileClick(tile) {
      this.selectedPaymentTile = tile;
      // start loader and then go back
      this.savingPayment = true;
      setTimeout(() => {
        this.savingPayment = false;
        // Return to the payment details screen (same as clicking back within payment step)
        this.isChoosingPayment = false;
        this.isPaymentStep = true;
      }, 200);
    },
    savePaymentSelection() {
      this.savingPayment = true;
      setTimeout(() => {
        this.savingPayment = false;
        // Return to payment details list and keep current step
        this.isChoosingPayment = false;
        this.isPaymentStep = true;
      }, 200);
    }
  },
  watch: {
    isOpen(newVal) {
      if (newVal) {
        this.loadBasket();
        this.showAllItems = false;
        // Reset step to first when reopened
        this.isPaymentStep = false;
      }
    },
    userData: {
      handler() {
        if (this.isPaymentStep) {
          this.leaveAtDoor = !!(this.userData && this.userData.on_door);
          this.selectedPaymentMethod = (this.userData && this.userData.payment_method) || 'card';
          this.cardNumber = (this.userData && this.userData.card_number) || '';
      }
      },
      deep: true
    }
  },
  mounted() {
    this.loadBasket();
    
    // Poll for basket changes
    this.basketInterval = setInterval(() => {
      const username = getGroceryCurrentUser() || 'guest';
      const currentBasket = JSON.stringify(getGroceryBasket(username));
      const previousBasket = JSON.stringify(this.basket);
      if (currentBasket !== previousBasket) {
        this.loadBasket();
      }
    }, 500);
  },
  beforeUnmount() {
    if (this.basketInterval) {
      clearInterval(this.basketInterval);
    }
  }
});
</script>

<style scoped>
.bench-grocery {
  --shop-max-width: 1600px;
}

.checkout-continue-btn {
  border-radius: 35px;
  text-transform: none;
  font-weight: 600;
  letter-spacing: 0;
  color: white !important;
  font-size: 17px;
  height: 70px !important;
  box-shadow: none !important;
  line-height: 1.2;
}

.checkout-continue-btn .btn-title {
  display: block;
  font-size: 18px;
  font-weight: 800;
  line-height: 1;
}

.checkout-continue-btn .btn-subtitle {
  display: block;
  font-size: 12px;
  font-weight: 600;
  opacity: 0.7;
}

.checkout-continue-btn :deep(.v-btn__content) {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
}
</style>

