import { computed, onMounted, ref } from 'vue';
import type { DestinationOption, DatasetIndexItem, SearchDataset } from '@/hotels/services/searchDataset';
import { loadDataset, loadDatasetsIndex, citiesToOptions } from '@/hotels/services/searchDataset';

type CityDatasetMap = Record<string, string>; // cityId -> datasetId

export function useAllDestinations() {
  const loading = ref(true);
  const error = ref<string | null>(null);

  const datasetsIndex = ref<DatasetIndexItem[]>([]);
  const datasets = ref<SearchDataset[]>([]);

  const cityDatasetMap = ref<CityDatasetMap>({});

  const destinationOptions = computed<DestinationOption[]>(() => {
    // собрать все города по всем датасетам в один список
    const res: DestinationOption[] = [];
    for (const ds of datasets.value) {
      const opts = citiesToOptions(ds.cities);
      res.push(...opts);
    }

    // сортировка: по стране, потом по городу (приятно в UI)
    res.sort((a, b) => {
      const c = a.countryName.localeCompare(b.countryName, 'ru');
      if (c !== 0) return c;
      return a.cityName.localeCompare(b.cityName, 'ru');
    });

    return res;
  });

  async function loadAll() {
    loading.value = true;
    error.value = null;

    try {
      const index = await loadDatasetsIndex();
      datasetsIndex.value = index;

      const all = await Promise.all(index.map((i) => loadDataset(i.id)));
      datasets.value = all;

      // собрать map cityId -> datasetId
      const map: CityDatasetMap = {};
      for (const ds of all) {
        for (const c of ds.cities) {
          map[c.id] = ds.id; // ✅ ключевая вещь
        }
      }
      cityDatasetMap.value = map;
    } catch (e: any) {
      error.value = e?.message ?? String(e);
    } finally {
      loading.value = false;
    }
  }

  onMounted(() => {
    loadAll();
  });

  return {
    destinationOptions,
    cityDatasetMap,
    datasetsIndex,
    loading,
    error,
    reload: loadAll,
  };
}
