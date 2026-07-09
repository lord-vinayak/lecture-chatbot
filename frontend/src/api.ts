import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Video {
  id: string;
  title: string;
  instructor_id: string;
  transcription_status: 'pending' | 'completed' | 'failed';
  transcription_progress: number;
  transcript_text?: string;
  upload_date: string;
  file_path: string;
}

export interface ChatResponse {
  id: string;
  video_id: string;
  user_id: string;
  question: string;
  answer: string;
  source_chunks?: string[];
  created_at: string;
}

export const uploadVideo = async (
  file: File,
  title: string,
  instructorId: string,
  onProgress?: (percent: number) => void
): Promise<Video> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', title);
  formData.append('instructor_id', instructorId);

  const response = await api.post<Video>('/videos/upload', formData, {
    headers: { 'Content-Type': undefined },
    onUploadProgress: (event) => {
      if (onProgress && event.total) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    },
  });

  return response.data;
};

export const getVideo = async (videoId: string): Promise<Video> => {
  const response = await api.get<Video>(`/videos/${videoId}`);
  return response.data;
};

export const askQuestion = async (
  videoId: string,
  question: string,
  userId: string = 'anonymous'
): Promise<ChatResponse> => {
  const response = await api.post<ChatResponse>(
    `/chats/${videoId}/ask`,
    { question },
    { params: { user_id: userId } }
  );
  return response.data;
};

export const healthCheck = async (): Promise<{ status: string }> => {
  const response = await api.get('/health');
  return response.data;
};
