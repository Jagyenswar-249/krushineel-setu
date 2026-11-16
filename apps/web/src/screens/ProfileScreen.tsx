import React, { useState } from 'react';
import { UserRole, Language } from '../types';
import { translations } from '../i18n/translations';
import { getOutbox, flushOutbox } from '../services/offlineSync';
import {
  User, Shield, Globe, MapPin, Database, RefreshCw, CheckCircle,
  FileText, Award, Smartphone, Info
} from 'lucide-react';

interface ProfileScreenProps {
  language: Language;
  onLanguageChange: (lang: Language) => void;
  role: UserRole;
  onRoleChange: (role: UserRole) => void;
  isOnline: boolean;
  onOpenSMS: () => void;
}

export const ProfileScreen: React.FC<ProfileScreenProps> = ({
  language,
  onLanguageChange,
  role,
  onRoleChange,
  isOnline,
  onOpenSMS
}) => {
  const t = translations[language];
  const outboxItems = getOutbox();
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<string | null>(null);

  const demoUsers: { role: UserRole; name: string; phone: string; district: string }[] = [
    { role: 'farmer', name: 'Ramesh Sahoo', phone: '9876543210', district: 'Puri' },
    { role: 'fisher', name: 'Sanatan Behera', phone: '9876543211', district: 'Puri Coast' },
    { role: 'buyer', name: 'Rajesh Mohanty', phone: '9876543212', district: 'Bhubaneswar' },
    { role: 'fpo_admin', name: 'Priya Pattnaik', phone: '9876543213', district: 'Puri' },
    { role: 'admin', name: 'KrushiNeel Admin', phone: '9999999999', district: 'Odisha State' },
  ];

  const currentUser = demoUsers.find((u) => u.role === role) || demoUsers[0];

  const handleSyncOutbox = async () => {
    setSyncing(true);
    try {
      const count = await flushOutbox(async (endpoint, method, body) => {
        return fetch(`/api/v1${endpoint}`, {
          method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        });
      });
      setSyncResult(`Successfully flushed ${count} queued items to server.`);
      setTimeout(() => setSyncResult(null), 3000);
    } catch (e) {
      setSyncResult("Failed to flush some outbox items.");
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="pb-24 pt-3 max-w-4xl mx-auto px-3 sm:px-6 space-y-5">
      {/* User Card */}
      <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-primary to-teal-500 text-white font-black text-2xl flex items-center justify-center shadow-md">
            {currentUser.name.charAt(0)}
          </div>
          <div>
            <h2 className="text-xl font-black text-slate-900 tracking-tight">{currentUser.name}</h2>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-xs font-bold text-teal-800 bg-teal-100 px-2.5 py-0.5 rounded-full capitalize">
                {role.replace('_', ' ')}
              </span>
              <span className="text-xs font-semibold text-slate-500 flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5" />
                {currentUser.district}
              </span>
            </div>
            <p className="text-xs font-mono text-slate-400 mt-1">Phone: +91 {currentUser.phone}</p>
          </div>
        </div>

        <button
          onClick={onOpenSMS}
          className="bg-primary hover:bg-primary-dark text-white font-bold text-xs px-4 py-2.5 rounded-xl shadow-xs flex items-center gap-2 transition-colors self-stretch sm:self-auto justify-center"
        >
          <Smartphone className="w-4 h-4 text-teal-200" />
          <span>Launch SMS Console</span>
        </button>
      </div>

      {/* Switch Demo Persona */}
      <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-xs space-y-3">
        <h3 className="font-bold text-sm text-slate-900 flex items-center gap-2">
          <User className="w-4 h-4 text-primary" />
          <span>Quick Switch Demo Persona</span>
        </h3>
        <p className="text-xs text-slate-500">
          Switch roles instantly to evaluate different user experiences tailored for farmers, fishers, buyers, and FPOs:
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 pt-1">
          {demoUsers.map((u) => (
            <button
              key={u.role}
              onClick={() => onRoleChange(u.role)}
              className={`p-3 rounded-2xl border text-left transition-all ${
                role === u.role
                  ? 'bg-teal-50 border-primary shadow-xs ring-1 ring-primary'
                  : 'bg-slate-50 border-slate-200 hover:bg-slate-100'
              }`}
            >
              <span className="font-black text-xs text-slate-900 block">{u.name}</span>
              <span className="text-[11px] font-semibold text-primary capitalize block">{u.role.replace('_', ' ')}</span>
              <span className="text-[10px] text-slate-400">{u.district}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Offline Outbox Status */}
      <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-sm text-slate-900 flex items-center gap-2">
            <Database className="w-4 h-4 text-agri" />
            <span>Offline Sync & Outbox Queue</span>
          </h3>
          <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
            isOnline ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
          }`}>
            {isOnline ? 'Online Sync Active' : 'Offline Mode (Local Storage)'}
          </span>
        </div>

        <p className="text-xs text-slate-500">
          All actions made while at sea or in low-connectivity mandis (check-ins, produce listings, temperature logs) are stored in your device outbox and automatically synced upon signal restoration.
        </p>

        <div className="flex items-center justify-between bg-slate-50 p-3 rounded-2xl border border-slate-200">
          <span className="text-xs font-bold text-slate-700">
            {outboxItems.length} queued action(s) waiting for background upload
          </span>
          <button
            onClick={handleSyncOutbox}
            disabled={syncing || outboxItems.length === 0}
            className="bg-agri hover:bg-agri-dark text-white font-bold text-xs px-3.5 py-2 rounded-xl flex items-center gap-1.5 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
            <span>Sync Outbox Now</span>
          </button>
        </div>

        {syncResult && (
          <p className="text-xs font-bold text-emerald-700 bg-emerald-50 p-2 rounded-xl">
            {syncResult}
          </p>
        )}
      </div>

      {/* Honest Limitations & Pitch Evidence Notes */}
      <div className="bg-slate-900 text-slate-200 p-5 rounded-3xl shadow-md space-y-3 text-xs leading-relaxed">
        <div className="flex items-center gap-2 text-teal-300 font-bold text-sm">
          <Shield className="w-4 h-4" />
          <span>Honest Architecture & Pitch Notes</span>
        </div>
        <ul className="list-disc list-inside space-y-1.5 text-slate-300">
          <li><b>No Special Hardware Required:</b> ColdWatch runs web-only via quick manual logs, digital thermometer CSV import, HTTP Ingest API, and demo simulator.</li>
          <li><b>Supplement, Not Replace:</b> Fisherfolk safety alerts supplement official IMD and INCOIS warnings; emergency hotlines are displayed on all red alerts.</li>
          <li><b>Decision Support Grading:</b> GradeLens optical certificates provide verifiable decision-support grades for mandi price settlement, not statutory certification.</li>
          <li><b>Bilingual UCS-2 SMS:</b> Inbound SMS parser supports standard keywords (SAFE, TRIP, HELP, PRICE, SELL, WEATHER) in English and transliterated Odia.</li>
        </ul>
      </div>
    </div>
  );
};
