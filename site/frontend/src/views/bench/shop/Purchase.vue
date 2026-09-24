<template>
  <div v-if="configLoaded" class="bench-market purchase-page">
    <div class="simple-header">
      <div class="simple-header-content">
        <div class="header-logo" @click="goToMainPage">
          <img :src="logoSrc" alt="МАРКЕТ" />
        </div>
        <div class="header-info">
          <div class="info-item">
            <div class="info-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                <path fill="currentColor" d="M9.707 4.293a1 1 0 0 1 0 1.414L8.414 7H14a6 6 0 0 1 0 12H6a1 1 0 1 1 0-2h8a4 4 0 0 0 0-8H8.414l1.293 1.293a1 1 0 0 1-1.414 1.414l-3-3a1 1 0 0 1 0-1.414l3-3a1 1 0 0 1 1.414 0"></path>
              </svg>
            </div>
            <div class="info-text">
              <div class="info-title">Гарантия легкого возврата</div>
              <div class="info-subtitle">Заберем товар и быстро вернем деньги</div>
            </div>
          </div>
          <div class="info-item">
            <div class="info-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                <path fill="currentColor" d="m6 7.586 4.293-4.293a1 1 0 1 1 1.414 1.414l-5 5a.997.997 0 0 1-1.414 0l-3-3a1 1 0 1 1 1.414-1.414z"></path>
                <path fill="currentColor" d="M1 18a1 1 0 0 0 1 1h2.17a3.001 3.001 0 0 0 5.66 0h5.34a3.001 3.001 0 0 0 5.66 0H22a1 1 0 0 0 1-1v-3.597a5 5 0 0 0-1.096-3.123l-1.922-2.403A5 5 0 0 0 16.078 7H13a1 1 0 0 0-1 1v9H9.83a3.001 3.001 0 0 0-5.66 0H3v-6.874h-.008a1 1 0 1 0-1.984 0H1zm13-1v-4h2a1 1 0 1 0 0-2h-2V9h2.078a3 3 0 0 1 2.342 1.126l1.923 2.403A3 3 0 0 1 21 14.403V17h-.17a3.001 3.001 0 0 0-5.66 0zm-8 1a1 1 0 1 1 2 0 1 1 0 0 1-2 0m12 1a1 1 0 1 1 0-2 1 1 0 0 1 0 2"></path>
              </svg>
            </div>
            <div class="info-text">
              <div class="info-title">Доставка курьером без доплат от 2 500 ₽</div>
              <div class="info-subtitle">Доставка заказов до 2 500 ₽ – 149 ₽ / 249 ₽</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="purchase">
      <div class="topbar">
        <a class="back" href="javascript:void(0)" @click="toBasket">
          <span>Вернуться в корзину</span>
        </a>
        <div class="title">Оформление заказа</div>
      </div>

      <div class="content">
        <div class="left">
          <!-- Payment Method -->
          <div class="panel">
            <div class="panel-title">Способ оплаты</div>
            <div class="pay-options">
              <div class="pay-option" v-for="(opt, i) in payOptions" :key="'p'+i" :class="{ selected: i === selectedPayOption }" @click="selectedPayOption = i">
                <div class="pay-icon" :style="opt.style">
                  <img v-if="opt.img" :src="opt.img" :alt="opt.label" />
                </div>
              </div>
            </div>

            <div class="pay-after-delivery">
              <v-checkbox v-model="payOnDelivery" hide-details density="compact">
                <template v-slot:label>
                  <div class="checkbox-label">
                    <span class="label-text">Оплатить после получения</span>
                    <v-icon size="20" class="info-icon">mdi-information-outline</v-icon>
                  </div>
                </template>
              </v-checkbox>
            </div>

            <div class="payment-bonus">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" class="currency-icon">
                <path fill="currentColor" d="M10 11V7a1 1 0 0 1 1-1h2.5a3.5 3.5 0 1 1 0 7H12v1h3a1 1 0 1 1 0 2h-3v1a1 1 0 1 1-2 0v-1H9a1 1 0 1 1 0-2h1v-1H9a1 1 0 1 1 0-2zm2 0h1.5a1.5 1.5 0 0 0 0-3H12z"/>
                <path fill="currentColor" d="M12 1C5.925 1 1 5.925 1 12s4.925 11 11 11 11-4.925 11-11S18.075 1 12 1M3 12a9 9 0 1 1 18 0 9 9 0 0 1-18 0"/>
              </svg>
              <span>Скидка 169 ₽ при оплате МАРКЕТ Картой</span>
            </div>
          </div>

          <!-- Points and Bonuses -->
          <div class="panel">
            <div class="panel-header">
              <div class="panel-title">Баллы и бонусы</div>
              <v-icon size="20" color="#96a3ae">mdi-information-outline</v-icon>
            </div>
            <div class="points-options">
              <div class="point-option" :class="{ selected: pointsAction === 'add' }" @click="pointsAction = 'add'">
                <span>Начислить</span>
                <strong>{{ bonusPointsToAdd }}</strong>
              </div>
              <div class="point-option" :class="{ selected: pointsAction === 'use' }" @click="pointsAction = 'use'">
                <span>Списать</span>
                <strong>{{ bonusPointsBalance }}</strong>
              </div>
            </div>
          </div>

          <!-- Delivery Section -->
           
          <div class="delivery-label mt-8">ДОСТАВКА МАРКЕТ</div>
          <div class="panel">
            <div class="delivery-method-header">
              <div class="panel-title">Способ получения</div>
              <div class="delivery-tabs">
                <div class="delivery-tab" :class="{ active: deliveryMethod === 'pickup' }" @click="deliveryMethod = 'pickup'">
                  Самовывоз
                </div>
                <div class="delivery-tab" :class="{ active: deliveryMethod === 'courier' }" @click="deliveryMethod = 'courier'">
                  Курьером
                </div>
              </div>
            </div>

            <!-- Pickup Method Content -->
            <div v-if="deliveryMethod === 'pickup'">
              <div class="address-tile">
                <div class="tile-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                    <path fill="currentColor" d="M12 5a5 5 0 1 0 0 10 5 5 0 0 0 0-10m-3 5a3 3 0 1 1 6 0 3 3 0 0 1-6 0"/>
                    <path fill="currentColor" d="M12 1a9 9 0 0 0-9 9c0 2.514 1.136 4.848 2.699 6.942 1.565 2.099 3.631 4.05 5.643 5.81a1 1 0 0 0 1.316 0c2.012-1.76 4.078-3.711 5.644-5.81C19.864 14.848 21 12.514 21 10a9 9 0 0 0-9-9m-7 9a7 7 0 0 1 14 0c0 1.904-.864 3.82-2.302 5.746-1.275 1.71-2.945 3.353-4.698 4.92-1.753-1.567-3.423-3.21-4.699-4.92C5.864 13.82 5 11.904 5 10"/>
                  </svg>
                </div>
                <div class="tile-content">
                  <div class="tile-title">{{ shopBoxName }}</div>
                  <div class="tile-subtitle">
                    {{ shopBoxAddress }}
                    <br><br>
                    Срок хранения заказа — 2 дня
                  </div>
                </div>
                <v-btn class="link-btn" variant="text" size="small" @click="noop">Изменить</v-btn>
              </div>

              <div class="address-tile clickable">
                <div class="tile-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                    <path fill="currentColor" d="M8 11a1 1 0 1 1-2 0 1 1 0 0 1 2 0m10 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0m-8.3 4.286c.016.015.185.165.5.323.376.187.971.391 1.8.391s1.425-.204 1.8-.391c.175-.088.355-.19.5-.323a1 1 0 0 1 1.407 1.421C15.587 16.827 14.357 18 12 18c-2.358 0-3.587-1.173-3.707-1.293A1 1 0 0 1 9.7 15.286"/>
                    <path fill="currentColor" d="M11 2a1 1 0 0 1 1-1c6.075 0 11 4.925 11 11s-4.925 11-11 11S1 18.075 1 12a11 11 0 0 1 6.23-9.914 1 1 0 0 1 1.36.524c.292.72.69 1.565 1.362 2.233C10.592 5.481 11.524 6 13 6a1 1 0 1 1 0 2c-2.024 0-3.458-.743-4.459-1.74-.6-.596-1.027-1.267-1.34-1.875A9 9 0 1 0 12 3a1 1 0 0 1-1.001-1"/>
                  </svg>
                </div>
                <div class="tile-content">
                  <div class="tile-title" style="font-weight: 400;">{{ userName }} {{ userPhone }}</div>
                </div>
                <v-icon size="16" color="#96a3ae">mdi-chevron-right</v-icon>
              </div>
            </div>

            <!-- Courier Method Content -->
            <div v-else>
              <div class="address-tile">
                <div class="tile-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                    <path fill="currentColor" d="M1 4a1 1 0 0 1 1-1h11a1 1 0 1 1 0 2H3v12h1.17a3.001 3.001 0 0 1 5.66 0H12V8a1 1 0 0 1 1-1h3.078a5 5 0 0 1 3.904 1.877l1.922 2.403A5 5 0 0 1 23 14.403V18a1 1 0 0 1-1 1h-1.17a3.001 3.001 0 0 1-5.66 0H9.83a3.001 3.001 0 0 1-5.66 0H2a1 1 0 0 1-1-1zm13 13h1.17a3.001 3.001 0 0 1 5.66 0H21v-2.597a3 3 0 0 0-.657-1.874l-1.923-2.403A3 3 0 0 0 16.077 9H14v2h2a1 1 0 1 1 0 2h-2zm-6 1a1 1 0 1 0-2 0 1 1 0 0 0 2 0m10-1a1 1 0 1 0 0 2 1 1 0 0 0 0-2"/>
                  </svg>
                </div>
                <div class="tile-content">
                  <div class="tile-title">Курьером по адресу</div>
                  <div class="tile-subtitle">{{ userAddress }}</div>
                </div>
                <v-btn class="link-btn" variant="text" size="small" @click="noop">Изменить</v-btn>
              </div>

              <div class="address-tile clickable">
                <div class="tile-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                    <path fill="currentColor" d="M8 11a1 1 0 1 1-2 0 1 1 0 0 1 2 0m10 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0m-8.3 4.286c.016.015.185.165.5.323.376.187.971.391 1.8.391s1.425-.204 1.8-.391c.175-.088.355-.19.5-.323a1 1 0 0 1 1.407 1.421C15.587 16.827 14.357 18 12 18c-2.358 0-3.587-1.173-3.707-1.293A1 1 0 0 1 9.7 15.286"/>
                    <path fill="currentColor" d="M11 2a1 1 0 0 1 1-1c6.075 0 11 4.925 11 11s-4.925 11-11 11S1 18.075 1 12a11 11 0 0 1 6.23-9.914 1 1 0 0 1 1.36.524c.292.72.69 1.565 1.362 2.233C10.592 5.481 11.524 6 13 6a1 1 0 1 1 0 2c-2.024 0-3.458-.743-4.459-1.74-.6-.596-1.027-1.267-1.34-1.875A9 9 0 1 0 12 3a1 1 0 0 1-1.001-1"/>
                  </svg>
                </div>
                <div class="tile-content">
                  <div class="tile-title" style="font-weight: 400;">{{ userName }} {{ userPhone }}</div>
                </div>
                <v-icon size="16" color="#96a3ae">mdi-chevron-right</v-icon>
              </div>

              <!-- <div class="separator"></div> -->

              <div class="address-tile clickable">
                <div class="tile-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                    <path fill="currentColor" d="M11 3h6a5 5 0 0 1 3 9 7 7 0 0 0-7-7h-3a1 1 0 1 0 0 2h3a5 5 0 0 1 0 10h-3a1 1 0 0 0-.707.293L7 19.586v-1.669a1 1 0 0 0-.835-.986 5.002 5.002 0 0 1-.618-9.717 1 1 0 0 0 .667-.667A5 5 0 0 1 11 3m8.529 11.529A7.002 7.002 0 0 0 17 1h-6a7 7 0 0 0-6.529 4.471A7.002 7.002 0 0 0 5 18.71V22a1 1 0 0 0 1.707.707L10.414 19H13a7 7 0 0 0 6.529-4.471"/>
                    <path fill="currentColor" d="M7 12a1 1 0 1 1-2 0 1 1 0 0 1 2 0m4 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0m4 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0"/>
                  </svg>
                </div>
                <div class="tile-content">
                  <div class="tile-title" style="font-weight: 400;">Комментарий курьеру</div>
                </div>
                <v-icon size="16" color="#96a3ae">mdi-chevron-right</v-icon>
              </div>

              <div class="separator"></div>

              <div class="delivery-prefs">
                <v-checkbox v-model="leaveAtDoor" hide-details density="compact" label="Оставить у двери" />
                <v-checkbox v-model="callBefore" hide-details density="compact" label="Позвонить перед доставкой" />
                <v-icon size="20" color="#96a3ae">mdi-help-circle-outline</v-icon>
              </div>
            </div>
          </div>

          <!-- Expected Delivery -->
          <div class="panel">
            <div class="panel-subtitle bold">Ожидаемая дата доставки: завтра, {{ expectedDateLabel }}, {{ deliveryPriceLabel }}</div>
            <div class="order-summary-text">{{ itemsCount }} товар • {{ totalWeight }} кг</div>

            <div class="product-preview">
              <div class="product-thumb">
                <v-img :src="getImageSrc(firstItemThumb)" cover />
                <div class="hot-badge">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24">
                    <path fill="currentColor" d="M12 3.097c-3-.963-1 5.565-3 5.565-1 0-1.208-1.886-2.008-1.886-1 0-3.992 3.065-3.992 6.918C3 17.211 5 21 9 21c1 0 1.5-.318.938-.93-2.813-3.066-2.038-6.062-.946-5.712 1.41.453 2.735 2.668 3.836-2.026.279-1.27.979-.933 1.9 0 1.38 1.4 2.103 4.411-.54 7.737-.438.55.312.931 1.53.931C18.345 21 21 18.158 21 13.694c0-6.005-6-9.633-9-10.597"/>
                  </svg>
                </div>
              </div>
            </div>

            <div class="delivery-info" v-if="deliveryMethod != 'pickup'">
              <div class="delivery-method" style="font-size: 16px; font-weight: 600;">Курьерская доставка МАРКЕТ</div>
              <div class="delivery-dates">
                <div v-for="(d, di) in deliveryDays" :key="'d'+di" class="date-chip" :class="{ selected: di === 0 }">
                  <div class="date-main">{{ d.date }}</div>
                  <div class="date-label">{{ d.label }}</div>
                </div>
              </div>
              <div class="delivery-time-price">{{ timeWindow }}, <strong>{{ deliveryPriceLabel }}</strong></div>
            </div>            
            <div class="delivery-method" v-else style="font-size: 16px; font-weight: 600;">{{ `Доставка в ${shopBoxName}` }}</div>

          </div>
        </div>

        <div class="right">
          <div class="order-panels-wrapper">
          <!-- Order Summary -->
          <div class="order-panel">
            <v-btn class="btn-pay" color="#0b63ff" variant="flat" block height="48" size="large" :disabled="isPaying" @click="handlePay">
              <template v-if="isPaying">
                <v-progress-circular indeterminate size="20" width="3" color="white" class="mr-2"></v-progress-circular>
                Оплата...
              </template>
              <template v-else>
                Пополнить и оплатить
              </template>
            </v-btn>
            <div class="terms-text">
              Нажимая на кнопку, вы соглашаетесь с
              <a href="#" @click.prevent>Условиями обработки персональных данных</a>,
              а также с
              <a href="#" @click.prevent>Условиями продажи</a>
            </div>

            <div class="divider"></div>

            <div class="order-header">
              <span class="order-title">Ваш заказ</span>
              <span class="order-meta">{{ itemsCount }} товар • {{ totalWeight }} кг</span>
            </div>

            <div class="order-row">
              <span class="row-label">Товары ({{ itemsCount }})</span>
              <span class="row-value">{{ formatCurrency(totalWithoutCard, 'RUB') }}</span>
            </div>

            <div class="order-row">
              <div class="row-label-group">
                <span class="row-label">Скидка</span>
                <button class="details-btn" @click="noop">Подробнее</button>
              </div>
              <span class="row-value discount">-{{ formatCurrency(totalDiscount, 'RUB') }}</span>
            </div>

            <div class="order-row">
              <div class="row-label-group">
                <span class="row-label">Доставка</span>
                <!-- <button class="details-btn" @click="noop">Подробнее</button> -->
              </div>
              <span class="row-value" :class="{ 'free-delivery': isFreeDelivery }">
                {{ isFreeDelivery ? 'Без доплат' : formatCurrency(deliveryFee, 'RUB') }}
              </span>
            </div>

            <div v-if="pointsAction === 'use'" class="order-row">
              <div class="row-label-group">
                <span class="row-label">Оплата бонусными баллами</span>
              </div>
              <span class="row-value discount" style="color: #111;">-{{ bonusPointsBalance }}</span>
            </div>

            <div class="order-total">
              <span class="total-label">Итого</span>
              <span class="total-value">{{ formatCurrency(finalTotal, 'RUB') }}</span>
            </div>

            <!-- <div class="order-without-card">
              <span class="without-label">Без МАРКЕТ Карты</span>
              <span class="without-value">{{ formatCurrency(totalWithoutCard + deliveryFee, 'RUB') }}</span>
            </div> -->
          </div>

          <!-- Courier Tips -->
          <div class="order-panel">
            <div class="tips-header">
              <span class="panel-title">Чаевые курьеру</span>
              <v-icon size="20" color="#96a3ae">mdi-information-outline</v-icon>
            </div>
            <div class="tips-subtitle">Спишем с карты после получения заказа</div>
            <div class="tips-options">
              <div v-for="(t, ti) in tips" :key="'t'+ti"
                   class="tip-option"
                   :class="{ selected: selectedTip === ti }"
                   @click="selectedTip = ti">
                {{ t }}
              </div>
            </div>
          </div>

          <!-- Seller Bonus -->
          <div v-if="pointsAction === 'add'" class="order-panel">
            <div class="bonus-header">
              <span class="panel-title">Начислим {{ bonusPointsToAdd }} бонуса продавца</span>
              <v-icon size="20" color="#96a3ae">mdi-chevron-down</v-icon>
            </div>
            <div class="bonus-details">
              <div class="bonus-row">
                <span class="bonus-name">Бонусы продавца</span>
                <div class="bonus-value">
                  <span>{{ bonusPointsToAdd }}</span>
                  <div class="bonus-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <path d="M6 5C4.34315 5 3 6.34315 3 8C3 9.65685 4.34315 11 6 11C7.65685 11 9 9.65685 9 8C9 6.34315 7.65685 5 6 5ZM1 8C1 5.23858 3.23858 3 6 3C8.76142 3 11 5.23858 11 8C11 10.7614 8.76142 13 6 13C3.23858 13 1 10.7614 1 8ZM11.1344 4.03443C11.4109 3.55637 12.0227 3.39301 12.5007 3.66955C13.9926 4.53256 15 6.14806 15 8.00003C15 9.85199 13.9926 11.4675 12.5007 12.3305C12.0227 12.607 11.4109 12.4437 11.1344 11.9656C10.8579 11.4876 11.0212 10.8758 11.4993 10.5993C12.3986 10.0791 13 9.10919 13 8.00003C13 6.89086 12.3986 5.92099 11.4993 5.40076C11.0212 5.12422 10.8579 4.51249 11.1344 4.03443Z" fill="black"/>
                    </svg>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Promo Code -->
          <div class="order-panel promo-panel">
            <div class="promo-header">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" class="promo-icon">
                <path fill="currentColor" d="M12 3a9 9 0 0 0-9 9c0 1.169.222 2.283.626 3.305a1 1 0 0 1-1.86.734A11 11 0 0 1 1 12C1 5.925 5.925 1 12 1s11 4.925 11 11-4.925 11-11 11a10.97 10.97 0 0 1-7.621-3.068 1.197 1.197 0 0 1-.016-1.71l10.93-10.93a1 1 0 1 1 1.414 1.415L6.382 19.032A8.96 8.96 0 0 0 12 21a9 9 0 1 0 0-18"/>
                <path fill="currentColor" d="M10 8.5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0m7 7a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0"/>
              </svg>
              <span>Промокод или сертификат</span>
              <v-icon size="16" color="#96a3ae">mdi-chevron-down</v-icon>
            </div>
          </div>
          </div>
        </div>
      </div>
    </div>

    <shop-login-dialog v-model="loginDialog" :loginData="testData && testData.login_data" @success="onLoginSuccess" />
  </div>
  <div v-else />
</template>

<script>
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import { benchUserContextMixin } from '@/common/benchUserContextMixin.js';
import { GET_TRACK_CONFIG, GET_KV_STORE } from '@/store/actions.type';
import MenuBar from './components/MenuBar.vue';
import ShopLoginDialog from './components/ShopLoginDialog.vue';
import { syncMockLoggedInFromTrack, setCurrentUsername, getShopBasket, getShopSelectedItems, clearShopBasket, clearShopSelectedItems } from '@/utils/localCache.js';
import { shopAssets } from '@/assets/shop-assets.js';
import { _logActivity } from '@/common/trackHelper';
import { isUnifiedBench } from '@/common/benchTheme';
import { navigateToShopBasket, pushBenchRoute } from '@/common/benchNavigation';
import { resolveAssetUrl } from '@/common/cdnUrls';

export default defineComponent({
  name: 'ShopPurchase',
  mixins: [benchUserContextMixin],
  components: { MenuBar, ShopLoginDialog },
  data() {
    return {
      loginDialog: false,
      loggedIn: false,
      payOnDelivery: false,
      deliveryMethod: 'pickup',
      selectedPayOption: 0,
      selectedTip: 0,
      pointsAction: 'add',
      leaveAtDoor: true,
      callBefore: false,
      countdownTimer: '06:58:46',
      timerInterval: null,
      isPaying: false
    };
  },
  computed: {
    ...mapGetters(['trackConfig', 'kvStore']),
    isLoggedIn() { return this.loggedIn; },
    configLoaded() { return this.trackConfig && Object.keys(this.trackConfig).length > 0; },
    common() { return (this.trackConfig && this.trackConfig.common_elements) || {}; },
    testData() { return (this.trackConfig && this.trackConfig.test_data) || {}; },
    logoSrc() {
      const img = this.common && this.common.header && this.common.header.logo && this.common.header.logo.image;
      return img ? shopAssets[img] : shopAssets['logo'];
    },
    username() { return this.benchSessionUser || 'guest'; },
    userName() { return this.shopUser.fullName || ''; },
    userEmail() { return this.shopUser.email || ''; },
    userPhone() { return this.shopUser.phone || ''; },
    userAddress() { return this.shopUser.address || ''; },
    shopBoxName() { return this.shopUser.shop_box_name || ''; },
    shopBoxAddress() { return this.shopUser.shop_box_address || ''; },
    bonusPointsBalance() { return Number(this.shopUser.bonus_points_balance || 0); },
    bonusPointsToAdd() { return Number(this.shopUser.bonus_points_to_add || 0); },
    selectedItemsMap() { return getShopSelectedItems(this.username) || {}; },
    basketMap() {
      // Purchase page should reflect "selected items" from basket, not always the whole basket.
      // If selection is empty, fallback to full basket for robustness.
      const full = getShopBasket(this.username) || {};
      const selected = this.selectedItemsMap || {};
      const selectedKeys = Object.keys(selected).filter(k => !!selected[k]);
      if (!selectedKeys.length) return full;
      const filtered = {};
      selectedKeys.forEach(k => {
        const qty = Number(full[k] || 0);
        if (qty > 0) filtered[k] = qty;
      });
      return Object.keys(filtered).length ? filtered : full;
    },
    basketResolvedItems() {
      const kv = this.kvStore || {};
      const entries = Object.entries(this.basketMap || {});
      return entries.map(([key, count]) => ({ key, count: Number(count) || 0, item: kv[key] || null }));
    },
    itemsCount() { return this.basketResolvedItems.reduce((s, bi) => s + Math.max(0, bi.count), 0); },
    totalWithCard() {
      return this.roundCurrency(this.basketResolvedItems.reduce((s, bi) => s + this.getCurrentPriceValue(bi.item) * Math.max(0, bi.count), 0));
    },
    totalWithoutCard() {
      return this.basketResolvedItems.reduce((s, bi) => {
        const basePrice = this.getCurrentPriceValue(bi.item);
        const discount = Number(bi.item?.discount || 0);
        return s + (basePrice + discount) * Math.max(0, bi.count);
      }, 0);
    },
    totalDiscount() {
      return this.basketResolvedItems.reduce((s, bi) => {
        const discount = Number(bi.item?.discount || 0);
        return s + discount * Math.max(0, bi.count);
      }, 0);
    },
    finalTotal() {
      let total = this.totalWithCard + this.deliveryFee;
      if (this.pointsAction === 'use') {
        total = Math.max(0, total - this.bonusPointsBalance);
      }
      return total;
    },
    totalWeight() {
      return this.basketResolvedItems.reduce((s, bi) => {
        const weight = (bi.item && bi.item.weight) || 1.12;
        return s + weight * Math.max(0, bi.count);
      }, 0).toFixed(2);
    },
    firstItemThumb() {
      const it = (this.basketResolvedItems[0] && this.basketResolvedItems[0].item) || null;
      return (it && (it.thumbnail || it.img)) || '';
    },
    expectedDateLabel() {
      const d = new Date(); d.setDate(d.getDate() + 1);
      const day = d.getDate();
      const months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];
      return `${day} ${months[d.getMonth()]}`;
    },
    deliveryPriceLabel() { return this.formatCurrency(this.deliveryFee, 'RUB'); },
    deliveryFee() { return this.isFreeDelivery ? 0 : 149; },
    isFreeDelivery() { return this.totalWithCard > 2500; },
    payOptions() {
      return [
        { label: 'Карта', img: '/shop/pay-card.svg', style: { backgroundImage: 'url(/shop/pay-card.svg)' } },
        { label: 'СБП', img: '/shop/pay-sbp.svg', style: { backgroundImage: 'url(/shop/pay-sbp.svg)' } },
        { label: 'Кошелёк', img: '/shop/pay-wallet.svg', style: { backgroundImage: 'url(/shop/pay-wallet.svg)' } },
      ];
    },
    tips() { return ['Без чаевых', '49 ₽', '99 ₽', '149 ₽', '199 ₽']; },
    deliveryDays() {
      const today = new Date();
      const days = [];
      const dayLabels = ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб'];
      const months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];

      for (let i = 1; i <= 11; i++) {
        const d = new Date(today);
        d.setDate(today.getDate() + i);
        days.push({
          date: `${d.getDate()} ${months[d.getMonth()].slice(0, 3)}`,
          label: i === 1 ? 'завтра' : dayLabels[d.getDay()]
        });
      }
      return days;
    },
    timeWindow() { return '12:00–23:00'; }
  },
  methods: {
    openLoginDialog() { this.loginDialog = true; },
    onLoginSuccess() {
      this.loggedIn = true;
      const username = this.benchSessionUser || 'guest';
      setCurrentUsername(username);
    },
    goToMainPage() {
      this.$router.push({ name: 'bench_catalog_main', params: { state_id: 'state_main', track_id: this.$route.params.track_id } });
    },
    getImageSrc(s) {
      return resolveAssetUrl(s);
    },
    formatCurrency(value, currencyCode) {
      const num = Number(value || 0);
      if (!currencyCode || currencyCode === 'RUB') {
        const f = num.toLocaleString('ru-RU', {
          minimumFractionDigits: num % 1 === 0 ? 0 : 2,
          maximumFractionDigits: 2
        });
        return `${f}\u00A0₽`;
      }
      return `${num.toLocaleString('ru-RU')} ${currencyCode}`.trim();
    },
    roundCurrency(value) {
      return Math.round(Number(value || 0));
    },
    getBasePriceValue(it) {
      if (!it) return 0;
      const raw = typeof it.data_price === 'number' ? it.data_price : Number(it.price || it.price_current || 0);
      return this.roundCurrency(raw);
    },
    getPriceWithoutCardValue(it) {
      if (!it) return 0;
      const basePrice = this.getBasePriceValue(it);
      const discountPercent = Number(it.discount || 0);
      const discounted = basePrice - basePrice * (discountPercent / 100);
      return this.roundCurrency(Math.max(0, discounted));
    },
    getPriceWithCardValue(it) {
      if (!it) return 0;
      const withoutCard = this.getPriceWithoutCardValue(it);
      const cardDiscount = Number(it.card_discount_value || 0);
      return this.roundCurrency(Math.max(0, withoutCard - cardDiscount));
    },
    getCurrentPriceValue(it) {
      return this.getPriceWithCardValue(it);
    },
    getOldPriceValue(it) {
      if (!it) return 0;
      return Number(it.price_old || 0);
    },
    toBasket() {
      if (isUnifiedBench(this.trackConfig)) {
        navigateToShopBasket(this.$router, this.$route.params.track_id);
        return;
      }
      pushBenchRoute(this.$router, {
        name: 'bench_catalog_basket',
        stateId: 'state_basket',
        trackId: this.$route.params.track_id });
    },
    handlePay() {
      if (this.isPaying) return;
      try {
        const username = this.username;
        const basketMap = getShopBasket(username) || {};
        const basket = Object.keys(basketMap).reduce((arr, k) => {
          const qty = Number(basketMap[k] || 0);
          for (let i = 0; i < qty; i++) arr.push(k);
          return arr;
        }, []);
        const amount = Number(this.finalTotal || 0);
        _logActivity(this, { type: 'submit_payment', username, amount, basket });
      } catch(e) {}
      this.isPaying = true;
      setTimeout(() => {
        try {
          const username = this.username;
          clearShopBasket(username);
          clearShopSelectedItems(username);
        } catch (e) {}
        pushBenchRoute(this.$router, {
          name: 'bench_catalog_payment_success',
          stateId: 'state_payment_success',
          trackId: this.$route.params.track_id,
        });
      }, 200);
    },
    noop() {},
    startCountdownTimer() {
      // Start countdown from 6:58:46
      let totalSeconds = 6 * 3600 + 58 * 60 + 46;

      this.timerInterval = setInterval(() => {
        if (totalSeconds <= 0) {
          clearInterval(this.timerInterval);
          return;
        }

        totalSeconds--;
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;

        this.countdownTimer = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
      }, 1000);
    },
    getTrackConfig() {
      this.$store
        .dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id })
        .then(() => {
          this.loggedIn = syncMockLoggedInFromTrack(this.trackConfig);
          const kvPath = (this.trackConfig && this.trackConfig.test_data && this.trackConfig.test_data.kv_store_path) || '';
          if (kvPath) return this.$store.dispatch(GET_KV_STORE, { kvPath });
          return Promise.resolve();
        });
    }
  },
  mounted() {
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
    }
    this.loggedIn = syncMockLoggedInFromTrack(this.trackConfig);
    this.startCountdownTimer();
  },
  beforeUnmount() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }
  }
});
</script>

<style src="@/assets/shop.css"></style>

<style scoped>
/* Page Background */
.purchase-page {
  background-color: var(--bench-surface, #f2f3f5);
  min-height: 100vh;
}

/* Simple Header */
.simple-header {
  background-color: var(--bench-surface, #f2f3f5);
  border-bottom: 1px solid #e6eaed;
  padding: 20px 0;
}

.simple-header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.header-logo {
  flex-shrink: 0;
}

.header-logo img {
  height: 44px;
  display: block;
  cursor: pointer;
}

.header-info {
  display: flex;
  gap: 32px;
  align-items: center;
}

.info-item {
  display: flex;
  gap: 8px;
  align-items: center;
}

.info-icon {
  flex-shrink: 0;
  color: #001a34;
  display: flex;
  align-items: center;
  justify-content: center;
}

.info-icon svg {
  display: block;
}

.info-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.info-title {
  font-size: 14px;
  font-weight: 500;
  color: #001a34;
  line-height: 1.3;
}

.info-subtitle {
  font-size: 12px;
  color: #808d9a;
  line-height: 1.3;
}

@media (max-width: 1024px) {
  .header-info {
    display: none;
  }
}

/* Promo Banner */
.promo-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background-color: #fff;
  border-radius: 25px;
  margin-bottom: 12px;
}

.promo-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  color: #f1117e;
}

.promo-text {
  flex: 1;
}

.promo-title {
  font-size: 14px;
  font-weight: 500;
  color: #001a34;
  margin-bottom: 2px;
}

.promo-subtitle {
  font-size: 12px;
  color: #808d9a;
}

.promo-timer {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background-color: #f1117e;
  border-radius: 6px;
}

.timer-label {
  font-size: 12px;
  color: white;
}

.timer-value {
  font-size: 12px;
  font-weight: 500;
  color: white;
  font-variant-numeric: tabular-nums;
}

/* Payment Options */
.pay-options {
  display: flex;
  gap: 8px;
  margin: 16px 0;
  overflow-x: auto;
}

.pay-option {
  min-width: 110px;
  height: 70px;
  border: 2px solid #e6eaed;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  overflow: hidden;
  padding: 3px;
}

.pay-option.selected {
  border-color: #0b63ff;
  box-shadow: 0 0 0 2px rgba(11, 99, 255, 0.1);
}

.pay-option:hover {
  border-color: #0b63ff;
}

.pay-icon {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-size: contain;
  background-position: center;
  background-repeat: no-repeat;
  font-size: 12px;
  font-weight: 500;
}

.pay-icon img {
  max-width: 90%;
  max-height: 90%;
  object-fit: contain;
}

.pay-after-delivery {
  margin: 20px 0 30px;
  background: #f5f7fa;
  border-radius: 20px;
  padding: 2px 10px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.label-text {
  font-size: 16px;
  font-weight: 500;
}

.info-icon {
  color: #96a3ae;
  margin-left: 4px;
}

.payment-bonus {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 2 20px;
  border-radius: 12px;
  margin-top: 12px;
}

.currency-icon {
  color: #001a34;
  flex-shrink: 0;
}

.payment-bonus span {
  font-size: 16px;
  font-weight: 400;
  color: #001a34;
}

/* Points and Bonuses */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0px;
}

.points-options {
  display: flex;
  gap: 12px;
  background-color: #f5f7fa;
  border-radius: 20px;
}

.point-option {
  flex: 1;
  padding: 8px 16px;
  background: transparent;
  border: 0;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 16px;
  line-height: 20px;
  color: #001a34;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  border-radius: 20px;
}

.point-option.selected {
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  cursor: default;
}

.point-option strong {
  font-weight: 600;
}

/* Delivery Section */
.delivery-label {
  font-size: 14px;
  color: #686b6d;
  margin-bottom: 12px;
  font-weight: 500;
}

.delivery-method-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.delivery-method-header .panel-title {
  margin-bottom: 0;
}

.delivery-tabs {
  display: flex;
  gap: 0px;
}

.delivery-tab {
  padding: 5px 10px;
  border-radius: 5px;
  text-align: center;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
  white-space: nowrap;
  background-color: #0096ff14;
  color: #0b63ff;
}

.delivery-tab.active {
  background-color: #0b63ff;
  color: white;
  border-color: #0b63ff;
}

.address-tile {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
}

.address-tile.clickable {
  cursor: pointer;
}

.address-tile.clickable:hover {
  opacity: 0.7;
}

.tile-icon {
  flex-shrink: 0;
  color: #001a34;
}

.tile-icon svg {
  display: block;
}

.tile-content {
  flex: 1;
}

.tile-title {
  font-size: 16px;
  font-weight: 600;
  color: #001a34;
  margin-bottom: 4px;
}

.tile-subtitle {
  font-size: 13px;
  color: #001a34;
  line-height: 1.4;
}

.link-btn {
  text-transform: none;
  color: #0b63ff;
  font-size: 14px;
}

.separator {
  height: 1px;
  background-color: #e6eaed;
  margin: 0 -24px;
}

.delivery-prefs {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 0 0;
  justify-content: space-between;
}

.panel-subtitle.bold {
  font-weight: 700;
  color: #001a34;
  font-size: 20px;
  margin-bottom: 8px;
}

.order-summary-text {
  font-size: 14px;
  color: #808d9a;
  margin-bottom: 16px;
}

/* Product Preview */
.product-preview {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.product-thumb {
  position: relative;
  width: 92px;
  height: 92px;
  border-radius: 12px;
  overflow: hidden;
  flex-shrink: 0;
}

.hot-badge {
  position: absolute;
  bottom: 4px;
  left: 4px;
  width: 24px;
  height: 24px;
  background-color: #fef0e6;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hot-badge svg {
  color: #ff6b00;
}

/* Delivery Info */
.delivery-info {
  flex: 1;
}

.delivery-method {
  font-size: 14px;
  font-weight: 500;
  color: #001a34;
  margin-bottom: 12px;
}

.delivery-dates {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  margin-bottom: 12px;
  padding-bottom: 4px;
}

.date-chip {
  min-width: 60px;
  padding: 8px 12px;
  border: 1px solid #e6eaed;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.date-chip.selected {
  border-color: #0b63ff;
  background-color: #f0f5ff;
}

.date-main {
  font-size: 13px;
  color: #001a34;
  font-weight: 500;
  margin-bottom: 2px;
}

.date-label {
  font-size: 11px;
  color: #808d9a;
}

.delivery-time-price {
  font-size: 14px;
  color: #001a34;
}

/* Order Panel */
.terms-text {
  font-size: 12px;
  color: #808d9a;
  margin-top: 12px;
  line-height: 1.5;
}

.terms-text a {
  color: #0b63ff;
  text-decoration: none;
}

.terms-text a:hover {
  text-decoration: underline;
}

.divider {
  height: 1px;
  background-color: #e6eaed;
  margin: 16px 0;
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.order-title {
  font-size: 20px;
  font-weight: 700;
  color: #111827;
}

.order-meta {
  font-size: 14px;
  color: #9ca3af;
}

.order-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  font-size: 14px;
}

.row-label-group {
  display: flex;
  flex-direction: row;
  gap: 8px;
  align-items: center;
}

.row-label {
  font-size: 14px;
  color: #2b2c2d;
}

.row-value {
  font-size: 14px;
  color: #111827;
  font-weight: 600;
}

.row-value.discount {
  color: #f1117e;
}

.row-value.free-delivery {
  color: #22c55e;
  font-weight: 700;
}

.details-btn {
  background: none;
  border: none;
  color: #0b63ff;
  font-size: 14px;
  cursor: pointer;
  padding: 0;
  font-weight: 600;
}

.details-btn:hover {
  opacity: 0.8;
}

.order-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f3f4f6;
}

.total-label {
  font-size: 20px;
  color: #111827;
  font-weight: 700;
}

.total-value {
  font-size: 20px;
  font-weight: 700;
  color: #111;
}

.order-without-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  font-size: 13px;
}

.without-label {
  color: #8b8b8b;
  font-size: 14px;
}

.without-value {
  color: #909295;
  font-weight: 700;
}

/* Tips Section */
.tips-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tips-subtitle {
  font-size: 14px;
  color: #2b2c2d;
  margin-bottom: 12px;
}

.tips-options {
  display: flex;
  gap: 8px;
  overflow-x: auto;
}

.tip-option {
  min-width: 80px;
  padding: 8px 8px;
  border: 1px solid #e6eaed;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  white-space: nowrap;
}

.tip-option.selected {
  border-color: #0b63ff;
  background-color: #f0f5ff;
  font-weight: 500;
}

/* Bonus Section */
.bonus-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0px;
}

.bonus-details {
  padding-top: 8px;
}

.bonus-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.bonus-name {
  font-size: 14px;
  color: #001a34;
}

.bonus-value {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #001a34;
}

.bonus-icon svg {
  display: block;
}

/* Promo Panel */
.promo-panel .promo-header {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.promo-panel .promo-icon {
  color: #0b63ff;
  width: auto;
  height: auto;
  background: none;
  border-radius: 0;
}

.promo-panel span {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: #001a34;
}

/* Purchase Layout - Override МАРКЕТ.css with more specific selectors */
/* Using .bench-market.purchase-page for higher specificity than .bench-market .purchase in МАРКЕТ.css */
.bench-market.purchase-page .purchase {
  max-width: 1200px !important;
  margin: 0 auto;
  padding: 0 16px;
}

.bench-market.purchase-page .topbar {
  padding: 16px 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.bench-market.purchase-page .topbar .back {
  display: flex;
  align-items: center;
  color: #0b63ff;
  text-decoration: none;
  font-size: 14px;
  margin-bottom: 12px;
  align-self: flex-start;
}

.bench-market.purchase-page .topbar .back:hover {
  opacity: 0.8;
}

.bench-market.purchase-page .purchase .content {
  display: grid !important;
  grid-template-columns: 650px 1fr !important;
  gap: 24px !important;
}

@media (max-width: 1024px) {
  .bench-market.purchase-page .purchase .content {
    grid-template-columns: 1fr !important;
  }

  .bench-market.purchase-page .right {
    order: -1;
  }
}

.bench-market.purchase-page .panel {
  background: var(--bench-surface-elevated, #fff);
  border-radius: 25px !important;
  padding: 24px !important;
  margin-bottom: 12px;
}

.bench-market.purchase-page .panel-title {
  font-size: 20px;
  font-weight: 700;
  color: #001a34;
}

.bench-market.purchase-page .panel-title.small {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 0;
}

.bench-market.purchase-page .order-panels-wrapper {
  position: sticky;
  top: 24px;
  align-self: start;
}

.bench-market.purchase-page .order-panel {
  background: var(--bench-surface-elevated, #fff);
  border-radius: 25px !important;
  padding: 20px !important;
  margin-bottom: 12px;
}

.bench-market.purchase-page .btn-pay {
  text-transform: none;
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 0;
}


.social-link svg {
  display: block;
}

@media (max-width: 768px) {
  .footer-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .footer-text {
    font-size: 13px;
  }
}
</style>


