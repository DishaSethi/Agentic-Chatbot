import axios from 'axios';

const api=axios.create(
    {
        baseURL:'http://localhost:8000/api',
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

