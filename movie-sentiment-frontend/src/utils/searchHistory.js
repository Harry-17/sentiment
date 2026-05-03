const DEFAULT_HISTORY_LIMIT = 8;

function canUseLocalStorage() {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';
}

export function getSearchHistory(storageKey) {
  if (!canUseLocalStorage()) {
    return [];
  }

  try {
    const rawValue = window.localStorage.getItem(storageKey);
    if (!rawValue) {
      return [];
    }

    const parsed = JSON.parse(rawValue);
    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed.filter((item) => typeof item === 'string' && item.trim().length > 0);
  } catch (error) {
    return [];
  }
}

export function addSearchHistoryItem(storageKey, value, limit = DEFAULT_HISTORY_LIMIT) {
  if (!canUseLocalStorage()) {
    return [];
  }

  const normalizedValue = value.trim();
  if (!normalizedValue) {
    return getSearchHistory(storageKey);
  }

  const existingItems = getSearchHistory(storageKey);
  const dedupedItems = existingItems.filter(
    (item) => item.toLowerCase() !== normalizedValue.toLowerCase()
  );
  const nextItems = [normalizedValue, ...dedupedItems].slice(0, limit);

  window.localStorage.setItem(storageKey, JSON.stringify(nextItems));
  return nextItems;
}

export function clearSearchHistory(storageKey) {
  if (!canUseLocalStorage()) {
    return;
  }

  window.localStorage.removeItem(storageKey);
}
