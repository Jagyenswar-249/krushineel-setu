import React, { useEffect, useState } from 'react';
import { Language, NotificationItem } from '../types';
import { translations } from '../i18n/translations';
import { X, Bell, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import { api } from '../services/api';

interface NotificationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  language: Language;
}

export const NotificationDrawer: React.FC<NotificationDrawerProps> = ({
  isOpen,
  onClose,
  language
}) => {
  if (!isOpen) return null;

  const t = translations[language];
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchNotifs = async () => {
      setLoading(true);
      try {
        const data = await api.getNotifications();
        setNotifications(data || []);
      } catch (e) {
        console.error("Failed to load notifications:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchNotifs();
  }, [isOpen]);

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-xs">
      <div className="bg-white w-full max-w-sm h-full shadow-2xl flex flex-col border-l border-slate-200">
        {/* Header */}
        <div className="bg-primary text-white p-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bell className="w-5 h-5 text-teal-200" />
            <h3 className="font-bold text-base">Alerts & Notifications</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-white/10 text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content list */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
          {loading && (
            <p className="text-center text-xs text-slate-400 py-6">{t.common.loading}</p>
          )}
          {!loading && notifications.length === 0 && (
            <div className="text-center py-10 px-4 text-slate-400">
              <CheckCircle className="w-10 h-10 mx-auto text-emerald-400 mb-2" />
              <p className="text-xs font-medium">No alerts at this moment. All cold rooms and sea trips safe.</p>
            </div>
          )}
          {notifications.map((n) => (
            <div
              key={n.id}
              className="p-3 rounded-xl border border-slate-200 bg-slate-50 hover:bg-white transition-colors shadow-xs"
            >
              <div className="flex items-start justify-between gap-1.5 mb-1">
                <span className="font-semibold text-xs text-slate-900">
                  {language === 'or' ? n.title_or : n.title_en}
                </span>
                <span className="text-[10px] text-slate-400 whitespace-nowrap">
                  {new Date(n.sent_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                {language === 'or' ? n.body_or : n.body_en}
              </p>
              <div className="mt-2 flex items-center gap-2">
                <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-teal-100 text-teal-800">
                  {n.channel}
                </span>
                <span className="text-[10px] text-slate-400">
                  {new Date(n.sent_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
