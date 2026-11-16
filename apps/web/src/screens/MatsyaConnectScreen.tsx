import React, { useState, useEffect } from 'react';
import { Language, CatchListing, BuyerRequest, Match, LandingSite } from '../types';
import { translations } from '../i18n/translations';
import { api } from '../services/api';
import {
  Fish, Plus, MapPin, Tag, Phone, ShieldCheck, CheckCircle2,
  Clock, ArrowRight, UserCheck, AlertCircle
} from 'lucide-react';

interface MatsyaConnectScreenProps {
  language: Language;
}

export const MatsyaConnectScreen: React.FC<MatsyaConnectScreenProps> = ({ language }) => {
  const t = translations[language];

  const [listings, setListings] = useState<CatchListing[]>([]);
  const [buyerRequests, setBuyerRequests] = useState<BuyerRequest[]>([]);
  const [matches, setMatches] = useState<Match[]>([]);
  const [landingSites, setLandingSites] = useState<LandingSite[]>([]);
  const [selectedSpecies, setSelectedSpecies] = useState<string>('all');
  const [loading, setLoading] = useState(true);

  // New listing modal
  const [isListingModalOpen, setIsListingModalOpen] = useState(false);
  const [newSiteId, setNewSiteId] = useState<number>(1);
  const [newSpecies, setNewSpecies] = useState('Hilsa (Ilish)');
  const [newQty, setNewQty] = useState('40');
  const [newPrice, setNewPrice] = useState('550');
  const [listingSuccess, setListingSuccess] = useState(false);

  const fetchData = async () => {
    try {
      const [lList, rList, mList, sList] = await Promise.all([
        api.getListings(),
        api.getBuyerRequests(),
        api.getMatches(),
        api.getLandingSites()
      ]);
      setListings(lList || []);
      setBuyerRequests(rList || []);
      setMatches(mList || []);
      setLandingSites(sList || []);
      if (sList && sList.length > 0) setNewSiteId(sList[0].id);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateListing = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createListing(newSiteId, newSpecies, parseFloat(newQty), parseFloat(newPrice));
      setListingSuccess(true);
      setTimeout(() => {
        setListingSuccess(false);
        setIsListingModalOpen(false);
      }, 1200);
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleAcceptMatch = async (matchId: number) => {
    try {
      await api.acceptMatch(matchId);
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const filteredListings = selectedSpecies === 'all'
    ? listings
    : listings.filter((l) => l.species.toLowerCase().includes(selectedSpecies.toLowerCase()));

  return (
    <div className="pb-24 pt-3 max-w-7xl mx-auto px-3 sm:px-6 space-y-5">
      {/* Header Bar */}
      <div className="bg-white p-4 rounded-2xl shadow-xs border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <Fish className="w-6 h-6 text-primary" />
            <span>{t.matsya.title}</span>
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            {t.matsya.subtitle}
          </p>
        </div>

        <button
          onClick={() => setIsListingModalOpen(true)}
          className="bg-primary hover:bg-primary-dark text-white font-extrabold text-xs sm:text-sm px-4 py-2.5 rounded-xl flex items-center gap-2 shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>{t.matsya.postCatchBtn}</span>
        </button>
      </div>

      {/* AI Matches Banner (If matches exist) */}
      {matches.length > 0 && (
        <div className="bg-gradient-to-r from-teal-50 via-emerald-50 to-teal-50 p-4 sm:p-5 rounded-3xl border border-teal-200 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-extrabold text-sm sm:text-base text-slate-900 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-600" />
              <span>{t.matsya.smartMatches} ({matches.length})</span>
            </h3>
            <span className="text-[11px] font-bold text-teal-800 bg-teal-100 px-2 py-0.5 rounded-full">
              Automated Fair Matching
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {matches.map((m) => (
              <div key={m.id} className="bg-white p-4 rounded-2xl border border-teal-200 shadow-xs flex flex-col justify-between space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-xs font-bold text-slate-400 block uppercase">
                      Landing Site: {m.landing_site}
                    </span>
                    <h4 className="font-black text-base text-slate-900">
                      {m.qty_kg} kg {m.species}
                    </h4>
                    <p className="text-xs font-bold text-primary">₹{m.price} / kg</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-black text-emerald-700 bg-emerald-100 px-2.5 py-1 rounded-xl">
                      {m.score}% Match
                    </span>
                  </div>
                </div>

                {/* Contact reveal status */}
                <div className="border-t border-slate-100 pt-2 flex items-center justify-between text-xs">
                  {m.status === 'accepted' ? (
                    <div className="flex items-center gap-2 text-emerald-700 font-bold">
                      <Phone className="w-4 h-4" />
                      <span>Buyer: {m.buyer_name} ({m.buyer_phone})</span>
                    </div>
                  ) : (
                    <span className="text-slate-400 italic text-[11px]">
                      Contact hidden until accepted
                    </span>
                  )}

                  {m.status !== 'accepted' && (
                    <button
                      onClick={() => handleAcceptMatch(m.id)}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs px-3.5 py-1.5 rounded-xl transition-colors shadow-xs"
                    >
                      {t.matsya.acceptMatchBtn}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        {['all', 'Hilsa', 'Tiger Prawn', 'Pomfret', 'Rohu', 'Crab'].map((sp) => (
          <button
            key={sp}
            onClick={() => setSelectedSpecies(sp)}
            className={`px-3.5 py-1.5 rounded-xl font-bold whitespace-nowrap transition-colors ${
              selectedSpecies === sp
                ? 'bg-primary text-white shadow-xs'
                : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            {sp === 'all' ? 'All Species (ସମସ୍ତ ପ୍ରଜାତି)' : sp}
          </button>
        ))}
      </div>

      {/* Listings & Demand Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Active Catch Listings (Left) */}
        <div className="lg:col-span-8 space-y-3">
          <h3 className="font-bold text-base text-slate-900 flex items-center gap-2">
            <Fish className="w-5 h-5 text-primary" />
            <span>{t.matsya.activeListings}</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {filteredListings.map((l) => (
              <div key={l.id} className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs hover:border-primary/40 transition-all flex flex-col justify-between">
                <div>
                  <div className="flex items-start justify-between mb-1.5">
                    <span className="text-xs font-bold text-slate-400 flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-primary" />
                      <span>{l.site_name || 'Coast'} ({l.district || 'Puri'})</span>
                    </span>
                    <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                      Active
                    </span>
                  </div>

                  <h4 className="font-black text-lg text-slate-900 mb-1">
                    {l.species}
                  </h4>

                  <div className="flex items-baseline gap-2 mb-2">
                    <span className="text-2xl font-black text-primary">₹{l.ask_price}</span>
                    <span className="text-xs font-semibold text-slate-500">/ kg</span>
                    <span className="text-xs font-bold text-slate-400">({l.qty_kg} kg available)</span>
                  </div>

                  {/* Benchmark Price Band */}
                  {l.reference_price_min && l.reference_price_max && (
                    <div className="bg-slate-50 p-2 rounded-xl text-[11px] text-slate-600 border border-slate-200 mb-3">
                      <span className="font-semibold block text-slate-400 text-[10px] uppercase">
                        {t.matsya.refPriceBand}
                      </span>
                      <span className="font-bold text-slate-800">
                        ₹{l.reference_price_min} - ₹{l.reference_price_max} / kg
                      </span>
                    </div>
                  )}
                </div>

                <div className="border-t border-slate-100 pt-2 flex items-center justify-between text-xs text-slate-500">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    <span>Listed {new Date(l.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </span>
                  <span className="font-bold text-slate-700">{l.fisher_name}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Buyer Demand Board (Right) */}
        <div className="lg:col-span-4 bg-white p-4 sm:p-5 rounded-2xl border border-slate-200 shadow-xs space-y-4">
          <h3 className="font-bold text-base text-slate-900 flex items-center gap-2">
            <UserCheck className="w-5 h-5 text-agri" />
            <span>{t.matsya.buyerRequests}</span>
          </h3>

          <p className="text-xs text-slate-500">
            Registered wholesale buyers, restaurants, and cold chains with active purchase orders:
          </p>

          <div className="space-y-2.5">
            {buyerRequests.map((b) => (
              <div key={b.id} className="p-3 rounded-xl border border-slate-200 bg-slate-50 shadow-xs">
                <div className="flex items-start justify-between">
                  <span className="font-bold text-sm text-slate-900">{b.species}</span>
                  <span className="font-black text-xs text-primary">Up to ₹{b.max_price}/kg</span>
                </div>
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                  <span>Demand: {b.qty_kg} kg</span>
                  <span>Radius: {b.radius_km} km</span>
                </div>
                <div className="mt-2 text-[11px] font-semibold text-slate-400">
                  Buyer: {b.buyer_name || 'Verified Trader'}
                </div>
              </div>
            ))}
          </div>

          {/* SMS Trade Hint */}
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl text-blue-950 text-xs">
            <p className="font-bold mb-0.5">SMS Listing Keyword:</p>
            <p className="font-mono text-[11px] text-blue-800">SELL HILSA 40 500 PURI</p>
          </div>
        </div>
      </div>

      {/* Post Catch Modal */}
      {isListingModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-sm w-full p-5 shadow-2xl border border-slate-200">
            <h3 className="font-bold text-lg text-slate-900 mb-1">{t.matsya.postCatchBtn}</h3>
            <p className="text-xs text-slate-500 mb-4">Post catch landed at coastal port to broadcast to buyers:</p>

            <form onSubmit={handleCreateListing} className="space-y-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Fish / Shellfish Species
                </label>
                <select
                  value={newSpecies}
                  onChange={(e) => setNewSpecies(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 font-bold text-xs sm:text-sm rounded-xl px-3 py-2 text-slate-800"
                >
                  <option value="Hilsa (Ilish)">Hilsa (ଇଲିସି)</option>
                  <option value="Tiger Prawn">Tiger Prawn (ବାଘ ଚିଙ୍ଗୁଡ଼ି)</option>
                  <option value="Pomfret">Pomfret / Chandee (ଚାନ୍ଦି)</option>
                  <option value="Rohu">Rohu / Freshwater (ରୋହି)</option>
                  <option value="Mud Crab">Mud Crab (କଙ୍କଡ଼ା)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Landing Site
                </label>
                <select
                  value={newSiteId}
                  onChange={(e) => setNewSiteId(Number(e.target.value))}
                  className="w-full bg-slate-50 border border-slate-300 font-bold text-xs sm:text-sm rounded-xl px-3 py-2 text-slate-800"
                >
                  {landingSites.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.district})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Quantity (Kg)
                </label>
                <input
                  type="number"
                  step="1"
                  required
                  value={newQty}
                  onChange={(e) => setNewQty(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 font-bold text-sm rounded-xl px-3 py-2 text-slate-800"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Asking Price (₹ / Kg)
                </label>
                <input
                  type="number"
                  step="10"
                  required
                  value={newPrice}
                  onChange={(e) => setNewPrice(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 font-bold text-sm rounded-xl px-3 py-2 text-slate-800"
                />
              </div>

              {listingSuccess && (
                <div className="p-2 rounded-lg bg-emerald-50 text-emerald-800 text-xs font-bold flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Listing posted! Matching buyers notified.</span>
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsListingModalOpen(false)}
                  className="px-3.5 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl"
                >
                  {t.common.cancel}
                </button>
                <button
                  type="submit"
                  className="bg-primary hover:bg-primary-dark text-white font-bold text-xs px-4 py-2 rounded-xl transition-colors shadow-xs"
                >
                  Publish Listing
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
