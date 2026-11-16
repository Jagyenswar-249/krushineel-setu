import React, { useState, useEffect } from 'react';
import { Language, GradingResult } from '../types';
import { translations } from '../i18n/translations';
import { api } from '../services/api';
import {
  Camera, Upload, Award, CheckCircle, AlertTriangle, QrCode, Share2,
  FileText, ShieldCheck, ChevronRight, Eye
} from 'lucide-react';

interface GradeLensScreenProps {
  language: Language;
}

export const GradeLensScreen: React.FC<GradeLensScreenProps> = ({ language }) => {
  const t = translations[language];

  const [selectedCommodity, setSelectedCommodity] = useState('Tomato');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GradingResult | null>(null);
  const [recentGradings, setRecentGradings] = useState<GradingResult[]>([]);
  const [showCertificate, setShowCertificate] = useState(false);
  const [certData, setCertData] = useState<any>(null);

  const fetchHistory = async () => {
    try {
      const history = await api.getGradings();
      setRecentGradings(history || []);
      if (history && history.length > 0 && !result) {
        setResult(history[0]);
      }
    } catch (e) {
      console.error("Grading history error:", e);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  // Preset demo sample generator (creates canvas drawing of a tomato)
  const loadPresetSample = (type: 'grade_a' | 'grade_b' | 'reject') => {
    const canvas = document.createElement('canvas');
    canvas.width = 224;
    canvas.height = 224;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Draw background
    ctx.fillStyle = '#f8fafc';
    ctx.fillRect(0, 0, 224, 224);

    // Draw tomato body
    ctx.beginPath();
    ctx.arc(112, 115, 75, 0, 2 * Math.PI);
    if (type === 'grade_a') {
      ctx.fillStyle = '#dc2626'; // Deep vibrant red
    } else if (type === 'grade_b') {
      ctx.fillStyle = '#ea580c'; // Red-orange with minor imperfection
    } else {
      ctx.fillStyle = '#7f1d1d'; // Dark brown-red with mold blemishes
    }
    ctx.fill();

    // Stem
    ctx.fillStyle = '#15803d';
    ctx.beginPath();
    ctx.arc(112, 45, 12, 0, Math.PI);
    ctx.fill();

    // Blemishes for B and Reject
    if (type === 'grade_b') {
      ctx.fillStyle = '#78350f';
      ctx.beginPath();
      ctx.arc(130, 110, 6, 0, 2 * Math.PI);
      ctx.fill();
    } else if (type === 'reject') {
      ctx.fillStyle = '#292524';
      ctx.beginPath();
      ctx.arc(110, 110, 22, 0, 2 * Math.PI);
      ctx.arc(140, 140, 15, 0, 2 * Math.PI);
      ctx.fill();
    }

    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], `sample_${type}.jpg`, { type: 'image/jpeg' });
        setSelectedFile(file);
        setPreviewUrl(URL.createObjectURL(file));
      }
    }, 'image/jpeg');
  };

  const handleGrade = async () => {
    if (!selectedFile) return;
    setLoading(true);
    try {
      const res = await api.gradeProduce(selectedFile, selectedCommodity);
      setResult(res);
      fetchHistory();
    } catch (e) {
      console.error("Grading failed:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleViewCertificate = async (id: number) => {
    try {
      const data = await api.getCertificate(id);
      setCertData(data);
      setShowCertificate(true);
    } catch (e) {
      console.error(e);
    }
  };

  const getGradeBadge = (grade: string) => {
    switch (grade) {
      case 'A':
        return { label: t.gradelens.gradeA, color: 'bg-emerald-500 text-white border-emerald-600' };
      case 'B':
        return { label: t.gradelens.gradeB, color: 'bg-blue-500 text-white border-blue-600' };
      case 'C':
        return { label: t.gradelens.gradeC, color: 'bg-amber-500 text-white border-amber-600' };
      case 'Reject':
      default:
        return { label: t.gradelens.gradeReject, color: 'bg-rose-600 text-white border-rose-700' };
    }
  };

  return (
    <div className="pb-24 pt-3 max-w-7xl mx-auto px-3 sm:px-6 space-y-5">
      {/* Header Bar */}
      <div className="bg-white p-4 rounded-2xl shadow-xs border border-slate-200">
        <h2 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
          <Camera className="w-6 h-6 text-primary" />
          <span>{t.gradelens.title}</span>
        </h2>
        <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
          {t.gradelens.subtitle}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Upload & Capture Panel (Left) */}
        <div className="lg:col-span-5 bg-white p-4 sm:p-5 rounded-2xl border border-slate-200 shadow-xs space-y-4">
          <h3 className="font-bold text-base text-slate-900 flex items-center gap-2">
            <Upload className="w-5 h-5 text-primary" />
            <span>Produce Capture & Inspection</span>
          </h3>

          {/* Commodity Dropdown */}
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              {t.gradelens.commoditySelect}
            </label>
            <select
              value={selectedCommodity}
              onChange={(e) => setSelectedCommodity(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 font-semibold text-sm rounded-xl px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="Tomato">Tomato (ଟମାଟୋ)</option>
              <option value="Brinjal">Brinjal / Eggplant (ବାଇଗଣ)</option>
              <option value="Potato">Potato (ଆଳୁ)</option>
              <option value="Pointed Gourd">Pointed Gourd / Potala (ପୋଟଳ)</option>
            </select>
          </div>

          {/* File Picker or Camera */}
          <div className="border-2 border-dashed border-slate-300 rounded-2xl p-4 text-center hover:bg-slate-50 transition-colors">
            {previewUrl ? (
              <div className="relative mx-auto max-w-[200px] rounded-xl overflow-hidden shadow-md">
                <img src={previewUrl} alt="Produce" className="w-full h-44 object-cover" />
              </div>
            ) : (
              <div className="py-6 flex flex-col items-center">
                <div className="w-12 h-12 rounded-full bg-teal-50 flex items-center justify-center text-primary mb-2">
                  <Camera className="w-6 h-6" />
                </div>
                <p className="text-xs font-bold text-slate-700">Tap to photograph produce</p>
                <p className="text-[11px] text-slate-400 mt-0.5">Supports high-res mobile photos</p>
              </div>
            )}

            <input
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handleFileChange}
              className="mt-3 block w-full text-xs text-slate-500 file:mr-2 file:py-1.5 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-primary file:text-white cursor-pointer"
            />
          </div>

          {/* Sample Preset Presets */}
          <div>
            <p className="text-xs font-bold text-slate-600 mb-1.5">Or try sample test photos:</p>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => loadPresetSample('grade_a')}
                className="p-1.5 bg-emerald-50 border border-emerald-300 rounded-lg text-emerald-800 font-semibold text-xs hover:bg-emerald-100 transition-colors"
              >
                Grade A Sample
              </button>
              <button
                type="button"
                onClick={() => loadPresetSample('grade_b')}
                className="p-1.5 bg-amber-50 border border-amber-300 rounded-lg text-amber-800 font-semibold text-xs hover:bg-amber-100 transition-colors"
              >
                Grade B Sample
              </button>
              <button
                type="button"
                onClick={() => loadPresetSample('reject')}
                className="p-1.5 bg-rose-50 border border-rose-300 rounded-lg text-rose-800 font-semibold text-xs hover:bg-rose-100 transition-colors"
              >
                Cull / Reject
              </button>
            </div>
          </div>

          {/* Analyze Button */}
          <button
            onClick={handleGrade}
            disabled={!selectedFile || loading}
            className="w-full bg-primary hover:bg-primary-dark text-white font-extrabold text-sm py-3 rounded-xl shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? (
              <span>Running Optical Grading Model...</span>
            ) : (
              <>
                <Award className="w-5 h-5 text-teal-200" />
                <span>Compute Grade & Issue Certificate</span>
              </>
            )}
          </button>
        </div>

        {/* Results Panel (Right) */}
        <div className="lg:col-span-7 space-y-4">
          {result ? (
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-4">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div>
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                    {t.gradelens.gradeResult} ({result.commodity})
                  </span>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className={`text-xl sm:text-2xl font-black px-3 py-1 rounded-xl border ${getGradeBadge(result.grade).color}`}>
                      Grade {result.grade}
                    </span>
                    <span className="text-sm font-bold text-slate-700">
                      {getGradeBadge(result.grade).label}
                    </span>
                  </div>
                </div>

                <button
                  onClick={() => handleViewCertificate(result.id)}
                  className="bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs px-3.5 py-2 rounded-xl flex items-center gap-1.5 transition-colors shadow-xs"
                >
                  <FileText className="w-4 h-4 text-teal-300" />
                  <span>{t.gradelens.certBtn}</span>
                </button>
              </div>

              {/* Confidence Meter */}
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <div className="flex justify-between text-xs font-bold mb-1">
                  <span className="text-slate-600">{t.gradelens.confidence}:</span>
                  <span className="text-primary">{Math.round(result.confidence * 100)}%</span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden">
                  <div
                    className="bg-primary h-2.5 rounded-full transition-all"
                    style={{ width: `${result.confidence * 100}%` }}
                  ></div>
                </div>
              </div>

              {/* Optical Parameters Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200">
                  <span className="text-[11px] font-semibold text-slate-500 block">{t.gradelens.colorScore}</span>
                  <span className="text-lg font-black text-slate-900">{result.color_score}%</span>
                </div>
                <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200">
                  <span className="text-[11px] font-semibold text-slate-500 block">{t.gradelens.blemishPct}</span>
                  <span className={`text-lg font-black ${result.blemish_pct > 15 ? 'text-rose-600' : 'text-slate-900'}`}>
                    {result.blemish_pct}%
                  </span>
                </div>
                <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200">
                  <span className="text-[11px] font-semibold text-slate-500 block">{t.gradelens.shapeUniformity}</span>
                  <span className="text-lg font-black text-slate-900">{result.shape_uniformity}</span>
                </div>
                <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200">
                  <span className="text-[11px] font-semibold text-slate-500 block">{t.gradelens.sizeGrade}</span>
                  <span className="text-lg font-black text-slate-900">{result.size_est}</span>
                </div>
              </div>

              {/* Review Badge if confidence low */}
              {result.needs_review && (
                <div className="p-3 rounded-xl bg-amber-50 border border-amber-300 text-amber-900 text-xs font-semibold flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                  <span>{t.gradelens.reviewBadge}</span>
                </div>
              )}

              {/* Certificate Quick Preview */}
              <div className="border border-slate-200 rounded-xl p-3 bg-teal-50/40 flex items-center justify-between">
                <div>
                  <p className="text-xs font-bold text-slate-800">Certificate ID: {result.certificate_id}</p>
                  <p className="text-[11px] text-slate-500 mt-0.5">Model: {result.model_version}</p>
                </div>
                <QrCode className="w-8 h-8 text-slate-700" />
              </div>
            </div>
          ) : (
            <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-xs text-center text-slate-400">
              <Camera className="w-12 h-12 mx-auto text-slate-300 mb-2" />
              <p className="text-sm font-semibold">Photograph or select sample produce to inspect grade.</p>
            </div>
          )}

          {/* Recent Inspection Lots History */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
            <h4 className="font-bold text-sm text-slate-900 mb-2">Recent Grading History</h4>
            <div className="space-y-2">
              {recentGradings.slice(0, 4).map((g) => (
                <div
                  key={g.id}
                  onClick={() => setResult(g)}
                  className="p-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 cursor-pointer flex items-center justify-between transition-colors"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="w-8 h-8 rounded-lg bg-primary text-white font-black text-xs flex items-center justify-center">
                      {g.grade}
                    </span>
                    <div>
                      <p className="font-bold text-xs text-slate-800">{g.commodity}</p>
                      <p className="text-[10px] text-slate-400">{g.certificate_id}</p>
                    </div>
                  </div>
                  <span className="text-xs font-semibold text-slate-500">
                    {Math.round(g.confidence * 100)}% Conf
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Printable Certificate Modal */}
      {showCertificate && certData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border-4 border-primary">
            {/* Certificate Header */}
            <div className="text-center border-b border-slate-200 pb-4">
              <div className="w-12 h-12 rounded-2xl bg-primary text-white font-black text-xl flex items-center justify-center mx-auto mb-2 shadow-md">
                KS
              </div>
              <h3 className="font-black text-lg text-slate-900">{t.gradelens.certTitle}</h3>
              <p className="text-xs font-bold text-primary tracking-wide">KrushiNeel Setu Quality Assurance</p>
              <p className="text-[11px] font-mono text-slate-500 mt-1">{certData.certificate_id}</p>
            </div>

            {/* Cert Body */}
            <div className="py-4 space-y-3 text-xs">
              <div className="flex justify-between border-b border-slate-100 pb-2">
                <span className="text-slate-500">Commodity:</span>
                <span className="font-bold text-slate-900">{certData.commodity}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-2">
                <span className="text-slate-500">Certified Grade:</span>
                <span className="font-black text-emerald-700 text-sm">GRADE {certData.grade}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-2">
                <span className="text-slate-500">Model Confidence:</span>
                <span className="font-bold text-slate-900">{certData.confidence}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-2">
                <span className="text-slate-500">Defect Ratio:</span>
                <span className="font-bold text-slate-900">{certData.blemish_defect_pct}</span>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-2">
                <span className="text-slate-500">Issued Timestamp:</span>
                <span className="font-medium text-slate-700">{new Date(certData.issued_at).toLocaleString()}</span>
              </div>

              {/* Disclaimer */}
              <p className="text-[10px] text-slate-400 italic bg-slate-50 p-2.5 rounded-xl border border-slate-200 leading-normal">
                {language === 'or' ? certData.disclaimer_or : certData.disclaimer_en}
              </p>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between pt-2 border-t border-slate-200">
              <button
                onClick={() => window.print()}
                className="bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs px-3.5 py-2 rounded-xl"
              >
                Print / PDF
              </button>
              <button
                onClick={() => setShowCertificate(false)}
                className="bg-primary hover:bg-primary-dark text-white font-bold text-xs px-4 py-2 rounded-xl transition-colors"
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
