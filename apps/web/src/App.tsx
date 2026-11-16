import React, { useState, useEffect } from 'react';
import { UserRole, Language } from './types';
import { Header } from './components/Header';
import { BottomNav, TabType } from './components/BottomNav';
import { SMSConsoleModal } from './components/SMSConsoleModal';
import { NotificationDrawer } from './components/NotificationDrawer';
import { ColdWatchScreen } from './screens/ColdWatchScreen';
import { GradeLensScreen } from './screens/GradeLensScreen';
import { SagarSurakshaScreen } from './screens/SagarSurakshaScreen';
import { MandiMitraScreen } from './screens/MandiMitraScreen';
import { MatsyaConnectScreen } from './screens/MatsyaConnectScreen';
import { ProfileScreen } from './screens/ProfileScreen';
import { flushOutbox } from './services/offlineSync';

export const App: React.FC = () => {
  const [language, setLanguage] = useState<Language>('or');
  const [role, setRole] = useState<UserRole>('farmer');
  const [currentTab, setCurrentTab] = useState<TabType>('mandi');
  const [isOnline, setIsOnline] = useState<boolean>(navigator.onLine);
  const [isSMSModalOpen, setIsSMSModalOpen] = useState<boolean>(false);
  const [isNotifDrawerOpen, setIsNotifDrawerOpen] = useState<boolean>(false);

  // Monitor network status
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      // Auto-flush outbox upon signal recovery
      flushOutbox(async (endpoint, method, body) => {
        return fetch(`/api/v1${endpoint}`, {
          method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        });
      });
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Update default tab when role changes
  useEffect(() => {
    switch (role) {
      case 'farmer':
        setCurrentTab('mandi');
        break;
      case 'fisher':
        setCurrentTab('sagar');
        break;
      case 'fpo_admin':
        setCurrentTab('coldwatch');
        break;
      case 'buyer':
        setCurrentTab('matsya');
        break;
      case 'admin':
        setCurrentTab('coldwatch');
        break;
    }
  }, [role]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans selection:bg-teal-100 selection:text-teal-900">
      {/* Top Navigation & App Bar */}
      <Header
        language={language}
        onLanguageChange={setLanguage}
        role={role}
        onRoleChange={setRole}
        isOnline={isOnline}
        onOpenSMS={() => setIsSMSModalOpen(true)}
        onOpenNotifications={() => setIsNotifDrawerOpen(true)}
        unreadCount={1}
      />

      {/* Main View Area */}
      <main className="flex-1 w-full">
        {currentTab === 'coldwatch' && <ColdWatchScreen language={language} />}
        {currentTab === 'gradelens' && <GradeLensScreen language={language} />}
        {currentTab === 'sagar' && <SagarSurakshaScreen language={language} />}
        {currentTab === 'mandi' && <MandiMitraScreen language={language} />}
        {currentTab === 'matsya' && <MatsyaConnectScreen language={language} />}
        {currentTab === 'profile' && (
          <ProfileScreen
            language={language}
            onLanguageChange={setLanguage}
            role={role}
            onRoleChange={setRole}
            isOnline={isOnline}
            onOpenSMS={() => setIsSMSModalOpen(true)}
          />
        )}
      </main>

      {/* Role-tailored Bottom Tab Navigation */}
      <BottomNav
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        role={role}
        language={language}
      />

      {/* Virtual SMS Feature Phone Simulator Modal */}
      <SMSConsoleModal
        isOpen={isSMSModalOpen}
        onClose={() => setIsSMSModalOpen(false)}
        language={language}
      />

      {/* Notifications Drawer */}
      <NotificationDrawer
        isOpen={isNotifDrawerOpen}
        onClose={() => setIsNotifDrawerOpen(false)}
        language={language}
      />
    </div>
  );
};

export default App;
