import React from 'react';
import { UserRole, Language } from '../types';
import { translations } from '../i18n/translations';
import { Globe, Wifi, WifiOff, MessageSquare, Bell, ShieldAlert } from 'lucide-react';

interface HeaderProps {
  language: Language;
  onLanguageChange: (lang: Language) => void;
  role: UserRole;
  onRoleChange: (role: UserRole) => void;
  isOnline: boolean;
  onOpenSMS: () => void;
  onOpenNotifications: () => void;
  unreadCount?: number;
}

export const Header: React.FC<HeaderProps> = ({
  language,
  onLanguageChange,
  role,
  onRoleChange,
  isOnline,
  onOpenSMS,
  onOpenNotifications,
  unreadCount = 0
}) => {
  const t = translations[language];

  return (
    <header className="sticky top-0 z-30 bg-primary text-white shadow-md border-b border-teal-800">
      <div className="max-w-7xl mx-auto px-3 sm:px-6 py-2.5 flex items-center justify-between flex-wrap gap-2">
        {/* Brand */}
        <div className="flex items-center space-x-2.5">
          <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center font-bold text-xl tracking-wider text-teal-200 border border-white/20">
            KS
          </div>
          <div>
            <h1 className="text-lg sm:text-xl font-bold tracking-tight leading-tight flex items-center gap-1.5">
              <span>{t.appTitle}</span>
              <span className="text-xs bg-emerald-500/30 text-emerald-300 font-semibold px-1.5 py-0.5 rounded border border-emerald-400/30">
                v1.0
              </span>
            </h1>
            <p className="text-xs text-teal-100 hidden sm:block">
              {t.tagline}
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-2">
          {/* Online/Offline status pill */}
          <div
            className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${
              isOnline ? 'bg-emerald-500/20 text-emerald-200 border border-emerald-400/30' : 'bg-amber-500/20 text-amber-200 border border-amber-400/40 animate-pulse'
            }`}
            title={isOnline ? t.common.online : t.common.offline}
          >
            {isOnline ? <Wifi className="w-3.5 h-3.5" /> : <WifiOff className="w-3.5 h-3.5" />}
            <span className="hidden md:inline">{isOnline ? t.common.online : t.common.offline}</span>
          </div>

          {/* SMS Simulator Button */}
          <button
            onClick={onOpenSMS}
            className="flex items-center gap-1.5 bg-white/15 hover:bg-white/25 text-white px-2.5 py-1.5 rounded-lg text-xs font-medium border border-white/20 transition-colors shadow-sm"
            title="Open Interactive SMS Simulator"
          >
            <MessageSquare className="w-3.5 h-3.5 text-teal-200" />
            <span className="hidden sm:inline">SMS Console</span>
          </button>

          {/* Role Switcher */}
          <select
            value={role}
            onChange={(e) => onRoleChange(e.target.value as UserRole)}
            className="bg-primary-dark text-teal-50 text-xs rounded-lg px-2 py-1.5 border border-teal-700 focus:outline-none focus:ring-1 focus:ring-teal-400 font-medium"
          >
            <option value="farmer">{t.roles.farmer}</option>
            <option value="fisher">{t.roles.fisher}</option>
            <option value="fpo_admin">{t.roles.fpo_admin}</option>
            <option value="buyer">{t.roles.buyer}</option>
            <option value="admin">{t.roles.admin}</option>
          </select>

          {/* Language Switcher */}
          <button
            onClick={() => onLanguageChange(language === 'or' ? 'en' : 'or')}
            className="flex items-center gap-1 bg-white text-primary font-bold px-2.5 py-1 rounded-lg text-xs shadow-sm hover:bg-teal-50 transition-colors"
          >
            <Globe className="w-3.5 h-3.5" />
            <span>{language === 'or' ? 'English' : 'ଓଡ଼ିଆ'}</span>
          </button>

          {/* Notifications Trigger */}
          <button
            onClick={onOpenNotifications}
            className="relative p-1.5 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
            title="Alerts & Notifications"
          >
            <Bell className="w-4 h-4 text-teal-100" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 bg-danger text-white text-[10px] w-4 h-4 rounded-full flex items-center justify-center font-bold">
                {unreadCount}
              </span>
            )}
          </button>
        </div>
      </div>
    </header>
  );
};
