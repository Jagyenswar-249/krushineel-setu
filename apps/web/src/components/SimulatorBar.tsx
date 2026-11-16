import React, { useState } from 'react';
import { Language } from '../types';
import { translations } from '../i18n/translations';
import { Play, AlertTriangle, Sun, RefreshCw, ZapOff, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';

interface SimulatorBarProps {
  language: Language;
  coldRoomId: number;
  onScenarioTriggered: () => void;
}

export const SimulatorBar: React.FC<SimulatorBarProps> = ({
  language,
  coldRoomId,
  onScenarioTriggered
}) => {
  const t = translations[language];
  const [loading, setLoading] = useState(false);
  const [activeScenario, setActiveScenario] = useState<string>('normal');

  const runScenario = async (scenario: string) => {
    setLoading(true);
    try {
      await api.triggerScenario(coldRoomId, scenario);
      setActiveScenario(scenario);
      onScenarioTriggered();
    } catch (e) {
      console.error("Scenario trigger failed:", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gradient-to-r from-amber-500/10 via-amber-500/15 to-amber-500/10 border-b border-amber-300/60 px-3 py-2 text-xs">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2">
        {/* Label & Badge */}
        <div className="flex items-center gap-2">
          <span className="bg-amber-500 text-white font-extrabold px-2 py-0.5 rounded text-[10px] tracking-wider uppercase shadow-sm flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" />
            {t.common.simulated}
          </span>
          <span className="font-semibold text-amber-900 hidden sm:inline">
            {t.coldwatch.simulatorTitle}:
          </span>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            onClick={() => runScenario('normal')}
            disabled={loading}
            className={`px-2.5 py-1 rounded-md font-medium border flex items-center gap-1 transition-all ${
              activeScenario === 'normal'
                ? 'bg-emerald-600 text-white border-emerald-700 shadow-sm'
                : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-100'
            }`}
          >
            <CheckCircle2 className="w-3 h-3" />
            <span>{t.coldwatch.scenarioNormal}</span>
          </button>

          <button
            onClick={() => runScenario('door_open')}
            disabled={loading}
            className={`px-2.5 py-1 rounded-md font-medium border flex items-center gap-1 transition-all ${
              activeScenario === 'door_open'
                ? 'bg-amber-600 text-white border-amber-700 shadow-sm'
                : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-100'
            }`}
          >
            <AlertTriangle className="w-3 h-3 text-amber-500" />
            <span>{t.coldwatch.scenarioDoorOpen}</span>
          </button>

          <button
            onClick={() => runScenario('power_cut')}
            disabled={loading}
            className={`px-2.5 py-1 rounded-md font-medium border flex items-center gap-1 transition-all ${
              activeScenario === 'power_cut'
                ? 'bg-rose-600 text-white border-rose-700 shadow-sm'
                : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-100'
            }`}
          >
            <ZapOff className="w-3 h-3 text-rose-500" />
            <span>{t.coldwatch.scenarioPowerCut}</span>
          </button>

          <button
            onClick={() => runScenario('recovery')}
            disabled={loading}
            className={`px-2.5 py-1 rounded-md font-medium border flex items-center gap-1 transition-all ${
              activeScenario === 'recovery'
                ? 'bg-teal-600 text-white border-teal-700 shadow-sm'
                : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-100'
            }`}
          >
            <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
            <span>{t.coldwatch.scenarioRecovery}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
