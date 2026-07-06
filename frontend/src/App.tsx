import React, { useState, useEffect } from 'react';
import { VideoPlayer } from './VideoPlayer';
import { ChatBox } from './ChatBox';
import { Video, getVideo, healthCheck } from './api';
import './App.css';

const App: React.FC = () => {
  const [currentVideo, setCurrentVideo] = useState<Video | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Check backend connection on mount
    healthCheck()
      .then(() => setIsConnected(true))
      .catch(() => setIsConnected(false));
  }, []);

  const handleVideoLoaded = async (video: Video) => {
    setCurrentVideo(video);

    // Poll for transcription status
    const pollInterval = setInterval(async () => {
      try {
        const updated = await getVideo(video.id);
        setCurrentVideo(updated);

        if (updated.transcription_status !== 'pending') {
          clearInterval(pollInterval);
        }
      } catch (error) {
        console.error('Failed to check transcription status:', error);
      }
    }, 3000); // Poll every 3 seconds
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
