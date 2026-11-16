export type UserRole = 'farmer' | 'fisher' | 'buyer' | 'fpo_admin' | 'admin';
export type Language = 'or' | 'en';

export interface User {
  id: number;
  phone: string;
  name: string;
  role: UserRole;
  language: Language;
  district: string;
}

export interface ColdRoom {
  id: number;
  name: string;
  location: string;
  district: string;
  capacity_kg: number;
  min_temp: number;
  max_temp: number;
  min_rh: number;
  max_rh: number;
  log_interval_min: number;
  latest_temp?: number;
  latest_rh?: number;
  latest_ts?: string;
  status: 'optimal' | 'warning' | 'danger' | 'stale';
  is_simulated: boolean;
  active_alerts_count: number;
}

export interface SensorReading {
  id: number;
  cold_room_id: number;
  ts: string;
  temp_c: number;
  rh: number;
  entered_by: string;
  is_simulated: boolean;
}

export interface Batch {
  id: number;
  cold_room_id: number;
  commodity: string;
  qty_kg: number;
  stored_at: string;
  shelf_life_days_ref: number;
  current_risk_pct: number;
  remaining_days: number;
  status: string;
  notes?: string;
}

export interface Alert {
  id: number;
  cold_room_id: number;
  kind: string;
  severity: 'info' | 'warning' | 'danger';
  opened_at: string;
  acked_at?: string;
  acked_by?: string;
  message_en: string;
  message_or: string;
  payload?: string;
}

export interface GradingResult {
  id: number;
  commodity: string;
  grade: 'A' | 'B' | 'C' | 'Reject';
  confidence: number;
  color_score: number;
  blemish_pct: number;
  shape_uniformity: number;
  size_est: string;
  model_version: string;
  needs_review: boolean;
  reviewed_grade?: string;
  certificate_id: string;
  qr_code_data?: string;
  image_url: string;
  created_at: string;
}

export interface LandingSite {
  id: number;
  name: string;
  district: string;
  lat: number;
  lon: number;
  active_fishers_count: number;
}

export interface MarineRisk {
  site_id: number;
  site_name: string;
  district: string;
  ts: string;
  wave_m: number;
  wind_kmh: number;
  gust_kmh: number;
  risk_level: 'green' | 'amber' | 'red';
  advice_en: string;
  advice_or: string;
}

export interface Boat {
  id: number;
  reg_no: string;
  name: string;
  landing_site_id: number;
  landing_site_name?: string;
  crew_size: number;
  contact_phone: string;
}

export interface Trip {
  id: number;
  boat_id: number;
  boat_name?: string;
  boat_reg_no?: string;
  departed_at: string;
  expected_return_at: string;
  returned_at?: string;
  status: 'active' | 'overdue' | 'returned' | 'sos';
  checkin_interval_min: number;
  last_checkin_at?: string;
  is_overdue: boolean;
  checkins_count: number;
}

export interface EmergencyContact {
  id: number;
  name: string;
  phone: string;
  kind: string;
}

export interface Geofence {
  id: number;
  name: string;
  name_or: string;
  kind: string;
  polygon: [number, number][];
  alert_message_en: string;
  alert_message_or: string;
  is_active: boolean;
}

export interface Mandi {
  id: number;
  name: string;
  name_or: string;
  district: string;
  lat: number;
  lon: number;
}

export interface Commodity {
  id: number;
  name_en: string;
  name_or: string;
  category: string;
  unit: string;
}

export interface PricePoint {
  date: string;
  modal_price: number;
  min_price: number;
  max_price: number;
  arrivals: number;
}

export interface ForecastPoint {
  date: string;
  p10: number;
  p50: number;
  p90: number;
}

export interface PriceAdvice {
  commodity: string;
  commodity_or: string;
  mandi: string;
  mandi_or: string;
  current_price: number;
  forecast_7d_p50: number;
  expected_gain_pct: number;
  storage_cost_per_day: number;
  spoilage_risk_pct: number;
  net_storage_profit: number;
  verdict: 'HOLD' | 'SELL';
  verdict_or: string;
  horizon_days: number;
  reason_en: string;
  reason_or: string;
  historical: PricePoint[];
  forecast: ForecastPoint[];
}

export interface CatchListing {
  id: number;
  fisher_id: number;
  fisher_name?: string;
  site_id: number;
  site_name?: string;
  district?: string;
  species: string;
  qty_kg: number;
  ask_price: number;
  status: string;
  created_at: string;
  expires_at?: string;
  reference_price_min?: number;
  reference_price_max?: number;
}

export interface BuyerRequest {
  id: number;
  buyer_id: number;
  buyer_name?: string;
  species: string;
  qty_kg: number;
  max_price: number;
  radius_km: number;
  status: string;
  created_at: string;
}

export interface Match {
  id: number;
  listing_id: number;
  request_id: number;
  score: number;
  status: string;
  species: string;
  qty_kg: number;
  price: number;
  landing_site: string;
  buyer_name?: string;
  buyer_phone?: string;
  fisher_name?: string;
  fisher_phone?: string;
  proposed_at: string;
}

export interface NotificationItem {
  id: number;
  channel: string;
  title_en: string;
  title_or: string;
  body_en: string;
  body_or: string;
  status: string;
  sent_at: string;
}
