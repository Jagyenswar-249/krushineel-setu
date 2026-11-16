export interface OutboxItem {
  id: string;
  endpoint: string;
  method: string;
  body: any;
  timestamp: number;
}

const OUTBOX_KEY = "kns_offline_outbox";

export const getOutbox = (): OutboxItem[] => {
  try {
    const raw = localStorage.getItem(OUTBOX_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
};

export const queueOfflineAction = (endpoint: string, method: string, body: any): OutboxItem => {
  const item: OutboxItem = {
    id: `outbox_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
    endpoint,
    method,
    body,
    timestamp: Date.now()
  };
  const list = getOutbox();
  list.push(item);
  localStorage.setItem(OUTBOX_KEY, JSON.stringify(list));
  return item;
};

export const flushOutbox = async (apiCall: (endpoint: string, method: string, body: any) => Promise<any>): Promise<number> => {
  const list = getOutbox();
  if (list.length === 0) return 0;

  let syncedCount = 0;
  const remaining: OutboxItem[] = [];

  for (const item of list) {
    try {
      await apiCall(item.endpoint, item.method, item.body);
      syncedCount++;
    } catch (e) {
      // Keep if network failure
      remaining.push(item);
    }
  }

  localStorage.setItem(OUTBOX_KEY, JSON.stringify(remaining));
  return syncedCount;
};
