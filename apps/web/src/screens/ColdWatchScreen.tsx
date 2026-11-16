import React, { useState, useEffect } from 'react';
import { Language, ColdRoom, SensorReading, Batch, Alert } from '../types';
import { translations } from '../i18n/translations';
import { SimulatorBar } from '../components/SimulatorBar';
import { api } from '../services/api';
import {
  Thermometer, Droplets, Clock, AlertTriangle, Plus, Upload, Key,
  CheckCircle, ChevronRight, RefreshCw, Box, ShieldAlert
} from 'lucide-react';

interface ColdWatchScreenProps {
  language: Language;
}

export const ColdWatchScreen: React.FC<ColdWatchScreenProps> = ({ language }) => {
  const t = translations[language];

  const [coldRooms, setColdRooms] = useState<ColdRoom[]>([]);
  const [selectedRoomId, setSelectedRoomId] = useState<number>(1);
  const [readings, setReadings] = useState<SensorReading[]>([]);
  const [batches, setBatches] = useState<Batch[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [isQuickLogOpen, setIsQuickLogOpen] = useState(false);
  const [isCSVModalOpen, setIsCSVModalOpen] = useState(false);
  const [isTokenModalOpen, setIsTokenModalOpen] = useState(false);

  // Quick log state
  const [logTemp, setLogTemp] = useState('4.2');
  const [logRh, setLogRh] = useState('88');
  const [quickLogSuccess, setQuickLogSuccess] = useState(false);

  // CSV file state
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvStatus, setCsvStatus] = useState<string | null>(null);

  // API Token state
  const [generatedToken, setGeneratedToken] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const rooms = await api.getColdRooms();
      setColdRooms(rooms || []);
      const activeId = rooms && rooms.length > 0 ? (selectedRoomId || rooms[0].id) : 1;
      setSelectedRoomId(activeId);

      const [rData, bData, aData] = await Promise.all([
        api.getReadings(activeId, 24),
        api.getBatches(activeId),
        api.getAlerts(activeId)
      ]);

      setReadings(rData || []);
      setBatches(bData || []);
      setAlerts(aData || []);
    } catch (e) {
      console.error("ColdWatch fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedRoomId]);

  const activeRoom = coldRooms.find((r) => r.id === selectedRoomId) || coldRooms[0];

  const handleQuickLog = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeRoom) return;
    try {
      await api.addReading(activeRoom.id, parseFloat(logTemp), parseFloat(logRh));
      setQuickLogSuccess(true);
      setTimeout(() => {
        setQuickLogSuccess(false);
        setIsQuickLogOpen(false);
      }, 1200);
      fetchData();
    } catch (err) {
      console.error("Log error:", err);
    }
  };

  const handleCSVUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!csvFile || !activeRoom) return;
    try {
      setCsvStatus("Uploading and parsing logger readings...");
      const res = await api.importCSV(activeRoom.id, csvFile);
      setCsvStatus(`Success! Imported ${res.data?.imported_rows || 'all'} rows.`);
      setTimeout(() => {
        setIsCSVModalOpen(false);
        setCsvStatus(null);
        setCsvFile(null);
      }, 1500);
      fetchData();
    } catch (err: any) {
      setCsvStatus(`Failed: ${err.message || 'Error processing CSV'}`);
    }
  };

  const handleGenerateToken = async () => {
    if (!activeRoom) return;
    try {
      const res = await api.createDataSource(activeRoom.id, "Automated Digital Logger", "api");
      setGeneratedToken(res.token || "kns_token_created");
    } catch (err) {
      console.error(err);
    }
  };

  const handleAckAlert = async (alertId: number) => {
    try {
      await api.ackAlert(alertId);
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="pb-24 pt-2">
      {/* Simulator Bar */}
      <SimulatorBar
        language={language}
        coldRoomId={selectedRoomId}
        onScenarioTriggered={fetchData}
      />

      <div className="max-w-7xl mx-auto px-3 sm:px-6 mt-4 space-y-5">
        {/* Title & Room Selector */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-4 rounded-2xl shadow-xs border border-slate-200">
          <div>
            <h2 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
              <Thermometer className="w-6 h-6 text-primary" />
              <span>{t.coldwatch.title}</span>
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
              {t.coldwatch.subtitle}
            </p>
          </div>

          {/* Room Dropdown & Actions */}
          <div className="flex items-center gap-2 flex-wrap">
            <select
              value={selectedRoomId}
              onChange={(e) => setSelectedRoomId(Number(e.target.value))}
              className="bg-slate-100 border border-slate-300 text-xs sm:text-sm font-semibold rounded-xl px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {coldRooms.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name} ({r.district})
                </option>
              ))}
            </select>

            <button
              onClick={() => setIsQuickLogOpen(true)}
              className="bg-agri hover:bg-agri-dark text-white font-bold text-xs sm:text-sm px-3.5 py-2 rounded-xl shadow-xs flex items-center gap-1.5 transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>{t.coldwatch.quickLogBtn}</span>
            </button>

            <button
              onClick={() => setIsCSVModalOpen(true)}
              className="bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 font-semibold text-xs sm:text-sm px-3 py-2 rounded-xl flex items-center gap-1.5 transition-colors"
            >
              <Upload className="w-4 h-4 text-slate-500" />
              <span className="hidden md:inline">{t.coldwatch.csvImportBtn}</span>
            </button>

            <button
              onClick={() => { setIsTokenModalOpen(true); handleGenerateToken(); }}
              className="bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 font-semibold text-xs sm:text-sm px-2.5 py-2 rounded-xl flex items-center gap-1.5 transition-colors"
              title="HTTP Ingest API Token"
            >
              <Key className="w-4 h-4 text-slate-500" />
            </button>
          </div>
        </div>

        {/* Live Gauges & Status Tiles */}
        {activeRoom && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            {/* Temp Tile */}
            <div className={`p-4 rounded-2xl border shadow-xs transition-all ${
              (activeRoom.latest_temp ?? 4) > activeRoom.max_temp
                ? 'bg-rose-50 border-rose-300 text-rose-900'
                : 'bg-white border-slate-200 text-slate-900'
            }`}>
              <div className="flex items-center justify-between text-slate-500 mb-1">
                <span className="text-xs font-bold uppercase tracking-wider">{t.coldwatch.currentTemp}</span>
                <Thermometer className="w-5 h-5 text-primary" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl sm:text-4xl font-black tracking-tight">
                  {activeRoom.latest_temp !== undefined ? `${activeRoom.latest_temp}°C` : '--'}
                </span>
                {activeRoom.is_simulated && (
                  <span className="text-[10px] bg-amber-500 text-white font-extrabold px-1.5 py-0.5 rounded uppercase">
                    SIMULATED
                  </span>
                )}
              </div>
              <div className="mt-2 text-xs font-medium text-slate-500 flex items-center justify-between">
                <span>{t.coldwatch.optimalRange}: {activeRoom.min_temp}°C - {activeRoom.max_temp}°C</span>
                <span className={`font-bold ${
                  (activeRoom.latest_temp ?? 4) > activeRoom.max_temp ? 'text-rose-600' : 'text-emerald-600'
                }`}>
                  {(activeRoom.latest_temp ?? 4) > activeRoom.max_temp ? 'HIGH TEMP' : 'OPTIMAL'}
                </span>
              </div>
            </div>

            {/* Humidity Tile */}
            <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between text-slate-500 mb-1">
                <span className="text-xs font-bold uppercase tracking-wider">{t.coldwatch.currentRh}</span>
                <Droplets className="w-5 h-5 text-cyan-600" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight">
                  {activeRoom.latest_rh !== undefined ? `${activeRoom.latest_rh}%` : '--'}
                </span>
              </div>
              <div className="mt-2 text-xs font-medium text-slate-500">
                <span>{t.coldwatch.optimalRange}: {activeRoom.min_rh}% - {activeRoom.max_rh}%</span>
              </div>
            </div>

            {/* Capacity Tile */}
            <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between text-slate-500 mb-1">
                <span className="text-xs font-bold uppercase tracking-wider">Storage Capacity</span>
                <Box className="w-5 h-5 text-indigo-600" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight">
                  {batches.reduce((acc, b) => acc + b.qty_kg, 0).toLocaleString()}
                </span>
                <span className="text-xs font-bold text-slate-400">/ {activeRoom.capacity_kg.toLocaleString()} kg</span>
              </div>
              <div className="mt-2 w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-indigo-600 h-2 rounded-full"
                  style={{ width: `${Math.min(100, (batches.reduce((acc, b) => acc + b.qty_kg, 0) / activeRoom.capacity_kg) * 100)}%` }}
                ></div>
              </div>
            </div>

            {/* Active Alerts Tile */}
            <div className={`p-4 rounded-2xl border shadow-xs ${
              alerts.length > 0 ? 'bg-amber-50 border-amber-300' : 'bg-white border-slate-200'
            }`}>
              <div className="flex items-center justify-between text-slate-500 mb-1">
                <span className="text-xs font-bold uppercase tracking-wider">{t.coldwatch.activeAlerts}</span>
                <ShieldAlert className={`w-5 h-5 ${alerts.length > 0 ? 'text-amber-600' : 'text-slate-400'}`} />
              </div>
              <div className="flex items-baseline gap-2">
                <span className={`text-3xl sm:text-4xl font-black tracking-tight ${
                  alerts.length > 0 ? 'text-amber-600' : 'text-slate-900'
                }`}>
                  {alerts.length}
                </span>
                <span className="text-xs font-medium text-slate-500">
                  {alerts.length === 0 ? 'Normal' : 'Requires Attention'}
                </span>
              </div>
              <div className="mt-2 text-xs text-slate-500">
                Log Interval: Every {activeRoom.log_interval_min} min
              </div>
            </div>
          </div>
        )}

        {/* 24h Trend Chart */}
        <div className="bg-white p-4 sm:p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-bold text-base text-slate-900 flex items-center gap-2">
              <Clock className="w-5 h-5 text-primary" />
              <span>{t.coldwatch.liveReadings}</span>
            </h3>
            <span className="text-xs text-slate-400">Past 24 Hours</span>
          </div>

          {/* SVG Trend Line Chart */}
          <div className="w-full h-48 bg-slate-50 rounded-xl border border-slate-200 p-2 relative overflow-hidden flex items-end">
            {readings.length === 0 ? (
              <p className="text-xs text-slate-400 m-auto">No readings recorded yet.</p>
            ) : (
              <div className="w-full h-full flex items-end justify-between gap-1 pt-6 pb-4">
                {readings.map((r, idx) => {
                  // Normalize temp between -5 to 30 for visualization
                  const heightPct = Math.min(100, Math.max(10, ((r.temp_c + 2) / 25) * 100));
                  const isHigh = r.temp_c > (activeRoom?.max_temp || 8);
                  return (
                    <div
                      key={idx}
                      className="flex-1 flex flex-col items-center group relative h-full justify-end"
                    >
                      {/* Tooltip on hover */}
                      <div className="absolute -top-7 hidden group-hover:flex bg-slate-900 text-white text-[10px] font-bold px-1.5 py-0.5 rounded shadow whitespace-nowrap z-20">
                        {r.temp_c}°C | {r.rh}% RH
                      </div>
                      <div
                        className={`w-full rounded-t-sm transition-all ${
                          isHigh ? 'bg-rose-500' : 'bg-primary hover:bg-teal-700'
                        }`}
                        style={{ height: `${heightPct}%` }}
                      ></div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
          <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2">
            <span>24 Hours Ago</span>
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-full bg-primary inline-block"></span>
                <span>Optimal (2°C - 8°C)</span>
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block"></span>
                <span>Above Safe Max</span>
              </span>
            </div>
            <span>Just Now</span>
          </div>
        </div>

        {/* Stored Batches & Spoilage Prediction */}
        <div className="bg-white p-4 sm:p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-base text-slate-900 flex items-center gap-2">
                <Box className="w-5 h-5 text-agri" />
                <span>{t.coldwatch.batchesTitle}</span>
              </h3>
              <p className="text-xs text-slate-500">
                Arrhenius Q10 predictive shelf-life model factoring room temperature history.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {batches.map((b) => {
              const riskColor = b.current_risk_pct > 70 ? 'text-rose-600 bg-rose-50 border-rose-200' : b.current_risk_pct > 30 ? 'text-amber-600 bg-amber-50 border-amber-200' : 'text-emerald-600 bg-emerald-50 border-emerald-200';
              const progressPct = Math.min(100, Math.max(0, (b.remaining_days / b.shelf_life_days_ref) * 100));

              return (
                <div key={b.id} className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-white transition-colors shadow-xs">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-bold text-sm text-slate-900">{b.commodity}</h4>
                      <p className="text-xs text-slate-500">{b.qty_kg} kg stored</p>
                    </div>
                    <span className={`text-xs font-black px-2 py-0.5 rounded-full border ${riskColor}`}>
                      {b.current_risk_pct}% Risk
                    </span>
                  </div>

                  {/* Remaining Days Counter */}
                  <div className="mt-3">
                    <div className="flex justify-between text-xs font-semibold mb-1">
                      <span className="text-slate-600">Remaining Shelf Life:</span>
                      <span className="font-bold text-slate-900">{b.remaining_days} {t.coldwatch.remainingDays}</span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-2 rounded-full ${b.remaining_days < 3 ? 'bg-rose-500' : 'bg-agri'}`}
                        style={{ width: `${progressPct}%` }}
                      ></div>
                    </div>
                  </div>

                  <p className="text-[11px] text-slate-400 mt-2 italic truncate">
                    {b.notes || `Reference: ${b.shelf_life_days_ref} days at 4°C`}
                  </p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Active Alerts Table */}
        {alerts.length > 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 shadow-xs">
            <h3 className="font-bold text-sm text-amber-900 flex items-center gap-2 mb-3">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span>{t.coldwatch.activeAlerts} ({alerts.length})</span>
            </h3>
            <div className="space-y-2">
              {alerts.map((a) => (
                <div key={a.id} className="bg-white p-3 rounded-xl border border-amber-200 flex items-center justify-between gap-3 flex-wrap">
                  <div>
                    <span className="text-xs font-bold text-amber-900 block">
                      {language === 'or' ? a.message_or : a.message_en}
                    </span>
                    <span className="text-[10px] text-slate-400">
                      Opened at: {new Date(a.opened_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <button
                    onClick={() => handleAckAlert(a.id)}
                    className="bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs px-3 py-1.5 rounded-lg transition-colors"
                  >
                    {t.coldwatch.ackAlert}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Quick Log Modal */}
      {isQuickLogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-sm w-full p-5 shadow-2xl border border-slate-200">
            <h3 className="font-bold text-lg text-slate-900 mb-1">{t.coldwatch.quickLogBtn}</h3>
            <p className="text-xs text-slate-500 mb-4">Enter current digital thermometer readings for {activeRoom?.name}:</p>

            <form onSubmit={handleQuickLog} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Temperature (°C)
                </label>
                <input
                  type="number"
                  step="0.1"
                  required
                  value={logTemp}
                  onChange={(e) => setLogTemp(e.target.value)}
                  className="w-full text-xl font-bold bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Relative Humidity (%)
                </label>
                <input
                  type="number"
                  step="0.5"
                  required
                  value={logRh}
                  onChange={(e) => setLogRh(e.target.value)}
                  className="w-full text-xl font-bold bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              {quickLogSuccess && (
                <div className="p-2 rounded-lg bg-emerald-50 text-emerald-800 text-xs font-bold flex items-center gap-1.5">
                  <CheckCircle className="w-4 h-4 text-emerald-600" />
                  <span>{t.coldwatch.logSuccess}</span>
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsQuickLogOpen(false)}
                  className="px-3.5 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl"
                >
                  {t.common.cancel}
                </button>
                <button
                  type="submit"
                  className="bg-primary hover:bg-primary-dark text-white font-bold text-xs px-4 py-2 rounded-xl transition-colors shadow-xs"
                >
                  {t.common.save}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CSV Import Modal */}
      {isCSVModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-md w-full p-5 shadow-2xl border border-slate-200">
            <h3 className="font-bold text-lg text-slate-900 mb-1">{t.coldwatch.csvImportBtn}</h3>
            <p className="text-xs text-slate-500 mb-4">
              Upload exported CSV file from your digital logger (e.g. Elitech, Lascar USB loggers). Columns are automatically mapped.
            </p>

            <form onSubmit={handleCSVUpload} className="space-y-4">
              <div className="border-2 border-dashed border-slate-300 rounded-xl p-4 text-center hover:bg-slate-50 cursor-pointer">
                <input
                  type="file"
                  accept=".csv,.txt"
                  required
                  onChange={(e) => setCsvFile(e.target.files ? e.target.files[0] : null)}
                  className="w-full text-xs text-slate-500 file:mr-2 file:py-1 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-bold file:bg-primary file:text-white"
                />
              </div>

              {csvStatus && (
                <p className="text-xs font-medium text-primary text-center">
                  {csvStatus}
                </p>
              )}

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCSVModalOpen(false)}
                  className="px-3.5 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl"
                >
                  {t.common.cancel}
                </button>
                <button
                  type="submit"
                  disabled={!csvFile}
                  className="bg-primary hover:bg-primary-dark text-white font-bold text-xs px-4 py-2 rounded-xl transition-colors disabled:opacity-50"
                >
                  Upload & Commit
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* API Ingest Key Modal */}
      {isTokenModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-md w-full p-5 shadow-2xl border border-slate-200">
            <h3 className="font-bold text-lg text-slate-900 mb-1 flex items-center gap-2">
              <Key className="w-5 h-5 text-primary" />
              <span>HTTP Ingest API Token</span>
            </h3>
            <p className="text-xs text-slate-500 mb-3">
              Use this secret token to push readings from automated scripts, IoT devices, or microcontrollers:
            </p>

            <div className="bg-slate-900 p-3 rounded-xl font-mono text-xs text-emerald-400 break-all select-all border border-slate-700">
              {generatedToken || 'Generating token...'}
            </div>

            <div className="mt-3 text-[11px] text-slate-500 space-y-1 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
              <p className="font-bold text-slate-700">Endpoint: POST /api/v1/ingest/readings</p>
              <p>Header: <code className="bg-slate-200 px-1 py-0.5 rounded">X-Source-Token: {generatedToken || 'token'}</code></p>
              <p>Payload: <code className="bg-slate-200 px-1 py-0.5 rounded">[&#123;"ts":"...", "temp_c": 4.2, "rh": 88&#125;]</code></p>
            </div>

            <div className="flex justify-end pt-4">
              <button
                type="button"
                onClick={() => setIsTokenModalOpen(false)}
                className="bg-primary text-white font-bold text-xs px-4 py-2 rounded-xl hover:bg-primary-dark transition-colors"
              >
                {t.common.close}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
