import { Copy, Download, Loader2, Play, CheckSquare } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import MermaidDisplay from './MermaidDisplay';

const GeneratorTab = ({ prompt, setPrompt, planData, finalDoc, isPlanning, isGenerating, handlePlan, handleApprove }) => {

  const handleCopy = () => {
    navigator.clipboard.writeText(finalDoc);
    alert("Markdown copied! Paste this into Google Docs.");
  };

  const handleDownload = () => {
    const blob = new Blob([finalDoc], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${planData?.system_title?.replace(/\s+/g, '_') || 'architecture'}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Input Section */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
        <h2 className="text-xl font-semibold mb-2">Design a New System</h2>
        <p className="text-slate-400 text-sm mb-4">
          Describe the application you want to build. The agents will research and draft a plan.
        </p>

        <textarea
          className="w-full bg-slate-950 border border-slate-800 rounded-lg p-4 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors resize-none h-28"
          placeholder="e.g. A real-time multiplayer chess engine using websockets..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        />
        <div className="mt-4 flex justify-end">
          <button
            onClick={handlePlan}
            disabled={isPlanning || !prompt}
            className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-lg font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {isPlanning ? <Loader2 className="animate-spin" size={18} /> : <Play size={18} />}
            {isPlanning ? 'Researching & Planning...' : 'Generate Plan'}
          </button>
        </div>
      </div>

      {/* Planning Review Section */}
      {planData && !finalDoc && (
        <div className="bg-slate-900 border border-indigo-900/50 rounded-xl p-6 shadow-xl animate-in fade-in slide-in-from-bottom-4">
          <div className="flex items-center justify-between mb-6">
            <div>
              <span className="text-indigo-400 text-xs font-bold uppercase tracking-wider mb-1 block">Review Required</span>
              <h3 className="text-2xl font-bold">{planData.system_title}</h3>
            </div>
            <button
              onClick={handleApprove}
              disabled={isGenerating}
              className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2 rounded-lg font-medium flex items-center gap-2 disabled:opacity-50 transition-all shadow-lg shadow-emerald-900/20"
            >
              {isGenerating ? <Loader2 className="animate-spin" size={18} /> : <CheckSquare size={18} />}
              {isGenerating ? 'Drafting Document...' : 'Approve & Write Document'}
            </button>
          </div>

          <h4 className="text-slate-400 font-medium mb-3">Planned Sections:</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {planData.tasks.map((task, i) => (
              <div key={i} className="bg-slate-950 border border-slate-800 rounded-lg p-3 flex items-start gap-3">
                <div className="bg-slate-800 text-slate-300 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0">{i + 1}</div>
                <div>
                  <p className="text-slate-200 text-sm leading-relaxed">{task.title}</p>
                  <p className="text-slate-400 text-xs mt-1">{task.goal}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Final Document Render Section */}
      {finalDoc && (
        <div className="mt-12 animate-in fade-in slide-in-from-bottom-4">
          <div className="flex justify-end gap-3 mb-4 max-w-4xl mx-auto">
            <button onClick={handleCopy} className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 py-2 rounded-lg text-sm font-medium transition-colors">
              <Copy size={16} /> Copy for Google Docs
            </button>
            <button onClick={handleDownload} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors shadow-lg shadow-blue-900/20">
              <Download size={16} /> Download .md
            </button>
          </div>

          <div className="prose prose-slate prose-blue max-w-none prose-headings:font-bold prose-h1:text-4xl prose-h2:text-2xl prose-h2:border-b prose-h2:pb-2 prose-h2:mt-10">
            <ReactMarkdown
              components={{
                code(props) {
                  const { children, className, node, ...rest } = props;
                  const match = /language-(\w+)/.exec(className || '');

                  // 1. Render Mermaid diagrams
                  if (match && match[1] === 'mermaid') {
                    return <MermaidDisplay chart={String(children).replace(/\n$/, '')} />;
                  }

                  // 2. Render standard dark-mode code blocks
                  if (match) {
                    return (
                      <code className="block bg-slate-900 text-slate-300 rounded-lg p-4 my-6 overflow-x-auto text-sm font-mono shadow-inner not-prose" {...rest}>
                        {children}
                      </code>
                    );
                  }

                  // 3. Render inline code highlighting
                  return (
                    <code className="bg-slate-100 text-pink-600 px-1.5 py-0.5 rounded text-sm font-mono border border-slate-200" {...rest}>
                      {children}
                    </code>
                  );
                }
              }}
            >
              {finalDoc}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
};

export default GeneratorTab;