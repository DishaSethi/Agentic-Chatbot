import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : 'http://localhost:8000/api';

const api=axios.create(
    {
        baseURL:API_BASE_URL,
    }
);


export const planArchitecture=async(userPrompt)=>{
    const response=await api.post('/plan',{topic:userPrompt});
    return response.data;
};



export const generateArchitecture=async(threadId,userTopic)=>{
    const response=await api.post('/generate',{thread_id:threadId,topic:userTopic});
    return response.data;
};


export const evaluateArchitecture=async(userArchitecture)=>{
    const response=await api.post('/evaluate',{user_architecture:userArchitecture});
    return response.data;
}



export const fetchHistory=async()=>{
    const response=await api.get('/history');
    return response.data;
}

export const fetchDocumentById=async(docId)=>{
    const response=await api.get(`/history/${docId}`);
    return response.data;
};