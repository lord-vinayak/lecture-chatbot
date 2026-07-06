import React, { useState, useEffect, useRef } from 'react';
import { VideoPlayer } from './VideoPlayer';
import { ChatBox } from './ChatBox';
import { Video, getVideo, healthCheck } from './api';
import './App.css';

const App: React.FC = () => {
  const [currentVideo, setCurrentVideo] = useState<Video | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    // Check backend connection on mount
    healthCheck()
      .then(() => setIsConnected(true))
      .catch(() => setIsConnected(false));
  }, []);

  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  const handleVideoLoaded = async (video: Video) => {
    setCurrentVideo(video);

    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

    // Poll for transcription status
    pollIntervalRef.current = setInterval(async () => {
      try {
        const updated = await getVideo(video.id);
        setCurrentVideo(updated);

        if (updated.transcription_status !== 'pending') {
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
      } catch (error) {
        console.error('Failed to check transcription status:', error);
      }
    }, 3000);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>📹 Video Course Q&A</h1>
        <div className="connection-status">
          {isConnected ? (
            <span className="status-ok">✓ Connected</span>
          ) : (
            <span className="status-error">✗ Backend unavailable</span>
          )}
        </div>
      </header>

      <div className="app-content">
        <VideoPlayer
          currentVideo={currentVideo}
          onVideoLoaded={handleVideoLoaded}
        />
        <ChatBox video={currentVideo} />
      </div>
    </div>
  );
};

export default App;
