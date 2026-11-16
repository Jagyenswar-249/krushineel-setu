import React, { useState, useEffect } from 'react';
import { Language, Mandi, Commodity, PriceAdvice, PricePoint, ForecastPoint } from '../types';
import { translations } from '../i18n/translations';
import { api } from '../services/api';
import {
  TrendingUp, Calendar, AlertCircle, ArrowUpRight, ArrowDownRight,
  DollarSign, Bell, CheckCircle2, ChevronRight, HelpCircle
} from 'lucide-react';

interface MandiMitraScreenProps {
  language: Language;
}

export const MandiMitraScreen: React.FC<MandiMitraScreenProps> = ({ language }) => {
  const t = translations[language];

  const [mandis, setMandis] = useState<Mandi[]>([]);
  const [commodities, setCommodities] = useState<Commodity[]>([]);
  const [selectedMandiId, setSelectedMandiId] = useState<number>(1);
  const [selectedCommId, setSelectedCommId] = useState<number>(1);
  const [storageCost, setStorageCost] = useState<number>(25.0); // Rs per Qtl / day
  const [advice, setAdvice] = useState<PriceAdvice | null>(null);
  const [loading, setLoading] = useState(true);

  // Price alert modal
  const [isAlertModalOpen, setIsAlertModalOpen] = useState(false);
  const [alertThreshold, setAlertThreshold] = useState('2400');
  const [alertSuccess, setAlertSuccess] = useState(false);

  const fetchFilters = async () => {
    try {
      const [mList, cList] = await Promise.all([
        api.getMandis(),
        api.getCommodities()
      ]);
      const validMandis = Array.isArray(mList) ? mList : [];
      const validCommodities = Array.isArray(cList) ? cList : [];
      setMandis(validMandis);
      setCommodities(validCommodities);
      if (validMandis.length > 0) setSelectedMandiId(validMandis[0].id);
      if (validCommodities.length > 0) setSelectedCommId(validCommodities[0].id);
    } catch (e) {
      console.error(e);
      setMandis([]);
      setCommodities([]);
    }
  };

  const fetchAdvice = async () => {
    if (!selectedMandiId || !selectedCommId) return;
    setLoading(true);
    try {
      const data = await api.getAdvice(selectedMandiId, selectedCommId, storageCost);
      setAdvice(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFilters();
  }, []);

  useEffect(() => {
    fetchAdvice();
  }, [selectedMandiId, selectedCommId, storageCost]);

  const handleCreateAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createPriceAlert(selectedMandiId, selectedCommId, parseFloat(alertThreshold), "above");
      setAlertSuccess(true);
      setTimeout(() => {
        setAlertSuccess(false);
        setIsAlertModalOpen(false);
      }, 1500);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="pb-24 pt-3 max-w-7xl mx-auto px-3 sm:px-6 space-y-5">
      {/* Header Bar */}
      <div className="bg-white p-4 rounded-2xl shadow-xs border border-slate-200">
        <h2 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
          <TrendingUp className="w-6 h-6 text-primary" />
          <span>{t.mandi.title}</span>
        </h2>
        <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
          {t.mandi.subtitle}
        </p>
      </div>

      {/* Selectors Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3 flex-wrap flex-1">
          {/* Mandi Selector */}
          <div>
            <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1">
              {t.mandi.selectMandi}
            </label>
            <select
              value={selectedMandiId}
              onChange={(e) => setSelectedMandiId(Number(e.target.value))}
              className="bg-slate-50 border border-slate-300 font-bold text-xs sm:text-sm rounded-xl px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {mandis.map((m) => (
                <option key={m.id} value={m.id}>
                  {language === 'or' ? m.name_or : m.name} ({m.district})
                </option>
              ))}
            </select>
          </div>

          {/* Commodity Selector */}
          <div>
            <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1">
              {t.mandi.selectCommodity}
            </label>
            <select
              value={selectedCommId}
              onChange={(e) => setSelectedCommId(Number(e.target.value))}
              className="bg-slate-50 border border-slate-300 font-bold text-xs sm:text-sm rounded-xl px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {commodities.map((c) => (
                <option key={c.id} value={c.id}>
                  {language === 'or' ? c.name_or : c.name_en} ({c.unit})
                </option>
              ))}
            </select>
          </div>

          {/* Cold Storage Cost Slider */}
          <div className="hidden sm:block">
            <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1">
              Cold Storage Rate (₹/Qtl/Day)
            </label>
            <input
              type="number"
              min="0"
              max="100"
              value={storageCost}
              onChange={(e) => setStorageCost(Number(e.target.value))}
              className="w-28 bg-slate-50 border border-slate-300 font-bold text-xs sm:text-sm rounded-xl px-2.5 py-1.5 text-slate-800"
            />
          </div>
        </div>

        <button
          onClick={() => setIsAlertModalOpen(true)}
          className="bg-primary hover:bg-primary-dark text-white font-bold text-xs px-3.5 py-2 rounded-xl flex items-center gap-1.5 transition-colors shadow-xs"
        >
          <Bell className="w-4 h-4 text-teal-200" />
          <span>{t.mandi.setAlertBtn}</span>
        </button>
      </div>

      {advice && (
        <div className="space-y-5">
          {/* AI Decision Verdict Card */}
          <div className={`p-5 rounded-3xl border shadow-md transition-all ${
            advice.verdict === 'HOLD'
              ? 'bg-gradient-to-br from-emerald-50 via-teal-50 to-white border-emerald-300'
              : 'bg-gradient-to-br from-amber-50 via-orange-50 to-white border-amber-300'
          }`}>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-black/10 pb-3 mb-3">
              <div>
                <span className="text-xs font-black uppercase tracking-wider text-slate-500">
                  AI Sell / Hold Advisory Verdict
                </span>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-xl sm:text-2xl font-black px-3.5 py-1 rounded-2xl ${
                    advice.verdict === 'HOLD' ? 'bg-emerald-600 text-white' : 'bg-amber-600 text-white'
                  }`}>
                    {advice.verdict === 'HOLD' ? t.mandi.verdictHold : t.mandi.verdictSell}
                  </span>
                  <span className="text-xs sm:text-sm font-bold text-slate-700">
                    {advice.horizon_days > 0 ? `Target horizon: ${advice.horizon_days} days` : 'Immediate liquidation'}
                  </span>
                </div>
              </div>

              {/* Today's Modal Price */}
              <div className="bg-white p-3 rounded-2xl border border-slate-200 shadow-xs text-right">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                  {t.mandi.currentModalPrice}
                </span>
                <span className="text-2xl font-black text-slate-900">
                  ₹{advice.current_price.toLocaleString()}
                </span>
                <span className="text-xs font-semibold text-slate-500"> / Quintal</span>
              </div>
            </div>

            {/* Plain-language Odia & English Rationale */}
            <div className="bg-white/80 p-4 rounded-2xl border border-black/5 shadow-xs mb-4">
              <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                <HelpCircle className="w-3.5 h-3.5 text-primary" />
                <span>{t.mandi.decisionReason}</span>
              </h4>
              <p className="text-sm font-extrabold text-slate-900 leading-relaxed">
                {language === 'or' ? advice.reason_or : advice.reason_en}
              </p>
            </div>

            {/* Financial Breakdown Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs font-semibold">
              <div className="bg-white/90 p-3 rounded-xl border border-black/5">
                <span className="text-slate-500 text-[11px] block">7-Day Projected (P50)</span>
                <span className="text-lg font-black text-slate-900">₹{advice.forecast_7d_p50}</span>
              </div>
              <div className="bg-white/90 p-3 rounded-xl border border-black/5">
                <span className="text-slate-500 text-[11px] block">{t.mandi.expectedGain}</span>
                <span className={`text-lg font-black ${advice.expected_gain_pct >= 0 ? 'text-emerald-700' : 'text-rose-600'}`}>
                  {advice.expected_gain_pct >= 0 ? '+' : ''}{advice.expected_gain_pct}%
                </span>
              </div>
              <div className="bg-white/90 p-3 rounded-xl border border-black/5">
                <span className="text-slate-500 text-[11px] block">Storage Cost (ColdWatch)</span>
                <span className="text-lg font-black text-slate-900">₹{advice.storage_cost_per_day * advice.horizon_days}</span>
              </div>
              <div className="bg-white/90 p-3 rounded-xl border border-black/5">
                <span className="text-slate-500 text-[11px] block">Net ROI After Costs</span>
                <span className={`text-lg font-black ${advice.net_storage_profit >= 0 ? 'text-emerald-700' : 'text-slate-600'}`}>
                  {advice.net_storage_profit >= 0 ? '+' : ''}₹{advice.net_storage_profit}/Qtl
                </span>
              </div>
            </div>
          </div>

          {/* 7-Day Price Forecast with P10 / P50 / P90 Error Bands */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="font-bold text-base text-slate-900 flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-primary" />
                  <span>{t.mandi.forecast7d}</span>
                </h3>
                <p className="text-xs text-slate-500">
                  Quantile LightGBM projection: P10 (conservative lower bound), P50 (expected median), P90 (optimistic upper bound).
                </p>
              </div>
            </div>

            {/* SVG Forecast Graph */}
            <div className="w-full h-56 bg-slate-50 rounded-xl border border-slate-200 p-3 relative overflow-hidden flex items-end">
              <div className="w-full h-full flex items-end justify-between gap-2 pt-6 pb-2">
                {advice.forecast.map((f, idx) => {
                  const minBase = Math.min(...advice.forecast.map((p) => p.p10)) * 0.95;
                  const maxBase = Math.max(...advice.forecast.map((p) => p.p90)) * 1.05;
                  const range = maxBase - minBase || 100;

                  const p10Pct = ((f.p10 - minBase) / range) * 100;
                  const p50Pct = ((f.p50 - minBase) / range) * 100;
                  const p90Pct = ((f.p90 - minBase) / range) * 100;

                  return (
                    <div key={idx} className="flex-1 flex flex-col items-center justify-end h-full relative group">
                      {/* Tooltip */}
                      <div className="absolute -top-8 hidden group-hover:flex bg-slate-900 text-white text-[10px] font-bold px-2 py-0.5 rounded shadow z-20 whitespace-nowrap">
                        P50: ₹{f.p50} (Band: ₹{f.p10} - ₹{f.p90})
                      </div>

                      {/* Uncertainty Band Bar */}
                      <div
                        className="w-full bg-teal-100/70 border border-teal-300 rounded-t-md relative flex items-center justify-center transition-all"
                        style={{ height: `${Math.max(15, p90Pct - p10Pct)}%` }}
                      >
                        {/* Median P50 Line */}
                        <div className="w-full h-1 bg-primary absolute top-1/2 -translate-y-1/2"></div>
                      </div>

                      <span className="text-[10px] font-bold text-slate-500 mt-1">
                        D+{idx + 1}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="flex items-center justify-between text-[11px] text-slate-500 mt-2 px-1">
              <span>Today ({advice.current_price} ₹/Qtl)</span>
              <div className="flex items-center gap-3 font-semibold">
                <span className="flex items-center gap-1">
                  <span className="w-3 h-1 bg-primary inline-block"></span>
                  <span>P50 Expected</span>
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 bg-teal-100 border border-teal-300 rounded-xs inline-block"></span>
                  <span>Confidence Band (P10-P90)</span>
                </span>
              </div>
              <span>Day 7 Horizon</span>
            </div>
          </div>

          {/* Past 25 Days Historical Mandi Price Trend */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
            <h3 className="font-bold text-sm text-slate-900 mb-3 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-agri" />
              <span>{t.mandi.historical30d}</span>
            </h3>
            <div className="w-full h-36 bg-slate-50 rounded-xl border border-slate-200 p-2 flex items-end justify-between gap-1">
              {advice.historical.map((h, i) => {
                const minH = Math.min(...advice.historical.map((x) => x.modal_price));
                const maxH = Math.max(...advice.historical.map((x) => x.modal_price));
                const pct = ((h.modal_price - minH) / (maxH - minH || 1)) * 80 + 15;
                return (
                  <div key={i} className="flex-1 flex flex-col items-center justify-end h-full group relative">
                    <div className="absolute -top-6 hidden group-hover:block bg-slate-800 text-white text-[9px] px-1 py-0.5 rounded whitespace-nowrap z-10">
                      {h.date}: ₹{h.modal_price}
                    </div>
                    <div
                      className="w-full bg-agri/80 hover:bg-agri rounded-t-xs"
                      style={{ height: `${pct}%` }}
                    ></div>
                  </div>
                );
              })}
            </div>
            <div className="flex justify-between text-[10px] text-slate-400 mt-1.5 px-1">
              <span>25 Days Ago</span>
              <span>Agmarknet Verified Odisha Mandi Data</span>
              <span>Latest</span>
            </div>
          </div>
        </div>
      )}

      {/* Price Alert Modal */}
      {isAlertModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-sm w-full p-5 shadow-2xl border border-slate-200">
            <h3 className="font-bold text-lg text-slate-900 mb-1">{t.mandi.setAlertBtn}</h3>
            <p className="text-xs text-slate-500 mb-4">
              Receive instant SMS alert when price crosses your desired threshold:
            </p>

            <form onSubmit={handleCreateAlert} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Threshold Price (₹ per Quintal)
                </label>
                <input
                  type="number"
                  step="50"
                  required
                  value={alertThreshold}
                  onChange={(e) => setAlertThreshold(e.target.value)}
                  className="w-full text-xl font-bold bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              {alertSuccess && (
                <div className="p-2 rounded-lg bg-emerald-50 text-emerald-800 text-xs font-bold flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>SMS alert active! You will be alerted upon price rise.</span>
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsAlertModalOpen(false)}
                  className="px-3.5 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl"
                >
                  {t.common.cancel}
                </button>
                <button
                  type="submit"
                  className="bg-primary hover:bg-primary-dark text-white font-bold text-xs px-4 py-2 rounded-xl transition-colors shadow-xs"
                >
                  Save Alert
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
