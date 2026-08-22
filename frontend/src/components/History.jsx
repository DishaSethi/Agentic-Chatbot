import { useState, useEffect } from 'react';
import { History, Loader2, Layout } from 'lucide-react';
import { fetchHistory } from '../api';

const HistoryTab = ({ onSelectDocument }) => {
  const [historyList, setHistoryList] = useState([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setIsLoadingHistory(true);
    try {
      const response = await fetchHistory();
      let safeArray = [];

      if (Array.isArray(response)) safeArray = response;
      else if (response && Array.isArray(response.data)) safeArray = response.data;
      else if (response?.data?.history) safeArray = response.data.history;

      if (safeArray.length === 0) {
         console.warn("The backend returned data, but the array is empty!");
      }
      setHistoryList(safeArray);
    } catch (error) {
      console.error("Failed to load history:", error);
      alert("Network Error! Check console.");
      setHistoryList([]);
    }
    setIsLoadingHistory(false);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl animate-in fade-in">
      <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
        <History size={20} className="text-blue-400" />
        Past Architectures ({Array.isArray(historyList) ? historyList.length : 0})
      </h2>

      {isLoadingHistory ? (
        <div className="flex flex-col items-center justify-center py-12 text-slate-400">
          <Loader2 className="animate-spin mb-2" size={24} />
          <p>Loading database records...</p>
        </div>
      ) : Array.isArray(historyList) && historyList.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {historyList.map((doc, index) => (
            <div
              key={doc?.id || index}
              onClick={() => onSelectDocument(doc?.id, doc?.topic)}
              className="bg-slate-950 border border-slate-800 hover:border-blue-500/50 p-4 rounded-lg cursor-pointer transition-all hover:shadow-lg hover:shadow-blue-900/10 group flex items-start gap-3"
            >
              <div className="bg-slate-800 text-blue-400 p-2 rounded-md group-hover:bg-blue-600 group-hover:text-white transition-colors">
                <Layout size={18} />
              </div>
              <div>
                <h3 className="text-slate-200 font-medium line-clamp-2 text-sm leading-snug">{doc?.topic || "Unknown Topic"}</h3>
                <p className="text-slate-500 text-xs mt-1">ID: #{doc?.id || "N/A"}</p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 text-slate-500 overflow-x-auto">
          <History size={48} className="mx-auto mb-3 opacity-20" />
          <p>No architectures saved yet (or data format error).</p>
        </div>
      )}
    </div>
  );
};

export default HistoryTab;