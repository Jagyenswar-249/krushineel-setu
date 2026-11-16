import React, { useState, useEffect } from 'react';
import { Language, LandingSite, MarineRisk, Boat, Trip, Geofence, EmergencyContact } from '../types';
import { translations } from '../i18n/translations';
import { api } from '../services/api';
import {
  Shield, AlertTriangle, LifeBuoy, Compass, Wind, Waves, CheckCircle2,
  PhoneCall, MapPin, Anchor, Plus, Clock, AlertOctagon
} from 'lucide-react';

interface SagarSurakshaScreenProps {
  language: Language;
}

export const SagarSurakshaScreen: React.FC<SagarSurakshaScreenProps> = ({ language }) => {
  const t = translations[language];

  const [landingSites, setLandingSites] = useState<LandingSite[]>([]);
  const [selectedSiteId, setSelectedSiteId] = useState<number>(1);
  const [marineRisk, setMarineRisk] = useState<MarineRisk | null>(null);
  const [boats, setBoats] = useState<Boat[]>([]);
  const [activeTrips, setActiveTrips] = useState<Trip[]>([]);
  const [geofences, setGeofences] = useState<Geofence[]>([]);
  const [contacts, setContacts] = useState<EmergencyContact[]>([]);
  const [loading, setLoading] = useState(true);

  // Checkin feedback
  const [checkinMessage, setCheckinMessage] = useState<string | null>(null);
  const [isSOSConfirmOpen, setIsSOSConfirmOpen] = useState(false);

  const fetchData = async () => {
    try {
      const sites = await api.getLandingSites();
      setLandingSites(sites || []);
      const activeId = sites && sites.length > 0 ? (selectedSiteId || sites[0].id) : 1;
      setSelectedSiteId(activeId);

      const [risk, bList, tList, gList, cList] = await Promise.all([
        api.getMarineRisk(activeId),
        api.getBoats(),
        api.getActiveTrips(),
        api.getGeofences(),
        api.getContacts()
      ]);

      setMarineRisk(risk);
      setBoats(bList || []);
      setActiveTrips(tList || []);
      setGeofences(gList || []);
      setContacts(cList || []);
    } catch (e) {
      console.error("SagarSuraksha error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedSiteId]);

  const activeTrip = activeTrips.length > 0 ? activeTrips[0] : null;

  const handleSafeCheckin = async () => {
    if (!activeTrip) return;
    try {
      const res = await api.tripCheckin(activeTrip.id, 19.78, 85.85, false, "I'm safe (app tap)");
      setCheckinMessage("Check-in saved! Watchdog timer reset. Safe fishing!");
      setTimeout(() => setCheckinMessage(null), 3000);
      fetchData();
    } catch (e) {
      console.error(e);
    }
  };

  const handleSOS = async () => {
    if (!activeTrip) return;
    try {
      await api.tripCheckin(activeTrip.id, 19.78, 85.85, true, "EMERGENCY SOS TRIGGERED");
      setIsSOSConfirmOpen(false);
      setCheckinMessage("EMERGENCY ALERT SENT to Family, Fisheries Dept, and Coast Guard!");
      fetchData();
    } catch (e) {
      console.error(e);
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'red':
        return { bg: 'bg-rose-50 border-rose-300', text: 'text-rose-900', badge: 'bg-rose-600 text-white' };
      case 'amber':
        return { bg: 'bg-amber-50 border-amber-300', text: 'text-amber-900', badge: 'bg-amber-500 text-white' };
      case 'green':
      default:
        return { bg: 'bg-emerald-50 border-emerald-300', text: 'text-emerald-900', badge: 'bg-emerald-600 text-white' };
    }
  };

  return (
    <div className="pb-24 pt-3 max-w-7xl mx-auto px-3 sm:px-6 space-y-5">
      {/* Header Bar */}
      <div className="bg-white p-4 rounded-2xl shadow-xs border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <Shield className="w-6 h-6 text-primary" />
            <span>{t.sagar.title}</span>
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            {t.sagar.subtitle}
          </p>
        </div>

        {/* Site Picker */}
        <select
          value={selectedSiteId}
          onChange={(e) => setSelectedSiteId(Number(e.target.value))}
          className="bg-slate-100 border border-slate-300 font-semibold text-xs sm:text-sm rounded-xl px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary"
        >
          {landingSites.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name} ({s.district})
            </option>
          ))}
        </select>
      </div>

      {/* Marine Weather Risk Banner */}
      {marineRisk && (
        <div className={`p-5 rounded-2xl border shadow-sm ${getRiskColor(marineRisk.risk_level).bg}`}>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-black/10 pb-3 mb-3">
            <div className="flex items-center gap-2.5">
              <span className={`text-xs font-black px-2.5 py-1 rounded-full uppercase tracking-wider ${getRiskColor(marineRisk.risk_level).badge}`}>
                {marineRisk.risk_level === 'green' ? t.sagar.riskGreen : marineRisk.risk_level === 'amber' ? t.sagar.riskAmber : t.sagar.riskRed}
              </span>
              <span className="text-xs font-bold text-slate-700">
                Landing Site: {marineRisk.site_name}
              </span>
            </div>
            <span className="text-[11px] text-slate-500 font-medium">
              Source: Open-Meteo Marine (Calibrated IMD Odisha)
            </span>
          </div>

          <p className="text-sm font-bold leading-relaxed mb-4">
            {language === 'or' ? marineRisk.advice_or : marineRisk.advice_en}
          </p>

          <div className="grid grid-cols-3 gap-2 sm:gap-4 text-xs font-semibold">
            <div className="bg-white/80 p-2.5 rounded-xl border border-black/5 flex items-center gap-2">
              <Waves className="w-4 h-4 text-primary" />
              <div>
                <span className="text-slate-500 text-[10px] block">{t.sagar.waveHeight}</span>
                <span className="font-extrabold text-sm text-slate-900">{marineRisk.wave_m} meters</span>
              </div>
            </div>
            <div className="bg-white/80 p-2.5 rounded-xl border border-black/5 flex items-center gap-2">
              <Wind className="w-4 h-4 text-primary" />
              <div>
                <span className="text-slate-500 text-[10px] block">{t.sagar.windSpeed}</span>
                <span className="font-extrabold text-sm text-slate-900">{marineRisk.wind_kmh} km/h</span>
              </div>
            </div>
            <div className="bg-white/80 p-2.5 rounded-xl border border-black/5 flex items-center gap-2">
              <Compass className="w-4 h-4 text-primary" />
              <div>
                <span className="text-slate-500 text-[10px] block">{t.sagar.windGust}</span>
                <span className="font-extrabold text-sm text-slate-900">{marineRisk.gust_kmh} km/h</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Primary Trip Action Card: Big "I'm Safe" and SOS */}
      <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm text-center">
        {activeTrip ? (
          <div className="space-y-4">
            <div className="flex items-center justify-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping"></span>
              <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                Voyage in Progress: {activeTrip.boat_name || 'Boat'} ({activeTrip.boat_reg_no})
              </span>
            </div>

            {/* Huge 1-Tap "I'M SAFE" Button */}
            <div className="py-2">
              <button
                onClick={handleSafeCheckin}
                className="w-full sm:w-80 mx-auto py-5 px-6 rounded-3xl bg-emerald-600 hover:bg-emerald-700 text-white font-black text-xl sm:text-2xl shadow-xl hover:shadow-2xl active:scale-95 transition-all flex items-center justify-center gap-3 border-4 border-emerald-400"
              >
                <CheckCircle2 className="w-8 h-8" />
                <span>{t.sagar.safeCheckinBtn}</span>
              </button>
            </div>

            <p className="text-xs text-slate-500 max-w-md mx-auto">
              {t.sagar.safePrompt}
            </p>

            {checkinMessage && (
              <div className="p-3 bg-emerald-100 text-emerald-900 font-bold text-xs rounded-xl inline-block">
                {checkinMessage}
              </div>
            )}

            {/* Emergency SOS Button */}
            <div className="pt-2">
              <button
                onClick={() => setIsSOSConfirmOpen(true)}
                className="text-rose-600 hover:text-rose-800 text-xs font-bold tracking-wide flex items-center gap-1.5 mx-auto p-2 hover:bg-rose-50 rounded-xl transition-colors"
              >
                <AlertOctagon className="w-4 h-4" />
                <span>{t.sagar.sosBtn}</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="py-6 space-y-3">
            <Anchor className="w-12 h-12 text-slate-300 mx-auto" />
            <h3 className="font-bold text-base text-slate-800">No Active Sea Voyage</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Starting a voyage activates the overdue check-in watchdog and SMS safety alert engine.
            </p>
            <button
              onClick={async () => {
                if (boats.length > 0) {
                  await api.startTrip(boats[0].id, 12, 180);
                  fetchData();
                }
              }}
              className="bg-primary hover:bg-primary-dark text-white font-bold text-xs px-5 py-2.5 rounded-xl shadow-md transition-colors"
            >
              Start Sea Voyage (12 Hours)
            </button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Coastal Geofences & Conservation Map (Left) */}
        <div className="lg:col-span-7 bg-white p-4 sm:p-5 rounded-2xl border border-slate-200 shadow-xs space-y-3">
          <h3 className="font-bold text-base text-slate-900 flex items-center gap-2">
            <MapPin className="w-5 h-5 text-primary" />
            <span>{t.sagar.geofenceTitle}</span>
          </h3>

          {/* Stylized SVG Map of Odisha Coastline */}
          <div className="w-full h-60 bg-gradient-to-b from-sky-50 via-teal-50 to-blue-50 rounded-xl border border-slate-200 relative overflow-hidden p-3">
            <svg viewBox="0 0 400 240" className="w-full h-full">
              {/* Coastline outline */}
              <path
                d="M 60,20 Q 140,80 200,120 T 320,200 L 400,240 L 400,0 L 0,0 Z"
                fill="#f1f5f9"
                stroke="#cbd5e1"
                strokeWidth="2"
              />
              <path
                d="M 60,20 Q 140,80 200,120 T 320,200"
                fill="none"
                stroke="#0d5c56"
                strokeWidth="3"
                strokeDasharray="4 2"
              />

              {/* Bay of Bengal label */}
              <text x="260" y="70" fill="#0284c7" fontSize="12" fontWeight="bold" opacity="0.6">
                Bay of Bengal (ସମୁଦ୍ର)
              </text>

              {/* Geofence 1: Gahirmatha Olive Ridley Sanctuary */}
              <polygon
                points="220,130 260,110 280,140 240,160"
                fill="rgba(239, 68, 68, 0.25)"
                stroke="#dc2626"
                strokeWidth="1.5"
              />
              <text x="245" y="135" fill="#991b1b" fontSize="8" fontWeight="bold">
                Gahirmatha (Sanctuary)
              </text>

              {/* Geofence 2: Rushikulya Rookery */}
              <polygon
                points="90,40 130,30 140,60 100,70"
                fill="rgba(245, 158, 11, 0.25)"
                stroke="#d97706"
                strokeWidth="1.5"
              />
              <text x="95" y="52" fill="#92400e" fontSize="8" fontWeight="bold">
                Rushikulya (Nov-May Ban)
              </text>

              {/* Landing Sites markers */}
              <circle cx="170" cy="100" r="5" fill="#0d5c56" />
              <text x="178" y="103" fill="#0f172a" fontSize="9" fontWeight="bold">Puri</text>

              <circle cx="215" cy="125" r="5" fill="#0d5c56" />
              <text x="223" y="128" fill="#0f172a" fontSize="9" fontWeight="bold">Paradip</text>

              <circle cx="80" cy="35" r="5" fill="#0d5c56" />
              <text x="88" y="38" fill="#0f172a" fontSize="9" fontWeight="bold">Gopalpur</text>

              {/* Active Boat Pin */}
              {activeTrip && (
                <g>
                  <circle cx="190" cy="115" r="6" fill="#16a34a" className="animate-pulse" />
                  <text x="200" y="118" fill="#15803d" fontSize="9" fontWeight="extrabold">
                    Maa Mangala (OD-02)
                  </text>
                </g>
              )}
            </svg>
          </div>

          <div className="space-y-2 mt-2">
            {geofences.map((gf) => (
              <div key={gf.id} className="p-2.5 rounded-xl border border-slate-200 bg-slate-50 flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h5 className="font-bold text-xs text-slate-900">
                    {language === 'or' ? gf.name_or : gf.name}
                  </h5>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    {language === 'or' ? gf.alert_message_or : gf.alert_message_en}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Emergency Escalation Contacts (Right) */}
        <div className="lg:col-span-5 bg-white p-4 sm:p-5 rounded-2xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-base text-slate-900 flex items-center gap-2">
              <PhoneCall className="w-5 h-5 text-primary" />
              <span>{t.sagar.contactsTitle}</span>
            </h3>
          </div>

          <p className="text-xs text-slate-500">
            If a check-in is overdue beyond grace period, automatic alerts are escalated to these verified numbers:
          </p>

          <div className="space-y-2.5">
            {contacts.map((c) => (
              <div key={c.id} className="p-3 rounded-xl border border-slate-200 bg-slate-50 flex items-center justify-between">
                <div>
                  <span className="font-bold text-xs text-slate-900 block">{c.name}</span>
                  <span className="text-[10px] uppercase font-bold text-teal-700 bg-teal-100 px-1.5 py-0.5 rounded">
                    {c.kind}
                  </span>
                </div>
                <a
                  href={`tel:${c.phone}`}
                  className="font-mono text-xs font-bold text-primary bg-white px-2.5 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50"
                >
                  {c.phone}
                </a>
              </div>
            ))}
          </div>

          {/* Feature Phone Fallback Reminder */}
          <div className="p-3 bg-teal-50 border border-teal-200 rounded-xl text-teal-950 text-xs leading-normal">
            <p className="font-bold mb-1">Feature Phone SMS Fallback:</p>
            <p className="text-[11px] text-teal-800">
              When out of data coverage, send <b>SAFE</b> via SMS to reset the watchdog timer directly without an app.
            </p>
          </div>
        </div>
      </div>

      {/* SOS Confirmation Dialog */}
      {isSOSConfirmOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs">
          <div className="bg-white rounded-3xl max-w-sm w-full p-6 shadow-2xl text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mx-auto">
              <AlertOctagon className="w-7 h-7" />
            </div>
            <h3 className="font-black text-lg text-slate-900">Confirm Emergency Distress Alert</h3>
            <p className="text-xs text-slate-500">
              This will immediately send high-priority SMS alerts to your family, the local Fisheries Officer, and the Coast Guard station.
            </p>
            <div className="flex items-center gap-2 pt-2">
              <button
                onClick={() => setIsSOSConfirmOpen(false)}
                className="flex-1 py-2.5 rounded-xl border border-slate-300 font-bold text-xs text-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={handleSOS}
                className="flex-1 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-black text-xs shadow-md"
              >
                YES, SEND SOS
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
