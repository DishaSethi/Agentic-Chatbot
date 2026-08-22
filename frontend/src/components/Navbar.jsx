import { Layout, CheckSquare, Hammer, History } from 'lucide-react';

const Navbar = ({ activeTab, setActiveTab }) => {
  return (
    <nav className="border-b border-slate-800 bg-slate-900 p-4 sticky top-0 z-50">
      <div className="max-w-5xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2 text-blue-400">
          <Layout size={24} />
          <h1 className="text-xl font-bold tracking-wide">AI Architect</h1>
        </div>
        <div className="flex gap-2 bg-slate-950 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setActiveTab('generator')}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'generator' ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/20' : 'text-slate-400 hover:text-slate-200'}`}
          >
            <Hammer size={16} /> Designer
          </button>

          <button
            onClick={() => setActiveTab('evaluator')}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'evaluator' ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/20' : 'text-slate-400 hover:text-slate-200'}`}
          >
            <CheckSquare size={16} />Grade my answer
          </button>

          <button
            onClick={() => setActiveTab('history')}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'history' ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/20' : 'text-slate-400 hover:text-slate-200'}`}
          >
            <History size={16} /> History
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;