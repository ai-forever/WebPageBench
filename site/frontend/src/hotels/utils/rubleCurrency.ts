export const rubleCurrency = (value: number) => {
  const rub = new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 });
  return rub.format(value);
}