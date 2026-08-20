import { useState } from 'react';
import { planArchitecture, generateArchitecture, fetchDocumentById } from './api';

import Navbar from './components/Navbar';
import GeneratorTab from './components/GeneratorTab';
import EvaluatorTab from './components/EvaluatorTab';
import HistoryTab from './components/HistoryTab';

function App() {
  const [activeTab, setActiveTab] = useState('generator');

  // Shared generator state (kept here so History can override it)
  const [prompt, setPrompt] = useState('');
  const [planData, setPlanData] = useState(null);
  const [finalDoc, setFinalDoc] = useState(null);

  const [isPlanning, setIsPlanning] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const handlePlan = async () => {
    if (!prompt) return;
    setIsPlanning(true);
    setPlanData(null);
    setFinalDoc(null);
    try {
      const data = await planArchitecture(prompt);
      setPlanData(data);
    } catch (error) {
      console.error("Planning failed:", error);
      alert("API Error. Check console.");
    }
    setIsPlanning(false);
  };

  const handleApprove = async () => {
    if (!planData?.thread_id) return;
    setIsGenerating(true);
    try {
      const data = await generateArchitecture(planData.thread_id, prompt);
      setFinalDoc(data.markdown);
    } catch (error) {
      console.error("Generation failed:", error);
      alert("API Error. Check console.");
    }
    setIsGenerating(false);
  };

  const handleViewPastDocument = async (id, topic) => {
    try {
      const data = await fetchDocumentById(id);
      // Pre-fill the generator tab with the history document
      setPlanData({ system_title: topic, tasks: [] });
      setFinalDoc(data.markdown);
      setActiveTab('generator');
    } catch (error) {
      console.error("Failed to load document:", error);
      alert("Could not load the document");
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-blue-500/30">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="max-w-5xl mx-auto p-6 mt-6">
        {activeTab === 'generator' && (
          <GeneratorTab
            prompt={prompt}
            setPrompt={setPrompt}
            planData={planData}
            finalDoc={finalDoc}
            isPlanning={isPlanning}
            isGenerating={isGenerating}
            handlePlan={handlePlan}
            handleApprove={handleApprove}
          />
        )}

        {activeTab === 'evaluator' && <EvaluatorTab />}

        {activeTab === 'history' && (
          <HistoryTab onSelectDocument={handleViewPastDocument} />
        )}
      </main>
    </div>
  );
}

export default App;