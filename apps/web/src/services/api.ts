import { queueOfflineAction } from "./offlineSync";

const API_BASE = "/api/v1";

const getHeaders = (isMultipart = false) => {
  const token = localStorage.getItem("kns_jwt_token");
  const headers: Record<string, string> = {};
  if (!isMultipart) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
};

export const api = {
  // Auth
  requestOTP: async (phone: string) => {
    const res = await fetch(`${API_BASE}/auth/otp/request`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ phone })
    });
    return res.json();
  },

  verifyOTP: async (phone: string, code: string, role = "farmer", name?: string) => {
    const res = await fetch(`${API_BASE}/auth/otp/verify`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ phone, code, role, name })
    });
    const data = await res.json();
    if (data.access_token) {
      localStorage.setItem("kns_jwt_token", data.access_token);
      localStorage.setItem("kns_user", JSON.stringify(data.user));
    }
    return data;
  },

  getMe: async () => {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getHeaders()
    });
    return res.json();
  },

  // ColdWatch
  getColdRooms: async () => {
    const res = await fetch(`${API_BASE}/coldrooms`, { headers: getHeaders() });
    return res.json();
  },

  getReadings: async (roomId: number, hours = 24) => {
    const res = await fetch(`${API_BASE}/coldrooms/${roomId}/readings?hours=${hours}`, { headers: getHeaders() });
    return res.json();
  },

  addReading: async (roomId: number, temp_c: number, rh: number, is_simulated = false) => {
    if (!navigator.onLine) {
      queueOfflineAction(`/coldrooms/${roomId}/readings`, "POST", { temp_c, rh, is_simulated });
      return { temp_c, rh, ts: new Date().toISOString(), is_simulated, offline_queued: true };
    }
    const res = await fetch(`${API_BASE}/coldrooms/${roomId}/readings`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ temp_c, rh, is_simulated })
    });
    return res.json();
  },

  importCSV: async (roomId: number, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE}/coldrooms/${roomId}/import`, {
      method: "POST",
      headers: getHeaders(true),
      body: formData
    });
    return res.json();
  },

  createDataSource: async (roomId: number, name: string, kind = "api") => {
    const res = await fetch(`${API_BASE}/coldrooms/${roomId}/sources`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ name, kind })
    });
    return res.json();
  },

  getAlerts: async (roomId: number) => {
    const res = await fetch(`${API_BASE}/coldrooms/${roomId}/alerts`, { headers: getHeaders() });
    return res.json();
  },

  ackAlert: async (alertId: number, acked_by = "Staff") => {
    const res = await fetch(`${API_BASE}/alerts/${alertId}/ack`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ acked_by })
    });
    return res.json();
  },

  getBatches: async (roomId?: number) => {
    const url = roomId ? `${API_BASE}/batches?room_id=${roomId}` : `${API_BASE}/batches`;
    const res = await fetch(url, { headers: getHeaders() });
    return res.json();
  },

  addBatch: async (roomId: number, commodity: string, qty_kg: number, shelf_life_days_ref = 14) => {
    const res = await fetch(`${API_BASE}/batches?room_id=${roomId}`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ commodity, qty_kg, shelf_life_days_ref })
    });
    return res.json();
  },

  // GradeLens
  gradeProduce: async (file: File, commodity = "Tomato", notes?: string) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("commodity", commodity);
    if (notes) formData.append("notes", notes);

    const res = await fetch(`${API_BASE}/grading`, {
      method: "POST",
      headers: getHeaders(true),
      body: formData
    });
    return res.json();
  },

  getGradings: async () => {
    const res = await fetch(`${API_BASE}/grading`, { headers: getHeaders() });
    return res.json();
  },

  getCertificate: async (gradingId: number) => {
    const res = await fetch(`${API_BASE}/grading/${gradingId}/certificate`, { headers: getHeaders() });
    return res.json();
  },

  reviewGrading: async (gradingId: number, reviewed_grade: string, reviewer_notes?: string) => {
    const res = await fetch(`${API_BASE}/grading/${gradingId}/review`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ reviewed_grade, reviewer_notes })
    });
    return res.json();
  },

  // SagarSuraksha
  getLandingSites: async () => {
    const res = await fetch(`${API_BASE}/sites`, { headers: getHeaders() });
    return res.json();
  },

  getMarineRisk: async (siteId: number) => {
    const res = await fetch(`${API_BASE}/sites/${siteId}/marine-risk`, { headers: getHeaders() });
    return res.json();
  },

  getBoats: async () => {
    const res = await fetch(`${API_BASE}/boats`, { headers: getHeaders() });
    return res.json();
  },

  registerBoat: async (reg_no: string, name: string, landing_site_id: number, crew_size = 4, contact_phone = "") => {
    const res = await fetch(`${API_BASE}/boats`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ reg_no, name, landing_site_id, crew_size, contact_phone })
    });
    return res.json();
  },

  getActiveTrips: async () => {
    const res = await fetch(`${API_BASE}/trips/active`, { headers: getHeaders() });
    return res.json();
  },

  startTrip: async (boat_id: number, expected_duration_hours = 12, checkin_interval_min = 180) => {
    const res = await fetch(`${API_BASE}/trips`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ boat_id, expected_duration_hours, checkin_interval_min })
    });
    return res.json();
  },

  tripCheckin: async (tripId: number, lat?: number, lon?: number, is_sos = false, note = "I'm safe") => {
    if (!navigator.onLine) {
      queueOfflineAction(`/trips/${tripId}/checkin`, "POST", { lat, lon, is_sos, note, source: "app" });
      return { status: "success", offline_queued: true, message: "Checkin queued offline. Will sync automatically." };
    }
    const res = await fetch(`${API_BASE}/trips/${tripId}/checkin`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ lat, lon, is_sos, note, source: "app" })
    });
    return res.json();
  },

  endTrip: async (tripId: number) => {
    const res = await fetch(`${API_BASE}/trips/${tripId}/end`, {
      method: "POST",
      headers: getHeaders()
    });
    return res.json();
  },

  getGeofences: async () => {
    const res = await fetch(`${API_BASE}/geofences`, { headers: getHeaders() });
    return res.json();
  },

  getContacts: async () => {
    const res = await fetch(`${API_BASE}/contacts`, { headers: getHeaders() });
    return res.json();
  },

  addContact: async (name: string, phone: string, kind = "family") => {
    const res = await fetch(`${API_BASE}/contacts`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ name, phone, kind })
    });
    return res.json();
  },

  // MandiMitra
  getMandis: async () => {
    const res = await fetch(`${API_BASE}/mandis`, { headers: getHeaders() });
    return res.json();
  },

  getCommodities: async () => {
    const res = await fetch(`${API_BASE}/commodities`, { headers: getHeaders() });
    return res.json();
  },

  getPrices: async (mandiId?: number, commId?: number) => {
    const params = new URLSearchParams();
    if (mandiId) params.append("mandi_id", mandiId.toString());
    if (commId) params.append("commodity_id", commId.toString());
    const res = await fetch(`${API_BASE}/prices?${params.toString()}`, { headers: getHeaders() });
    return res.json();
  },

  getAdvice: async (mandiId: number, commodityId: number, storageCost = 25.0) => {
    const res = await fetch(`${API_BASE}/advice/sell-hold?mandi_id=${mandiId}&commodity_id=${commodityId}&storage_cost=${storageCost}`, {
      headers: getHeaders()
    });
    return res.json();
  },

  getPriceAlerts: async () => {
    const res = await fetch(`${API_BASE}/price-alerts`, { headers: getHeaders() });
    return res.json();
  },

  createPriceAlert: async (mandi_id: number, commodity_id: number, threshold: number, direction = "above") => {
    const res = await fetch(`${API_BASE}/price-alerts`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ mandi_id, commodity_id, threshold, direction })
    });
    return res.json();
  },

  // MatsyaConnect
  getListings: async (species?: string, siteId?: number) => {
    const params = new URLSearchParams();
    if (species) params.append("species", species);
    if (siteId) params.append("site_id", siteId.toString());
    const res = await fetch(`${API_BASE}/listings?${params.toString()}`, { headers: getHeaders() });
    return res.json();
  },

  createListing: async (site_id: number, species: string, qty_kg: number, ask_price: number) => {
    if (!navigator.onLine) {
      queueOfflineAction(`/listings`, "POST", { site_id, species, qty_kg, ask_price });
      return { site_id, species, qty_kg, ask_price, status: "active", offline_queued: true };
    }
    const res = await fetch(`${API_BASE}/listings`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ site_id, species, qty_kg, ask_price })
    });
    return res.json();
  },

  getBuyerRequests: async () => {
    const res = await fetch(`${API_BASE}/buyer-requests`, { headers: getHeaders() });
    return res.json();
  },

  createBuyerRequest: async (species: string, qty_kg: number, max_price: number, radius_km = 50) => {
    const res = await fetch(`${API_BASE}/buyer-requests`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ species, qty_kg, max_price, radius_km })
    });
    return res.json();
  },

  getMatches: async () => {
    const res = await fetch(`${API_BASE}/matches`, { headers: getHeaders() });
    return res.json();
  },

  acceptMatch: async (matchId: number) => {
    const res = await fetch(`${API_BASE}/matches/${matchId}/accept`, {
      method: "POST",
      headers: getHeaders()
    });
    return res.json();
  },

  // SMS Simulator
  simulateSMS: async (message: string, from_phone = "9876543210") => {
    const res = await fetch(`${API_BASE}/sms/simulate`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ message, from_phone })
    });
    return res.json();
  },

  getSMSLogs: async () => {
    const res = await fetch(`${API_BASE}/sms/logs`, { headers: getHeaders() });
    return res.json();
  },

  // Notifications
  getNotifications: async () => {
    const res = await fetch(`${API_BASE}/notifications`, { headers: getHeaders() });
    return res.json();
  },

  // Admin & Simulator
  getStats: async () => {
    const res = await fetch(`${API_BASE}/admin/stats`, { headers: getHeaders() });
    return res.json();
  },

  triggerScenario: async (cold_room_id: number, scenario: string) => {
    const res = await fetch(`${API_BASE}/admin/simulator/scenario`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ cold_room_id, scenario })
    });
    return res.json();
  }
};
