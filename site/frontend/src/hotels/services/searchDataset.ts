import { DataService } from '@/common/api.service';

export type DatasetIndexItem = { id: string; label: string };

export type City = {
  id: string;
  name: string;
  countryCode: string;
  countryName: string;
};

export type DestinationOption = {
  type: 'city';
  cityId: string;
  label: string;
  cityName: string;
  countryName: string;
};

export type HotelType =
  | 'hotel'
  | 'hostel'
  | 'apartment'
  | 'aparthotel'
  | 'guest_house'
  | 'villa';

export type Amenity = 'wifi' | 'parking' | 'breakfast' | 'pets' | 'accessible' | 'airConditioning';

export type MealPlan = 'none' | 'breakfast';
export type CancellationPolicy = 'free' | 'no_free';
export type PaymentType = 'online' | 'at_hotel';

export type HotelOffer = {
  roomTitle: string;
  beds: string;
  mealPlan: MealPlan;
  cancellation: CancellationPolicy;
  payment: PaymentType;
};

export type Hotel = {
  id: string;
  cityId: string;
  name: string;
  address: string;
  stars: 2 | 3 | 4 | 5;
  rating: number;
  reviews: number;
  priceTotalRub: number;
  nights: number;
  distanceKm: number;
  type: HotelType;
  amenities: Amenity[];
  imageUrl: string;
  images: string[];
  offer?: HotelOffer;
};

export type SearchDataset = {
  id: string;
  label: string;
  cities: City[];
  hotels: Hotel[];
};

const datasetCache = new Map<string, Promise<SearchDataset>>();
const indexCache: { p?: Promise<DatasetIndexItem[]> } = {};

function parseKv(res: { data: { kv_store: string } }) {
  return JSON.parse(res.data.kv_store);
}

export function loadDatasetsIndex() {
  if (!indexCache.p) {
    indexCache.p = DataService.getKvStore({
      kvPath: 'hotels/hotels_index.json',
    }).then(parseKv);
  }

  return indexCache.p;
}

export function loadDataset(datasetId: string): Promise<SearchDataset> {
  const key = (datasetId || 'ch').trim();

  if (!datasetCache.has(key)) {
    datasetCache.set(
      key,
      DataService.getKvStore({
        kvPath: `hotels/hotels_${key}.json`,
      }).then(parseKv),
    );
  }

  return datasetCache.get(key)!;
}

export function citiesToOptions(cities: City[]): DestinationOption[] {
  return cities.map((c) => ({
    type: 'city',
    cityId: c.id,
    cityName: c.name,
    countryName: c.countryName,
    label: `${c.name}, ${c.countryName}`,
  }));
}