import React from 'react';
import { UserRole, Language } from '../types';
import { translations } from '../i18n/translations';
import { Thermometer, Camera, Shield, TrendingUp, Fish, User as UserIcon, LayoutDashboard } from 'lucide-react';

export type TabType = 'coldwatch' | 'gradelens' | 'sagar' | 'mandi' | 'matsya' | 'profile';

interface BottomNavProps {
  currentTab: TabType;
  onTabChange: (tab: TabType) => void;
  role: UserRole;
  language: Language;
}

export const BottomNav: React.FC<BottomNavProps> = ({
  currentTab,
  onTabChange,
  role,
  language
}) => {
  const t = translations[language];

  // Define tab items tailored by role
  const getTabsForRole = (): { id: TabType; label: string; icon: React.ReactNode }[] => {
    switch (role) {
      case 'farmer':
        return [
          { id: 'mandi', label: t.modules.mandi, icon: <TrendingUp className="w-5 h-5" /> },
          { id: 'gradelens', label: t.modules.gradelens, icon: <Camera className="w-5 h-5" /> },
          { id: 'coldwatch', label: t.modules.coldwatch, icon: <Thermometer className="w-5 h-5" /> },
          { id: 'profile', label: t.modules.profile, icon: <UserIcon className="w-5 h-5" /> },
        ];
      case 'fisher':
        return [
          { id: 'sagar', label: t.modules.sagar, icon: <Shield className="w-5 h-5" /> },
          { id: 'matsya', label: t.modules.matsya, icon: <Fish className="w-5 h-5" /> },
          { id: 'mandi', label: t.modules.mandi, icon: <TrendingUp className="w-5 h-5" /> },
          { id: 'profile', label: t.modules.profile, icon: <UserIcon className="w-5 h-5" /> },
        ];
      case 'fpo_admin':
        return [
          { id: 'coldwatch', label: t.modules.coldwatch, icon: <Thermometer className="w-5 h-5" /> },
          { id: 'gradelens', label: t.modules.gradelens, icon: <Camera className="w-5 h-5" /> },
          { id: 'mandi', label: t.modules.mandi, icon: <TrendingUp className="w-5 h-5" /> },
          { id: 'profile', label: t.modules.profile, icon: <UserIcon className="w-5 h-5" /> },
        ];
      case 'buyer':
        return [
          { id: 'matsya', label: t.modules.matsya, icon: <Fish className="w-5 h-5" /> },
          { id: 'mandi', label: t.modules.mandi, icon: <TrendingUp className="w-5 h-5" /> },
          { id: 'profile', label: t.modules.profile, icon: <UserIcon className="w-5 h-5" /> },
        ];
      case 'admin':
      default:
        return [
          { id: 'coldwatch', label: t.modules.coldwatch, icon: <Thermometer className="w-5 h-5" /> },
          { id: 'gradelens', label: t.modules.gradelens, icon: <Camera className="w-5 h-5" /> },
          { id: 'sagar', label: t.modules.sagar, icon: <Shield className="w-5 h-5" /> },
          { id: 'mandi', label: t.modules.mandi, icon: <TrendingUp className="w-5 h-5" /> },
          { id: 'matsya', label: t.modules.matsya, icon: <Fish className="w-5 h-5" /> },
          { id: 'profile', label: t.modules.profile, icon: <UserIcon className="w-5 h-5" /> },
        ];
    }
  };

  const tabs = getTabsForRole();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-30 bg-white border-t border-slate-200 shadow-lg safe-area-bottom">
      <div className="max-w-md md:max-w-2xl mx-auto flex justify-around items-center">
        {tabs.map((tab) => {
          const isActive = currentTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`flex flex-col items-center justify-center flex-1 py-2 min-h-[56px] transition-colors ${
                isActive
                  ? 'text-primary font-bold border-t-2 border-primary bg-teal-50/50'
                  : 'text-slate-500 hover:text-slate-800 font-medium'
              }`}
            >
              <div className={isActive ? 'text-primary scale-110 transition-transform' : 'text-slate-400'}>
                {tab.icon}
              </div>
              <span className="text-[11px] sm:text-xs tracking-tight mt-1 truncate max-w-[80px]">
                {tab.label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};
