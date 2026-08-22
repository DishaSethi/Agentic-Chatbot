import { useState } from 'react';
import { Loader2, Play, Link } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { evaluateArchitecture } from '../api';

const EvaluatorTab = () => {
  const [userArchitecture, setUserArchitecture] = useState('');
  const [evalResult, setEvalResult] = useState(null);
  const [isEvaluating, setIsEvaluating] = useState(false);

  const handleEvaluate = async () => {
    if (!userArchitecture) return;

    setIsEvaluating(true);
    setEvalResult(null);
    try {
      const data = await evaluateArchitecture(userArchitecture);
      setEvalResult(data);
    } catch (error) {
      console.error("Evaluation failed:", error);
      alert("API Error. Check console");
    }
    setIsEvaluating(false);
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
        <h2 className="text-xl font-semibold mb-2">Architecture Evaluator (RAG)</h2>
        <p className="text-slate-400 text-sm mb-4">
          Paste your system architecture here. The AI will cross-reference it against Neon DB best practices.
        </p>

        <textarea
          className="w-full bg-slate-950 border border-slate-800 rounded-lg p-4 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors resize-none h-40 font-mono text-sm"
          placeholder="e.g. I am using a monolithic Node server with local PostgreSQL and no Redis cache..."
          value={userArchitecture}
          onChange={(e) => setUserArchitecture(e.target.value)}
        />

        <div className="mt-4 flex justify-end">
          <button
            onClick={handleEvaluate}
            disabled={isEvaluating || !userArchitecture}
            className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-lg font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {isEvaluating ? <Loader2 className="animate-spin" size={18} /> : <Play size={18} />}
            {isEvaluating ? 'Evaluating Vector DB...' : 'Evaluate System'}
          </button>
        </div>
      </div>

      {evalResult && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 shadow-xl animate-in fade-in">
          <div className="mb-6 inline-flex items-center gap-2 bg-slate-950 border border-slate-800 px-4 py-2 rounded-full">
            <span className="text-slate-400 text-sm">Neon DB Rules Matched:</span>
            <span className="text-blue-400 font-bold">{evalResult.matched_rules_count}</span>
          </div>

          <div className="prose prose-invert max-w-none prose-headings:text-blue-400">
            <ReactMarkdown>{evalResult.evaluation_scorecard}</ReactMarkdown>
          </div>

          {evalResult?.citations && evalResult.citations.length > 0 && (
            <div className="mt-8 pt-6 border-t border-slate-800">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                <Link size={16} />
                Engineering Standards Applied
              </h3>
              <div className="flex flex-wrap gap-2">
                {evalResult.citations.map((cite, index) => (
                  <a
                    key={index}
                    href={cite.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-3 py-1.5 bg-slate-950 hover:bg-slate-800 border border-slate-800 hover:border-blue-500/50 text-slate-300 hover:text-blue-400 rounded-md text-xs font-medium transition-colors group cursor-pointer"
                  >
                    <span className="bg-slate-800 group-hover:bg-blue-900/50 text-slate-500 group-hover:text-blue-500 px-1.5 py-0.5 rounded text-[10px] font-bold">
                      REF
                    </span>
                    {cite.title}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EvaluatorTab;